# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 10 zone core/perimeter building
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

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# SteamSystemAutoSize_DistrictHeatingSteam.idf
# - DistrictHeating:Steam
# - Pump:VariableSpeed:Condensate
# - AirTerminal:SingleDuct:VAV:Reheat
# - Coil:Heating:Steam

# 5ZoneSteamBaseboard.idf
# - Boiler:Steam
# - Pump:VariableSpeed:Condensate
# - AirTerminal:SingleDuct:VAV:Reheat
# - Coil:Heating:Steam
# - ZoneHVAC:Baseboard:RadiantConvective:Steam

# Add a steam plant to supply the baseboard heaters
# This could be baked into HVAC templates in the future
hotSteamPlant = OpenStudio::Model::PlantLoop.new(model)
hotSteamPlant.setName('Hot Steam Plant')

sizingPlant = hotSteamPlant.sizingPlant
sizingPlant.setLoopType('Heating')
sizingPlant.setDesignLoopExitTemperature(82.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

steamOutletNode = hotSteamPlant.supplyOutletNode
steamInletNode = hotSteamPlant.supplyInletNode

pump = OpenStudio::Model::PumpVariableSpeedCondensate.new(model)
pump.addToNode(steamInletNode)

# Boiler steam
boiler = OpenStudio::Model::BoilerSteam.new(model)
node = hotSteamPlant.supplySplitter.lastOutletModelObject.get.to_Node.get
boiler.addToNode(node)

# District heating steam
district_heating_steam = OpenStudio::Model::DistrictHeatingSteam.new(model)
district_heating_steam.addToNode(node)

pipe = OpenStudio::Model::PipeAdiabatic.new(model)
hotSteamPlant.addSupplyBranchForComponent(pipe)

pipe2 = OpenStudio::Model::PipeAdiabatic.new(model)
pipe2.addToNode(steamOutletNode)

## Make a steam temperature schedule

osTime = OpenStudio::Time.new(0, 24, 0, 0)

steamTempSchedule = OpenStudio::Model::ScheduleRuleset.new(model)
steamTempSchedule.setName('Steam Temperature')

### Winter Design Day
steamTempScheduleWinter = OpenStudio::Model::ScheduleDay.new(model)
steamTempSchedule.setWinterDesignDaySchedule(steamTempScheduleWinter)
steamTempSchedule.winterDesignDaySchedule.setName('Steam Temperature Winter Design Day')
steamTempSchedule.winterDesignDaySchedule.addValue(osTime, 67)

### Summer Design Day
steamTempScheduleSummer = OpenStudio::Model::ScheduleDay.new(model)
steamTempSchedule.setSummerDesignDaySchedule(steamTempScheduleSummer)
steamTempSchedule.summerDesignDaySchedule.setName('Steam Temperature Summer Design Day')
steamTempSchedule.summerDesignDaySchedule.addValue(osTime, 67)

### All other days
steamTempSchedule.defaultDaySchedule.setName('Steam Temperature Default')
steamTempSchedule.defaultDaySchedule.addValue(osTime, 67)

steamSPM = OpenStudio::Model::SetpointManagerScheduled.new(model, steamTempSchedule)
steamSPM.addToNode(steamOutletNode)

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

# new airloop
airLoopHVAC = OpenStudio::Model::AirLoopHVAC.new(model)

# OA controller
controllerOutdoorAir = OpenStudio::Model::ControllerOutdoorAir.new(model)
outdoorAirSystem = OpenStudio::Model::AirLoopHVACOutdoorAirSystem.new(model, controllerOutdoorAir)

# add the equipment to the airloop
supplyOutletNode = airLoopHVAC.supplyOutletNode
outdoorAirSystem.addToNode(supplyOutletNode)

# Make a time stamp to use in multiple places
os_time = OpenStudio::Time.new(0, 24, 0, 0)

# always On Schedule
# Schedule Ruleset
always_on_sch = OpenStudio::Model::ScheduleRuleset.new(model)
always_on_sch.setName('Always_On')
# Winter Design Day
always_on_sch_winter = OpenStudio::Model::ScheduleDay.new(model)
always_on_sch.setWinterDesignDaySchedule(always_on_sch_winter)
always_on_sch.winterDesignDaySchedule.setName('Always_On_Winter_Design_Day')
always_on_sch.winterDesignDaySchedule.addValue(os_time, 1)
# Summer Design Day
always_on_sch_summer = OpenStudio::Model::ScheduleDay.new(model)
always_on_sch.setSummerDesignDaySchedule(always_on_sch_summer)
always_on_sch.summerDesignDaySchedule.setName('Always_On_Summer_Design_Day')
always_on_sch.summerDesignDaySchedule.addValue(os_time, 1)
# All other days
always_on_sch.defaultDaySchedule.setName('Always_On_Default')
always_on_sch.defaultDaySchedule.addValue(os_time, 1)

# Add ZoneHVACBaseboardRadiantConvectiveSteam
zoneHVACBaseboardRadiantConvectiveSteam = OpenStudio::Model::ZoneHVACBaseboardRadiantConvectiveSteam.new(model)
baseboard_coil = zoneHVACBaseboardRadiantConvectiveSteam.heatingCoil
hotSteamPlant.addDemandBranchForComponent(baseboard_coil)
zoneHVACBaseboardRadiantConvectiveSteam.addToThermalZone(story_1_core_thermal_zone)

# Add CoilHeatingSteam
steamReheatCoil = OpenStudio::Model::CoilHeatingSteam.new(model, always_on_sch)
steamTerminal = OpenStudio::Model::AirTerminalSingleDuctVAVReheat.new(model, always_on_sch, steamReheatCoil)
airLoopHVAC.addBranchForHVACComponent(steamTerminal)
hotSteamPlant.addDemandBranchForComponent(steamReheatCoil)
airLoopHVAC.addBranchForZone(story_1_north_thermal_zone)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
