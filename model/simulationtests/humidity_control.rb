# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 2,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 1,
                     'perimeter_zone_depth' => 3 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add ASHRAE System type 03, PSZ-AC
model.add_hvac({ 'ashrae_sys_num' => '03' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# pick out on of the zone/system pairs and add a humidifier
# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = model.getThermalZones.sort_by { |z| z.name.to_s }

# Try out all 3 different types of humidity setpoint managers
# on three different airloops in the same model.
for i in 0..2

  zone = zones[i]

  # Add a humidistat at 50% RH to the zone
  dehumidify_sch = OpenStudio::Model::ScheduleConstant.new(model)
  dehumidify_sch.setValue(50)
  humidistat = OpenStudio::Model::ZoneControlHumidistat.new(model)
  humidistat.setHumidifyingRelativeHumiditySetpointSchedule(dehumidify_sch)
  zone.setZoneControlHumidistat(humidistat)

  air_system = zone.airLoopHVAC.get
  humidifier_outlet_node = nil

  if i == 0
    # Add a humidifier after the gas heating coil and before the fan
    htg_coil = air_system.supplyComponents(OpenStudio::Model::CoilHeatingGas.iddObjectType).first.to_CoilHeatingGas.get
    htg_coil_outlet_node = htg_coil.outletModelObject.get.to_Node.get
    humidifier = OpenStudio::Model::HumidifierSteamElectric.new(model)
    humidifier.addToNode(htg_coil_outlet_node)
    humidifier_outlet_node = humidifier.outletModelObject.get.to_Node.get
  else
    # Add a humidifier after all other components
    humidifier = OpenStudio::Model::HumidifierSteamElectric.new(model)
    humidifier.addToNode(air_system.supplyOutletNode)
    humidifier_outlet_node = humidifier.outletModelObject.get.to_Node.get
  end

  # Try out all 3 different types of humidity setpoint managers
  # by adding them to the humidifier outlet node.
  case i
  when 0
    spm = OpenStudio::Model::SetpointManagerSingleZoneHumidityMinimum.new(model)
    spm.addToNode(humidifier_outlet_node)
  when 1
    spm = OpenStudio::Model::SetpointManagerMultiZoneHumidityMinimum.new(model)
    spm.addToNode(humidifier_outlet_node)
  when 2
    spm = OpenStudio::Model::SetpointManagerMultiZoneMinimumHumidityAverage.new(model)
    spm.addToNode(humidifier_outlet_node)
  end

end

# add output reports
add_out_vars = false
if add_out_vars
  # Request timeseries data for debugging
  reporting_frequency = 'hourly'
  var_names = []
  var_names << 'System Node Setpoint Temperature'
  var_names << 'System Node Setpoint Minimum Humidity Ratio'
  var_names << 'System Node Setpoint Humidity Ratio'
  var_names << 'Zone Mean Air Humidity Ratio'
  var_names << 'Zone Mean Air Temperature'
  var_names << 'Zone Air Relative Humidity'
  var_names << 'Humidifier Water Volume Flow Rate'
  var_names.each do |var_name|
    outputVariable = OpenStudio::Model::OutputVariable.new(var_name, model)
    outputVariable.setReportingFrequency(reporting_frequency)
  end
end
# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
