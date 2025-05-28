# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 2 story, 100m X 50m, 15 zone core/perimeter building
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

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac({ 'ashrae_sys_num' => '07' })

# In order to produce more consistent results between different runs,
# We ensure we do get the same object each time
zones = model.getThermalZones.sort_by { |z| z.name.to_s }

airLoops = model.getAirLoopHVACs.sort_by { |a| a.name.to_s }
regularAirLoopHVAC = airLoops[0]

chillers = model.getChillerElectricEIRs.sort_by { |c| c.name.to_s }
boilers = model.getBoilerHotWaters.sort_by { |c| c.name.to_s }

cooling_loop = chillers.first.plantLoop.get
heating_loop = boilers.first.plantLoop.get

alwaysOn = model.alwaysOnDiscreteSchedule

fan = OpenStudio::Model::FanSystemModel.new(model)
# Demonstrate API
fan.setName('My FanSystemModel')

# Availability Schedule Name: Required Object
sch = OpenStudio::Model::ScheduleConstant.new(model)
sch.setName('Fan Avail Schedule')
sch.setValue(1.0)
fan.setAvailabilitySchedule(sch)

# Design Maximum Air Flow Rate: Required Double, Autosizable
# fan.setDesignMaximumAirFlowRate(0.1)
fan.autosizeDesignMaximumAirFlowRate

# Speed Control Method: Required String
# OpenStudio::Model::FanSystemModel::speedControlMethodValues()
fan.setSpeedControlMethod('Discrete')

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
fan.autosizeDesignElectricPowerConsumption

# Design Power Sizing Method: Required String (choice)
# OpenStudio::Model::FanSystemModel::designPowerSizingMethodValues()
fan.setDesignPowerSizingMethod('TotalEfficiencyAndPressure')

# These two may not be used depending on the Design Power Sizing Method
# Electric Power Per Unit Flow Rate: Required Double
fan.setElectricPowerPerUnitFlowRate(1254.0)

# Electric Power Per Unit Flow Rate Per Unit Pressure: Required Double
fan.setElectricPowerPerUnitFlowRatePerUnitPressure(1.345)

# Fan Total Efficiency: Required Double
fan.setFanTotalEfficiency(0.59)

# Electric Power Function of Flow Fraction Curve Name: Optional Object
# Taken from PackagedTerminalHeatPump.idf
fanPowerFuncFlowCurve = OpenStudio::Model::CurveCubic.new(model)
fanPowerFuncFlowCurve.setName('CombinedPowerAndFanEff')
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
fan.setEndUseSubcategory('My Fan')

# Speeds: used when Speed Control Method = Discrete
# You can add speeds one by one
fan.addSpeed(0.25, 0.1)
# Or you can call setSpeeds, which will clear any existing ones via
# `fan.removeAllSpeeds`
# You can use a vector, or just a ruby array
# speeds = OpenStudio::Model::FanSystemModelSpeedVector.new
speeds = [
  OpenStudio::Model::FanSystemModelSpeed.new(0.25, 0.1),
  OpenStudio::Model::FanSystemModelSpeed.new(0.5, 0.3),
  OpenStudio::Model::FanSystemModelSpeed.new(0.75, 0.7),
  OpenStudio::Model::FanSystemModelSpeed.new(1.0, 1.0)

]
fan.setSpeeds(speeds)

# Add this fan as the supply fan of a regular AirLoopHVAC, removing the
# existing FanVariableVolume
regularAirLoopHVAC.supplyFan.get.remove
fan.addToNode(regularAirLoopHVAC.supplyOutletNode)

# AirLoopHVACUnitaryHeatPumpAirToAir
# TODO: Currently not supported in E+
is_working_AirLoopHVACUnitaryHeatPumpAirToAir = false

# Unitary: MultiSpeed
# TODO: Currently not supported in E+
is_working_AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed = false

