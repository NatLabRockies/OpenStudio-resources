import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac(ashrae_sys_num="07")

# In order to produce more consistent results between different runs,
# We ensure we do get the same object each time
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

airLoops = sorted(model.getAirLoopHVACs(), key=lambda a: a.nameString())
regularAirLoopHVAC = airLoops[0]

chillers = sorted(model.getChillerElectricEIRs(), key=lambda c: c.nameString())
boilers = sorted(model.getBoilerHotWaters(), key=lambda c: c.nameString())

cooling_loop = chillers[0].plantLoop().get()
heating_loop = boilers[0].plantLoop().get()

alwaysOn = model.alwaysOnDiscreteSchedule()

###############################################################################
#                       D E M O N S T R A T E    A P I                        #
###############################################################################

fan = openstudio.model.FanComponentModel(model)
# Demonstrate API
fan.setName("My FanComponentModel")

# Availability Schedule Name: Required Object
sch = openstudio.model.ScheduleConstant(model)
sch.setName("Fan Avail Schedule")
sch.setValue(1.0)
fan.setAvailabilitySchedule(sch)

vSDExample = openstudio.model.CurveFanPressureRise(model)
vSDExample.setName("VSD Example")
vSDExample.setCoefficient1C1(1446.75833497653)
vSDExample.setCoefficient2C2(0.0)
vSDExample.setCoefficient3C3(0.0)
vSDExample.setCoefficient4C4(1.0)
vSDExample.setMinimumValueofQfan(0.0)
vSDExample.setMaximumValueofQfan(100.0)
vSDExample.setMinimumValueofPsm(62.5)
vSDExample.setMaximumValueofPsm(300.0)
vSDExample.setMinimumCurveOutput(0.0)
vSDExample.setMaximumCurveOutput(5000.0)

diagnosticSPR = openstudio.model.CurveLinear(model)
diagnosticSPR.setName("DiagnosticSPR")
diagnosticSPR.setCoefficient1Constant(248.84)
diagnosticSPR.setCoefficient2x(0.0)
diagnosticSPR.setMinimumValueofx(0.0)
diagnosticSPR.setMaximumValueofx(100.0)
diagnosticSPR.setMinimumCurveOutput(62.5)
diagnosticSPR.setMaximumCurveOutput(248.84)
# diagnosticSPR.setInputUnitTypeforX("")
# diagnosticSPR.setOutputUnitType("")

fanEff120CPLANormal = openstudio.model.CurveExponentialSkewNormal(model)
fanEff120CPLANormal.setName("FanEff120CPLANormal")
fanEff120CPLANormal.setCoefficient1C1(0.072613)
fanEff120CPLANormal.setCoefficient2C2(0.833213)
fanEff120CPLANormal.setCoefficient3C3(0.0)
fanEff120CPLANormal.setCoefficient4C4(0.013911)
fanEff120CPLANormal.setMinimumValueofx(-4.0)
fanEff120CPLANormal.setMaximumValueofx(5.0)
fanEff120CPLANormal.setMinimumCurveOutput(0.1)
fanEff120CPLANormal.setMaximumCurveOutput(1.0)
# fanEff120CPLANormal.setInputUnitTypeforx("")
# fanEff120CPLANormal.setOutputUnitType("")

fanEff120CPLAStall = openstudio.model.CurveExponentialSkewNormal(model)
fanEff120CPLAStall.setName("FanEff120CPLAStall")
fanEff120CPLAStall.setCoefficient1C1(-1.674931)
fanEff120CPLAStall.setCoefficient2C2(1.980182)
fanEff120CPLAStall.setCoefficient3C3(0.0)
fanEff120CPLAStall.setCoefficient4C4(1.84495)
fanEff120CPLAStall.setMinimumValueofx(-4.0)
fanEff120CPLAStall.setMaximumValueofx(5.0)
fanEff120CPLAStall.setMinimumCurveOutput(0.1)
fanEff120CPLAStall.setMaximumCurveOutput(1.0)
# fanEff120CPLAStall.setInputUnitTypeforx("")
# fanEff120CPLAStall.setOutputUnitType("")

