import openstudio
from lib.baseline_model import BaselineModel

m = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone core/perimeter building
m.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
m.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
m.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type()

# add design days to the model (Chicago)
m.add_design_days()

# add ASHRAE System type 07, VAV w/ Reheat
m.add_hvac(ashrae_sys_num="07")

# In order to produce more consistent results between different runs,
# we sort the zones by names (only one here anyways...)
zones = sorted(m.getThermalZones(), key=lambda z: z.nameString())

### Water Side Economizer Model ###

zone = zones[0]
airloop = zone.airLoopHVAC().get()
airloop.setName("AirLoopHVAC CoilSystemCoolingWater")

# create a CoilSystemCoolingWater object
coil_system = openstudio.model.CoilSystemCoolingWater(m)
coil_system.setName("CoilSystemCoolingWater WaterSide")

water_coil = coil_system.coolingCoil().to_CoilCoolingWater().get()
water_coil.setName("CoilSystemCoolingWater WaterSide CoolingCoil")

# Set coil conditions to mimic "Free Cooling Coil" from WaterSideEconomizer_PreCoolCoil.idf
water_coil.setDesignInletWaterTemperature(11.0)
water_coil.setDesignInletAirTemperature(34.0)
water_coil.setDesignOutletAirTemperature(16.0)
water_coil.setDesignInletAirHumidityRatio(0.009)
water_coil.setDesignOutletAirHumidityRatio(0.009)

# As a water-side economizer the CoilSystem:Cooling:Water object is placed upstream of packaged DX systems or chilled water main cooling coil
# We have a Chilled water coil already, so let's keep it
central_cooling_coil = (
    airloop.supplyComponents(openstudio.model.CoilCoolingWater.iddObjectType())[0].to_CoilCoolingWater().get()
)
central_cooling_coil.setName("Central ChW Coil")

# Note that we connect the CoilSystem, NOT the underlying CoilCoolingWater
coil_system.addToNode(central_cooling_coil.airInletModelObject().get().to_Node().get())
# But we have to connect the water_coil itself. Ideally this would be on a Condenser Loop, so let's get it
cts = sorted(m.getCoolingTowerSingleSpeeds(), key=lambda c: c.nameString())
condenser_loop = cts[0].plantLoop().get()
condenser_loop.addDemandBranchForComponent(water_coil)

# Rename some nodes and such, for ease of debugging
airloop.supplyInletNode().setName(f"{airloop.nameString()} Supply Inlet Node")
airloop.supplyOutletNode().setName(f"{airloop.nameString()} Supply Outlet Node")
airloop.mixedAirNode().get().setName(f"{airloop.nameString()} Mixed Air Node")

central_heating_coil = (
    airloop.supplyComponents(openstudio.model.CoilHeatingWater.iddObjectType())[0].to_CoilHeatingWater().get()
)
central_heating_coil.setName("Central HW Coil")
coil_system.outletModelObject().get().to_Node().get().setName(
    f"{coil_system.nameString()} Air Outlet to {central_cooling_coil.nameString()} Inlet Node"
)
central_cooling_coil.airOutletModelObject().get().to_Node().get().setName(
    f"{central_cooling_coil.nameString()} Air Outlet to {central_heating_coil.nameString()} Inlet Node"
)

water_coil.waterInletModelObject().get().setName(f"{water_coil.nameString()} Water Inlet Node")
water_coil.waterOutletModelObject().get().setName(f"{water_coil.nameString()} Water Outlet Node")
# water_coil.controllerWaterCoil.get.setName("#{water_coil.name} Controller")

fan = airloop.supplyFan().get()
fan.setName("Supply Fan")

central_heating_coil.waterOutletModelObject().get().setName(f"{airloop.nameString()} Heating Coil Water Outlet Node")
central_heating_coil.controllerWaterCoil().get().setName(f"{airloop.nameString()} Heating Coil Controller")
central_heating_coil.airOutletModelObject().get().setName(
    f"{central_heating_coil.nameString()} Air Outlet to {fan.nameString()} Inlet Node"
)

######

### Wrap Around Water Coil Heat Recovery Mode ###

# 5ZoneAirCooled_RunaroundHeatRecovery.idf
#
# create heat recovery plant loop
hr_loop = openstudio.model.PlantLoop(m)
hr_loop.setName("Run Around Coil HR Loop")

plant_siz = hr_loop.sizingPlant()
plant_siz.setLoopType("Cooling")
plant_siz.setDesignLoopExitTemperature(7)
plant_siz.setLoopDesignTemperatureDifference(4)

