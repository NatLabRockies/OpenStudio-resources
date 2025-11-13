# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# In order to produce more consistent results between different runs,
# we sort the zones by names (only one here anyways...)
zones = model.getThermalZones.sort_by { |z| z.name.to_s }
zone = zones[0]

###############################################################################
#                       M A K E    S O M E    L O O P S                       #
###############################################################################

############### HEATING / COOLING (LOAD) LOOPS  ###############

hw_loop = OpenStudio::Model::PlantLoop.new(model)
hw_loop.setName('Hot Water Loop Air Source')
hw_loop.setMinimumLoopTemperature(10)
hw_temp_f = 140
hw_delta_t_r = 20 # 20F delta-T
hw_temp_c = OpenStudio.convert(hw_temp_f, 'F', 'C').get
hw_delta_t_k = OpenStudio.convert(hw_delta_t_r, 'R', 'K').get
hw_temp_sch = OpenStudio::Model::ScheduleRuleset.new(model)
hw_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), hw_temp_c)
hw_stpt_manager = OpenStudio::Model::SetpointManagerScheduled.new(model, hw_temp_sch)
hw_stpt_manager.addToNode(hw_loop.supplyOutletNode)
sizing_plant = hw_loop.sizingPlant
sizing_plant.setLoopType('Heating')
sizing_plant.setDesignLoopExitTemperature(hw_temp_c)
sizing_plant.setLoopDesignTemperatureDifference(hw_delta_t_k)
# Pump
hw_pump = OpenStudio::Model::PumpVariableSpeed.new(model)
hw_pump_head_ft_h2o = 60.0
hw_pump_head_press_pa = OpenStudio.convert(hw_pump_head_ft_h2o, 'ftH_{2}O', 'Pa').get
hw_pump.setRatedPumpHead(hw_pump_head_press_pa)
hw_pump.setPumpControlType('Intermittent')
hw_pump.addToNode(hw_loop.supplyInletNode)

chw_loop = OpenStudio::Model::PlantLoop.new(model)
chw_loop.setName('Chilled Water Loop Air Source')
chw_loop.setMaximumLoopTemperature(98)
chw_loop.setMinimumLoopTemperature(1)
chw_temp_f = 44
chw_delta_t_r = 10.1 # 10.1F delta-T
chw_temp_c = OpenStudio.convert(chw_temp_f, 'F', 'C').get
chw_delta_t_k = OpenStudio.convert(chw_delta_t_r, 'R', 'K').get
chw_temp_sch = OpenStudio::Model::ScheduleRuleset.new(model)
chw_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), chw_temp_c)
chw_stpt_manager = OpenStudio::Model::SetpointManagerScheduled.new(model, chw_temp_sch)
chw_stpt_manager.addToNode(chw_loop.supplyOutletNode)
sizing_plant = chw_loop.sizingPlant
sizing_plant.setLoopType('Cooling')
sizing_plant.setDesignLoopExitTemperature(chw_temp_c)
sizing_plant.setLoopDesignTemperatureDifference(chw_delta_t_k)
# Pump
pri_chw_pump = OpenStudio::Model::HeaderedPumpsConstantSpeed.new(model)
pri_chw_pump.setName('Chilled Water Loop Primary Pump Air Source')
pri_chw_pump_head_ft_h2o = 15
pri_chw_pump_head_press_pa = OpenStudio.convert(pri_chw_pump_head_ft_h2o, 'ftH_{2}O', 'Pa').get
pri_chw_pump.setRatedPumpHead(pri_chw_pump_head_press_pa)
pri_chw_pump.setMotorEfficiency(0.9)
pri_chw_pump.setPumpControlType('Intermittent')
pri_chw_pump.addToNode(chw_loop.supplyInletNode)

###############################################################################
#                         A I R    S O U R C E    H P                         #
###############################################################################

# PlantLoopHeatPump_EIR_AirSource_and_AWHP.idf

