# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 1,
                     'perimeter_zone_depth' => 3 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add ASHRAE System type 03, PSZ-AC
model.add_hvac({ 'ashrae_sys_num' => '03' })

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = model.getThermalZones.sort_by { |z| z.name.to_s }

## hot water system
# zone = zones.first
# plant = OpenStudio::Model::PlantLoop.new(model)
# pump = OpenStudio::Model::PumpConstantSpeed.new(model)
# pump.addToNode(plant.supplyInletNode())

# hot_water_heater = OpenStudio::Model::WaterHeaterHeatPump.new(model)
# hot_water_heater.addToThermalZone(zone)
# tank = hot_water_heater.tank()
# plant.addSupplyBranchForComponent(tank)
#
# hot_water_heater = OpenStudio::Model::WaterHeaterHeatPump.new(model)
# tank = hot_water_heater.tank()
# plant.addSupplyBranchForComponent(tank)
#
# hot_water_temp_sch = OpenStudio::Model::ScheduleRuleset.new(model)
# hot_water_temp_sch.setName("Hot_Water_Temperature")
# hot_water_temp_sch.defaultDaySchedule().addValue(OpenStudio::Time.new(0,24,0,0),55.0)
# hot_water_spm = OpenStudio::Model::SetpointManagerScheduled.new(model,hot_water_temp_sch)
# hot_water_spm.addToNode(plant.supplyOutletNode())
#
# water_connections = OpenStudio::Model::WaterUseConnections.new(model)
# plant.addDemandBranchForComponent(water_connections)
# water_def = OpenStudio::Model::WaterUseEquipmentDefinition.new(model)
# water_equipment = OpenStudio::Model::WaterUseEquipment.new(water_def)
# water_connections.addWaterUseEquipment(water_equipment)

# hot water system 2
zone = zones.first
plant = OpenStudio::Model::PlantLoop.new(model)
pump = OpenStudio::Model::PumpConstantSpeed.new(model)
pump.addToNode(plant.supplyInletNode)

hot_water_heater = OpenStudio::Model::WaterHeaterHeatPumpWrappedCondenser.new(model)
hot_water_heater.addToThermalZone(zone)
tank = hot_water_heater.tank
plant.addSupplyBranchForComponent(tank)

# hot_water_heater = OpenStudio::Model::WaterHeaterHeatPumpWrappedCondenser.new(model)
# tank = hot_water_heater.tank()
# plant.addSupplyBranchForComponent(tank)

hot_water_temp_sch = OpenStudio::Model::ScheduleRuleset.new(model)
hot_water_temp_sch.setName('Hot_Water_Temperature')
hot_water_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 55.0)
hot_water_spm = OpenStudio::Model::SetpointManagerScheduled.new(model, hot_water_temp_sch)
hot_water_spm.addToNode(plant.supplyOutletNode)

water_connections = OpenStudio::Model::WaterUseConnections.new(model)
plant.addDemandBranchForComponent(water_connections)
water_def = OpenStudio::Model::WaterUseEquipmentDefinition.new(model)
water_equipment = OpenStudio::Model::WaterUseEquipment.new(water_def)
water_connections.addWaterUseEquipment(water_equipment)

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
