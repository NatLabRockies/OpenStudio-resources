# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# No zones, just a LoadProfile:Plant
# This is unfortunate but the only E+ example file that uses it is PlantHorizontalGroundHX.idf
# and it has just a LoadProfile:Plant, and nothing autosized
# We couldn't get this file to not throw a Plant run away temperature so we're
# matching the E+ test instead

# add design days to the model (Chicago)
model.add_design_days

USE_PIPE_INDOOR = false

raise 'Cannot use XING on 3.5.1 and below' if Gem::Version.new(OpenStudio.openStudioVersion) <= Gem::Version.new('3.5.1')

# Add a hot water plant to supply the water to air heat pump
# This could be baked into HVAC templates in the future
condenserWaterPlant = OpenStudio::Model::PlantLoop.new(model)
condenserWaterPlant.setName('Condenser Water Plant')

sizingPlant = condenserWaterPlant.sizingPlant()
sizingPlant.setLoopType('Heating')
sizingPlant.setDesignLoopExitTemperature(30.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

condenserWaterOutletNode = condenserWaterPlant.supplyOutletNode
condenserWaterInletNode = condenserWaterPlant.supplyInletNode

pump = OpenStudio::Model::PumpVariableSpeed.new(model)
pump.addToNode(condenserWaterInletNode)

xing = OpenStudio::Model::SiteGroundTemperatureUndisturbedXing.new(model)
xing.setSoilThermalConductivity(1.08)
xing.setSoilDensity(962)
xing.setSoilSpecificHeat(2576)
xing.setAverageSoilSurfaceTemperature(11.1)
xing.setSoilSurfaceTemperatureAmplitude1(13.4)
xing.setSoilSurfaceTemperatureAmplitude2(0.7)
xing.setPhaseShiftofTemperatureAmplitude1(25)
xing.setPhaseShiftofTemperatureAmplitude2(30)
hGroundHX2 = OpenStudio::Model::GroundHeatExchangerHorizontalTrench.new(model, xing)
condenserWaterPlant.addSupplyBranchForComponent(hGroundHX2)

if USE_PIPE_INDOOR
  pipe_mat = OpenStudio::Model::StandardOpaqueMaterial.new(model, 'Smooth', 3.00E-03, 45.31, 7833.0, 500.0)
  pipe_mat.setThermalAbsorptance(OpenStudio::OptionalDouble.new(0.9))
  pipe_mat.setSolarAbsorptance(OpenStudio::OptionalDouble.new(0.5))
  pipe_mat.setVisibleAbsorptance(OpenStudio::OptionalDouble.new(0.5))
  pipe_const = OpenStudio::Model::Construction.new(model)
  pipe_const.insertLayer(0, pipe_mat)

  pipe = OpenStudio::Model::PipeIndoor.new(model)
  pipe.setAmbientTemperatureZone(zone)
  pipe.setConstruction(pipe_const)
  condenserWaterPlant.addSupplyBranchForComponent(pipe)

  pipe2 = OpenStudio::Model::PipeIndoor.new(model)
  pipe2.setAmbientTemperatureZone(zone)
  pipe2.setConstruction(pipe_const)
  pipe2.addToNode(condenserWaterOutletNode)

  pipe3 = OpenStudio::Model::PipeIndoor.new(model)
  pipe3.setAmbientTemperatureZone(zone)
  pipe3.setConstruction(pipe_const)
  pipe3.addToNode(condenserWaterPlant.demandInletNode)

  pipe4 = OpenStudio::Model::PipeIndoor.new(model)
  pipe4.setAmbientTemperatureZone(zone)
  pipe4.setConstruction(pipe_const)
  pipe4.addToNode(condenserWaterPlant.demandOutletNode)

  pipe5 = OpenStudio::Model::PipeIndoor.new(model)
  pipe5.setAmbientTemperatureZone(zone)
  pipe5.setConstruction(pipe_const)
  condenserWaterPlant.addDemandBranchForComponent(pipe5)
end

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

condenserWaterPlant.setMaximumLoopTemperature(80.0)
condenserWaterPlant.setMaximumLoopFlowRate(0.004)
condenserWaterPlant.setFluidType('PropyleneGlycol')
condenserWaterPlant.setGlycolConcentration(70)

pump.setRatedFlowRate(0.004)
pump.setRatedPumpHead(5000.0)
pump.setRatedPowerConsumption(25.0)
pump.setFractionofMotorInefficienciestoFluidStream(0.0)
pump.setPumpControlType('Intermittent')

# Load Profile
loadProfile = OpenStudio::Model::LoadProfilePlant.new(model)
loadProfile.setPeakFlowRate(0.004)

flowFracSchedule = OpenStudio::Model::ScheduleConstant.new(model)
flowFracSchedule.setName('FlowFracSchedule')
flowFracSchedule.setValue(1.0)
loadProfile.setFlowRateFractionSchedule(flowFracSchedule)

loadSchedule = OpenStudio::Model::ScheduleRuleset.new(model)
loadSchedule.setName('LoadSchedule')
loadSchedule.defaultDaySchedule.addValue(osTime, 2000.0)
loadSchedule_may_to_sept_rule = OpenStudio::Model::ScheduleRule.new(loadSchedule)
loadSchedule_may_to_sept_rule.setStartDate(OpenStudio::Date.new('May'.to_MonthOfYear, 1))
loadSchedule_may_to_sept_rule.setEndDate(OpenStudio::Date.new('September'.to_MonthOfYear, 30))
loadSchedule_may_to_sept_rule.daySchedule.addValue(osTime, -3000.0)
loadProfile.setLoadSchedule(loadSchedule)

condenserWaterPlant.addDemandBranchForComponent(loadProfile)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
