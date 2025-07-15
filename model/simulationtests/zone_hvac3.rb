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
hotSteamPlant = OpenStudio::Model::PlantLoop.new(model)
hotSteamPlant.setName('Hot Steam Plant')
# hotSteamPlant.setFluidType('Steam')

sizingPlant = hotSteamPlant.sizingPlant
sizingPlant.setLoopType('Heating')
sizingPlant.setDesignLoopExitTemperature(82.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

steamOutletNode = hotSteamPlant.supplyOutletNode
steamInletNode = hotSteamPlant.supplyInletNode

pump = OpenStudio::Model::PumpVariableSpeedCondensate.new(model)
pump.addToNode(steamInletNode)

boiler = OpenStudio::Model::BoilerSteam.new(model)
node = hotSteamPlant.supplySplitter.lastOutletModelObject.get.to_Node.get
boiler.addToNode(node)

pipe = OpenStudio::Model::PipeAdiabatic.new(model)
hotSteamPlant.addSupplyBranchForComponent(pipe)

pipe2 = OpenStudio::Model::PipeAdiabatic.new(model)
pipe2.addToNode(steamOutletNode)

## Make a hot Water temperature schedule

osTime = OpenStudio::Time.new(0, 24, 0, 0)

steamTempSchedule = OpenStudio::Model::ScheduleRuleset.new(model)
steamTempSchedule.setName('Hot Water Temperature')

### Winter Design Day
steamTempScheduleWinter = OpenStudio::Model::ScheduleDay.new(model)
steamTempSchedule.setWinterDesignDaySchedule(steamTempScheduleWinter)
steamTempSchedule.winterDesignDaySchedule.setName('Hot Water Temperature Winter Design Day')
steamTempSchedule.winterDesignDaySchedule.addValue(osTime, 67)

### Summer Design Day
steamTempScheduleSummer = OpenStudio::Model::ScheduleDay.new(model)
steamTempSchedule.setSummerDesignDaySchedule(steamTempScheduleSummer)
steamTempSchedule.summerDesignDaySchedule.setName('Hot Water Temperature Summer Design Day')
steamTempSchedule.summerDesignDaySchedule.addValue(osTime, 67)

### All other days
steamTempSchedule.defaultDaySchedule.setName('Hot Water Temperature Default')
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
zoneHVACBaseboardRadiantConvectiveSteam = OpenStudio::Model::ZoneHVACBaseboardRadiantConvectiveSteam.new(model)
baseboard_coil = zoneHVACBaseboardRadiantConvectiveSteam.heatingCoil
hotSteamPlant.addDemandBranchForComponent(baseboard_coil)
zoneHVACBaseboardRadiantConvectiveSteam.addToThermalZone(story_1_core_thermal_zone)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
