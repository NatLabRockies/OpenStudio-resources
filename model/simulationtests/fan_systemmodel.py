import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 15 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=3, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

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

fan = openstudio.model.FanSystemModel(model)
# Demonstrate API
fan.setName("My FanSystemModel")

# Availability Schedule Name: Required Object
sch = openstudio.model.ScheduleConstant(model)
sch.setName("Fan Avail Schedule")
sch.setValue(1.0)
fan.setAvailabilitySchedule(sch)

# Design Maximum Air Flow Rate: Required Double, Autosizable
# fan.setDesignMaximumAirFlowRate(0.1)
fan.autosizeDesignMaximumAirFlowRate()

# Speed Control Method: Required String
# openstudio.model.FanSystemModel.speedControlMethodValues()
fan.setSpeedControlMethod("Discrete")

# Electric Power Minimum Flow Rate Fraction: Required Double
fan.setElectricPowerMinimumFlowRateFraction(0.0)

# Design Pressure Rise: Required Double
fan.setDesignPressureRise(121.5)

# Motor Efficiency: Required Double
fan.setMotorEfficiency(0.54)

# Motor In Air Stream Fraction: Required Double
fan.setMotorInAirStreamFraction(0.87)

# Design Electric Power Consumption: Required Double, Autosizable
# fan.setDesignElectricPowerConsumption(3112.8)
fan.autosizeDesignElectricPowerConsumption()

# Design Power Sizing Method: Required String (choice)
# openstudio.model.FanSystemModel.designPowerSizingMethodValues()
fan.setDesignPowerSizingMethod("TotalEfficiencyAndPressure")

# These two may not be used depending on the Design Power Sizing Method
# Electric Power Per Unit Flow Rate: Required Double
fan.setElectricPowerPerUnitFlowRate(1254.0)

# Electric Power Per Unit Flow Rate Per Unit Pressure: Required Double
fan.setElectricPowerPerUnitFlowRatePerUnitPressure(1.345)

# Fan Total Efficiency: Required Double
fan.setFanTotalEfficiency(0.59)

# Electric Power Function of Flow Fraction Curve Name: Optional Object
# Taken from PackagedTerminalHeatPump.idf
fanPowerFuncFlowCurve = openstudio.model.CurveCubic(model)
fanPowerFuncFlowCurve.setName("CombinedPowerAndFanEff")
fanPowerFuncFlowCurve.setCoefficient1Constant(0.0)
fanPowerFuncFlowCurve.setCoefficient2x(0.027411)
fanPowerFuncFlowCurve.setCoefficient3xPOW2(0.008740)
fanPowerFuncFlowCurve.setCoefficient4xPOW3(0.969563)
fanPowerFuncFlowCurve.setMinimumValueofx(0.5)
fanPowerFuncFlowCurve.setMaximumValueofx(1.5)
fanPowerFuncFlowCurve.setMinimumCurveOutput(0.01)
fanPowerFuncFlowCurve.setMaximumCurveOutput(1.5)
fan.setElectricPowerFunctionofFlowFractionCurve(fanPowerFuncFlowCurve)

# Night Ventilation Mode Pressure Rise: Optional Double
fan.setNightVentilationModePressureRise(356.0)

# Night Ventilation Mode Flow Fraction: Optional Double
fan.setNightVentilationModeFlowFraction(0.37)

# Motor Loss Zone Name: Optional Object
fan.setMotorLossZone(zones[0])

# Motor Loss Radiative Fraction: Required Double
fan.setMotorLossRadiativeFraction(0.15)

# End-Use Subcategory: Required String
fan.setEndUseSubcategory("My Fan")

# Speeds: used when Speed Control Method = Discrete
# You can add speeds one by one
fan.addSpeed(0.25, 0.1)
# Or you can call setSpeeds, which will clear any existing ones via
# `fan.removeAllSpeeds`
# You can use a vector, or just a ruby array
# speeds = openstudio.model.FanSystemModelSpeedVector.new
speeds = [
    openstudio.model.FanSystemModelSpeed(0.25, 0.1),
    openstudio.model.FanSystemModelSpeed(0.5, 0.3),
    openstudio.model.FanSystemModelSpeed(0.75, 0.7),
    openstudio.model.FanSystemModelSpeed(1.0, 1.0),
]
fan.setSpeeds(speeds)

# Add this fan as the supply fan of a regular AirLoopHVAC, removing the
# existing FanVariableVolume
regularAirLoopHVAC.supplyFan().get().remove()
fan.addToNode(regularAirLoopHVAC.supplyOutletNode())

# AirLoopHVACUnitaryHeatPumpAirToAir
# TODO: Currently not supported in E+
is_working_AirLoopHVACUnitaryHeatPumpAirToAir = False

# Unitary: MultiSpeed
# TODO: Currently not supported in E+
is_working_AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed = False

