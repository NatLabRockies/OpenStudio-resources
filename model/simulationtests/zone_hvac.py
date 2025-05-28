import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 3 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=3, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# Add a hot water plant to supply the baseboard heaters
# This could be baked into HVAC templates in the future
hotWaterPlant = openstudio.model.PlantLoop(model)
hotWaterPlant.setName("Hot Water Plant")

sizingPlant = hotWaterPlant.sizingPlant()
sizingPlant.setLoopType("Heating")
sizingPlant.setDesignLoopExitTemperature(82.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

hotWaterOutletNode = hotWaterPlant.supplyOutletNode()
hotWaterInletNode = hotWaterPlant.supplyInletNode()

pump = openstudio.model.PumpVariableSpeed(model)
pump.addToNode(hotWaterInletNode)

boiler = openstudio.model.BoilerHotWater(model)
node = hotWaterPlant.supplySplitter().lastOutletModelObject().get().to_Node().get()
boiler.addToNode(node)

pipe = openstudio.model.PipeAdiabatic(model)
hotWaterPlant.addSupplyBranchForComponent(pipe)

pipe2 = openstudio.model.PipeAdiabatic(model)
pipe2.addToNode(hotWaterOutletNode)

## Make a hot Water temperature schedule

osTime = openstudio.Time(0, 24, 0, 0)

hotWaterTempSchedule = openstudio.model.ScheduleRuleset(model)
hotWaterTempSchedule.setName("Hot Water Temperature")

### Winter Design Day
hotWaterTempScheduleWinter = openstudio.model.ScheduleDay(model)
hotWaterTempSchedule.setWinterDesignDaySchedule(hotWaterTempScheduleWinter)
hotWaterTempSchedule.winterDesignDaySchedule().setName("Hot Water Temperature Winter Design Day")
hotWaterTempSchedule.winterDesignDaySchedule().addValue(osTime, 67)

### Summer Design Day
hotWaterTempScheduleSummer = openstudio.model.ScheduleDay(model)
hotWaterTempSchedule.setSummerDesignDaySchedule(hotWaterTempScheduleSummer)
hotWaterTempSchedule.summerDesignDaySchedule().setName("Hot Water Temperature Summer Design Day")
hotWaterTempSchedule.summerDesignDaySchedule().addValue(osTime, 67)

### All other days
hotWaterTempSchedule.defaultDaySchedule().setName("Hot Water Temperature Default")
hotWaterTempSchedule.defaultDaySchedule().addValue(osTime, 67)

hotWaterSPM = openstudio.model.SetpointManagerScheduled(model, hotWaterTempSchedule)
hotWaterSPM.addToNode(hotWaterOutletNode)

# Add a hot water plant to supply the water to air heat pump
# This could be baked into HVAC templates in the future
condenserWaterPlant = openstudio.model.PlantLoop(model)
condenserWaterPlant.setName("Condenser Water Plant")

sizingPlant = condenserWaterPlant.sizingPlant()
sizingPlant.setLoopType("Heating")
sizingPlant.setDesignLoopExitTemperature(30.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

condenserWaterOutletNode = condenserWaterPlant.supplyOutletNode()
condenserWaterInletNode = condenserWaterPlant.supplyInletNode()

pump = openstudio.model.PumpVariableSpeed(model)
pump.addToNode(condenserWaterInletNode)

distHeating = openstudio.model.DistrictHeating(model)
condenserWaterPlant.addSupplyBranchForComponent(distHeating)

fluidCooler = openstudio.model.EvaporativeFluidCoolerSingleSpeed(model)
condenserWaterPlant.addSupplyBranchForComponent(fluidCooler)

groundHX = openstudio.model.GroundHeatExchangerVertical(model)
condenserWaterPlant.addSupplyBranchForComponent(groundHX)

# hGroundHX = openstudio.model.GroundHeatExchangerHorizontalTrench(model)
# condenserWaterPlant.addSupplyBranchForComponent(hGroundHX)

pipe = openstudio.model.PipeAdiabatic(model)
condenserWaterPlant.addSupplyBranchForComponent(pipe)

pipe2 = openstudio.model.PipeAdiabatic(model)
pipe2.addToNode(condenserWaterOutletNode)

## Make a condenser Water temperature schedule

osTime = openstudio.Time(0, 24, 0, 0)

condenserWaterTempSchedule = openstudio.model.ScheduleRuleset(model)
condenserWaterTempSchedule.setName("Condenser Water Temperature")

### Winter Design Day
condenserWaterTempScheduleWinter = openstudio.model.ScheduleDay(model)
condenserWaterTempSchedule.setWinterDesignDaySchedule(condenserWaterTempScheduleWinter)
condenserWaterTempSchedule.winterDesignDaySchedule().setName("Condenser Water Temperature Winter Design Day")
condenserWaterTempSchedule.winterDesignDaySchedule().addValue(osTime, 24)

### Summer Design Day
condenserWaterTempScheduleSummer = openstudio.model.ScheduleDay(model)
condenserWaterTempSchedule.setSummerDesignDaySchedule(condenserWaterTempScheduleSummer)
condenserWaterTempSchedule.summerDesignDaySchedule().setName("Condenser Water Temperature Summer Design Day")
condenserWaterTempSchedule.summerDesignDaySchedule().addValue(osTime, 24)

### All other days
condenserWaterTempSchedule.defaultDaySchedule().setName("Condenser Water Temperature Default")
condenserWaterTempSchedule.defaultDaySchedule().addValue(osTime, 24)

condenserWaterSPM = openstudio.model.SetpointManagerScheduled(model, condenserWaterTempSchedule)
condenserWaterSPM.addToNode(condenserWaterOutletNode)

# chilled Water Temp Schedule
# Schedule Ruleset
chilled_water_temp_sch = openstudio.model.ScheduleRuleset(model)
chilled_water_temp_sch.setName("Chilled_Water_Temperature")
# Winter Design Day
chilled_water_temp_schWinter = openstudio.model.ScheduleDay(model)
chilled_water_temp_sch.setWinterDesignDaySchedule(chilled_water_temp_schWinter)
chilled_water_temp_sch.winterDesignDaySchedule().setName("Chilled_Water_Temperature_Winter_Design_Day")
chilled_water_temp_sch.winterDesignDaySchedule().addValue(osTime, 6.7)
# Summer Design Day
chilled_water_temp_schSummer = openstudio.model.ScheduleDay(model)
chilled_water_temp_sch.setSummerDesignDaySchedule(chilled_water_temp_schSummer)
chilled_water_temp_sch.summerDesignDaySchedule().setName("Chilled_Water_Temperature_Summer_Design_Day")
chilled_water_temp_sch.summerDesignDaySchedule().addValue(osTime, 6.7)
# All other days
chilled_water_temp_sch.defaultDaySchedule().setName("Chilled_Water_Temperature_Default")
chilled_water_temp_sch.defaultDaySchedule().addValue(osTime, 6.7)

# Chilled Water Plant
chilledWaterPlant = openstudio.model.PlantLoop(model)
chilledWaterPlant.setName("Chilled Water Plant")
chilledWaterSizing = chilledWaterPlant.sizingPlant()
chilledWaterSizing.setLoopType("Cooling")
chilledWaterSizing.setDesignLoopExitTemperature(7.22)
chilledWaterSizing.setLoopDesignTemperatureDifference(6.67)
chilledWaterOutletNode = chilledWaterPlant.supplyOutletNode()
chilledWaterInletNode = chilledWaterPlant.supplyInletNode()
chilledWaterDemandOutletNode = chilledWaterPlant.demandOutletNode()
chilledWaterDemandInletNode = chilledWaterPlant.demandInletNode()
chilledWaterSPM = openstudio.model.SetpointManagerScheduled(model, chilled_water_temp_sch)
chilledWaterSPM.addToNode(chilledWaterOutletNode)

# pump
chilledWaterPump = openstudio.model.PumpVariableSpeed(model)
chilledWaterPump.addToNode(chilledWaterInletNode)

# district cooling
district_cooling = openstudio.model.DistrictCooling(model)
chilledWaterPlant.addSupplyBranchForComponent(district_cooling)

chilledWaterDemandBypass = openstudio.model.PipeAdiabatic(model)
chilledWaterPlant.addSupplyBranchForComponent(chilledWaterDemandBypass)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# assign thermal zones to variables
story_1_core_thermal_zone = model.getThermalZoneByName("Story 1 Core Thermal Zone").get()
story_1_north_thermal_zone = model.getThermalZoneByName("Story 1 North Perimeter Thermal Zone").get()
story_1_south_thermal_zone = model.getThermalZoneByName("Story 1 South Perimeter Thermal Zone").get()
story_1_east_thermal_zone = model.getThermalZoneByName("Story 1 East Perimeter Thermal Zone").get()
story_1_west_thermal_zone = model.getThermalZoneByName("Story 1 West Perimeter Thermal Zone").get()
story_2_core_thermal_zone = model.getThermalZoneByName("Story 2 Core Thermal Zone").get()
story_2_north_thermal_zone = model.getThermalZoneByName("Story 2 North Perimeter Thermal Zone").get()
story_2_south_thermal_zone = model.getThermalZoneByName("Story 2 South Perimeter Thermal Zone").get()
story_2_east_thermal_zone = model.getThermalZoneByName("Story 2 East Perimeter Thermal Zone").get()
story_2_west_thermal_zone = model.getThermalZoneByName("Story 2 West Perimeter Thermal Zone").get()
story_3_core_thermal_zone = model.getThermalZoneByName("Story 3 Core Thermal Zone").get()
story_3_north_thermal_zone = model.getThermalZoneByName("Story 3 North Perimeter Thermal Zone").get()
story_3_south_thermal_zone = model.getThermalZoneByName("Story 3 South Perimeter Thermal Zone").get()
story_3_east_thermal_zone = model.getThermalZoneByName("Story 3 East Perimeter Thermal Zone").get()
story_3_west_thermal_zone = model.getThermalZoneByName("Story 3 West Perimeter Thermal Zone").get()

# add a unit heater to next available zone
fan = openstudio.model.FanConstantVolume(model, model.alwaysOnDiscreteSchedule())
coil = openstudio.model.CoilHeatingElectric(model, model.alwaysOnDiscreteSchedule())
unit_heater = openstudio.model.ZoneHVACUnitHeater(model, model.alwaysOnDiscreteSchedule(), fan, coil)
unit_heater.addToThermalZone(story_1_core_thermal_zone)

# add a zone exhaust fan to next available zone
zone_exhaust_fan = openstudio.model.FanZoneExhaust(model)
zone_exhaust_fan.addToThermalZone(story_1_north_thermal_zone)

# add baseboard heater to next available zone
baseboard_coil = openstudio.model.CoilHeatingWaterBaseboard(model)
baseboard_heater = openstudio.model.ZoneHVACBaseboardConvectiveWater(
    model, model.alwaysOnDiscreteSchedule(), baseboard_coil
)
baseboard_heater.addToThermalZone(story_1_south_thermal_zone)
hotWaterPlant.addDemandBranchForComponent(baseboard_coil)

# add water to air heat pump to next available zone
fanPowerFtSpeedCurve = openstudio.model.CurveExponent(model)
fanPowerFtSpeedCurve.setCoefficient1Constant(0.0)
fanPowerFtSpeedCurve.setCoefficient2Constant(1.0)
fanPowerFtSpeedCurve.setCoefficient3Constant(3.0)
fanPowerFtSpeedCurve.setMinimumValueofx(0.0)
fanPowerFtSpeedCurve.setMaximumValueofx(1.5)
fanPowerFtSpeedCurve.setMinimumCurveOutput(0.01)
fanPowerFtSpeedCurve.setMaximumCurveOutput(1.5)

fanEfficiencyFtSpeedCurve = openstudio.model.CurveCubic(model)
fanEfficiencyFtSpeedCurve.setCoefficient1Constant(0.33856828)
fanEfficiencyFtSpeedCurve.setCoefficient2x(1.72644131)
fanEfficiencyFtSpeedCurve.setCoefficient3xPOW2(-1.49280132)
fanEfficiencyFtSpeedCurve.setCoefficient4xPOW3(0.42776208)
fanEfficiencyFtSpeedCurve.setMinimumValueofx(0.5)
fanEfficiencyFtSpeedCurve.setMaximumValueofx(1.5)
fanEfficiencyFtSpeedCurve.setMinimumCurveOutput(0.3)
fanEfficiencyFtSpeedCurve.setMaximumCurveOutput(1.0)

supplyFan = openstudio.model.FanOnOff(
    model, model.alwaysOnDiscreteSchedule(), fanPowerFtSpeedCurve, fanEfficiencyFtSpeedCurve
)
wahpDXHC = openstudio.model.CoilHeatingWaterToAirHeatPumpEquationFit(model)
wahpDXCC = openstudio.model.CoilCoolingWaterToAirHeatPumpEquationFit(model)
supplementalHC = openstudio.model.CoilHeatingElectric(model, model.alwaysOnDiscreteSchedule())
wtahp = openstudio.model.ZoneHVACWaterToAirHeatPump(
    model, model.alwaysOnDiscreteSchedule(), supplyFan, wahpDXHC, wahpDXCC, supplementalHC
)
wtahp.addToThermalZone(story_1_east_thermal_zone)

condenserWaterPlant.addDemandBranchForComponent(wahpDXHC)
condenserWaterPlant.addDemandBranchForComponent(wahpDXCC)

# Add a four pipe fan coil

fourPipeFan = openstudio.model.FanOnOff(model, model.alwaysOnDiscreteSchedule())
fourPipeHeat = openstudio.model.CoilHeatingWater(model, model.alwaysOnDiscreteSchedule())
hotWaterPlant.addDemandBranchForComponent(fourPipeHeat)
fourPipeCool = openstudio.model.CoilCoolingWater(model, model.alwaysOnDiscreteSchedule())
chilledWaterPlant.addDemandBranchForComponent(fourPipeCool)
fourPipeFanCoil = openstudio.model.ZoneHVACFourPipeFanCoil(
    model, model.alwaysOnDiscreteSchedule(), fourPipeFan, fourPipeCool, fourPipeHeat
)
fourPipeFanCoil.addToThermalZone(story_1_west_thermal_zone)

# Add a four pipe fan coil via connected through a DOAS AirLoopHVAC system

fourPipeFan2 = openstudio.model.FanOnOff(model, model.alwaysOnDiscreteSchedule())
fourPipeHeat2 = openstudio.model.CoilHeatingWater(model, model.alwaysOnDiscreteSchedule())
hotWaterPlant.addDemandBranchForComponent(fourPipeHeat2)
fourPipeCool2 = openstudio.model.CoilCoolingWater(model, model.alwaysOnDiscreteSchedule())
chilledWaterPlant.addDemandBranchForComponent(fourPipeCool2)
fourPipeFanCoil2 = openstudio.model.ZoneHVACFourPipeFanCoil(
    model, model.alwaysOnDiscreteSchedule(), fourPipeFan2, fourPipeCool2, fourPipeHeat2
)

controllerOutdoorAir = openstudio.model.ControllerOutdoorAir(model)
outdoorAirSystem = openstudio.model.AirLoopHVACOutdoorAirSystem(model, controllerOutdoorAir)
doasFan = openstudio.model.FanVariableVolume(model, model.alwaysOnDiscreteSchedule())
doasCool = openstudio.model.CoilCoolingWater(model, model.alwaysOnDiscreteSchedule())
chilledWaterPlant.addDemandBranchForComponent(doasCool)
doasHeat = openstudio.model.CoilHeatingWater(model, model.alwaysOnDiscreteSchedule())
hotWaterPlant.addDemandBranchForComponent(doasHeat)
air_loop = openstudio.model.AirLoopHVAC(model)
air_loop_supply_node = air_loop.supplyOutletNode()
outdoorAirSystem.addToNode(air_loop_supply_node)
doasCool.addToNode(air_loop_supply_node)
doasHeat.addToNode(air_loop_supply_node)
doasFan.addToNode(air_loop_supply_node)

os_time = openstudio.Time(0, 24, 0, 0)
deck_temp_sch = openstudio.model.ScheduleRuleset(model)
deck_temp_sch.setName("Deck_Temperature")
deck_temp_sch.defaultDaySchedule().setName("Deck_Temperature_Default")
deck_temp_sch.defaultDaySchedule().addValue(os_time, 22.0)
deck_spm = openstudio.model.SetpointManagerScheduled(model, deck_temp_sch)
deck_spm.addToNode(air_loop_supply_node)

terminal = openstudio.model.AirTerminalSingleDuctInletSideMixer(model)
air_loop.addBranchForZone(story_2_core_thermal_zone, terminal)
fourPipeFanCoil2.addToNode(terminal.outletModelObject().get().to_Node().get())

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
