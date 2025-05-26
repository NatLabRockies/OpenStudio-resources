# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 5 zone building, all zones are equally sized
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 5,
                     'floor_to_floor_height' => 3,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 0 })

# NOTE: Make all spaces under a single zone
model.getThermalZones.each(&:remove)
z = OpenStudio::Model::ThermalZone.new(model)
z.setName('Zone with 5 Spaces')
model.getSpaces.each { |s| s.setThermalZone(z) }

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# Add ASHRAE System type 07, VAV w/ Reheat, this creates a ChW, a HW loop and a
# Condenser Loop
model.add_hvac({ 'ashrae_sys_num' => '07' })

raise 'Expected 1 thermal zone' unless model.getThermalZones.size == 1
raise 'Expected 5 spaces' unless model.getSpaces.size == 5
raise 'Expected 1 air loop' unless model.getAirLoopHVACs.size == 1

air_loop = model.getAirLoopHVACs.first
raise 'Expected 1 VAV terminal with reheat' unless model.getAirTerminalSingleDuctVAVReheats.size == 1

atu = model.getAirTerminalSingleDuctVAVReheats.first
raise 'Failed to setControlForOutdoorAir' unless atu.setControlForOutdoorAir(true)

# In order to produce more consistent results between different runs,
# we sort the spaces by names
spaces = model.getSpaces.sort_by(&:nameString)

model.getDesignSpecificationOutdoorAirs.each(&:remove)

# Create a Design Specification Outdoor Air for each space, but the last one
spaces[0..-2].each do |space|
  # Create a Design Specification Outdoor Air object for each space
  # We set it as an absolute outdoor air flow rate but as 0.01 m3/s per m2 of floor area
  dsoa = OpenStudio::Model::DesignSpecificationOutdoorAir.new(model)
  dsoa.setOutdoorAirFlowRate(0.01 * space.floorArea)
  dsoa.setName("#{space.nameString} DSOA")
  space.setDesignSpecificationOutdoorAir(dsoa)
  # puts "For '#{space.nameString()}' created '#{dsoa.nameString()}'")
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