fanDimFlowNormal = openstudio.model.CurveSigmoid(model)
fanDimFlowNormal.setName("FanDimFlowNormal")
fanDimFlowNormal.setCoefficient1C1(0.0)
fanDimFlowNormal.setCoefficient2C2(1.001423)
fanDimFlowNormal.setCoefficient3C3(0.123935)
fanDimFlowNormal.setCoefficient4C4(-0.476026)
fanDimFlowNormal.setCoefficient5C5(1.0)
fanDimFlowNormal.setMinimumValueofx(-4.0)
fanDimFlowNormal.setMaximumValueofx(5.0)
fanDimFlowNormal.setMinimumCurveOutput(0.05)
fanDimFlowNormal.setMaximumCurveOutput(1.0)
# fanDimFlowNormal.setInputUnitTypeforx("")
# fanDimFlowNormal.setOutputUnitType("")

fanDimFlowStall = openstudio.model.CurveSigmoid(model)
fanDimFlowStall.setName("FanDimFlowStall")
fanDimFlowStall.setCoefficient1C1(0.0)
fanDimFlowStall.setCoefficient2C2(5.924993)
fanDimFlowStall.setCoefficient3C3(-1.91636)
fanDimFlowStall.setCoefficient4C4(-0.851779)
fanDimFlowStall.setCoefficient5C5(1.0)
fanDimFlowStall.setMinimumValueofx(-4.0)
fanDimFlowStall.setMaximumValueofx(5.0)
fanDimFlowStall.setMinimumCurveOutput(0.05)
fanDimFlowStall.setMaximumCurveOutput(1.0)
# fanDimFlowStall.setInputUnitTypeforx("")
# fanDimFlowStall.setOutputUnitType("")

beltMaxEffMedium = openstudio.model.CurveQuartic(model)
beltMaxEffMedium.setName("BeltMaxEffMedium")
beltMaxEffMedium.setCoefficient1Constant(-0.09504)
beltMaxEffMedium.setCoefficient2x(0.03415)
beltMaxEffMedium.setCoefficient3xPOW2(-0.008897)
beltMaxEffMedium.setCoefficient4xPOW3(0.001159)
beltMaxEffMedium.setCoefficient5xPOW4(-6.132e-05)
beltMaxEffMedium.setMinimumValueofx(-1.2)
beltMaxEffMedium.setMaximumValueofx(6.2)
beltMaxEffMedium.setMinimumCurveOutput(-4.6)
beltMaxEffMedium.setMaximumCurveOutput(0.0)
# beltMaxEffMedium.setInputUnitTypeforX("")
# beltMaxEffMedium.setOutputUnitType("")

beltPartLoadRegion1 = openstudio.model.CurveRectangularHyperbola2(model)
beltPartLoadRegion1.setName("BeltPartLoadRegion1")
beltPartLoadRegion1.setCoefficient1C1(0.920797)
beltPartLoadRegion1.setCoefficient2C2(0.0262686)
beltPartLoadRegion1.setCoefficient3C3(0.151594)
beltPartLoadRegion1.setMinimumValueofx(0.0)
beltPartLoadRegion1.setMaximumValueofx(1.0)
beltPartLoadRegion1.setMinimumCurveOutput(0.01)
beltPartLoadRegion1.setMaximumCurveOutput(1.0)
# beltPartLoadRegion1.setInputUnitTypeforx("")
# beltPartLoadRegion1.setOutputUnitType("")

