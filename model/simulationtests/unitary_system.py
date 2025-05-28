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

# Unitary System test 1
airLoop_1 = openstudio.model.AirLoopHVAC(model)
airLoop_1_supplyNode = airLoop_1.supplyOutletNode()

unitary_1 = openstudio.model.AirLoopHVACUnitarySystem(model)
fan_1 = openstudio.model.FanVariableVolume(model, schedule)
cooling_coil_1 = openstudio.model.CoilCoolingDXSingleSpeed(
    model, schedule, cooling_curve_1, cooling_curve_2, cooling_curve_3, cooling_curve_4, cooling_curve_5
)
heating_coil_1 = openstudio.model.CoilHeatingDXSingleSpeed(
    model, schedule, heating_curve_1, heating_curve_2, heating_curve_3, heating_curve_4, heating_curve_5
)
supp_heating_coil_1 = openstudio.model.CoilHeatingElectric(model, schedule)
unitary_1.setControllingZoneorThermostatLocation(zones[0])
unitary_1.setFanPlacement("DrawThrough")
dehumidify_sch = openstudio.model.ScheduleConstant(model)
dehumidify_sch.setValue(50)
humidistat = openstudio.model.ZoneControlHumidistat(model)
humidistat.setHumidifyingRelativeHumiditySetpointSchedule(dehumidify_sch)
zones[0].setZoneControlHumidistat(humidistat)
unitary_1.setDehumidificationControlType("CoolReheat")
# unitary_1.setControlType("SetPoint")
unitary_1.setSupplyAirFanOperatingModeSchedule(schedule)
unitary_1.setSupplyFan(fan_1)
unitary_1.setCoolingCoil(cooling_coil_1)
unitary_1.setHeatingCoil(heating_coil_1)
unitary_1.setSupplementalHeatingCoil(supp_heating_coil_1)

unitary_1.addToNode(airLoop_1_supplyNode)
node_1 = unitary_1.airOutletModelObject().get().to_Node().get()
setpointMMA_1 = openstudio.model.SetpointManagerSingleZoneReheat(model)
setpointMMA_1.addToNode(node_1)

air_terminal_1 = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)
airLoop_1.addBranchForZone(zones[0], air_terminal_1)

# Unitary System test 2
# airLoop_2 = openstudio.model.AirLoopHVAC(model)
# airLoop_2_supplyNode = airLoop_2.supplyOutletNode()
#
# unitary_2 = openstudio.model.AirLoopHVACUnitarySystem(model)
# fan_2 = openstudio.model.FanVariableVolume(model, schedule)
# cooling_coil_2 = openstudio.model.CoilCoolingWater(model, schedule)
# chilledWaterPlant.addDemandBranchForComponent(cooling_coil_2)
# heating_coil_2 = openstudio.model.CoilHeatingWater(model, schedule)
# hotWaterPlant.addDemandBranchForComponent(heating_coil_2)
# unitary_2.setControllingZoneorThermostatLocation(zones[4])
# unitary_2.setFanPlacement("DrawThrough")
# unitary_2.setSupplyAirFanOperatingModeSchedule(schedule)
# unitary_2.setSupplyFan(fan_2)
# unitary_2.setCoolingCoil(cooling_coil_2)
# unitary_2.setHeatingCoil(heating_coil_2)
#
# hotWaterPlant.addSupplyBranchForComponent(unitary_2)
#
# unitary_2.addToNode(airLoop_2_supplyNode)
#
# air_terminal_2 = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)
# airLoop_2.addBranchForZone(zones[4], air_terminal_2)

# Unitary System test 3
airLoop_3 = openstudio.model.AirLoopHVAC(model)
airLoop_3_supplyNode = airLoop_3.supplyOutletNode()

unitary_3 = openstudio.model.AirLoopHVACUnitarySystem(model)
fan_3 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_3 = openstudio.model.CoilCoolingWaterToAirHeatPumpEquationFit(model)
chilledWaterPlant.addDemandBranchForComponent(cooling_coil_3)
heating_coil_3 = openstudio.model.CoilHeatingGas(model, schedule)
unitary_3.setControllingZoneorThermostatLocation(zones[2])
unitary_3.setFanPlacement("BlowThrough")
unitary_3.setSupplyAirFanOperatingModeSchedule(schedule)
unitary_3.setSupplyFan(fan_3)
unitary_3.setCoolingCoil(cooling_coil_3)
unitary_3.setHeatingCoil(heating_coil_3)

