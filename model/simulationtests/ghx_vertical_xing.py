import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# No zones, just a LoadProfile:Plant

# add design days to the model (Chicago)
model.add_design_days()

USE_PIPE_INDOOR = False

if openstudio.VersionString(openstudio.openStudioVersion()) <= openstudio.VersionString("3.5.1"):
    raise ValueError("Cannot use XING on 3.5.1 and below")

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

xing = openstudio.model.SiteGroundTemperatureUndisturbedXing(model)
xing.setSoilThermalConductivity(1.08)
xing.setSoilDensity(962)
xing.setSoilSpecificHeat(2576)
xing.setAverageSoilSurfaceTemperature(11.1)
xing.setSoilSurfaceTemperatureAmplitude1(13.4)
xing.setSoilSurfaceTemperatureAmplitude2(0.7)
xing.setPhaseShiftofTemperatureAmplitude1(25)
xing.setPhaseShiftofTemperatureAmplitude2(30)
hGroundHX2 = openstudio.model.GroundHeatExchangerVertical(model, xing)
condenserWaterPlant.addSupplyBranchForComponent(hGroundHX2)

if USE_PIPE_INDOOR:
    pipe_mat = openstudio.model.StandardOpaqueMaterial(model, "Smooth", 3.00e-03, 45.31, 7833.0, 500.0)
    pipe_mat.setThermalAbsorptance(openstudio.OptionalDouble(0.9))
    pipe_mat.setSolarAbsorptance(openstudio.OptionalDouble(0.5))
    pipe_mat.setVisibleAbsorptance(openstudio.OptionalDouble(0.5))
    pipe_const = openstudio.model.Construction(model)
    pipe_const.insertLayer(0, pipe_mat)

    pipe = openstudio.model.PipeIndoor(model)
    pipe.setAmbientTemperatureZone(zone)
    pipe.setConstruction(pipe_const)
    condenserWaterPlant.addSupplyBranchForComponent(pipe)

    pipe2 = openstudio.model.PipeIndoor(model)
    pipe2.setAmbientTemperatureZone(zone)
    pipe2.setConstruction(pipe_const)
    pipe2.addToNode(condenserWaterOutletNode)

    pipe3 = openstudio.model.PipeIndoor(model)
    pipe3.setAmbientTemperatureZone(zone)
    pipe3.setConstruction(pipe_const)
    pipe3.addToNode(condenserWaterPlant.demandInletNode())

    pipe4 = openstudio.model.PipeIndoor(model)
    pipe4.setAmbientTemperatureZone(zone)
    pipe4.setConstruction(pipe_const)
    pipe4.addToNode(condenserWaterPlant.demandOutletNode())

    pipe5 = openstudio.model.PipeIndoor(model)
    pipe5.setAmbientTemperatureZone(zone)
    pipe5.setConstruction(pipe_const)
    condenserWaterPlant.addDemandBranchForComponent(pipe5)


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

condenserWaterPlant.setMaximumLoopTemperature(80.0)
condenserWaterPlant.setMaximumLoopFlowRate(0.004)
condenserWaterPlant.setFluidType("PropyleneGlycol")
condenserWaterPlant.setGlycolConcentration(70)

pump.setRatedFlowRate(0.004)
pump.setRatedPumpHead(5000.0)
pump.setRatedPowerConsumption(25.0)
pump.setFractionofMotorInefficienciestoFluidStream(0.0)
pump.setPumpControlType("Intermittent")

# Load Profile
loadProfile = openstudio.model.LoadProfilePlant(model)
loadProfile.setPeakFlowRate(0.004)

flowFracSchedule = openstudio.model.ScheduleConstant(model)
flowFracSchedule.setName("FlowFracSchedule")
flowFracSchedule.setValue(1.0)
loadProfile.setFlowRateFractionSchedule(flowFracSchedule)

loadSchedule = openstudio.model.ScheduleRuleset(model)
loadSchedule.setName("LoadSchedule")
loadSchedule.defaultDaySchedule().addValue(osTime, 2000.0)
loadSchedule_may_to_sept_rule = openstudio.model.ScheduleRule(loadSchedule)
loadSchedule_may_to_sept_rule.setStartDate(openstudio.Date(openstudio.MonthOfYear("May"), 1))
loadSchedule_may_to_sept_rule.setEndDate(openstudio.Date(openstudio.MonthOfYear("September"), 30))
loadSchedule_may_to_sept_rule.daySchedule().addValue(osTime, -3000.0)
loadProfile.setLoadSchedule(loadSchedule)

condenserWaterPlant.addDemandBranchForComponent(loadProfile)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