# AirLoopHVACUnitaryHeatPumpAirToAir
if is_working_AirLoopHVACUnitaryHeatPumpAirToAir
  heating_coil = OpenStudio::Model::CoilCoolingDXSingleSpeed.new(model)
  cooling_coil = OpenStudio::Model::CoilCoolingDXSingleSpeed.new(model)
  supp_heating_coil = OpenStudio::Model::CoilHeatingElectric.new(model)
  unitary_air_to_air = OpenStudio::Model::AirLoopHVACUnitaryHeatPumpAirToAir.new(model, alwaysOn, fan, heating_coil, cooling_coil, supp_heating_coil)
  unitary_air_to_airAirLoopHVAC = OpenStudio::Model::AirLoopHVAC.new(model)
  unitary_air_to_airAirLoopHVAC.setName('UnitaryHPAirToAir AirLoopHVAC')
  unitary_air_to_air.addToNode(unitary_air_to_airAirLoopHVAC.supplyOutletNode)
end

# Unitary: MultiSpeed
if is_working_AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed
  unitary_fan = OpenStudio::Model::FanSystemModel.new(model)
  unitary_htg_coil = OpenStudio::Model::CoilHeatingDXMultiSpeed.new(model)
  htg_stage_1 = OpenStudio::Model::CoilHeatingDXMultiSpeedStageData.new(model)
  htg_stage_2 = OpenStudio::Model::CoilHeatingDXMultiSpeedStageData.new(model)
  htg_stage_3 = OpenStudio::Model::CoilHeatingDXMultiSpeedStageData.new(model)
  htg_stage_4 = OpenStudio::Model::CoilHeatingDXMultiSpeedStageData.new(model)
  unitary_htg_coil.addStage(htg_stage_1)
  unitary_htg_coil.addStage(htg_stage_2)
  unitary_htg_coil.addStage(htg_stage_3)
  unitary_htg_coil.addStage(htg_stage_4)
  unitary_clg_coil = OpenStudio::Model::CoilCoolingDXMultiSpeed.new(model)
  clg_stage_1 = OpenStudio::Model::CoilCoolingDXMultiSpeedStageData.new(model)
  clg_stage_2 = OpenStudio::Model::CoilCoolingDXMultiSpeedStageData.new(model)
  clg_stage_3 = OpenStudio::Model::CoilCoolingDXMultiSpeedStageData.new(model)
  clg_stage_4 = OpenStudio::Model::CoilCoolingDXMultiSpeedStageData.new(model)
  unitary_clg_coil.addStage(clg_stage_1)
  unitary_clg_coil.addStage(clg_stage_2)
  unitary_clg_coil.addStage(clg_stage_3)
  unitary_clg_coil.addStage(clg_stage_4)
  sup_unitary_htg_coil = OpenStudio::Model::CoilHeatingElectric.new(model)
  unitary_multispeed = OpenStudio::Model::AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed.new(model, unitary_fan, unitary_htg_coil, unitary_clg_coil, sup_unitary_htg_coil)
  unitary_multispeed.setNumberofSpeedsforHeating(4)
  unitary_multispeed.setNumberofSpeedsforCooling(4)
  unitary_hp_airtoair_multispeedAirLoopHVAC = OpenStudio::Model::AirLoopHVAC.new(model)
  unitary_hp_airtoair_multispeedAirLoopHVAC.setName('UnitaryHPAirToAirMultiSpeed AirLoopHVAC')
  unitary_multispeed.addToNode(unitary_hp_airtoair_multispeedAirLoopHVAC.supplyOutletNode)
end

# AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass
unitary_vav_fan = OpenStudio::Model::FanSystemModel.new(model)
unitary_vav_cc = OpenStudio::Model::CoilCoolingDXSingleSpeed.new(model)
unitary_vav_hc = OpenStudio::Model::CoilHeatingGas.new(model)
unitary_vav_changeover = OpenStudio::Model::AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass.new(model, unitary_vav_fan, unitary_vav_cc, unitary_vav_hc)
unitary_vav_changeoverAirLoopHVAC = OpenStudio::Model::AirLoopHVAC.new(model)
unitary_vav_changeoverAirLoopHVAC.setName('AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass AirLoopHVAC')
unitary_vav_changeover.addToNode(unitary_vav_changeoverAirLoopHVAC.supplyOutletNode)

