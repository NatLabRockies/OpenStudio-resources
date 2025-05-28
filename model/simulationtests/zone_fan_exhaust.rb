# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 3 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add ASHRAE System type 08, VAV w/ PFP Boxes
model.add_hvac({ 'ashrae_sys_num' => '08' })

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = model.getThermalZones.sort_by { |z| z.name.to_s }

# find all the zones
north_zone = nil
east_zone = nil
south_zone = nil
west_zone = nil
core_zone = nil
zones.each do |zone|
  case zone.name.to_s
  when /North/
    north_zone = zone
  when /East/
    east_zone = zone
  when /South/
    south_zone = zone
  when /West/
    west_zone = zone
  when /Core/
    core_zone = zone
  end
end

# add exhaust fan to north zone
# exhaust_rate = 1.71187 # calc heating design rate
# exhaust_rate = 1.61 # 5 ACH
# exhaust_rate = 0.047 # 100 cfm
exhaust_rate = 0.17

exhaust = OpenStudio::Model::FanZoneExhaust.new(model)
exhaust.addToThermalZone(north_zone)
exhaust.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule)
exhaust.setMaximumFlowRate(exhaust_rate)
exhaust.setFlowFractionSchedule(model.alwaysOnContinuousSchedule)
exhaust.setBalancedExhaustFractionSchedule(model.alwaysOnContinuousSchedule)

# add mixing air from core zone to north zone
m = OpenStudio::Model::ZoneMixing.new(north_zone)
m.setSourceZone(core_zone)
m.setDesignFlowRate(exhaust_rate)
m.setSchedule(model.alwaysOnContinuousSchedule)

# add mixing air from east, south, and west zones to core zone
m = OpenStudio::Model::ZoneMixing.new(core_zone)
m.setSourceZone(east_zone)
m.setDesignFlowRate(exhaust_rate / 3.0)
m.setSchedule(model.alwaysOnContinuousSchedule)

m = OpenStudio::Model::ZoneMixing.new(core_zone)
m.setSourceZone(south_zone)
m.setDesignFlowRate(exhaust_rate / 3.0)
m.setSchedule(model.alwaysOnContinuousSchedule)

m = OpenStudio::Model::ZoneMixing.new(core_zone)
m.setSourceZone(west_zone)
m.setDesignFlowRate(exhaust_rate / 3.0)
m.setSchedule(model.alwaysOnContinuousSchedule)

# conserve some mass
zamfc = model.getZoneAirMassFlowConservation
zamfc.setAdjustZoneMixingForZoneAirMassFlowBalance(true)
if Gem::Version.new(OpenStudio.openStudioVersion) <= Gem::Version.new('3.4.0')
  # Does nothing as of 1.9.3, removed after 3.4.0
  zamfc.setSourceZoneInfiltrationTreatment('AddInfiltrationFlow')
end

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# add zone exhaust
zones.each do |z|
  # TODO: given the above comment "add zone exhaust", it looks like it's
  # missing the actual zone exhaust object...
  puts z
end

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# add output reports
add_out_vars = false
if add_out_vars
  OpenStudio::Model::OutputVariable.new('Zone Mixing Volume', model)
  OpenStudio::Model::OutputVariable.new('Zone Supply Air Mass Flow Rate', model)
  OpenStudio::Model::OutputVariable.new('Zone Exhaust Air Mass Flow Rate', model)
  OpenStudio::Model::OutputVariable.new('Zone Return Air Mass Flow Rate', model)
  OpenStudio::Model::OutputVariable.new('Zone Mixing Receiving Air Mass Flow Rate', model)
  OpenStudio::Model::OutputVariable.new('Zone Mixing Source Air Mass Flow Rate', model)
  OpenStudio::Model::OutputVariable.new('Zone Infiltration Air Mass Flow Balance Status', model)
  OpenStudio::Model::OutputVariable.new('Zone Mass Balance Infiltration Air Mass Flow Rate', model)
  OpenStudio::Model::OutputVariable.new('System Node Mass Flow Rate', model)
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