beltPartLoadRegion2 = openstudio.model.CurveExponentialDecay(model)
beltPartLoadRegion2.setName("BeltPartLoadRegion2")
beltPartLoadRegion2.setCoefficient1C1(1.011965)
beltPartLoadRegion2.setCoefficient2C2(-0.339038)
beltPartLoadRegion2.setCoefficient3C3(-3.43626)
beltPartLoadRegion2.setMinimumValueofx(0.0)
beltPartLoadRegion2.setMaximumValueofx(1.0)
beltPartLoadRegion2.setMinimumCurveOutput(0.01)
beltPartLoadRegion2.setMaximumCurveOutput(1.0)
# beltPartLoadRegion2.setInputUnitTypeforx("")
# beltPartLoadRegion2.setOutputUnitType("")

beltPartLoadRegion3 = openstudio.model.CurveRectangularHyperbola2(model)
beltPartLoadRegion3.setName("BeltPartLoadRegion3")
beltPartLoadRegion3.setCoefficient1C1(1.037778)
beltPartLoadRegion3.setCoefficient2C2(0.0103068)
beltPartLoadRegion3.setCoefficient3C3(-0.0268146)
beltPartLoadRegion3.setMinimumValueofx(0.0)
beltPartLoadRegion3.setMaximumValueofx(1.0)
beltPartLoadRegion3.setMinimumCurveOutput(0.01)
beltPartLoadRegion3.setMaximumCurveOutput(1.0)
# beltPartLoadRegion3.setInputUnitTypeforx("")
# beltPartLoadRegion3.setOutputUnitType("")

motorMaxEffAvg = openstudio.model.CurveRectangularHyperbola1(model)
motorMaxEffAvg.setName("MotorMaxEffAvg")
motorMaxEffAvg.setCoefficient1C1(0.29228)
motorMaxEffAvg.setCoefficient2C2(3.368739)
motorMaxEffAvg.setCoefficient3C3(0.762471)
motorMaxEffAvg.setMinimumValueofx(0.0)
motorMaxEffAvg.setMaximumValueofx(7.6)
motorMaxEffAvg.setMinimumCurveOutput(0.01)
motorMaxEffAvg.setMaximumCurveOutput(1.0)
# motorMaxEffAvg.setInputUnitTypeforx("")
# motorMaxEffAvg.setOutputUnitType("")

motorPartLoad = openstudio.model.CurveRectangularHyperbola2(model)
motorPartLoad.setName("MotorPartLoad")
motorPartLoad.setCoefficient1C1(1.137209)
motorPartLoad.setCoefficient2C2(0.0502359)
motorPartLoad.setCoefficient3C3(-0.0891503)
motorPartLoad.setMinimumValueofx(0.0)
motorPartLoad.setMaximumValueofx(1.0)
motorPartLoad.setMinimumCurveOutput(0.01)
motorPartLoad.setMaximumCurveOutput(1.0)
# motorPartLoad.setInputUnitTypeforx("")
# motorPartLoad.setOutputUnitType("")

vFDPartLoad = openstudio.model.CurveRectangularHyperbola2(model)
vFDPartLoad.setName("VFDPartLoad")
vFDPartLoad.setCoefficient1C1(0.987405)
vFDPartLoad.setCoefficient2C2(0.0155361)
vFDPartLoad.setCoefficient3C3(-0.0059365)
vFDPartLoad.setMinimumValueofx(0.0)
vFDPartLoad.setMaximumValueofx(1.0)
vFDPartLoad.setMinimumCurveOutput(0.01)
vFDPartLoad.setMaximumCurveOutput(1.0)
# vFDPartLoad.setInputUnitTypeforx("")
# vFDPartLoad.setOutputUnitType("")

