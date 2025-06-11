# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 2 story, 100m X 50m, 2 zone building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 2,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 0 })

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

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = model.getThermalZones.sort_by { |z| z.name.to_s }
zone1 = zones[0]
zone2 = zones[1]

# Outdoor Air Systems
controller1 = OpenStudio::Model::ControllerOutdoorAir.new(model)
oas1 = OpenStudio::Model::AirLoopHVACOutdoorAirSystem.new(model, controller1)
airloop1 = OpenStudio::Model::AirLoopHVAC.new(model)
airloop1.setName('LOOP1')
supplyOutletNode1 = airloop1.supplyOutletNode
oas1.addToNode(supplyOutletNode1)
fan1 = OpenStudio::Model::FanVariableVolume.new(model)
fan1.addToNode(supplyOutletNode1)
atu1 = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, model.alwaysOnDiscreteSchedule)
airloop1.addBranchForZone(zone1, atu1)
oas1.outboardOANode.get.setName("#{airloop1.nameString} OA Inlet Node")
oas1.outboardReliefNode.get.setName("#{airloop1.nameString} Exhaust Node")

# Outdoor Air System 2
controller2 = OpenStudio::Model::ControllerOutdoorAir.new(model)
oas2 = OpenStudio::Model::AirLoopHVACOutdoorAirSystem.new(model, controller2)
airloop2 = OpenStudio::Model::AirLoopHVAC.new(model)
airloop2.setName('LOOP2')
supplyOutletNode2 = airloop2.supplyOutletNode
oas2.addToNode(supplyOutletNode2)
fan2 = OpenStudio::Model::FanVariableVolume.new(model)
fan2.addToNode(supplyOutletNode2)
atu2 = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, model.alwaysOnDiscreteSchedule)
airloop2.addBranchForZone(zone2, atu2)
oas2.outboardOANode.get.setName("#{airloop2.nameString} OA Inlet Node")
oas2.outboardReliefNode.get.setName("#{airloop2.nameString} Exhaust Node")

# Dedicated Outdoor Air System
controller = OpenStudio::Model::ControllerOutdoorAir.new(model) # this won't be translated
oas = OpenStudio::Model::AirLoopHVACOutdoorAirSystem.new(model, controller)
doas = OpenStudio::Model::AirLoopHVACDedicatedOutdoorAirSystem.new(oas)
doas.addAirLoop(airloop1)
doas.addAirLoop(airloop2)

# Equipment
coil_cooling_water = OpenStudio::Model::CoilCoolingWater.new(model)
coil_heating_water = OpenStudio::Model::CoilHeatingWater.new(model)
fan = OpenStudio::Model::FanSystemModel.new(model)
coil_cooling_water.addToNode(oas.outboardOANode.get)
coil_heating_water.addToNode(oas.outboardOANode.get)
fan.addToNode(oas.outboardOANode.get)
oas.outboardOANode.get.setName("#{oas.nameString} OA Inlet Node")
fan.outletModelObject.get.setName("#{oas.nameString} Fan Outlet Node")
coil_heating_water.airOutletModelObject.get.setName("#{oas.nameString} HC Outlet Node")
coil_cooling_water.airOutletModelObject.get.setName("#{oas.nameString} CC Outlet Node")

lat_temp_f = 70.0
lat_temp_c = OpenStudio.convert(lat_temp_f, 'F', 'C').get
lat_temp_sch = OpenStudio::Model::ScheduleRuleset.new(model)
lat_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), lat_temp_c)
lat_stpt_manager1 = OpenStudio::Model::SetpointManagerScheduled.new(model, lat_temp_sch)
lat_stpt_manager1.addToNode(coil_cooling_water.airOutletModelObject.get.to_Node.get)
lat_stpt_manager2 = lat_stpt_manager1.clone(model).to_SetpointManagerScheduled.get
lat_stpt_manager2.addToNode(coil_heating_water.airOutletModelObject.get.to_Node.get)

lat_stpt_manager3 = lat_stpt_manager1.clone(model).to_SetpointManagerScheduled.get
lat_stpt_manager3.addToNode(supplyOutletNode1)

lat_stpt_manager4 = lat_stpt_manager1.clone(model).to_SetpointManagerScheduled.get
lat_stpt_manager4.addToNode(supplyOutletNode2)

# Chilled Water Plant
chw_loop = OpenStudio::Model::PlantLoop.new(model)
chw_loop.setMaximumLoopTemperature(98)
chw_loop.setMinimumLoopTemperature(1)
chw_temp_f = 44
chw_delta_t_r = 10.1 # 10.1F delta-T
chw_temp_c = OpenStudio.convert(chw_temp_f, 'F', 'C').get
chw_delta_t_k = OpenStudio.convert(chw_delta_t_r, 'R', 'K').get
chw_temp_sch = OpenStudio::Model::ScheduleRuleset.new(model)
chw_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), chw_temp_c)
chw_stpt_manager = OpenStudio::Model::SetpointManagerScheduled.new(model, chw_temp_sch)
chw_stpt_manager.addToNode(chw_loop.supplyOutletNode)
sizing_plant = chw_loop.sizingPlant
sizing_plant.setLoopType('Cooling')
sizing_plant.setDesignLoopExitTemperature(chw_temp_c)
sizing_plant.setLoopDesignTemperatureDifference(chw_delta_t_k)
chw_pump = OpenStudio::Model::PumpVariableSpeed.new(model)
chw_pump.addToNode(chw_loop.supplyInletNode)
chw_loop.addDemandBranchForComponent(coil_cooling_water)
chiller = OpenStudio::Model::ChillerElectricEIR.new(model)
chw_loop.addSupplyBranchForComponent(chiller)

# Hot Water Plant
hw_loop = OpenStudio::Model::PlantLoop.new(model)
hw_loop.setMinimumLoopTemperature(10)
hw_temp_f = 140
hw_delta_t_r = 20 # 20F delta-T
hw_temp_c = OpenStudio.convert(hw_temp_f, 'F', 'C').get
hw_delta_t_k = OpenStudio.convert(hw_delta_t_r, 'R', 'K').get
hw_temp_sch = OpenStudio::Model::ScheduleRuleset.new(model)
hw_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), hw_temp_c)
hw_stpt_manager = OpenStudio::Model::SetpointManagerScheduled.new(model, hw_temp_sch)
hw_stpt_manager.addToNode(hw_loop.supplyOutletNode)
sizingPlant = hw_loop.sizingPlant
sizingPlant.setLoopType('Heating')
sizingPlant.setDesignLoopExitTemperature(82.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)
hw_pump = OpenStudio::Model::PumpVariableSpeed.new(model)
hw_pump.addToNode(hw_loop.supplyInletNode)
hw_loop.addDemandBranchForComponent(coil_heating_water)
boiler = OpenStudio::Model::BoilerHotWater.new(model)
hw_loop.addSupplyBranchForComponent(boiler)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd, 'osm_name' => 'in.osm' })