def make_awhp(model)
  awhp = OpenStudio::Model::HeatPumpAirToWater.new(model)
  awhp.setName('AWHP')
  awhp.setOperatingModeControlMethod('Load')
  awhp.setOperatingModeControlOptionforMultipleUnit('SingleMode')
  awhp.setMinimumPartLoadRatio(0.0)
  awhp.setAirInletNodeName(awhp.nameString + ' Air Inlet Node')
  awhp.setAirOutletNodeName(awhp.nameString + ' Air Outlet Node')

  awhp.setMaximumOutdoorDryBulbTemperatureForDefrostOperation(10.0)
  awhp.setHeatPumpDefrostControl('Timed')
  awhp.setHeatPumpDefrostTimePeriodFraction(0.2)
  awhp.setResistiveDefrostHeaterCapacity(100.0)

  # Defrost Energy Input Ratio Function of Temperature Curve Name: Optional Object, BivariateFunctions
  # defrostEnergyInputRatioFunctionofTemperatureCurve = OpenStudio::Model::CurveBiquadratic.new(model)
  # defrostEnergyInputRatioFunctionofTemperatureCurve.setName("#{awhp.nameString} Defrost EIR FT Curve")
  # defrostEnergyInputRatioFunctionofTemperatureCurve.setCoefficient1Constant(1.0)
  # defrostEnergyInputRatioFunctionofTemperatureCurve.setCoefficient2x(0.0)
  # defrostEnergyInputRatioFunctionofTemperatureCurve.setCoefficient3xPOW2(0.0)
  # defrostEnergyInputRatioFunctionofTemperatureCurve.setCoefficient4y(0.0)
  # defrostEnergyInputRatioFunctionofTemperatureCurve.setCoefficient5yPOW2(0.0)
  # defrostEnergyInputRatioFunctionofTemperatureCurve.setCoefficient6xTIMESY(0.0)
  # awhp.setDefrostEnergyInputRatioFunctionofTemperatureCurve(defrostEnergyInputRatioFunctionofTemperatureCurve)

  awhp.setHeatPumpMultiplier(2)
  awhp.setControlType('FixedSpeed')
  awhp.setCrankcaseHeaterCapacity(100.0)

  # Crankcase Heater Capacity Function of Temperature Curve Name: Optional Object, UnivariateFunctions
  crankcaseHeaterCapacityFunctionofTemperatureCurve = OpenStudio::Model::CurveQuadratic.new(model)
  crankcaseHeaterCapacityFunctionofTemperatureCurve.setName('CrankCaseHeaterPowerCurve')
  crankcaseHeaterCapacityFunctionofTemperatureCurve.setCoefficient1Constant(1.0)
  crankcaseHeaterCapacityFunctionofTemperatureCurve.setCoefficient2x(0.01)
  crankcaseHeaterCapacityFunctionofTemperatureCurve.setCoefficient3xPOW2(0.0)
  crankcaseHeaterCapacityFunctionofTemperatureCurve.setMinimumValueofx(-30.0)
  crankcaseHeaterCapacityFunctionofTemperatureCurve.setMaximumValueofx(30.0)
  awhp.setCrankcaseHeaterCapacityFunctionofTemperatureCurve(crankcaseHeaterCapacityFunctionofTemperatureCurve)

  awhp.setMaximumAmbientTemperatureforCrankcaseHeaterOperation(5.0)

  awhp
end

def get_or_create_constant_eirplr_curve(model)
  if model.getCurveQuadraticByName('EIRCurveFuncPLR_Constant').is_initialized
    return model.getCurveQuadraticByName('EIRCurveFuncPLR_Constant').get
  end

  constant_eirplr_curve = OpenStudio::Model::CurveQuadratic.new(model)
  constant_eirplr_curve.setName('EIRCurveFuncPLR_Constant')
  constant_eirplr_curve.setCoefficient1Constant(1.0)
  constant_eirplr_curve.setCoefficient2x(0.0)
  constant_eirplr_curve.setCoefficient3xPOW2(0.0)
  constant_eirplr_curve.setMinimumValueofx(0.0)
  constant_eirplr_curve.setMaximumValueofx(1.0)

  constant_eirplr_curve
end

###################
#  H E A T I N G  #
###################

