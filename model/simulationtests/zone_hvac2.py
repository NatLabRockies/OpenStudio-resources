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
sizingPlant.setLoopType("Condenser")
sizingPlant.setDesignLoopExitTemperature(30.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

condenserWaterOutletNode = condenserWaterPlant.supplyOutletNode()
condenserWaterInletNode = condenserWaterPlant.supplyInletNode()

pump = openstudio.model.PumpVariableSpeed(model)
pump.addToNode(condenserWaterInletNode)

distHeating = openstudio.model.DistrictHeating(model)
condenserWaterPlant.addSupplyBranchForComponent(distHeating)

distCooling = openstudio.model.DistrictCooling(model)
condenserWaterPlant.addSupplyBranchForComponent(distCooling)

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

# Add ZoneHVACBaseboardRadiantConvectiveWater
zoneHVACBaseboardRadiantConvectiveWater = openstudio.model.ZoneHVACBaseboardRadiantConvectiveWater(model)
baseboard_coil = zoneHVACBaseboardRadiantConvectiveWater.heatingCoil()
hotWaterPlant.addDemandBranchForComponent(baseboard_coil)
zoneHVACBaseboardRadiantConvectiveWater.addToThermalZone(story_1_core_thermal_zone)

# Add ZoneHVACBaseboardRadiantConvectiveElectric
zoneHVACBaseboardRadiantConvectiveElectric = openstudio.model.ZoneHVACBaseboardRadiantConvectiveElectric(model)
zoneHVACBaseboardRadiantConvectiveElectric.addToThermalZone(story_1_north_thermal_zone)

# Add ZoneHVACUnitVentilator
zoneHVACUnitVentilator = openstudio.model.ZoneHVACUnitVentilator(model)
heating_coil = openstudio.model.CoilHeatingElectric(model)
cooling_coil = openstudio.model.CoilCoolingWater(model)
chilledWaterPlant.addDemandBranchForComponent(cooling_coil)
zoneHVACUnitVentilator.setHeatingCoil(heating_coil)
zoneHVACUnitVentilator.setCoolingCoil(cooling_coil)
zoneHVACUnitVentilator.addToThermalZone(story_1_south_thermal_zone)

# Add ZoneHVACUnitVentilator
zoneHVACUnitVentilator = openstudio.model.ZoneHVACUnitVentilator(model)
cooling_coil = openstudio.model.CoilCoolingWater(model)
chilledWaterPlant.addDemandBranchForComponent(cooling_coil)
zoneHVACUnitVentilator.setCoolingCoil(cooling_coil)
zoneHVACUnitVentilator.addToThermalZone(story_2_south_thermal_zone)

# Add ZoneHVACUnitVentilator
zoneHVACUnitVentilator = openstudio.model.ZoneHVACUnitVentilator(model)
heating_coil = openstudio.model.CoilHeatingElectric(model)
zoneHVACUnitVentilator.setHeatingCoil(heating_coil)
zoneHVACUnitVentilator.addToThermalZone(story_3_south_thermal_zone)

# Add ZoneHVACEnergyRecoveryVentilator
zoneHVACEnergyRecoveryVentilator = openstudio.model.ZoneHVACEnergyRecoveryVentilator(model)
zoneHVACEnergyRecoveryVentilator.addToThermalZone(story_1_east_thermal_zone)

# Add ZoneHVACEnergyRecoveryVentilator
zoneHVACEnergyRecoveryVentilator = openstudio.model.ZoneHVACEnergyRecoveryVentilator(model)
zoneHVACEnergyRecoveryVentilatorController = openstudio.model.ZoneHVACEnergyRecoveryVentilatorController(model)
zoneHVACEnergyRecoveryVentilator.setController(zoneHVACEnergyRecoveryVentilatorController)
zoneHVACEnergyRecoveryVentilator.addToThermalZone(story_2_east_thermal_zone)

# Add ZoneHVACEnergyRecoveryVentilator
zoneHVACEnergyRecoveryVentilator = openstudio.model.ZoneHVACEnergyRecoveryVentilator(model)
zoneHVACEnergyRecoveryVentilatorController = openstudio.model.ZoneHVACEnergyRecoveryVentilatorController(model)
zoneHVACEnergyRecoveryVentilator.setController(zoneHVACEnergyRecoveryVentilatorController)
zoneHVACEnergyRecoveryVentilatorController.setHighHumidityControlFlag(True)
zoneHVACEnergyRecoveryVentilator.addToThermalZone(story_3_east_thermal_zone)
# Add a humidistat at 50% RH to the zone
dehumidify_sch = openstudio.model.ScheduleConstant(model)
dehumidify_sch.setValue(50)
humidistat = openstudio.model.ZoneControlHumidistat(model)
humidistat.setHumidifyingRelativeHumiditySetpointSchedule(dehumidify_sch)
story_3_east_thermal_zone.setZoneControlHumidistat(humidistat)

# Add ZoneHVACDehumidifierDX
zoneHVACDehumidifierDX = openstudio.model.ZoneHVACDehumidifierDX(model)
zoneHVACDehumidifierDX.addToThermalZone(story_1_west_thermal_zone)

# add water to air heat pump with variable speed coils to next available zone
supplyFan = openstudio.model.FanOnOff(model)

wahpDXHC = openstudio.model.CoilHeatingWaterToAirHeatPumpVariableSpeedEquationFit(model)
speedData = openstudio.model.CoilHeatingWaterToAirHeatPumpVariableSpeedEquationFitSpeedData(model)
wahpDXHC.addSpeed(speedData)

wahpDXCC = openstudio.model.CoilCoolingWaterToAirHeatPumpVariableSpeedEquationFit(model)
speedData = openstudio.model.CoilCoolingWaterToAirHeatPumpVariableSpeedEquationFitSpeedData(model)
wahpDXCC.addSpeed(speedData)

supplementalHC = openstudio.model.CoilHeatingElectric(model)
wtahp = openstudio.model.ZoneHVACWaterToAirHeatPump(
    model, model.alwaysOnDiscreteSchedule(), supplyFan, wahpDXHC, wahpDXCC, supplementalHC
)
wtahp.addToThermalZone(story_1_west_thermal_zone)

condenserWaterPlant.addDemandBranchForComponent(wahpDXHC)
condenserWaterPlant.addDemandBranchForComponent(wahpDXCC)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