# AirLoopHVACUnitarySystem
unitary_system = OpenStudio::Model::AirLoopHVACUnitarySystem.new(model)
unitary_system_fan = OpenStudio::Model::FanSystemModel.new(model)
unitary_system_cc = OpenStudio::Model::CoilCoolingDXSingleSpeed.new(model)
unitary_system_hc = OpenStudio::Model::CoilHeatingDXSingleSpeed.new(model)
supp_unitary_system_hc = OpenStudio::Model::CoilHeatingElectric.new(model)
# unitary_system.setControlType("SetPoint")
unitary_system.setSupplyAirFanOperatingModeSchedule(alwaysOn)
unitary_system.setSupplyFan(unitary_system_fan)
unitary_system.setCoolingCoil(unitary_system_cc)
unitary_system.setHeatingCoil(unitary_system_hc)
unitary_system.setSupplementalHeatingCoil(supp_unitary_system_hc)
unitary_systemAirLoopHVAC = OpenStudio::Model::AirLoopHVAC.new(model)
unitary_systemAirLoopHVAC.setName('AirLoopHVACUnitarySystem AirLoopHVAC')
unitary_system.addToNode(unitary_systemAirLoopHVAC.supplyOutletNode)

dhw_loop = OpenStudio::Model.addSHWLoop(model).to_PlantLoop.get

hpwh_pumped = OpenStudio::Model::WaterHeaterHeatPump.new(model)
hpwh_pumped_fan = OpenStudio::Model::FanSystemModel.new(model)
old_hpwh_pumped_fan = hpwh_pumped.fan
hpwh_pumped.setFan(hpwh_pumped_fan)
old_hpwh_pumped_fan.remove
dhw_loop.addSupplyBranchForComponent(hpwh_pumped.tank)

# TODO: ENABLE AFTER NEW E+ RELEASE (9.2.0+)
# Having both a HPWH:Pumped and a HPWH:Wrapped makes E+ crash
# Fixed by https://github.com/NREL/EnergyPlus/pull/7717 but not in any E+
# release yet
is_working_WaterThermalTanks = false
if is_working_WaterThermalTanks
  hpwh_wrapped = OpenStudio::Model::WaterHeaterHeatPumpWrappedCondenser.new(model)
  hpwh_wrapped_fan = OpenStudio::Model::FanSystemModel.new(model)
  old_hpwh_wrapped_fan = hpwh_wrapped.fan
  hpwh_wrapped.setFan(hpwh_wrapped_fan)
  old_hpwh_wrapped_fan.remove
  dhw_loop.addSupplyBranchForComponent(hpwh_wrapped.tank)
end