def make_awhp_heating_side(model)
  awhp_hc = OpenStudio::Model::HeatPumpAirToWaterHeating.new(model)

  awhp_hc.setName('AWHP Heating')
  awhp_hc.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule)
  awhp_hc.setRatedInletAirTemperature(20.0)
  awhp_hc.autosizeRatedAirFlowRate
  # awhp_hc.setRatedAirFlowRate(0.5)
  awhp_hc.setRatedLeavingWaterTemperature(50.0)
  awhp_hc.autosizeRatedWaterFlowRate
  # awhp_hc.setRatedWaterFlowRate(0.005)
  awhp_hc.setMinimumOutdoorAirTemperature(-20.0)
  awhp_hc.setMaximumOutdoorAirTemperature(25.0)

  awhp_hc_min_lwt_curve = OpenStudio::Model::CurveQuadratic.new(model)
  awhp_hc_min_lwt_curve.setName('MinHeatingSWTvsOAT')
  awhp_hc_min_lwt_curve.setCoefficient1Constant(0.0)
  awhp_hc_min_lwt_curve.setCoefficient2x(1.0)
  awhp_hc_min_lwt_curve.setCoefficient3xPOW2(0.0)
  awhp_hc_min_lwt_curve.setMinimumValueofx(-17.77778)
  awhp_hc_min_lwt_curve.setMaximumValueofx(35.0)
  awhp_hc_min_lwt_curve.setMinimumCurveOutput(20.0)
  awhp_hc_min_lwt_curve.setMaximumCurveOutput(35.0)
  awhp_hc_min_lwt_curve.setInputUnitTypeforX('Temperature')
  awhp_hc_min_lwt_curve.setOutputUnitType('Temperature')
  awhp_hc.setMinimumLeavingWaterTemperatureCurve(awhp_hc_min_lwt_curve)

  awhp_hc_max_lwt_curve = OpenStudio::Model::CurveQuadratic.new(model)
  awhp_hc_max_lwt_curve.setName('MaxHeatingSWTvsOAT')
  awhp_hc_max_lwt_curve.setCoefficient1Constant(100.0)
  awhp_hc_max_lwt_curve.setCoefficient2x(0.85)
  awhp_hc_max_lwt_curve.setCoefficient3xPOW2(0.0)
  awhp_hc_max_lwt_curve.setMinimumValueofx(-17.77778)
  awhp_hc_max_lwt_curve.setMaximumValueofx(35.0)
  awhp_hc_max_lwt_curve.setMinimumCurveOutput(20.0)
  awhp_hc_max_lwt_curve.setMaximumCurveOutput(150.0)
  awhp_hc.setMaximumLeavingWaterTemperatureCurve(awhp_hc_max_lwt_curve)

  awhp_hc.setSizingFactor(1.0)

  awhp_hc
end