# create supply side pump
pump = openstudio.model.PumpVariableSpeed(m)
pump.setName("HR Circ Pump")
pump.setCoefficient1ofthePartLoadPerformanceCurve(0)
pump.setCoefficient2ofthePartLoadPerformanceCurve(1)
pump.setCoefficient3ofthePartLoadPerformanceCurve(0)
pump.setCoefficient4ofthePartLoadPerformanceCurve(0)

hr_loop.addSupplyBranchForComponent(pump)

# zone = zones[1]
# airloop = zone.airLoopHVAC.get
# airloop.setName('AirLoopHVAC CoilSystemCoolingWater WrapAround')

oa_sys = airloop.airLoopHVACOutdoorAirSystem().get()

# TODO: use a CoilSystemCoolingWaterHeatExchangerAssisted
primary_coil = openstudio.model.CoilCoolingWater(m, m.alwaysOnDiscreteSchedule())
primary_coil.setName(f"{airloop.nameString()} Primary HR Coil")
# primary_coil.setDesignWaterTemperatureDifference(4)

companion_coil = openstudio.model.CoilCoolingWater(m, m.alwaysOnDiscreteSchedule())
companion_coil.setName(f"{airloop.nameString()} Companion HR Coil")
# companion_coil.setDesignWaterTemperatureDifference(4)

coil_sys = openstudio.model.CoilSystemCoolingWater(m, primary_coil)
coil_sys.setName("CoilSystemCoolingWater WrapAround")
coil_sys.setCompanionCoilUsedForHeatRecovery(companion_coil)
coil_sys.setMinimumAirToWaterTemperatureOffset(3.0)
coil_sys.setMinimumWaterLoopTemperatureForHeatRecovery(5.0)

coil_sys.addToNode(oa_sys.outboardOANode().get())
companion_coil.addToNode(oa_sys.outboardReliefNode().get())

# connect to plant loop
hr_loop.addDemandBranchForComponent(primary_coil)
pipe = openstudio.model.PipeAdiabatic(m)
pipe.addToNode(primary_coil.waterOutletModelObject().get().to_Node().get())
companion_coil.addToNode(pipe.outletModelObject().get().to_Node().get())

coil_spm_sch = openstudio.model.ScheduleConstant(m)
coil_spm_sch.setName("OA HR Supply Air Temp Sch")
coil_spm_sch.setValue(4.5)

primary_coil_spm = openstudio.model.SetpointManagerScheduled(m, coil_spm_sch)
primary_coil_spm.setName("OA Air Temp Manager HR1")
# primary_coil_spm.addToNode(coil_sys.airOutletModelObject.get.to_Node.get)
# primary_coil_spm.addToNode(coil_sys.outletModelObject.get.to_Node.get)

companion_coil_spm = openstudio.model.SetpointManagerScheduled(m, coil_spm_sch)
companion_coil_spm.setName("OA Air Temp Manager HR2")
# companion_coil_spm.addToNode(companion_coil.airOutletModelObject.get.to_Node.get)

hr_loop_spm = openstudio.model.SetpointManagerScheduled(m, coil_spm_sch)
hr_loop_spm.setName("OA Air Temp Manager HR3")
hr_loop_spm.addToNode(hr_loop.loopTemperatureSetpointNode())

sz = airloop.sizingSystem()
sz.setPreheatDesignTemperature(4.5)
sz.setPrecoolDesignTemperature(11.0)
sz.setCentralCoolingDesignSupplyAirTemperature(12.8)
sz.setCentralHeatingDesignSupplyAirTemperature(16.7)
sz.setAllOutdoorAirinCooling(False)
sz.setAllOutdoorAirinHeating(False)
sz.setCentralCoolingDesignSupplyAirHumidityRatio(0.008)
sz.setCentralCoolingCapacityControlMethod("VAV")

# Rename some nodes and such, for ease of debugging
oa_sys.outboardOANode().get().setName("OA Inlet Node")
oa_sys.outboardReliefNode().get().setName("OA Relief Node")
oa_sys.reliefAirModelObject().get().setName("Return to OA System Node")
oa_sys.outdoorAirModelObject().get().setName("OA System Outlet to Mixed Node")

primary_coil.waterInletModelObject().get().setName(f"{primary_coil.name()} Water Inlet Node")
primary_coil.waterOutletModelObject().get().setName(f"{primary_coil.name()} Water Outlet Node")
# primary_coil.controllerWaterCoil.get.setName("#{primary_coil.name} Controller")


######

# save the OpenStudio model (.osm)
m.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
