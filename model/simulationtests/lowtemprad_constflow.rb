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

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = model.getThermalZones.sort_by { |z| z.name.to_s }

# Add a hot water plant to supply the water to air heat pump
# This could be baked into HVAC templates in the future
hotWaterPlant = OpenStudio::Model::PlantLoop.new(model)
hotWaterPlant.setName('Hot Water Plant')

sizingPlant = hotWaterPlant.sizingPlant
sizingPlant.setLoopType('Heating')
sizingPlant.setDesignLoopExitTemperature(60.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

hotWaterOutletNode = hotWaterPlant.supplyOutletNode
hotWaterInletNode = hotWaterPlant.supplyInletNode

heatingPump = OpenStudio::Model::PumpVariableSpeed.new(model)
heatingPump.addToNode(hotWaterInletNode)

# create a chilled water plant
chilledWaterPlant = OpenStudio::Model::PlantLoop.new(model)
chilledWaterPlant.setName('Chilled Water Plant')

sizingPlant = chilledWaterPlant.sizingPlant
sizingPlant.setLoopType('Cooling')
sizingPlant.setDesignLoopExitTemperature(10.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

chilledWaterOutletNode = chilledWaterPlant.supplyOutletNode
chilledWaterInletNode = chilledWaterPlant.supplyInletNode

coolingPump = OpenStudio::Model::PumpVariableSpeed.new(model)
coolingPump.addToNode(chilledWaterInletNode)

distHeating = OpenStudio::Model::DistrictHeating.new(model)
hotWaterPlant.addSupplyBranchForComponent(distHeating)

distCooling = OpenStudio::Model::DistrictCooling.new(model)
chilledWaterPlant.addSupplyBranchForComponent(distCooling)

pipe_h = OpenStudio::Model::PipeAdiabatic.new(model)
hotWaterPlant.addSupplyBranchForComponent(pipe_h)

pipe_h1 = OpenStudio::Model::PipeAdiabatic.new(model)
pipe_h1.addToNode(hotWaterOutletNode)

pipe_c = OpenStudio::Model::PipeAdiabatic.new(model)
chilledWaterPlant.addSupplyBranchForComponent(pipe_c)

pipe_c1 = OpenStudio::Model::PipeAdiabatic.new(model)
pipe_c1.addToNode(chilledWaterOutletNode)

## Make a Hot Water temperature schedule

osTime = OpenStudio::Time.new(0, 24, 0, 0)

hotWaterTempSchedule = OpenStudio::Model::ScheduleRuleset.new(model)
hotWaterTempSchedule.setName('Hot Water Temperature')
### Winter Design Day
hotWaterTempScheduleWinter = OpenStudio::Model::ScheduleDay.new(model)
hotWaterTempSchedule.setWinterDesignDaySchedule(hotWaterTempScheduleWinter)
hotWaterTempSchedule.winterDesignDaySchedule.setName('Hot Water Temperature Winter Design Day')
hotWaterTempSchedule.winterDesignDaySchedule.addValue(osTime, 24)
### Summer Design Day
hotWaterTempScheduleSummer = OpenStudio::Model::ScheduleDay.new(model)
hotWaterTempSchedule.setSummerDesignDaySchedule(hotWaterTempScheduleSummer)
hotWaterTempSchedule.summerDesignDaySchedule.setName('Hot Water Temperature Summer Design Day')
hotWaterTempSchedule.summerDesignDaySchedule.addValue(osTime, 24)
### All other days
hotWaterTempSchedule.defaultDaySchedule.setName('Hot Water Temperature Default')
hotWaterTempSchedule.defaultDaySchedule.addValue(osTime, 24)

hotWaterSPM = OpenStudio::Model::SetpointManagerScheduled.new(model, hotWaterTempSchedule)
hotWaterSPM.addToNode(hotWaterOutletNode)

## Make a Chilled Water temperature schedule

chilledWaterTempSchedule = OpenStudio::Model::ScheduleRuleset.new(model)
chilledWaterTempSchedule.setName('Chilled Water Temperature')
### Winter Design Day
chilledWaterTempScheduleWinter = OpenStudio::Model::ScheduleDay.new(model)
chilledWaterTempSchedule.setWinterDesignDaySchedule(chilledWaterTempScheduleWinter)
chilledWaterTempSchedule.winterDesignDaySchedule.setName('Chilled Water Temperature Winter Design Day')
chilledWaterTempSchedule.winterDesignDaySchedule.addValue(osTime, 24)
### Summer Design Day
chilledWaterTempScheduleSummer = OpenStudio::Model::ScheduleDay.new(model)
chilledWaterTempSchedule.setSummerDesignDaySchedule(chilledWaterTempScheduleSummer)
chilledWaterTempSchedule.summerDesignDaySchedule.setName('Chilled Water Temperature Summer Design Day')
chilledWaterTempSchedule.summerDesignDaySchedule.addValue(osTime, 24)
### All other days
chilledWaterTempSchedule.defaultDaySchedule.setName('Chilled Water Temperature Default')
chilledWaterTempSchedule.defaultDaySchedule.addValue(osTime, 24)

chilledWaterSPM = OpenStudio::Model::SetpointManagerScheduled.new(model, chilledWaterTempSchedule)
chilledWaterSPM.addToNode(chilledWaterOutletNode)

# make some schedules to control the temperatures in the radiant coils
coolingHighWaterTempSched = OpenStudio::Model::ScheduleConstant.new(model)
coolingLowWaterTempSched = OpenStudio::Model::ScheduleConstant.new(model)
coolingHighControlTempSched = OpenStudio::Model::ScheduleConstant.new(model)
coolingLowControlTempSched = OpenStudio::Model::ScheduleConstant.new(model)
heatingHighWaterTempSched = OpenStudio::Model::ScheduleConstant.new(model)
heatingLowWaterTempSched = OpenStudio::Model::ScheduleConstant.new(model)
heatingHighControlTempSched = OpenStudio::Model::ScheduleConstant.new(model)
heatingLowControlTempSched = OpenStudio::Model::ScheduleConstant.new(model)

coolingHighWaterTempSched.setValue(15.0)
coolingLowWaterTempSched.setValue(10.0)
coolingHighControlTempSched.setValue(25.0)
coolingLowControlTempSched.setValue(21.0)
heatingHighWaterTempSched.setValue(50.0)
heatingLowWaterTempSched.setValue(30.0)
heatingHighControlTempSched.setValue(20.0)
heatingLowControlTempSched.setValue(17.0)

# add a Low Temperature Radiant system to each zone
zones.each do |z|
  heat_coil = OpenStudio::Model::CoilHeatingLowTempRadiantConstFlow.new(model, heatingHighWaterTempSched, heatingLowWaterTempSched, heatingHighControlTempSched, heatingLowControlTempSched)
  cool_coil = OpenStudio::Model::CoilCoolingLowTempRadiantConstFlow.new(model, coolingHighWaterTempSched, coolingLowWaterTempSched, coolingHighControlTempSched, coolingLowControlTempSched)

  lowtempradiant = OpenStudio::Model::ZoneHVACLowTempRadiantConstFlow.new(model, model.alwaysOnDiscreteSchedule, heat_coil, cool_coil, 200.0)
  lowtempradiant.setRadiantSurfaceType('Floors')
  lowtempradiant.setHydronicTubingInsideDiameter(0.154)
  lowtempradiant.setHydronicTubingLength(200)
  lowtempradiant.setTemperatureControlType('MeanRadiantTemperature')
  pumpflowratesch = OpenStudio::Model::ScheduleConstant.new(model)
  pumpflowratesch.setValue(1.0)
  lowtempradiant.setPumpFlowRateSchedule(pumpflowratesch)
  lowtempradiant.setRatedFlowRate(0.005)
  lowtempradiant.setMotorEfficiency(0.9)
  lowtempradiant.setRatedPowerConsumption(1200)

  lowtempradiant.addToThermalZone(z)

  hotWaterPlant.addDemandBranchForComponent(heat_coil)
  chilledWaterPlant.addDemandBranchForComponent(cool_coil)
end

# add thermostats
# model.add_thermostats({"heating_setpoint" => 24,"cooling_setpoint" => 28})

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# create an internalsourceconstruction

intSourceConst = OpenStudio::Model::ConstructionWithInternalSource.new(model)
intSourceConst.setSourcePresentAfterLayerNumber(3)
intSourceConst.setTemperatureCalculationRequestedAfterLayerNumber(3)
layers = [] # OpenStudio::Model::MaterialVector.new(model)
layers << concrete_sand_gravel = OpenStudio::Model::StandardOpaqueMaterial.new(model, 'MediumRough', 0.1014984, 1.729577, 2242.585, 836.8)
layers << rigid_insulation_2inch = OpenStudio::Model::StandardOpaqueMaterial.new(model, 'Rough', 0.05, 0.02, 56.06, 1210)
layers << gyp1 = OpenStudio::Model::StandardOpaqueMaterial.new(model, 'MediumRough', 0.0127, 0.7845, 1842.1221, 988)
layers << gyp2 = OpenStudio::Model::StandardOpaqueMaterial.new(model, 'MediumRough', 0.01905, 0.7845, 1842.1221, 988)
layers << finished_floor = OpenStudio::Model::StandardOpaqueMaterial.new(model, 'Smooth', 0.0016, 0.17, 1922.21, 1250)

intSourceConst.setLayers(layers)

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# find a surface that's of surface type floor and assign the surface internal source construction
model.getSurfaces.each do |s|
  if s.surfaceType == 'Floor'
    s.setConstruction(intSourceConst)
  end
end

# add design days to the model (Chicago)
model.add_design_days

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