def make_awhp_heating_low_speed(model)
  awhp_hc_low_speed_capft_curve = OpenStudio::Model::CurveBiquadratic.new(model)
  awhp_hc_low_speed_capft_curve.setName('CapCurveFuncTempHT')
  awhp_hc_low_speed_capft_curve.setCoefficient1Constant(0.899)
  awhp_hc_low_speed_capft_curve.setCoefficient2x(-0.00045)
  awhp_hc_low_speed_capft_curve.setCoefficient3xPOW2(0.00021)
  awhp_hc_low_speed_capft_curve.setCoefficient4y(0.0185)
  awhp_hc_low_speed_capft_curve.setCoefficient5yPOW2(-0.0108)
  awhp_hc_low_speed_capft_curve.setCoefficient6xTIMESY(0.000617)
  awhp_hc_low_speed_capft_curve.setMinimumValueofx(30.0)
  awhp_hc_low_speed_capft_curve.setMaximumValueofx(50.0)
  awhp_hc_low_speed_capft_curve.setMinimumValueofy(-7.0)
  awhp_hc_low_speed_capft_curve.setMaximumValueofy(20.0)
  awhp_hc_low_speed_capft_curve.setMinimumCurveOutput(0.5)
  awhp_hc_low_speed_capft_curve.setMaximumCurveOutput(1.3)
  awhp_hc_low_speed_capft_curve.setInputUnitTypeforX('Temperature')
  awhp_hc_low_speed_capft_curve.setInputUnitTypeforY('Temperature')
  awhp_hc_low_speed_capft_curve.setOutputUnitType('Dimensionless')

  awhp_hc_low_speed_eirft_curve = OpenStudio::Model::CurveBiquadratic.new(model)
  awhp_hc_low_speed_eirft_curve.setName('EIRCurveFuncTempHT')
  awhp_hc_low_speed_eirft_curve.setCoefficient1Constant(1.055)
  awhp_hc_low_speed_eirft_curve.setCoefficient2x(0.00035)
  awhp_hc_low_speed_eirft_curve.setCoefficient3xPOW2(-0.00027)
  awhp_hc_low_speed_eirft_curve.setCoefficient4y(-0.0108)
  awhp_hc_low_speed_eirft_curve.setCoefficient5yPOW2(0.0145)
  awhp_hc_low_speed_eirft_curve.setCoefficient6xTIMESY(-0.000230)
  awhp_hc_low_speed_eirft_curve.setMinimumValueofx(30.0)
  awhp_hc_low_speed_eirft_curve.setMaximumValueofx(50.0)
  awhp_hc_low_speed_eirft_curve.setMinimumValueofy(-7.0)
  awhp_hc_low_speed_eirft_curve.setMaximumValueofy(20.0)
  awhp_hc_low_speed_eirft_curve.setMinimumCurveOutput(0.7)
  awhp_hc_low_speed_eirft_curve.setMaximumCurveOutput(1.5)
  awhp_hc_low_speed_eirft_curve.setInputUnitTypeforX('Temperature')
  awhp_hc_low_speed_eirft_curve.setInputUnitTypeforY('Temperature')
  awhp_hc_low_speed_eirft_curve.setOutputUnitType('Dimensionless')

  awhp_hc_low_speed = OpenStudio::Model::HeatPumpAirToWaterHeatingSpeedData.new(
    model,
    awhp_hc_low_speed_capft_curve,
    awhp_hc_low_speed_eirft_curve,
    get_or_create_constant_eirplr_curve(model)
  )
  awhp_hc_low_speed.setName('AWHP Heating Low Speed')
  awhp_hc_low_speed.setRatedHeatingCapacity(20000.0)
  awhp_hc_low_speed.setRatedCOPforHeating(3.49)

  awhp_hc_low_speed
end