# AirLoopHVACUnitaryHeatPumpAirToAir
if is_working_AirLoopHVACUnitaryHeatPumpAirToAir:
    heating_coil = openstudio.model.CoilCoolingDXSingleSpeed(model)
    cooling_coil = openstudio.model.CoilCoolingDXSingleSpeed(model)
    supp_heating_coil = openstudio.model.CoilHeatingElectric(model)
    unitary_air_to_air = openstudio.model.AirLoopHVACUnitaryHeatPumpAirToAir(
        model, alwaysOn, fan, heating_coil, cooling_coil, supp_heating_coil
    )
    unitary_air_to_airAirLoopHVAC = openstudio.model.AirLoopHVAC(model)
    unitary_air_to_airAirLoopHVAC.setName("UnitaryHPAirToAir AirLoopHVAC")
    unitary_air_to_air.addToNode(unitary_air_to_airAirLoopHVAC.supplyOutletNode())


# Unitary: MultiSpeed
if is_working_AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed:
    unitary_fan = openstudio.model.FanSystemModel(model)
    unitary_htg_coil = openstudio.model.CoilHeatingDXMultiSpeed(model)
    htg_stage_1 = openstudio.model.CoilHeatingDXMultiSpeedStageData(model)
    htg_stage_2 = openstudio.model.CoilHeatingDXMultiSpeedStageData(model)
    htg_stage_3 = openstudio.model.CoilHeatingDXMultiSpeedStageData(model)
    htg_stage_4 = openstudio.model.CoilHeatingDXMultiSpeedStageData(model)
    unitary_htg_coil.addStage(htg_stage_1)
    unitary_htg_coil.addStage(htg_stage_2)
    unitary_htg_coil.addStage(htg_stage_3)
    unitary_htg_coil.addStage(htg_stage_4)
    unitary_clg_coil = openstudio.model.CoilCoolingDXMultiSpeed(model)
    clg_stage_1 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
    clg_stage_2 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
    clg_stage_3 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
    clg_stage_4 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
    unitary_clg_coil.addStage(clg_stage_1)
    unitary_clg_coil.addStage(clg_stage_2)
    unitary_clg_coil.addStage(clg_stage_3)
    unitary_clg_coil.addStage(clg_stage_4)
    sup_unitary_htg_coil = openstudio.model.CoilHeatingElectric(model)
    unitary_multispeed = openstudio.model.AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed(
        model, unitary_fan, unitary_htg_coil, unitary_clg_coil, sup_unitary_htg_coil
    )
    unitary_multispeed.setNumberofSpeedsforHeating(4)
    unitary_multispeed.setNumberofSpeedsforCooling(4)
    unitary_hp_airtoair_multispeedAirLoopHVAC = openstudio.model.AirLoopHVAC(model)
    unitary_hp_airtoair_multispeedAirLoopHVAC.setName("UnitaryHPAirToAirMultiSpeed AirLoopHVAC")
    unitary_multispeed.addToNode(unitary_hp_airtoair_multispeedAirLoopHVAC.supplyOutletNode())


# AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass
unitary_vav_fan = openstudio.model.FanSystemModel(model)
unitary_vav_cc = openstudio.model.CoilCoolingDXSingleSpeed(model)
unitary_vav_hc = openstudio.model.CoilHeatingGas(model)
unitary_vav_changeover = openstudio.model.AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass(
    model, unitary_vav_fan, unitary_vav_cc, unitary_vav_hc
)
unitary_vav_changeoverAirLoopHVAC = openstudio.model.AirLoopHVAC(model)
unitary_vav_changeoverAirLoopHVAC.setName("AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass AirLoopHVAC")
unitary_vav_changeover.addToNode(unitary_vav_changeoverAirLoopHVAC.supplyOutletNode())

# AirLoopHVACUnitarySystem
unitary_system = openstudio.model.AirLoopHVACUnitarySystem(model)
unitary_system_fan = openstudio.model.FanSystemModel(model)
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

dhw_loop = openstudio.model.addSHWLoop(model).to_PlantLoop().get()

hpwh_pumped = openstudio.model.WaterHeaterHeatPump(model)
hpwh_pumped_fan = openstudio.model.FanSystemModel(model)
old_hpwh_pumped_fan = hpwh_pumped.fan()
hpwh_pumped.setFan(hpwh_pumped_fan)
old_hpwh_pumped_fan.remove()
dhw_loop.addSupplyBranchForComponent(hpwh_pumped.tank())

