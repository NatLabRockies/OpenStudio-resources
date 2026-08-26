# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 3 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 3,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 1,
                     'perimeter_zone_depth' => 3 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# Add a hot water plant to supply the baseboard heaters
# This could be baked into HVAC templates in the future
hotWaterPlant = OpenStudio::Model::PlantLoop.new(model)
hotWaterPlant.setName('Hot Water Plant')

sizingPlant = hotWaterPlant.sizingPlant
sizingPlant.setLoopType('Heating')
sizingPlant.setDesignLoopExitTemperature(82.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

hotWaterOutletNode = hotWaterPlant.supplyOutletNode
hotWaterInletNode = hotWaterPlant.supplyInletNode

pump = OpenStudio::Model::PumpVariableSpeed.new(model)
pump.addToNode(hotWaterInletNode)

boiler = OpenStudio::Model::BoilerHotWater.new(model)
node = hotWaterPlant.supplySplitter.lastOutletModelObject.get.to_Node.get
boiler.addToNode(node)

pipe = OpenStudio::Model::PipeAdiabatic.new(model)
hotWaterPlant.addSupplyBranchForComponent(pipe)

pipe2 = OpenStudio::Model::PipeAdiabatic.new(model)
pipe2.addToNode(hotWaterOutletNode)

## Make a hot Water temperature schedule

osTime = OpenStudio::Time.new(0, 24, 0, 0)

hotWaterTempSchedule = OpenStudio::Model::ScheduleRuleset.new(model)
hotWaterTempSchedule.setName('Hot Water Temperature')

### Winter Design Day
hotWaterTempScheduleWinter = OpenStudio::Model::ScheduleDay.new(model)
hotWaterTempSchedule.setWinterDesignDaySchedule(hotWaterTempScheduleWinter)
hotWaterTempSchedule.winterDesignDaySchedule.setName('Hot Water Temperature Winter Design Day')
hotWaterTempSchedule.winterDesignDaySchedule.addValue(osTime, 67)

### Summer Design Day
hotWaterTempScheduleSummer = OpenStudio::Model::ScheduleDay.new(model)
hotWaterTempSchedule.setSummerDesignDaySchedule(hotWaterTempScheduleSummer)
hotWaterTempSchedule.summerDesignDaySchedule.setName('Hot Water Temperature Summer Design Day')
hotWaterTempSchedule.summerDesignDaySchedule.addValue(osTime, 67)

### All other days
hotWaterTempSchedule.defaultDaySchedule.setName('Hot Water Temperature Default')
hotWaterTempSchedule.defaultDaySchedule.addValue(osTime, 67)

hotWaterSPM = OpenStudio::Model::SetpointManagerScheduled.new(model, hotWaterTempSchedule)
hotWaterSPM.addToNode(hotWaterOutletNode)

# Add a hot water plant to supply the water to air heat pump
# This could be baked into HVAC templates in the future
condenserWaterPlant = OpenStudio::Model::PlantLoop.new(model)
condenserWaterPlant.setName('Condenser Water Plant')

sizingPlant = condenserWaterPlant.sizingPlant
sizingPlant.setLoopType('Condenser')
sizingPlant.setDesignLoopExitTemperature(30.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

condenserWaterOutletNode = condenserWaterPlant.supplyOutletNode
condenserWaterInletNode = condenserWaterPlant.supplyInletNode

pump = OpenStudio::Model::PumpVariableSpeed.new(model)
pump.addToNode(condenserWaterInletNode)

distHeating = OpenStudio::Model::DistrictHeating.new(model)
condenserWaterPlant.addSupplyBranchForComponent(distHeating)

distCooling = OpenStudio::Model::DistrictCooling.new(model)
condenserWaterPlant.addSupplyBranchForComponent(distCooling)

pipe = OpenStudio::Model::PipeAdiabatic.new(model)
condenserWaterPlant.addSupplyBranchForComponent(pipe)

pipe2 = OpenStudio::Model::PipeAdiabatic.new(model)
pipe2.addToNode(condenserWaterOutletNode)

## Make a condenser Water temperature schedule

osTime = OpenStudio::Time.new(0, 24, 0, 0)

condenserWaterTempSchedule = OpenStudio::Model::ScheduleRuleset.new(model)
condenserWaterTempSchedule.setName('Condenser Water Temperature')

### Winter Design Day
condenserWaterTempScheduleWinter = OpenStudio::Model::ScheduleDay.new(model)
condenserWaterTempSchedule.setWinterDesignDaySchedule(condenserWaterTempScheduleWinter)
condenserWaterTempSchedule.winterDesignDaySchedule.setName('Condenser Water Temperature Winter Design Day')
condenserWaterTempSchedule.winterDesignDaySchedule.addValue(osTime, 24)

### Summer Design Day
condenserWaterTempScheduleSummer = OpenStudio::Model::ScheduleDay.new(model)
condenserWaterTempSchedule.setSummerDesignDaySchedule(condenserWaterTempScheduleSummer)
condenserWaterTempSchedule.summerDesignDaySchedule.setName('Condenser Water Temperature Summer Design Day')
condenserWaterTempSchedule.summerDesignDaySchedule.addValue(osTime, 24)

### All other days
condenserWaterTempSchedule.defaultDaySchedule.setName('Condenser Water Temperature Default')
condenserWaterTempSchedule.defaultDaySchedule.addValue(osTime, 24)

condenserWaterSPM = OpenStudio::Model::SetpointManagerScheduled.new(model, condenserWaterTempSchedule)
condenserWaterSPM.addToNode(condenserWaterOutletNode)

# chilled Water Temp Schedule
# Schedule Ruleset
chilled_water_temp_sch = OpenStudio::Model::ScheduleRuleset.new(model)
chilled_water_temp_sch.setName('Chilled_Water_Temperature')
# Winter Design Day
chilled_water_temp_schWinter = OpenStudio::Model::ScheduleDay.new(model)
chilled_water_temp_sch.setWinterDesignDaySchedule(chilled_water_temp_schWinter)
chilled_water_temp_sch.winterDesignDaySchedule.setName('Chilled_Water_Temperature_Winter_Design_Day')
chilled_water_temp_sch.winterDesignDaySchedule.addValue(osTime, 6.7)
# Summer Design Day
chilled_water_temp_schSummer = OpenStudio::Model::ScheduleDay.new(model)
chilled_water_temp_sch.setSummerDesignDaySchedule(chilled_water_temp_schSummer)
chilled_water_temp_sch.summerDesignDaySchedule.setName('Chilled_Water_Temperature_Summer_Design_Day')
chilled_water_temp_sch.summerDesignDaySchedule.addValue(osTime, 6.7)
# All other days
chilled_water_temp_sch.defaultDaySchedule.setName('Chilled_Water_Temperature_Default')
chilled_water_temp_sch.defaultDaySchedule.addValue(osTime, 6.7)

# Chilled Water Plant
chilledWaterPlant = OpenStudio::Model::PlantLoop.new(model)
chilledWaterPlant.setName('Chilled Water Plant')
chilledWaterSizing = chilledWaterPlant.sizingPlant
chilledWaterSizing.setLoopType('Cooling')
chilledWaterSizing.setDesignLoopExitTemperature(7.22)
chilledWaterSizing.setLoopDesignTemperatureDifference(6.67)
chilledWaterOutletNode = chilledWaterPlant.supplyOutletNode
chilledWaterInletNode = chilledWaterPlant.supplyInletNode
chilledWaterDemandOutletNode = chilledWaterPlant.demandOutletNode
chilledWaterDemandInletNode = chilledWaterPlant.demandInletNode
chilledWaterSPM = OpenStudio::Model::SetpointManagerScheduled.new(model, chilled_water_temp_sch)
chilledWaterSPM.addToNode(chilledWaterOutletNode)

# pump
chilledWaterPump = OpenStudio::Model::PumpVariableSpeed.new(model)
chilledWaterPump.addToNode(chilledWaterInletNode)

# district cooling
district_cooling = OpenStudio::Model::DistrictCooling.new(model)
chilledWaterPlant.addSupplyBranchForComponent(district_cooling)

chilledWaterDemandBypass = OpenStudio::Model::PipeAdiabatic.new(model)
chilledWaterPlant.addSupplyBranchForComponent(chilledWaterDemandBypass)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# assign thermal zones to variables
story_1_core_thermal_zone = model.getThermalZoneByName('Story 1 Core Thermal Zone').get
story_1_north_thermal_zone = model.getThermalZoneByName('Story 1 North Perimeter Thermal Zone').get
story_1_south_thermal_zone = model.getThermalZoneByName('Story 1 South Perimeter Thermal Zone').get
story_1_east_thermal_zone = model.getThermalZoneByName('Story 1 East Perimeter Thermal Zone').get
story_1_west_thermal_zone = model.getThermalZoneByName('Story 1 West Perimeter Thermal Zone').get
story_2_core_thermal_zone = model.getThermalZoneByName('Story 2 Core Thermal Zone').get
story_2_north_thermal_zone = model.getThermalZoneByName('Story 2 North Perimeter Thermal Zone').get
story_2_south_thermal_zone = model.getThermalZoneByName('Story 2 South Perimeter Thermal Zone').get
story_2_east_thermal_zone = model.getThermalZoneByName('Story 2 East Perimeter Thermal Zone').get
story_2_west_thermal_zone = model.getThermalZoneByName('Story 2 West Perimeter Thermal Zone').get
story_3_core_thermal_zone = model.getThermalZoneByName('Story 3 Core Thermal Zone').get
story_3_north_thermal_zone = model.getThermalZoneByName('Story 3 North Perimeter Thermal Zone').get
story_3_south_thermal_zone = model.getThermalZoneByName('Story 3 South Perimeter Thermal Zone').get
story_3_east_thermal_zone = model.getThermalZoneByName('Story 3 East Perimeter Thermal Zone').get
story_3_west_thermal_zone = model.getThermalZoneByName('Story 3 West Perimeter Thermal Zone').get

# Add ZoneHVACBaseboardRadiantConvectiveWater
zoneHVACBaseboardRadiantConvectiveWater = OpenStudio::Model::ZoneHVACBaseboardRadiantConvectiveWater.new(model)
baseboard_coil = zoneHVACBaseboardRadiantConvectiveWater.heatingCoil
hotWaterPlant.addDemandBranchForComponent(baseboard_coil)
zoneHVACBaseboardRadiantConvectiveWater.addToThermalZone(story_1_core_thermal_zone)

# Add ZoneHVACBaseboardRadiantConvectiveElectric
zoneHVACBaseboardRadiantConvectiveElectric = OpenStudio::Model::ZoneHVACBaseboardRadiantConvectiveElectric.new(model)
zoneHVACBaseboardRadiantConvectiveElectric.addToThermalZone(story_1_north_thermal_zone)

# Add ZoneHVACUnitVentilator
zoneHVACUnitVentilator = OpenStudio::Model::ZoneHVACUnitVentilator.new(model)
heating_coil = OpenStudio::Model::CoilHeatingElectric.new(model)
cooling_coil = OpenStudio::Model::CoilCoolingWater.new(model)
chilledWaterPlant.addDemandBranchForComponent(cooling_coil)
zoneHVACUnitVentilator.setHeatingCoil(heating_coil)
zoneHVACUnitVentilator.setCoolingCoil(cooling_coil)
zoneHVACUnitVentilator.addToThermalZone(story_1_south_thermal_zone)

# Add ZoneHVACUnitVentilator
zoneHVACUnitVentilator = OpenStudio::Model::ZoneHVACUnitVentilator.new(model)
cooling_coil = OpenStudio::Model::CoilCoolingWater.new(model)
chilledWaterPlant.addDemandBranchForComponent(cooling_coil)
zoneHVACUnitVentilator.setCoolingCoil(cooling_coil)
zoneHVACUnitVentilator.addToThermalZone(story_2_south_thermal_zone)

# Add ZoneHVACUnitVentilator
zoneHVACUnitVentilator = OpenStudio::Model::ZoneHVACUnitVentilator.new(model)
heating_coil = OpenStudio::Model::CoilHeatingElectric.new(model)
zoneHVACUnitVentilator.setHeatingCoil(heating_coil)
zoneHVACUnitVentilator.addToThermalZone(story_3_south_thermal_zone)

# Add ZoneHVACEnergyRecoveryVentilator
zoneHVACEnergyRecoveryVentilator = OpenStudio::Model::ZoneHVACEnergyRecoveryVentilator.new(model)
zoneHVACEnergyRecoveryVentilator.addToThermalZone(story_1_east_thermal_zone)

# Add ZoneHVACEnergyRecoveryVentilator
zoneHVACEnergyRecoveryVentilator = OpenStudio::Model::ZoneHVACEnergyRecoveryVentilator.new(model)
zoneHVACEnergyRecoveryVentilatorController = OpenStudio::Model::ZoneHVACEnergyRecoveryVentilatorController.new(model)
zoneHVACEnergyRecoveryVentilator.setController(zoneHVACEnergyRecoveryVentilatorController)
zoneHVACEnergyRecoveryVentilator.addToThermalZone(story_2_east_thermal_zone)

# Add ZoneHVACEnergyRecoveryVentilator
zoneHVACEnergyRecoveryVentilator = OpenStudio::Model::ZoneHVACEnergyRecoveryVentilator.new(model)
zoneHVACEnergyRecoveryVentilatorController = OpenStudio::Model::ZoneHVACEnergyRecoveryVentilatorController.new(model)
zoneHVACEnergyRecoveryVentilator.setController(zoneHVACEnergyRecoveryVentilatorController)
zoneHVACEnergyRecoveryVentilatorController.setHighHumidityControlFlag(true)
zoneHVACEnergyRecoveryVentilator.addToThermalZone(story_3_east_thermal_zone)
# Add a humidistat at 50% RH to the zone
dehumidify_sch = OpenStudio::Model::ScheduleConstant.new(model)
dehumidify_sch.setValue(50)
humidistat = OpenStudio::Model::ZoneControlHumidistat.new(model)
humidistat.setHumidifyingRelativeHumiditySetpointSchedule(dehumidify_sch)
story_3_east_thermal_zone.setZoneControlHumidistat(humidistat)

# Add ZoneHVACDehumidifierDX
dx_hum_schedule = OpenStudio::Model::ScheduleConstant.new(model)
dx_hum_schedule.setName('Humidifying Schedule - OFF')
dx_hum_schedule.setValue(0.0)
dx_dehum_schedule = OpenStudio::Model::ScheduleConstant.new(model)
dx_dehum_schedule.setName('Dehumidifying Schedule 80 Percent')
dx_dehum_schedule.setValue(80.0)
dx_humidistat = OpenStudio::Model::ZoneControlHumidistat.new(model)
dx_humidistat.setHumidifyingRelativeHumiditySetpointSchedule(dx_hum_schedule)
dx_humidistat.setDehumidifyingRelativeHumiditySetpointSchedule(dx_dehum_schedule)
story_1_west_thermal_zone.setZoneControlHumidistat(dx_humidistat)
zoneHVACDehumidifierDX = OpenStudio::Model::ZoneHVACDehumidifierDX.new(model)
zoneHVACDehumidifierDX.addToThermalZone(story_1_west_thermal_zone)

# add water to air heat pump with variable speed coils to next available zone
supplyFan = OpenStudio::Model::FanOnOff.new(model)

wahpDXHC = OpenStudio::Model::CoilHeatingWaterToAirHeatPumpVariableSpeedEquationFit.new(model)
speedData = OpenStudio::Model::CoilHeatingWaterToAirHeatPumpVariableSpeedEquationFitSpeedData.new(model)
wahpDXHC.addSpeed(speedData)

wahpDXCC = OpenStudio::Model::CoilCoolingWaterToAirHeatPumpVariableSpeedEquationFit.new(model)
speedData = OpenStudio::Model::CoilCoolingWaterToAirHeatPumpVariableSpeedEquationFitSpeedData.new(model)
wahpDXCC.addSpeed(speedData)

supplementalHC = OpenStudio::Model::CoilHeatingElectric.new(model)
wtahp = OpenStudio::Model::ZoneHVACWaterToAirHeatPump.new(model, model.alwaysOnDiscreteSchedule, supplyFan, wahpDXHC, wahpDXCC, supplementalHC)
wtahp.addToThermalZone(story_1_west_thermal_zone)

condenserWaterPlant.addDemandBranchForComponent(wahpDXHC)
condenserWaterPlant.addDemandBranchForComponent(wahpDXCC)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