def make_awhp_heating_high_speed(model)
  awhp_hc_high_speed_capft_curve = OpenStudio::Model::CurveBiquadratic.new(model)
  awhp_hc_high_speed_capft_curve.setName('CapCurveFuncTempHT2')
  awhp_hc_high_speed_capft_curve.setCoefficient1Constant(0.885)
  awhp_hc_high_speed_capft_curve.setCoefficient2x(-0.00040)
  awhp_hc_high_speed_capft_curve.setCoefficient3xPOW2(0.00019)
  awhp_hc_high_speed_capft_curve.setCoefficient4y(0.0202)
  awhp_hc_high_speed_capft_curve.setCoefficient5yPOW2(-0.0096)
  awhp_hc_high_speed_capft_curve.setCoefficient6xTIMESY(0.000580)
  awhp_hc_high_speed_capft_curve.setMinimumValueofx(30.0)
  awhp_hc_high_speed_capft_curve.setMaximumValueofx(50.0)
  awhp_hc_high_speed_capft_curve.setMinimumValueofy(-7.0)
  awhp_hc_high_speed_capft_curve.setMaximumValueofy(20.0)
  awhp_hc_high_speed_capft_curve.setMinimumCurveOutput(0.5)
  awhp_hc_high_speed_capft_curve.setMaximumCurveOutput(1.3)
  awhp_hc_high_speed_capft_curve.setInputUnitTypeforX('Temperature')
  awhp_hc_high_speed_capft_curve.setInputUnitTypeforY('Temperature')
  awhp_hc_high_speed_capft_curve.setOutputUnitType('Dimensionless')

  awhp_hc_high_speed_eirft_curve = OpenStudio::Model::CurveBiquadratic.new(model)
  awhp_hc_high_speed_eirft_curve.setName('EIRCurveFuncTempHT2')
  awhp_hc_high_speed_eirft_curve.setCoefficient1Constant(1.055)
  awhp_hc_high_speed_eirft_curve.setCoefficient2x(0.00035)
  awhp_hc_high_speed_eirft_curve.setCoefficient3xPOW2(-0.00027)
  awhp_hc_high_speed_eirft_curve.setCoefficient4y(-0.0108)
  awhp_hc_high_speed_eirft_curve.setCoefficient5yPOW2(0.0145)
  awhp_hc_high_speed_eirft_curve.setCoefficient6xTIMESY(-0.000230)
  awhp_hc_high_speed_eirft_curve.setMinimumValueofx(30.0)
  awhp_hc_high_speed_eirft_curve.setMaximumValueofx(50.0)
  awhp_hc_high_speed_eirft_curve.setMinimumValueofy(-7.0)
  awhp_hc_high_speed_eirft_curve.setMaximumValueofy(20.0)
  awhp_hc_high_speed_eirft_curve.setMinimumCurveOutput(0.7)
  awhp_hc_high_speed_eirft_curve.setMaximumCurveOutput(1.5)
  awhp_hc_high_speed_eirft_curve.setInputUnitTypeforX('Temperature')
  awhp_hc_high_speed_eirft_curve.setInputUnitTypeforY('Temperature')
  awhp_hc_high_speed_eirft_curve.setOutputUnitType('Dimensionless')

  awhp_hc_high_speed = OpenStudio::Model::HeatPumpAirToWaterHeatingSpeedData.new(
    model,
    awhp_hc_high_speed_capft_curve,
    awhp_hc_high_speed_eirft_curve,
    get_or_create_constant_eirplr_curve(model)
  )
  awhp_hc_high_speed.setName('AWHP Heating High Speed')
  awhp_hc_high_speed.setRatedHeatingCapacity(40000.0)
  awhp_hc_high_speed.setRatedCOPforHeating(3.51)

  awhp_hc_high_speed
end

#############
#  COOLING  #
#############

def make_awhp_cooling_side(model)
  awhp_cc = OpenStudio::Model::HeatPumpAirToWaterCooling.new(model)

  awhp_cc.setName('AWHP Cooling')
  awhp_cc.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule)
  awhp_cc.setRatedInletAirTemperature(25.0)
  awhp_cc.setRatedAirFlowRate(20.0)
  # awhp_cc.autosizeRatedAirFlowRate
  awhp_cc.setRatedLeavingWaterTemperature(22.0)
  awhp_cc.autosizeRatedWaterFlowRate
  # awhp_cc.setRatedWaterFlowRate(0.005)
  awhp_cc.setMinimumOutdoorAirTemperature(18.0)
  awhp_cc.setMaximumOutdoorAirTemperature(40.0)

  awhp_cc_min_lwt_curve = OpenStudio::Model::CurveQuadratic.new(model)
  awhp_cc_min_lwt_curve.setName('MinCoolingSWTvsOAT')
  awhp_cc_min_lwt_curve.setCoefficient1Constant(-100.0)
  awhp_cc_min_lwt_curve.setCoefficient2x(0.0)
  awhp_cc_min_lwt_curve.setCoefficient3xPOW2(0.0)
  awhp_cc_min_lwt_curve.setMinimumValueofx(-17.77778)
  awhp_cc_min_lwt_curve.setMaximumValueofx(35.0)
  awhp_cc_min_lwt_curve.setMinimumCurveOutput(-100.0)
  awhp_cc_min_lwt_curve.setMaximumCurveOutput(35.0)
  awhp_cc_min_lwt_curve.setInputUnitTypeforX('Temperature')
  awhp_cc_min_lwt_curve.setOutputUnitType('Temperature')
  awhp_cc.setMinimumLeavingWaterTemperatureCurve(awhp_cc_min_lwt_curve)

  awhp_cc_max_lwt_curve = OpenStudio::Model::CurveQuadratic.new(model)
  awhp_cc_max_lwt_curve.setName('MaxCoolingSWTvsOAT')
  awhp_cc_max_lwt_curve.setCoefficient1Constant(53.1666666666667)
  awhp_cc_max_lwt_curve.setCoefficient2x(0.85)
  awhp_cc_max_lwt_curve.setCoefficient3xPOW2(0.0)
  awhp_cc_max_lwt_curve.setMinimumValueofx(-17.77778)
  awhp_cc_max_lwt_curve.setMaximumValueofx(35.0)
  awhp_cc_max_lwt_curve.setMinimumCurveOutput(20.0)
  awhp_cc_max_lwt_curve.setMaximumCurveOutput(60.0)
  awhp_cc_max_lwt_curve.setInputUnitTypeforX('Temperature')
  awhp_cc_max_lwt_curve.setOutputUnitType('Temperature')
  awhp_cc.setMaximumLeavingWaterTemperatureCurve(awhp_cc_max_lwt_curve)

  awhp_cc.setSizingFactor(0.9)

  awhp_cc
