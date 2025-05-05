# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

m = BaselineModel.new

# make a 1 story, 100m X 50m, 1 zone core/perimeter building
m.add_geometry({ 'length' => 100,
                 'width' => 50,
                 'num_floors' => 1,
                 'floor_to_floor_height' => 4,
                 'plenum_height' => 1,
                 'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
m.add_windows({ 'wwr' => 0.4,
                'offset' => 1,
                'application_type' => 'Above Floor' })

# add thermostats
m.add_thermostats({ 'heating_setpoint' => 24,
                    'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type

# add design days to the model (Chicago)
m.add_design_days

# add ASHRAE System type 07, VAV w/ Reheat
m.add_hvac({ 'ashrae_sys_num' => '07' })

# In order to produce more consistent results between different runs,
# we sort the zones by names (only one here anyways...)
zones = m.getThermalZones.sort_by { |z| z.name.to_s }

### Water Side Economizer Model ###

zone = zones[0]
airloop = zone.airLoopHVAC.get
airloop.setName('AirLoopHVAC CoilSystemCoolingWater')

# create a CoilSystemCoolingWater object
coil_system = OpenStudio::Model::CoilSystemCoolingWater.new(m)
coil_system.setName('CoilSystemCoolingWater WaterSide')

water_coil = coil_system.coolingCoil.to_CoilCoolingWater.get
water_coil.setName('CoilSystemCoolingWater WaterSide CoolingCoil')

# As a water-side economizer the CoilSystem:Cooling:Water object is placed upstream of packaged DX systems or chilled water main cooling coil
# We have a Chilled water coil already, so let's keep it
coil = airloop.supplyComponents(OpenStudio::Model::CoilCoolingWater.iddObjectType).first.to_CoilCoolingWater.get
coil.setName('Central ChW Coil')

# Note that we connect the CoilSystem, NOT the underlying CoilCoolingWater
coil_system.addToNode(coil.airInletModelObject.get.to_Node.get)
plant = coil.plantLoop.get
# But we have to connect the water_coil itself. Ideally this would be on a Condenser Loop, so let's get it
cts = m.getCoolingTowerSingleSpeeds.sort_by { |c| c.name.to_s }
condenser_loop = cts.first.plantLoop.get
condenser_loop.addDemandBranchForComponent(water_coil)

# Rename some nodes and such, for ease of debugging
airloop.supplyInletNode.setName("#{airloop.nameString} Supply Inlet Node")
airloop.supplyOutletNode.setName("#{airloop.nameString} Supply Outlet Node")
airloop.mixedAirNode.get.setName("#{airloop.nameString} Mixed Air Node")
coil_system.outletModelObject.get.to_Node.get.setName("#{coil_system.nameString} Outlet to #{coil.nameString} Inlet Node")

water_coil.waterInletModelObject.get.setName("#{water_coil.nameString} Water Inlet Node")
water_coil.waterOutletModelObject.get.setName("#{water_coil.nameString} Water Outlet Node")
# water_coil.controllerWaterCoil.get.setName("#{water_coil.name} Controller")

heating_coil = airloop.supplyComponents(OpenStudio::Model::CoilHeatingWater.iddObjectType).first.to_CoilHeatingWater.get
heating_coil.waterInletModelObject.get.setName("#{airloop.nameString} Heating Coil Water Inlet Node")
heating_coil.waterOutletModelObject.get.setName("#{airloop.nameString} Heating Coil Water Outlet Node")
heating_coil.controllerWaterCoil.get.setName("#{airloop.nameString} Heating Coil Controller")
heating_coil.airOutletModelObject.get.setName("#{airloop.nameString} Heating Coil Air Outlet to Fan Inlet Node")

######

### Wrap Around Water Coil Heat Recovery Mode ###

# create heat recovery plant loop
hr_loop = OpenStudio::Model::PlantLoop.new(m)
hr_loop.setName('Run Around Coil HR Loop')

plant_siz = hr_loop.sizingPlant
plant_siz.setLoopType('Cooling')
plant_siz.setDesignLoopExitTemperature(7)
plant_siz.setLoopDesignTemperatureDifference(4)

# create supply side pump
pump = OpenStudio::Model::PumpVariableSpeed.new(m)
pump.setName('HR Circ Pump')
pump.setCoefficient1ofthePartLoadPerformanceCurve(0)
pump.setCoefficient2ofthePartLoadPerformanceCurve(1)
pump.setCoefficient3ofthePartLoadPerformanceCurve(0)
pump.setCoefficient4ofthePartLoadPerformanceCurve(0)

hr_loop.addSupplyBranchForComponent(pump)

# zone = zones[1]
# airloop = zone.airLoopHVAC.get
# airloop.setName('AirLoopHVAC CoilSystemCoolingWater WrapAround')

oa_sys = airloop.airLoopHVACOutdoorAirSystem.get

# TODO: use a CoilSystemCoolingWaterHeatExchangerAssisted
primary_coil = OpenStudio::Model::CoilCoolingWater.new(m, m.alwaysOnDiscreteSchedule)
primary_coil.setName("#{airloop.name.get} Primary HR Coil")
# primary_coil.setDesignWaterTemperatureDifference(4)

companion_coil = OpenStudio::Model::CoilCoolingWater.new(m, m.alwaysOnDiscreteSchedule)
companion_coil.setName("#{airloop.name.get} Companion HR Coil")
# companion_coil.setDesignWaterTemperatureDifference(4)

coil_sys = OpenStudio::Model::CoilSystemCoolingWater.new(m, primary_coil)
coil_sys.setName('CoilSystemCoolingWater WrapAround')
coil_sys.setCompanionCoilUsedForHeatRecovery(companion_coil)
coil_sys.setMinimumWaterLoopTemperatureForHeatRecovery(3)

coil_sys.addToNode(oa_sys.outboardOANode.get)
companion_coil.addToNode(oa_sys.reliefAirModelObject.get.to_Node.get)

# connect to plant loop
hr_loop.addDemandBranchForComponent(primary_coil)
pipe = OpenStudio::Model::PipeAdiabatic.new(m)
pipe.addToNode(primary_coil.waterOutletModelObject.get.to_Node.get)
companion_coil.addToNode(pipe.outletModelObject.get.to_Node.get)

coil_spm_sch = OpenStudio::Model::ScheduleConstant.new(m)
coil_spm_sch.setName('OA HR Supply Air Temp Sch')
coil_spm_sch.setValue(4.5)

primary_coil_spm = OpenStudio::Model::SetpointManagerScheduled.new(m, coil_spm_sch)
primary_coil_spm.setName('OA Air Temp Manager HR1')
# primary_coil_spm.addToNode(coil_sys.airOutletModelObject.get.to_Node.get)
# primary_coil_spm.addToNode(coil_sys.outletModelObject.get.to_Node.get)

companion_coil_spm = OpenStudio::Model::SetpointManagerScheduled.new(m, coil_spm_sch)
companion_coil_spm.setName('OA Air Temp Manager HR2')
# companion_coil_spm.addToNode(companion_coil.airOutletModelObject.get.to_Node.get)

hr_loop_spm = OpenStudio::Model::SetpointManagerScheduled.new(m, coil_spm_sch)
hr_loop_spm.setName('OA Air Temp Manager HR3')
hr_loop_spm.addToNode(hr_loop.loopTemperatureSetpointNode)

# Rename some nodes and such, for ease of debugging
airloop.supplyInletNode.setName("#{airloop.name} Supply Inlet Node")
airloop.supplyOutletNode.setName("#{airloop.name} Supply Outlet Node")
airloop.mixedAirNode.get.setName("#{airloop.name} Mixed Air Node")
coil_system.outletModelObject.get.to_Node.get.setName("#{airloop.name} Outlet to Heating Coil Inlet Node")

primary_coil.waterInletModelObject.get.setName("#{primary_coil.name} Water Inlet Node")
primary_coil.waterOutletModelObject.get.setName("#{primary_coil.name} Water Outlet Node")
# primary_coil.controllerWaterCoil.get.setName("#{primary_coil.name} Controller")

heating_coil = airloop.supplyComponents(OpenStudio::Model::CoilHeatingWater.iddObjectType).first.to_CoilHeatingWater.get
heating_coil.waterInletModelObject.get.setName("#{airloop.name} Heating Coil Water Inlet Node")
heating_coil.waterOutletModelObject.get.setName("#{airloop.name} Heating Coil Water Outlet Node")
heating_coil.controllerWaterCoil.get.setName("#{airloop.name} Heating Coil Controller")
heating_coil.airOutletModelObject.get.setName("#{airloop.name} Heating Coil Air Outlet to Fan Inlet Node")

######

# save the OpenStudio model (.osm)
m.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                        'osm_name' => 'in.osm' })
