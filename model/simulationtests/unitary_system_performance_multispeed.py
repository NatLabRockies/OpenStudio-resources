import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

schedule = model.alwaysOnDiscreteSchedule()

_hotWaterSchedule = openstudio.model.ScheduleRuleset(model)
_hotWaterSchedule.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 67)

_chilledWaterSchedule = openstudio.model.ScheduleRuleset(model)
_chilledWaterSchedule.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 6.7)

# Hot Water Plant
hotWaterPlant = openstudio.model.PlantLoop(model)
sizingPlant = hotWaterPlant.sizingPlant()
sizingPlant.setLoopType("Heating")
sizingPlant.setDesignLoopExitTemperature(82.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

hotWaterOutletNode = hotWaterPlant.supplyOutletNode()
hotWaterInletNode = hotWaterPlant.supplyInletNode()
hotWaterDemandOutletNode = hotWaterPlant.demandOutletNode()
hotWaterDemandInletNode = hotWaterPlant.demandInletNode()

pump = openstudio.model.PumpVariableSpeed(model)
boiler = openstudio.model.BoilerHotWater(model)

pump.addToNode(hotWaterInletNode)
node = hotWaterPlant.supplySplitter().lastOutletModelObject().get().to_Node().get()
boiler.addToNode(node)

pipe = openstudio.model.PipeAdiabatic(model)
hotWaterPlant.addSupplyBranchForComponent(pipe)

hotWaterBypass = openstudio.model.PipeAdiabatic(model)
hotWaterDemandInlet = openstudio.model.PipeAdiabatic(model)
hotWaterDemandOutlet = openstudio.model.PipeAdiabatic(model)
hotWaterPlant.addDemandBranchForComponent(hotWaterBypass)
hotWaterDemandOutlet.addToNode(hotWaterDemandOutletNode)
hotWaterDemandInlet.addToNode(hotWaterDemandInletNode)

pipe2 = openstudio.model.PipeAdiabatic(model)
pipe2.addToNode(hotWaterOutletNode)

hotWaterSPM = openstudio.model.SetpointManagerScheduled(model, _hotWaterSchedule)
hotWaterSPM.addToNode(hotWaterOutletNode)

# Chilled Water Plant
chilledWaterPlant = openstudio.model.PlantLoop(model)
sizingPlant = chilledWaterPlant.sizingPlant()
sizingPlant.setLoopType("Cooling")
sizingPlant.setDesignLoopExitTemperature(7.22)
sizingPlant.setLoopDesignTemperatureDifference(6.67)

chilledWaterOutletNode = chilledWaterPlant.supplyOutletNode()
chilledWaterInletNode = chilledWaterPlant.supplyInletNode()
chilledWaterDemandOutletNode = chilledWaterPlant.demandOutletNode()
chilledWaterDemandInletNode = chilledWaterPlant.demandInletNode()

pump2 = openstudio.model.PumpVariableSpeed(model)
pump2.addToNode(chilledWaterInletNode)

ccFofT = openstudio.model.CurveBiquadratic(model)
ccFofT.setCoefficient1Constant(1.0215158)
ccFofT.setCoefficient2x(0.037035864)
ccFofT.setCoefficient3xPOW2(0.0002332476)
ccFofT.setCoefficient4y(-0.003894048)
ccFofT.setCoefficient5yPOW2(-6.52536e-005)
ccFofT.setCoefficient6xTIMESY(-0.0002680452)
ccFofT.setMinimumValueofx(5.0)
ccFofT.setMaximumValueofx(10.0)
ccFofT.setMinimumValueofy(24.0)
ccFofT.setMaximumValueofy(35.0)

eirToCorfOfT = openstudio.model.CurveBiquadratic(model)
eirToCorfOfT.setCoefficient1Constant(0.70176857)
eirToCorfOfT.setCoefficient2x(-0.00452016)
eirToCorfOfT.setCoefficient3xPOW2(0.0005331096)
eirToCorfOfT.setCoefficient4y(-0.005498208)
eirToCorfOfT.setCoefficient5yPOW2(0.0005445792)
eirToCorfOfT.setCoefficient6xTIMESY(-0.0007290324)
eirToCorfOfT.setMinimumValueofx(5.0)
eirToCorfOfT.setMaximumValueofx(10.0)
eirToCorfOfT.setMinimumValueofy(24.0)
eirToCorfOfT.setMaximumValueofy(35.0)

eirToCorfOfPlr = openstudio.model.CurveQuadratic(model)
eirToCorfOfPlr.setCoefficient1Constant(0.06369119)
eirToCorfOfPlr.setCoefficient2x(0.58488832)
eirToCorfOfPlr.setCoefficient3xPOW2(0.35280274)
eirToCorfOfPlr.setMinimumValueofx(0.0)
eirToCorfOfPlr.setMaximumValueofx(1.0)

chiller = openstudio.model.ChillerElectricEIR(model, ccFofT, eirToCorfOfT, eirToCorfOfPlr)

node = chilledWaterPlant.supplySplitter().lastOutletModelObject().get().to_Node().get()
chiller.addToNode(node)

pipe3 = openstudio.model.PipeAdiabatic(model)
chilledWaterPlant.addSupplyBranchForComponent(pipe3)

pipe4 = openstudio.model.PipeAdiabatic(model)
pipe4.addToNode(chilledWaterOutletNode)

chilledWaterSPM = openstudio.model.SetpointManagerScheduled(model, _chilledWaterSchedule)
chilledWaterSPM.addToNode(chilledWaterOutletNode)

chilledWaterBypass = openstudio.model.PipeAdiabatic(model)
chilledWaterDemandInlet = openstudio.model.PipeAdiabatic(model)
chilledWaterDemandOutlet = openstudio.model.PipeAdiabatic(model)
chilledWaterPlant.addDemandBranchForComponent(chilledWaterBypass)
chilledWaterDemandOutlet.addToNode(chilledWaterDemandOutletNode)
chilledWaterDemandInlet.addToNode(chilledWaterDemandInletNode)

# Condenser System
condenserSystem = openstudio.model.PlantLoop(model)
sizingPlant = condenserSystem.sizingPlant()
sizingPlant.setLoopType("Condenser")
sizingPlant.setDesignLoopExitTemperature(29.4)
sizingPlant.setLoopDesignTemperatureDifference(5.6)

# tower = openstudio.model.CoolingTowerSingleSpeed(model)
# condenserSystem.addSupplyBranchForComponent(tower)

distHeating = openstudio.model.DistrictHeating(model)
condenserSystem.addSupplyBranchForComponent(distHeating)

distCooling = openstudio.model.DistrictCooling(model)
condenserSystem.addSupplyBranchForComponent(distCooling)

condenserSupplyOutletNode = condenserSystem.supplyOutletNode()
condenserSupplyInletNode = condenserSystem.supplyInletNode()
condenserDemandOutletNode = condenserSystem.demandOutletNode()
condenserDemandInletNode = condenserSystem.demandInletNode()

pump3 = openstudio.model.PumpVariableSpeed(model)
pump3.addToNode(condenserSupplyInletNode)

# condenserSystem.addDemandBranchForComponent(chiller)

condenserSupplyBypass = openstudio.model.PipeAdiabatic(model)
condenserSystem.addSupplyBranchForComponent(condenserSupplyBypass)

condenserSupplyOutlet = openstudio.model.PipeAdiabatic(model)
condenserSupplyOutlet.addToNode(condenserSupplyOutletNode)

condenserBypass = openstudio.model.PipeAdiabatic(model)
condenserDemandInlet = openstudio.model.PipeAdiabatic(model)
condenserDemandOutlet = openstudio.model.PipeAdiabatic(model)
condenserSystem.addDemandBranchForComponent(condenserBypass)
condenserDemandOutlet.addToNode(condenserDemandOutletNode)
condenserDemandInlet.addToNode(condenserDemandInletNode)

spm = openstudio.model.SetpointManagerFollowOutdoorAirTemperature(model)
spm.addToNode(condenserSupplyOutletNode)

# In order to produce more consistent results between different runs,
# we sort the zones by names
# Otherwise the controlling Zone won't be the same
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

heating_curve_1 = openstudio.model.CurveCubic(model)
heating_curve_1.setCoefficient1Constant(0.758746)
heating_curve_1.setCoefficient2x(0.027626)
heating_curve_1.setCoefficient3xPOW2(0.000148716)
heating_curve_1.setCoefficient4xPOW3(0.0000034992)
heating_curve_1.setMinimumValueofx(-20.0)
heating_curve_1.setMaximumValueofx(20.0)

heating_curve_2 = openstudio.model.CurveCubic(model)
heating_curve_2.setCoefficient1Constant(0.84)
heating_curve_2.setCoefficient2x(0.16)
heating_curve_2.setCoefficient3xPOW2(0.0)
heating_curve_2.setCoefficient4xPOW3(0.0)
heating_curve_2.setMinimumValueofx(0.5)
heating_curve_2.setMaximumValueofx(1.5)

heating_curve_3 = openstudio.model.CurveCubic(model)
heating_curve_3.setCoefficient1Constant(1.19248)
heating_curve_3.setCoefficient2x(-0.0300438)
heating_curve_3.setCoefficient3xPOW2(0.00103745)
heating_curve_3.setCoefficient4xPOW3(-0.000023328)
heating_curve_3.setMinimumValueofx(-20.0)
heating_curve_3.setMaximumValueofx(20.0)

heating_curve_4 = openstudio.model.CurveQuadratic(model)
heating_curve_4.setCoefficient1Constant(1.3824)
heating_curve_4.setCoefficient2x(-0.4336)
heating_curve_4.setCoefficient3xPOW2(0.0512)
heating_curve_4.setMinimumValueofx(0.0)
heating_curve_4.setMaximumValueofx(1.0)

heating_curve_5 = openstudio.model.CurveQuadratic(model)
heating_curve_5.setCoefficient1Constant(0.75)
heating_curve_5.setCoefficient2x(0.25)
heating_curve_5.setCoefficient3xPOW2(0.0)
heating_curve_5.setMinimumValueofx(0.0)
heating_curve_5.setMaximumValueofx(1.0)

cooling_curve_1 = openstudio.model.CurveBiquadratic(model)
cooling_curve_1.setCoefficient1Constant(0.766956)
cooling_curve_1.setCoefficient2x(0.0107756)
cooling_curve_1.setCoefficient3xPOW2(-0.0000414703)
cooling_curve_1.setCoefficient4y(0.00134961)
cooling_curve_1.setCoefficient5yPOW2(-0.000261144)
cooling_curve_1.setCoefficient6xTIMESY(0.000457488)
cooling_curve_1.setMinimumValueofx(17.0)
cooling_curve_1.setMaximumValueofx(22.0)
cooling_curve_1.setMinimumValueofy(13.0)
cooling_curve_1.setMaximumValueofy(46.0)
cooling_curve_1_alt = cooling_curve_1.clone().to_CurveBiquadratic().get()

cooling_curve_2 = openstudio.model.CurveQuadratic(model)
cooling_curve_2.setCoefficient1Constant(0.8)
cooling_curve_2.setCoefficient2x(0.2)
cooling_curve_2.setCoefficient3xPOW2(0.0)
cooling_curve_2.setMinimumValueofx(0.5)
cooling_curve_2.setMaximumValueofx(1.5)
cooling_curve_2_alt = cooling_curve_2.clone().to_CurveQuadratic().get()

cooling_curve_3 = openstudio.model.CurveBiquadratic(model)
cooling_curve_3.setCoefficient1Constant(0.297145)
cooling_curve_3.setCoefficient2x(0.0430933)
cooling_curve_3.setCoefficient3xPOW2(-0.000748766)
cooling_curve_3.setCoefficient4y(0.00597727)
cooling_curve_3.setCoefficient5yPOW2(0.000482112)
cooling_curve_3.setCoefficient6xTIMESY(-0.000956448)
cooling_curve_3.setMinimumValueofx(17.0)
cooling_curve_3.setMaximumValueofx(22.0)
cooling_curve_3.setMinimumValueofy(13.0)
cooling_curve_3.setMaximumValueofy(46.0)
cooling_curve_3_alt = cooling_curve_3.clone().to_CurveBiquadratic().get()

cooling_curve_4 = openstudio.model.CurveQuadratic(model)
cooling_curve_4.setCoefficient1Constant(1.156)
cooling_curve_4.setCoefficient2x(-0.1816)
cooling_curve_4.setCoefficient3xPOW2(0.0256)
cooling_curve_4.setMinimumValueofx(0.5)
cooling_curve_4.setMaximumValueofx(1.5)
cooling_curve_4_alt = cooling_curve_4.clone().to_CurveQuadratic().get()

cooling_curve_5 = openstudio.model.CurveQuadratic(model)
cooling_curve_5.setCoefficient1Constant(0.75)
cooling_curve_5.setCoefficient2x(0.25)
cooling_curve_5.setCoefficient3xPOW2(0.0)
cooling_curve_5.setMinimumValueofx(0.0)
cooling_curve_5.setMaximumValueofx(1.0)
cooling_curve_5_alt = cooling_curve_5.clone().to_CurveQuadratic().get()

cooling_curve_6 = openstudio.model.CurveBiquadratic(model)
cooling_curve_6.setCoefficient1Constant(0.42415)
cooling_curve_6.setCoefficient2x(0.04426)
cooling_curve_6.setCoefficient3xPOW2(-0.00042)
cooling_curve_6.setCoefficient4y(0.00333)
cooling_curve_6.setCoefficient5yPOW2(-0.00008)
cooling_curve_6.setCoefficient6xTIMESY(-0.00021)
cooling_curve_6.setMinimumValueofx(17.0)
cooling_curve_6.setMaximumValueofx(22.0)
cooling_curve_6.setMinimumValueofy(13.0)
cooling_curve_6.setMaximumValueofy(46.0)

cooling_curve_7 = openstudio.model.CurveBiquadratic(model)
cooling_curve_7.setCoefficient1Constant(1.23649)
cooling_curve_7.setCoefficient2x(-0.02431)
cooling_curve_7.setCoefficient3xPOW2(0.00057)
cooling_curve_7.setCoefficient4y(-0.01434)
cooling_curve_7.setCoefficient5yPOW2(0.00063)
cooling_curve_7.setCoefficient6xTIMESY(-0.00038)
cooling_curve_7.setMinimumValueofx(17.0)
cooling_curve_7.setMaximumValueofx(22.0)
cooling_curve_7.setMinimumValueofy(13.0)
cooling_curve_7.setMaximumValueofy(46.0)

# Unitary System test 5
airLoop_5 = openstudio.model.AirLoopHVAC(model)
airLoop_5_supplyNode = airLoop_5.supplyOutletNode()

unitary_5 = openstudio.model.AirLoopHVACUnitarySystem(model)
fan_5 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_5 = openstudio.model.CoilCoolingDXMultiSpeed(model)
cool_stage_1 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
cool_stage_2 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
cooling_coil_5.addStage(cool_stage_1)
cooling_coil_5.addStage(cool_stage_2)
heating_coil_5 = openstudio.model.CoilHeatingDXMultiSpeed(model)
heat_stage_1 = openstudio.model.CoilHeatingDXMultiSpeedStageData(model)
heat_stage_2 = openstudio.model.CoilHeatingDXMultiSpeedStageData(model)
heating_coil_5.addStage(heat_stage_1)
heating_coil_5.addStage(heat_stage_2)
unitary_5.setControllingZoneorThermostatLocation(zones[4])
unitary_5.setFanPlacement("BlowThrough")
unitary_5.setSupplyAirFanOperatingModeSchedule(schedule)
unitary_5.setSupplyFan(fan_5)
unitary_5.setCoolingCoil(cooling_coil_5)
unitary_5.setHeatingCoil(heating_coil_5)

system_performance = openstudio.model.UnitarySystemPerformanceMultispeed(model)
system_performance.setSingleModeOperation(True)
system_performance.addSupplyAirflowRatioField(openstudio.model.SupplyAirflowRatioField())
system_performance.addSupplyAirflowRatioField(openstudio.model.SupplyAirflowRatioField(1.0, 1.0))
unitary_5.setDesignSpecificationMultispeedObject(system_performance)

unitary_5.addToNode(airLoop_5_supplyNode)
air_terminal_5 = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)
airLoop_5.addBranchForZone(zones[4], air_terminal_5)

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