end

def make_awhp_cooling_low_speed(model)
  awhp_cc_low_speed_capft_curve = OpenStudio::Model::CurveBiquadratic.new(model)
  awhp_cc_low_speed_capft_curve.setName('CapCurveFuncTempCL')
  awhp_cc_low_speed_capft_curve.setCoefficient1Constant(0.900)
  awhp_cc_low_speed_capft_curve.setCoefficient2x(-0.00038)
  awhp_cc_low_speed_capft_curve.setCoefficient3xPOW2(-0.00042)
  awhp_cc_low_speed_capft_curve.setCoefficient4y(-0.0102)
  awhp_cc_low_speed_capft_curve.setCoefficient5yPOW2(0.0225)
  awhp_cc_low_speed_capft_curve.setCoefficient6xTIMESY(-0.000210)
  awhp_cc_low_speed_capft_curve.setMinimumValueofx(5.0)
  awhp_cc_low_speed_capft_curve.setMaximumValueofx(15.0)
  awhp_cc_low_speed_capft_curve.setMinimumValueofy(15.0)
  awhp_cc_low_speed_capft_curve.setMaximumValueofy(45.0)
  awhp_cc_low_speed_capft_curve.setMinimumCurveOutput(0.7)
  awhp_cc_low_speed_capft_curve.setMaximumCurveOutput(1.3)
  awhp_cc_low_speed_capft_curve.setInputUnitTypeforX('Temperature')
  awhp_cc_low_speed_capft_curve.setInputUnitTypeforY('Temperature')
  awhp_cc_low_speed_capft_curve.setOutputUnitType('Dimensionless')

  awhp_cc_low_speed_eirft_curve = OpenStudio::Model::CurveBiquadratic.new(model)
  awhp_cc_low_speed_eirft_curve.setName('EIRCurveFuncTempCL')
  awhp_cc_low_speed_eirft_curve.setCoefficient1Constant(0.980)
  awhp_cc_low_speed_eirft_curve.setCoefficient2x(0.00021)
  awhp_cc_low_speed_eirft_curve.setCoefficient3xPOW2(0.00019)
  awhp_cc_low_speed_eirft_curve.setCoefficient4y(0.0068)
  awhp_cc_low_speed_eirft_curve.setCoefficient5yPOW2(-0.0085)
  awhp_cc_low_speed_eirft_curve.setCoefficient6xTIMESY(0.000158)
  awhp_cc_low_speed_eirft_curve.setMinimumValueofx(5.0)
  awhp_cc_low_speed_eirft_curve.setMaximumValueofx(15.0)
  awhp_cc_low_speed_eirft_curve.setMinimumValueofy(15.0)
  awhp_cc_low_speed_eirft_curve.setMaximumValueofy(45.0)
  awhp_cc_low_speed_eirft_curve.setMinimumCurveOutput(0.7)
  awhp_cc_low_speed_eirft_curve.setMaximumCurveOutput(1.3)
  awhp_cc_low_speed_eirft_curve.setInputUnitTypeforX('Temperature')
  awhp_cc_low_speed_eirft_curve.setInputUnitTypeforY('Temperature')
  awhp_cc_low_speed_eirft_curve.setOutputUnitType('Dimensionless')

  awhp_cc_low_speed = OpenStudio::Model::HeatPumpAirToWaterCoolingSpeedData.new(
    model,
    awhp_cc_low_speed_capft_curve,
    awhp_cc_low_speed_eirft_curve,
    get_or_create_constant_eirplr_curve(model)
  )
  awhp_cc_low_speed.setName('AWHP Cooling Low Speed')
  awhp_cc_low_speed.setRatedCoolingCapacity(200000.0)
  awhp_cc_low_speed.setRatedCOPforCooling(3.5)

  awhp_cc_low_speed