zones.each_with_index do |z, i|
  # ZoneHVACEnergyRecoveryVentilator
  if i == 0

    supplyFan = OpenStudio::Model::FanSystemModel.new(model)
    exhaustFan = OpenStudio::Model::FanSystemModel.new(model)

    heatExchanger = OpenStudio::Model::HeatExchangerAirToAirSensibleAndLatent.new(model)
    if Gem::Version.new(OpenStudio.openStudioVersion) >= Gem::Version.new('3.8.0')
      heatExchanger.assignHistoricalEffectivenessCurves
    end
    heatExchanger.setSupplyAirOutletTemperatureControl(false)

    zoneHVACEnergyRecoveryVentilator = OpenStudio::Model::ZoneHVACEnergyRecoveryVentilator.new(model, heatExchanger, supplyFan, exhaustFan)
    zoneHVACEnergyRecoveryVentilatorController = OpenStudio::Model::ZoneHVACEnergyRecoveryVentilatorController.new(model)
    zoneHVACEnergyRecoveryVentilator.setController(zoneHVACEnergyRecoveryVentilatorController)
    zoneHVACEnergyRecoveryVentilatorController.setHighHumidityControlFlag(false)
    zoneHVACEnergyRecoveryVentilator.addToThermalZone(z)

  # ZoneHVACFourPipeFanCoil
  elsif i == 1
    fan = OpenStudio::Model::FanSystemModel.new(model)

    # ** Severe  ** GetFanCoilUnits: ZoneHVAC:FourPipeFanCoil: ZONE HVAC FOUR PIPE FAN COIL 1
    # **   ~~~   ** ...the fan type of the object : FAN SYSTEM MODEL 1 does not match with the capacity control method selected : VARIABLEFANVARIABLEFLOW please see I/O reference
    # **   ~~~   ** ...for VariableFanVariableFlow or VariableFanConstantFlow a Fan:SystemModel should have Continuous speed control.
    fan.setSpeedControlMethod('Continuous')

    # ** Warning ** HVACFan constructor Fan:SystemModel="FAN SYSTEM MODEL 1", invalid entry.
    # **   ~~~   ** Continuous speed control requires a fan power curve in Electric Power Function of Flow Fraction Curve Name =
    # **  Fatal  ** HVACFan constructor Errors found in input for fan name = FAN SYSTEM MODEL 1.  Program terminates.
    fan.setElectricPowerFunctionofFlowFractionCurve(fanPowerFuncFlowCurve)

    heating_coil = OpenStudio::Model::CoilHeatingWater.new(model)
    cooling_coil = OpenStudio::Model::CoilCoolingWater.new(model)
    four_pipe_fan_coil = OpenStudio::Model::ZoneHVACFourPipeFanCoil.new(model, alwaysOn, fan, cooling_coil, heating_coil)
    four_pipe_fan_coil.addToThermalZone(z)
    heating_loop.addDemandBranchForComponent(heating_coil)
    cooling_loop.addDemandBranchForComponent(cooling_coil)

  # ZoneHVACPackagedTerminalAirConditioner
  elsif i == 2
    thermal_zone_vector = OpenStudio::Model::ThermalZoneVector.new
    thermal_zone_vector << z
    OpenStudio::Model.addSystemType1(model, thermal_zone_vector)
    fan = OpenStudio::Model::FanSystemModel.new(model)
    ptacs = model.getZoneHVACPackagedTerminalAirConditioners
    fan_cv = ptacs[0].supplyAirFan
    ptacs[0].setSupplyAirFan(fan)
    fan_cv.remove

  # ZoneHVACPackagedTerminalHeatPump
  elsif i == 3
    thermal_zone_vector = OpenStudio::Model::ThermalZoneVector.new
    thermal_zone_vector << z
    OpenStudio::Model.addSystemType2(model, thermal_zone_vector)
    fan = OpenStudio::Model::FanSystemModel.new(model)
    pthps = model.getZoneHVACPackagedTerminalHeatPumps
    fan_cv = pthps[0].supplyAirFan
    pthps[0].setSupplyAirFan(fan)
    fan_cv.remove

  # ZoneHVAC:TerminalUnit:VariableRefrigerantFlow
  elsif i == 4
    fan = OpenStudio::Model::FanSystemModel.new(model)
    cc = OpenStudio::Model::CoilCoolingDXVariableRefrigerantFlow.new(model)
    hc = OpenStudio::Model::CoilHeatingDXVariableRefrigerantFlow.new(model)
    vrf = OpenStudio::Model::AirConditionerVariableRefrigerantFlow.new(model)
    # E+ now throws when the CoolingEIRLowPLR has a curve minimum value of x which
    # is higher than the Minimum Heat Pump Part-Load Ratio.
    # The curve has a min of 0.5 here, so set the MinimumHeatPumpPartLoadRatio to
    # the same value
    vrf.setMinimumHeatPumpPartLoadRatio(0.5)

    vrf_terminal = OpenStudio::Model::ZoneHVACTerminalUnitVariableRefrigerantFlow.new(model, cc, hc, fan)
    vrf.addTerminal(vrf_terminal)
    vrf_terminal.addToThermalZone(z)

  # ZoneHVACUnitHeater
  elsif i == 5
    fan = OpenStudio::Model::FanSystemModel.new(model)
    heating_coil = OpenStudio::Model::CoilHeatingElectric.new(model)
    unit_heater = OpenStudio::Model::ZoneHVACUnitHeater.new(model, alwaysOn, fan, heating_coil)
    unit_heater.addToThermalZone(z)

  # ZoneHVACUnitVentilator
  elsif i == 6
    fan = OpenStudio::Model::FanSystemModel.new(model)
    zoneHVACUnitVentilator = OpenStudio::Model::ZoneHVACUnitVentilator.new(model, fan)
    heating_coil = OpenStudio::Model::CoilHeatingElectric.new(model)
    cooling_coil = OpenStudio::Model::CoilCoolingWater.new(model)
    cooling_loop.addDemandBranchForComponent(cooling_coil)
    zoneHVACUnitVentilator.setHeatingCoil(heating_coil)
    zoneHVACUnitVentilator.setCoolingCoil(cooling_coil)
    zoneHVACUnitVentilator.addToThermalZone(z)

  # ZoneHVACWaterToAirHeatPump
  elsif i == 7
    fan = OpenStudio::Model::FanSystemModel.new(model)
    heating_coil = OpenStudio::Model::CoilHeatingWaterToAirHeatPumpEquationFit.new(model)
    cooling_coil = OpenStudio::Model::CoilCoolingWaterToAirHeatPumpEquationFit.new(model)
    supp_heating_coil = OpenStudio::Model::CoilHeatingElectric.new(model)
    water_to_air_heat_pump = OpenStudio::Model::ZoneHVACWaterToAirHeatPump.new(model, alwaysOn, fan, heating_coil, cooling_coil, supp_heating_coil)
    water_to_air_heat_pump.addToThermalZone(z)
    heating_loop.addDemandBranchForComponent(heating_coil)
    cooling_loop.addDemandBranchForComponent(cooling_coil)

  # AirTerminalSingleDuctSeriesPIUReheat
  elsif i == 8
    air_loop = z.airLoopHVAC.get
    air_loop.removeBranchForZone(z)

    piu_fan = OpenStudio::Model::FanSystemModel.new(model)
    piu_supp_hc = OpenStudio::Model::CoilHeatingElectric.new(model)
    new_terminal = OpenStudio::Model::AirTerminalSingleDuctSeriesPIUReheat.new(model, piu_fan, piu_supp_hc)

    air_loop.addBranchForZone(z, new_terminal.to_StraightComponent)

  # AirTerminalSingleDuctParallelPIUReheat
  elsif i == 9
    air_loop = z.airLoopHVAC.get
    air_loop.removeBranchForZone(z)

    piu_fan = OpenStudio::Model::FanSystemModel.new(model)
    piu_supp_hc = OpenStudio::Model::CoilHeatingElectric.new(model)
    new_terminal = OpenStudio::Model::AirTerminalSingleDuctParallelPIUReheat.new(model, alwaysOn, piu_fan, piu_supp_hc)

    air_loop.addBranchForZone(z, new_terminal.to_StraightComponent)

  # AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass
  elsif i == 10
    air_loop = z.airLoopHVAC.get
    air_loop.removeBranchForZone(z)

    new_terminal = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, alwaysOn)

    unitary_vav_changeoverAirLoopHVAC.addBranchForZone(z, new_terminal.to_StraightComponent)
  # Doesn't exist: unitary_vav_changeover.setControllingZoneorThermostatLocation(z)

  # AirLoopHVACUnitarySystem
  elsif i == 11

    air_loop = z.airLoopHVAC.get
    air_loop.removeBranchForZone(z)

    new_terminal = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, alwaysOn)

    unitary_systemAirLoopHVAC.addBranchForZone(z, new_terminal.to_StraightComponent)
    unitary_system.setControllingZoneorThermostatLocation(z)

  # WaterHeaterHeatPump (PumpedCondenser)
  elsif i == 12
    hpwh_pumped.addToThermalZone(z)

  # WaterHeaterHeatPumpWrappedCondenser
  elsif i == 13 && is_working_WaterThermalTanks
    hpwh_wrapped.addToThermalZone(z)

  elsif i == 14 && is_working_AirLoopHVACUnitaryHeatPumpAirToAir
    air_loop = z.airLoopHVAC.get
    air_loop.removeBranchForZone(z)

    new_terminal = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, alwaysOn)

    unitary_air_to_airAirLoopHVAC.addBranchForZone(z, new_terminal.to_StraightComponent)
    unitary_air_to_air.setControllingZone(z)
  elsif i == 15 && is_working_AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed
    air_loop = z.airLoopHVAC.get
    air_loop.removeBranchForZone(z)

    new_terminal = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, alwaysOn)

    unitary_hp_airtoair_multispeedAirLoopHVAC.addBranchForZone(z, new_terminal.to_StraightComponent)
    unitary_multispeed.setControllingZoneorThermostatLocation(z)
  end
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