unitary_3.addToNode(airLoop_3_supplyNode)

air_terminal_3 = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)
airLoop_3.addBranchForZone(zones[2], air_terminal_3)

# Unitary System test 4
airLoop_4 = openstudio.model.AirLoopHVAC(model)
airLoop_4_supplyNode = airLoop_4.supplyOutletNode()

unitary_4 = openstudio.model.AirLoopHVACUnitarySystem(model)
fan_4 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_4 = openstudio.model.CoilCoolingWaterToAirHeatPumpVariableSpeedEquationFit(model)
speedData = openstudio.model.CoilCoolingWaterToAirHeatPumpVariableSpeedEquationFitSpeedData(model)
cooling_coil_4.addSpeed(speedData)
heating_coil_4 = openstudio.model.CoilHeatingWaterToAirHeatPumpVariableSpeedEquationFit(model)
speedData = openstudio.model.CoilHeatingWaterToAirHeatPumpVariableSpeedEquationFitSpeedData(model)
heating_coil_4.addSpeed(speedData)
unitary_4.setControllingZoneorThermostatLocation(zones[3])
unitary_4.setFanPlacement("BlowThrough")
unitary_4.setSupplyAirFanOperatingModeSchedule(schedule)
unitary_4.setSupplyFan(fan_4)
unitary_4.setCoolingCoil(cooling_coil_4)
unitary_4.setHeatingCoil(heating_coil_4)

condenserSystem.addDemandBranchForComponent(heating_coil_4)
condenserSystem.addDemandBranchForComponent(cooling_coil_4)

unitary_4.addToNode(airLoop_4_supplyNode)

air_terminal_4 = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)
airLoop_4.addBranchForZone(zones[3], air_terminal_4)

# Unitary System test 5
airLoop_5 = openstudio.model.AirLoopHVAC(model)
airLoop_5_supplyNode = airLoop_5.supplyOutletNode()

unitary_5 = openstudio.model.AirLoopHVACUnitarySystem(model)
fan_5 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_5 = openstudio.model.CoilCoolingDXTwoStageWithHumidityControlMode(model)
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

unitary_5.addToNode(airLoop_5_supplyNode)
air_terminal_5 = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)
airLoop_5.addBranchForZone(zones[4], air_terminal_5)

# Unitary System test 6
airLoop_6 = openstudio.model.AirLoopHVAC(model)
airLoop_6_supplyNode = airLoop_6.supplyOutletNode()

unitary_6 = openstudio.model.AirLoopHVACUnitarySystem(model)
fan_6 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_6 = openstudio.model.CoilCoolingWater(model)
chilledWaterPlant.addDemandBranchForComponent(cooling_coil_6)
heating_coil_6 = openstudio.model.CoilHeatingGasMultiStage(model)
heat_stage_1 = openstudio.model.CoilHeatingGasMultiStageStageData(model)
heat_stage_2 = openstudio.model.CoilHeatingGasMultiStageStageData(model)
heating_coil_6.addStage(heat_stage_1)
heating_coil_6.addStage(heat_stage_2)
unitary_6.setControllingZoneorThermostatLocation(zones[5])
unitary_6.setFanPlacement("BlowThrough")
unitary_6.setSupplyAirFanOperatingModeSchedule(schedule)
unitary_6.setSupplyFan(fan_6)
unitary_6.setCoolingCoil(cooling_coil_6)
unitary_6.setHeatingCoil(heating_coil_6)

unitary_6.addToNode(airLoop_6_supplyNode)
air_terminal_6 = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)
airLoop_6.addBranchForZone(zones[5], air_terminal_6)

# Unitary System test 7
airLoop_7 = openstudio.model.AirLoopHVAC(model)
airLoop_7_supplyNode = airLoop_7.supplyOutletNode()