end

def make_awhp_cooling_high_speed(model)
  awhp_cc_high_speed_capft_curve = OpenStudio::Model::CurveBiquadratic.new(model)
  awhp_cc_high_speed_capft_curve.setName('CapCurveFuncTempCL2')
  awhp_cc_high_speed_capft_curve.setCoefficient1Constant(0.910)
  awhp_cc_high_speed_capft_curve.setCoefficient2x(-0.00034)
  awhp_cc_high_speed_capft_curve.setCoefficient3xPOW2(-0.00040)
  awhp_cc_high_speed_capft_curve.setCoefficient4y(-0.0096)
  awhp_cc_high_speed_capft_curve.setCoefficient5yPOW2(0.0208)
  awhp_cc_high_speed_capft_curve.setCoefficient6xTIMESY(-0.000205)
  awhp_cc_high_speed_capft_curve.setMinimumValueofx(5.0)
  awhp_cc_high_speed_capft_curve.setMaximumValueofx(15.0)
  awhp_cc_high_speed_capft_curve.setMinimumValueofy(15.0)
  awhp_cc_high_speed_capft_curve.setMaximumValueofy(45.0)
  awhp_cc_high_speed_capft_curve.setMinimumCurveOutput(0.7)
  awhp_cc_high_speed_capft_curve.setMaximumCurveOutput(1.3)
  awhp_cc_high_speed_capft_curve.setInputUnitTypeforX('Temperature')
  awhp_cc_high_speed_capft_curve.setInputUnitTypeforY('Temperature')
  awhp_cc_high_speed_capft_curve.setOutputUnitType('Dimensionless')

  awhp_cc_high_speed_eirft_curve = OpenStudio::Model::CurveBiquadratic.new(model)
  awhp_cc_high_speed_eirft_curve.setName('EIRCurveFuncTempCL2')
  awhp_cc_high_speed_eirft_curve.setCoefficient1Constant(0.990)
  awhp_cc_high_speed_eirft_curve.setCoefficient2x(0.00019)
  awhp_cc_high_speed_eirft_curve.setCoefficient3xPOW2(0.00017)
  awhp_cc_high_speed_eirft_curve.setCoefficient4y(0.0075)
  awhp_cc_high_speed_eirft_curve.setCoefficient5yPOW2(-0.0078)
  awhp_cc_high_speed_eirft_curve.setCoefficient6xTIMESY(0.000165)
  awhp_cc_high_speed_eirft_curve.setMinimumValueofx(5.0)
  awhp_cc_high_speed_eirft_curve.setMaximumValueofx(15.0)
  awhp_cc_high_speed_eirft_curve.setMinimumValueofy(15.0)
  awhp_cc_high_speed_eirft_curve.setMaximumValueofy(45.0)
  awhp_cc_high_speed_eirft_curve.setMinimumCurveOutput(0.7)
  awhp_cc_high_speed_eirft_curve.setMaximumCurveOutput(1.3)
  awhp_cc_high_speed_eirft_curve.setInputUnitTypeforX('Temperature')
  awhp_cc_high_speed_eirft_curve.setInputUnitTypeforY('Temperature')
  awhp_cc_high_speed_eirft_curve.setOutputUnitType('Dimensionless')

  awhp_cc_high_speed = OpenStudio::Model::HeatPumpAirToWaterCoolingSpeedData.new(
    model,
    awhp_cc_high_speed_capft_curve,
    awhp_cc_high_speed_eirft_curve,
    get_or_create_constant_eirplr_curve(model)
  )
  awhp_cc_high_speed.setName('AWHP Cooling High Speed')
  awhp_cc_high_speed.setRatedCoolingCapacity(400000.0)
  awhp_cc_high_speed.setRatedCOPforCooling(3.5)

  awhp_cc_high_speed