# TODO: ENABLE AFTER NEW E+ RELEASE (9.2.0+)
# Having both a HPWH:Pumped and a HPWH:Wrapped makes E+ crash
# Fixed by https://github.com/NREL/energyplus/pull/7717 but not in any E+
# release yet
is_working_WaterThermalTanks = False
if is_working_WaterThermalTanks:
    hpwh_wrapped = openstudio.model.WaterHeaterHeatPumpWrappedCondenser(model)
    hpwh_wrapped_fan = openstudio.model.FanSystemModel(model)
    old_hpwh_wrapped_fan = hpwh_wrapped.fan()
    hpwh_wrapped.setFan(hpwh_wrapped_fan)
    old_hpwh_wrapped_fan.remove()
    dhw_loop.addSupplyBranchForComponent(hpwh_wrapped.tank())


for i, z in enumerate(zones):
    # ZoneHVACEnergyRecoveryVentilator
    if i == 0:

        supplyFan = openstudio.model.FanSystemModel(model)
        exhaustFan = openstudio.model.FanSystemModel(model)

        heatExchanger = openstudio.model.HeatExchangerAirToAirSensibleAndLatent(model)
        if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("3.8.0"):
            heatExchanger.assignHistoricalEffectivenessCurves()
        heatExchanger.setSupplyAirOutletTemperatureControl(False)

        zoneHVACEnergyRecoveryVentilator = openstudio.model.ZoneHVACEnergyRecoveryVentilator(
            model, heatExchanger, supplyFan, exhaustFan
        )
        zoneHVACEnergyRecoveryVentilatorController = openstudio.model.ZoneHVACEnergyRecoveryVentilatorController(model)
        zoneHVACEnergyRecoveryVentilator.setController(zoneHVACEnergyRecoveryVentilatorController)
        zoneHVACEnergyRecoveryVentilatorController.setHighHumidityControlFlag(False)
        zoneHVACEnergyRecoveryVentilator.addToThermalZone(z)

    # ZoneHVACFourPipeFanCoil
    elif i == 1:
        fan = openstudio.model.FanSystemModel(model)

        # ** Severe  ** GetFanCoilUnits: ZoneHVAC:FourPipeFanCoil: ZONE HVAC FOUR PIPE FAN COIL 1
        # **   ~~~   ** ...the fan type of the object : FAN SYSTEM MODEL 1 does not match with the capacity control method selected : VARIABLEFANVARIABLEFLOW please see I/O reference
        # **   ~~~   ** ...for VariableFanVariableFlow or VariableFanConstantFlow a Fan:Systemmodel should have Continuous speed control.
        fan.setSpeedControlMethod("Continuous")

        # ** Warning ** HVACFan constructor Fan:Systemmodel="FAN SYSTEM MODEL 1", invalid entry.
        # **   ~~~   ** Continuous speed control requires a fan power curve in Electric Power Function of Flow Fraction Curve Name =
        # **  Fatal  ** HVACFan constructor Errors found in input for fan name = FAN SYSTEM MODEL 1.  Program terminates.
        fan.setElectricPowerFunctionofFlowFractionCurve(fanPowerFuncFlowCurve)

        heating_coil = openstudio.model.CoilHeatingWater(model)
        cooling_coil = openstudio.model.CoilCoolingWater(model)
        four_pipe_fan_coil = openstudio.model.ZoneHVACFourPipeFanCoil(model, alwaysOn, fan, cooling_coil, heating_coil)
        four_pipe_fan_coil.addToThermalZone(z)
        heating_loop.addDemandBranchForComponent(heating_coil)
        cooling_loop.addDemandBranchForComponent(cooling_coil)

    # ZoneHVACPackagedTerminalAirConditioner
    elif i == 2:
        thermal_zone_vector = openstudio.model.ThermalZoneVector()
        thermal_zone_vector.append(z)
        openstudio.model.addSystemType1(model, thermal_zone_vector)
        fan = openstudio.model.FanSystemModel(model)
        ptacs = model.getZoneHVACPackagedTerminalAirConditioners()
        fan_cv = ptacs[0].supplyAirFan()
        ptacs[0].setSupplyAirFan(fan)
        fan_cv.remove()

    # ZoneHVACPackagedTerminalHeatPump
    elif i == 3:
        thermal_zone_vector = openstudio.model.ThermalZoneVector()
        thermal_zone_vector.append(z)
        openstudio.model.addSystemType2(model, thermal_zone_vector)
        fan = openstudio.model.FanSystemModel(model)
        pthps = model.getZoneHVACPackagedTerminalHeatPumps()
        fan_cv = pthps[0].supplyAirFan()
        pthps[0].setSupplyAirFan(fan)
        fan_cv.remove()

    # ZoneHVAC:TerminalUnit:VariableRefrigerantFlow
    elif i == 4:
        fan = openstudio.model.FanSystemModel(model)
        cc = openstudio.model.CoilCoolingDXVariableRefrigerantFlow(model)
        hc = openstudio.model.CoilHeatingDXVariableRefrigerantFlow(model)
        vrf = openstudio.model.AirConditionerVariableRefrigerantFlow(model)
        # E+ now throws when the CoolingEIRLowPLR has a curve minimum value of x which
        # is higher than the Minimum Heat Pump Part-Load Ratio.
        # The curve has a min of 0.5 here, so set the MinimumHeatPumpPartLoadRatio to
        # the same value
        vrf.setMinimumHeatPumpPartLoadRatio(0.5)

        vrf_terminal = openstudio.model.ZoneHVACTerminalUnitVariableRefrigerantFlow(model, cc, hc, fan)
        vrf.addTerminal(vrf_terminal)
        vrf_terminal.addToThermalZone(z)

    # ZoneHVACUnitHeater
    elif i == 5:
        fan = openstudio.model.FanSystemModel(model)
        heating_coil = openstudio.model.CoilHeatingElectric(model)
        unit_heater = openstudio.model.ZoneHVACUnitHeater(model, alwaysOn, fan, heating_coil)
        unit_heater.addToThermalZone(z)

    # ZoneHVACUnitVentilator
    elif i == 6:
        fan = openstudio.model.FanSystemModel(model)
        zoneHVACUnitVentilator = openstudio.model.ZoneHVACUnitVentilator(model, fan)
        heating_coil = openstudio.model.CoilHeatingElectric(model)
        cooling_coil = openstudio.model.CoilCoolingWater(model)
        cooling_loop.addDemandBranchForComponent(cooling_coil)
        zoneHVACUnitVentilator.setHeatingCoil(heating_coil)
        zoneHVACUnitVentilator.setCoolingCoil(cooling_coil)
        zoneHVACUnitVentilator.addToThermalZone(z)

    # ZoneHVACWaterToAirHeatPump
    elif i == 7:
        fan = openstudio.model.FanSystemModel(model)
        heating_coil = openstudio.model.CoilHeatingWaterToAirHeatPumpEquationFit(model)
        cooling_coil = openstudio.model.CoilCoolingWaterToAirHeatPumpEquationFit(model)
        supp_heating_coil = openstudio.model.CoilHeatingElectric(model)
        water_to_air_heat_pump = openstudio.model.ZoneHVACWaterToAirHeatPump(
            model, alwaysOn, fan, heating_coil, cooling_coil, supp_heating_coil
        )
        water_to_air_heat_pump.addToThermalZone(z)
        heating_loop.addDemandBranchForComponent(heating_coil)
        cooling_loop.addDemandBranchForComponent(cooling_coil)

    # AirTerminalSingleDuctSeriesPIUReheat
    elif i == 8:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        piu_fan = openstudio.model.FanSystemModel(model)
        piu_supp_hc = openstudio.model.CoilHeatingElectric(model)
        new_terminal = openstudio.model.AirTerminalSingleDuctSeriesPIUReheat(model, piu_fan, piu_supp_hc)

        air_loop.addBranchForZone(z, new_terminal.to_StraightComponent())

    # AirTerminalSingleDuctParallelPIUReheat
    elif i == 9:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        piu_fan = openstudio.model.FanSystemModel(model)
        piu_supp_hc = openstudio.model.CoilHeatingElectric(model)
        new_terminal = openstudio.model.AirTerminalSingleDuctParallelPIUReheat(model, alwaysOn, piu_fan, piu_supp_hc)

        air_loop.addBranchForZone(z, new_terminal.to_StraightComponent())

    # AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass
    elif i == 10:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        new_terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, alwaysOn)

        unitary_vav_changeoverAirLoopHVAC.addBranchForZone(z, new_terminal.to_StraightComponent())
    # Doesn't exist: unitary_vav_changeover.setControllingZoneorThermostatLocation(z)

    # AirLoopHVACUnitarySystem
    elif i == 11:

        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        new_terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, alwaysOn)

        unitary_systemAirLoopHVAC.addBranchForZone(z, new_terminal.to_StraightComponent())
        unitary_system.setControllingZoneorThermostatLocation(z)

    # WaterHeaterHeatPump (PumpedCondenser)
    elif i == 12:
        hpwh_pumped.addToThermalZone(z)

    # WaterHeaterHeatPumpWrappedCondenser
    elif i == 13 and is_working_WaterThermalTanks:
        hpwh_wrapped.addToThermalZone(z)

    elif i == 14 and is_working_AirLoopHVACUnitaryHeatPumpAirToAir:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        new_terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, alwaysOn)

        unitary_air_to_airAirLoopHVAC.addBranchForZone(z, new_terminal.to_StraightComponent())
        unitary_air_to_air.setControllingZone(z)
    elif i == 15 and is_working_AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        new_terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, alwaysOn)

        unitary_hp_airtoair_multispeedAirLoopHVAC.addBranchForZone(z, new_terminal.to_StraightComponent())
        unitary_multispeed.setControllingZoneorThermostatLocation(z)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