fan.setName("Fan Component model")
fan.autosizeMaximumFlowRate()
fan.autosizeMinimumFlowRate()
fan.setFanSizingFactor(1.0)
fan.setFanWheelDiameter(0.3048)
fan.setFanOutletArea(0.0873288576)
fan.setMaximumFanStaticEfficiency(0.514)
fan.setEulerNumberatMaximumFanStaticEfficiency(9.76)
fan.setMaximumDimensionlessFanAirflow(0.160331811647483)
fan.autosizeMotorFanPulleyRatio()
fan.autosizeBeltMaximumTorque()
fan.setBeltSizingFactor(1.0)
fan.setBeltFractionalTorqueTransition(0.167)
fan.setMotorMaximumSpeed(1800.0)
fan.autosizeMaximumMotorOutputPower()
fan.setMotorSizingFactor(1.0)
fan.setMotorInAirstreamFraction(1.0)
fan.setVFDEfficiencyType("Power")
fan.autosizeMaximumVFDOutputPower()
fan.setVFDSizingFactor(1.0)
fan.setFanPressureRiseCurve(vSDExample)
fan.setDuctStaticPressureResetCurve(diagnosticSPR)
fan.setNormalizedFanStaticEfficiencyCurveNonStallRegion(fanEff120CPLANormal)
fan.setNormalizedFanStaticEfficiencyCurveStallRegion(fanEff120CPLAStall)
fan.setNormalizedDimensionlessAirflowCurveNonStallRegion(fanDimFlowNormal)
fan.setNormalizedDimensionlessAirflowCurveStallRegion(fanDimFlowStall)
fan.setMaximumBeltEfficiencyCurve(beltMaxEffMedium)
fan.setNormalizedBeltEfficiencyCurveRegion1(beltPartLoadRegion1)
fan.setNormalizedBeltEfficiencyCurveRegion2(beltPartLoadRegion2)
fan.setNormalizedBeltEfficiencyCurveRegion3(beltPartLoadRegion3)
fan.setMaximumMotorEfficiencyCurve(motorMaxEffAvg)
fan.setNormalizedMotorEfficiencyCurve(motorPartLoad)
fan.setVFDEfficiencyCurve(vFDPartLoad)

# Add this fan as the supply fan of a regular AirLoopHVAC, removing the
# existing FanVariableVolume
regularAirLoopHVAC.supplyFan().get().remove()
fan.addToNode(regularAirLoopHVAC.supplyOutletNode())

# AirLoopHVACUnitarySystem
unitary_system = openstudio.model.AirLoopHVACUnitarySystem(model)
unitary_system_fan = openstudio.model.FanComponentModel(model)
unitary_system_cc = openstudio.model.CoilCoolingDXSingleSpeed(model)
unitary_system_hc = openstudio.model.CoilHeatingDXSingleSpeed(model)
supp_unitary_system_hc = openstudio.model.CoilHeatingElectric(model)
# unitary_system.setControlType("SetPoint")
unitary_system.setSupplyAirFanOperatingModeSchedule(alwaysOn)
unitary_system.setSupplyFan(unitary_system_fan)
unitary_system.setCoolingCoil(unitary_system_cc)
unitary_system.setHeatingCoil(unitary_system_hc)
unitary_system.setSupplementalHeatingCoil(supp_unitary_system_hc)
unitary_systemAirLoopHVAC = openstudio.model.AirLoopHVAC(model)
unitary_systemAirLoopHVAC.setName("AirLoopHVACUnitarySystem AirLoopHVAC")
unitary_system.addToNode(unitary_systemAirLoopHVAC.supplyOutletNode())

for i, z in enumerate(zones):
    # AirLoopHVACUnitarySystem
    if i == 0:

        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        new_terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, alwaysOn)

        unitary_systemAirLoopHVAC.addBranchForZone(z, new_terminal.to_StraightComponent())
        unitary_system.setControllingZoneorThermostatLocation(z)

    # ZoneHVACEvaporativeCoolerUnit: not wrapped yet as of 3.1.0
    # elif i == 1
    #   supplyFan = openstudio.model.FanSystemModel(model)
    #   zoneHVACEvaporativeCoolerUnit = openstudio.model.ZoneHVACEvaporativeCoolerUnit(model, supplyFan)
    #   zoneHVACEvaporativeCoolerUnit.addToThermalZone(z)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