end

#######################################################################################################################
#                                                 C O N N E C T I N G                                                 #
#######################################################################################################################

awhp = make_awhp(model)

awhp_hc = make_awhp_heating_side(model)
awhp.setHeatingOperationMode(awhp_hc)
hw_loop.addSupplyBranchForComponent(awhp_hc)

awhp_hc_low_speed = make_awhp_heating_low_speed(model)
awhp_hc_high_speed = make_awhp_heating_high_speed(model)
# Demonstration of speed API
awhp_hc.addSpeed(awhp_hc_low_speed)
awhp_hc.addSpeed(awhp_hc_high_speed)
raise unless awhp_hc.numberOfSpeeds == 2
raise unless awhp_hc.speeds == [awhp_hc_low_speed, awhp_hc_high_speed]

awhp_hc.removeAllSpeeds

awhp_hc.setSpeeds([awhp_hc_low_speed, awhp_hc_high_speed])
raise unless awhp_hc.numberOfSpeeds == 2
raise unless awhp_hc.speeds == [awhp_hc_low_speed, awhp_hc_high_speed]

# boosterModeOnSpeed = OpenStudio::Model::HeatPumpAirToWaterHeatingSpeedData.new(model)
# boosterModeOnSpeed.setName("#{awhp_hc.nameString} Booster Mode On Speed")
# boosterModeOnSpeed.setRatedHeatingCapacity(60000.0)
# boosterModeOnSpeed.setRatedCOPforHeating(3.0)
# boosterModeOnSpeed.normalizedHeatingCapacityFunctionofTemperatureCurve().setName(boosterModeOnSpeed.nameString() + " CapFT Curve")
# boosterModeOnSpeed.heatingEnergyInputRatioFunctionofTemperatureCurve().setName(boosterModeOnSpeed.nameString() + " EIRfT Curve")
# boosterModeOnSpeed.heatingEnergyInputRatioFunctionofPLRCurve().setName(boosterModeOnSpeed.nameString() + " EIRfPLR Curve")
# awhp_hc.setBoosterModeOnSpeed(boosterModeOnSpeed)

awhp_cc = make_awhp_cooling_side(model)
awhp.setCoolingOperationMode(awhp_cc)
chw_loop.addSupplyBranchForComponent(awhp_cc)

awhp_cc_low_speed = make_awhp_cooling_low_speed(model)
awhp_cc_high_speed = make_awhp_cooling_high_speed(model)
awhp_cc.addSpeed(awhp_cc_low_speed)
awhp_cc.addSpeed(awhp_cc_high_speed)

###############################################################################
#                            Z O N E    L E V E L                             #
###############################################################################

fourPipeFan = OpenStudio::Model::FanOnOff.new(model, model.alwaysOnDiscreteSchedule)
fourPipeHeat = OpenStudio::Model::CoilHeatingWater.new(model, model.alwaysOnDiscreteSchedule)
hw_loop.addDemandBranchForComponent(fourPipeHeat)
fourPipeCool = OpenStudio::Model::CoilCoolingWater.new(model, model.alwaysOnDiscreteSchedule)
chw_loop.addDemandBranchForComponent(fourPipeCool)
fourPipeFanCoil = OpenStudio::Model::ZoneHVACFourPipeFanCoil.new(model, model.alwaysOnDiscreteSchedule,
                                                                 fourPipeFan, fourPipeCool, fourPipeHeat)
fourPipeFanCoil.addToThermalZone(zone)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