unitary_7 = openstudio.model.AirLoopHVACUnitarySystem(model)
fan_7 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_7 = openstudio.model.CoilCoolingDXMultiSpeed(model)
cool_stage_1 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
cool_stage_2 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
cooling_coil_7.addStage(cool_stage_1)
cooling_coil_7.addStage(cool_stage_2)
heating_coil_7 = openstudio.model.CoilHeatingDXVariableSpeed(model)
heat_speed_1 = openstudio.model.CoilHeatingDXVariableSpeedSpeedData(model)
heat_speed_2 = openstudio.model.CoilHeatingDXVariableSpeedSpeedData(model)
heating_coil_7.addSpeed(heat_speed_1)
heating_coil_7.addSpeed(heat_speed_2)
unitary_7.setControllingZoneorThermostatLocation(zones[6])
unitary_7.setFanPlacement("BlowThrough")
unitary_7.setSupplyAirFanOperatingModeSchedule(schedule)
unitary_7.setSupplyFan(fan_7)
unitary_7.setCoolingCoil(cooling_coil_7)
unitary_7.setHeatingCoil(heating_coil_7)

unitary_7.addToNode(airLoop_7_supplyNode)
air_terminal_7 = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)
airLoop_7.addBranchForZone(zones[6], air_terminal_7)

# # Unitary System test 8
# airLoop_8 = openstudio.model.AirLoopHVAC(model)
# airLoop_8_supplyNode = airLoop_8.supplyOutletNode()

# unitary_8 = openstudio.model.AirLoopHVACUnitarySystem(model)
# fan_8 = openstudio.model.FanConstantVolume(model, schedule)
# coil_system_8 = openstudio.model.CoilSystemCoolingWaterHeatExchangerAssisted(model)
# hx_8 = openstudio.model.HeatExchangerAirToAirSensibleAndLatent(model)
# cooling_coil_8 = openstudio.model.CoilCoolingWater(model)
# chilledWaterPlant.addDemandBranchForComponent(cooling_coil_8)
# coil_system_8.setHeatExchanger(hx_8)
# coil_system_8.setCoolingCoil(cooling_coil_8)
# heating_coil_8 = openstudio.model.CoilHeatingWater(model)
# hotWaterPlant.addDemandBranchForComponent(heating_coil_8)
# unitary_8.setControllingZoneorThermostatLocation(zones[7])
# unitary_8.setFanPlacement("BlowThrough")
# unitary_8.setSupplyAirFanOperatingModeSchedule(schedule)
# unitary_8.setSupplyFan(fan_8)
# unitary_8.setCoolingCoil(coil_system_8)
# unitary_8.setHeatingCoil(heating_coil_8)

# unitary_8.addToNode(airLoop_8_supplyNode)
# air_terminal_8 = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)
# airLoop_8.addBranchForZone(zones[7], air_terminal_8)

# # Unitary System test 9
# airLoop_9 = openstudio.model.AirLoopHVAC(model)
# airLoop_9_supplyNode = airLoop_9.supplyOutletNode()

# unitary_9 = openstudio.model.AirLoopHVACUnitarySystem(model)
# fan_9 = openstudio.model.FanConstantVolume(model, schedule)
# coil_system_9 = openstudio.model.CoilSystemCoolingDXHeatExchangerAssisted(model)
# hx_9 = openstudio.model.HeatExchangerAirToAirSensibleAndLatent(model)
# cooling_coil_9 = openstudio.model.CoilCoolingDXSingleSpeed(model, schedule, cooling_curve_1, cooling_curve_2, cooling_curve_3, cooling_curve_4, cooling_curve_5)
# coil_system_9.setHeatExchanger(hx_9)
# coil_system_9.setCoolingCoil(cooling_coil_9)
# heating_coil_9 = openstudio.model.CoilHeatingWater(model)
# hotWaterPlant.addDemandBranchForComponent(heating_coil_9)
# unitary_9.setControllingZoneorThermostatLocation(zones[8])
# unitary_9.setFanPlacement("BlowThrough")
# unitary_9.setSupplyAirFanOperatingModeSchedule(schedule)
# unitary_9.setSupplyFan(fan_9)
# unitary_9.setCoolingCoil(coil_system_9)
# unitary_9.setHeatingCoil(heating_coil_9)

# unitary_9.addToNode(airLoop_9_supplyNode)
# air_terminal_9 = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)
# airLoop_9.addBranchForZone(zones[8], air_terminal_9)

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
