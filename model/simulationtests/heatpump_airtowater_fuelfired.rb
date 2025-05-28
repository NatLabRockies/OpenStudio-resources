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

# PlantLoopHeatPump_Fuel-Fired.idf

ffhp_airsource_htg = OpenStudio::Model::HeatPumpAirToWaterFuelFiredHeating.new(model)
ffhp_airsource_clg = OpenStudio::Model::HeatPumpAirToWaterFuelFiredCooling.new(model)

ffhp_airsource_htg.setName('Heat Pump Plant Loop Fuel Fired Heating - AirSource')
ffhp_airsource_htg.setCompanionCoolingHeatPump(ffhp_airsource_clg)

fuelEnergyInputRatioDefrostAdjustmentCurve = OpenStudio::Model::CurveQuadratic.new(model)
fuelEnergyInputRatioDefrostAdjustmentCurve.setName('EIRDefrostFoTCurve')
fuelEnergyInputRatioDefrostAdjustmentCurve.setCoefficient1Constant(1.0317)
fuelEnergyInputRatioDefrostAdjustmentCurve.setCoefficient2x(-0.006)
fuelEnergyInputRatioDefrostAdjustmentCurve.setCoefficient3xPOW2(-0.0011)
fuelEnergyInputRatioDefrostAdjustmentCurve.setMinimumValueofx(-100)
fuelEnergyInputRatioDefrostAdjustmentCurve.setMaximumValueofx(100)
fuelEnergyInputRatioDefrostAdjustmentCurve.setMinimumCurveOutput(1.0)
fuelEnergyInputRatioDefrostAdjustmentCurve.setMaximumCurveOutput(10.0)

cyclingRatioFactorCurve = OpenStudio::Model::CurveQuadratic.new(model)
cyclingRatioFactorCurve.setName('CRFCurve')
cyclingRatioFactorCurve.setCoefficient1Constant(1)
cyclingRatioFactorCurve.setCoefficient2x(0)
cyclingRatioFactorCurve.setCoefficient3xPOW2(0)
cyclingRatioFactorCurve.setMinimumValueofx(0)
cyclingRatioFactorCurve.setMaximumValueofx(100)
cyclingRatioFactorCurve.setMinimumCurveOutput(0)
cyclingRatioFactorCurve.setMaximumCurveOutput(10.0)

auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve = OpenStudio::Model::CurveBiquadratic.new(model)
auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve.setName('auxElecEIRCurveFuncTempCurve')
auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve.setCoefficient1Constant(1)
auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve.setCoefficient2x(0)
auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve.setCoefficient3xPOW2(0)
auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve.setCoefficient4y(0)
auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve.setCoefficient5yPOW2(0)
auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve.setCoefficient6xTIMESY(0)
auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve.setMinimumValueofx(-100)
auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve.setMaximumValueofx(100)
auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve.setMinimumValueofy(-100)
auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve.setMaximumValueofy(100)

auxiliaryElectricEnergyInputRatioFunctionofPLRCurve = OpenStudio::Model::CurveCubic.new(model)
auxiliaryElectricEnergyInputRatioFunctionofPLRCurve.setName('auxElecEIRFoPLRCurve')
auxiliaryElectricEnergyInputRatioFunctionofPLRCurve.setCoefficient1Constant(1)
auxiliaryElectricEnergyInputRatioFunctionofPLRCurve.setCoefficient2x(0)
auxiliaryElectricEnergyInputRatioFunctionofPLRCurve.setCoefficient3xPOW2(0)
auxiliaryElectricEnergyInputRatioFunctionofPLRCurve.setCoefficient4xPOW3(0)
auxiliaryElectricEnergyInputRatioFunctionofPLRCurve.setMinimumValueofx(-100)
auxiliaryElectricEnergyInputRatioFunctionofPLRCurve.setMaximumValueofx(100)

ffhp_airsource_htg.setNominalHeatingCapacity(80000)
ffhp_airsource_htg.setNominalCOP(1.5)
ffhp_airsource_htg.setDesignFlowRate(0.005)
ffhp_airsource_htg.setDesignSupplyTemperature(60)
ffhp_airsource_htg.setDesignTemperatureLift(13)
ffhp_airsource_htg.setSizingFactor(1.0)
ffhp_airsource_htg.setFlowMode('NotModulated')
ffhp_airsource_htg.setOutdoorAirTemperatureCurveInputVariable('DryBulb')
ffhp_airsource_htg.setWaterTemperatureCurveInputVariable('EnteringCondenser')
ffhp_airsource_htg.normalizedCapacityFunctionofTemperatureCurve.setName('CapCurveFuncTemp')
ffhp_airsource_htg.fuelEnergyInputRatioFunctionofTemperatureCurve.setName('EIRCurveFuncTemp')
ffhp_airsource_htg.fuelEnergyInputRatioFunctionofPLRCurve.setName('EIRCurveFuncPLR')
ffhp_airsource_htg.setMinimumPartLoadRatio(0.2)
ffhp_airsource_htg.setMaximumPartLoadRatio(1.0)
ffhp_airsource_htg.setDefrostControlType('OnDemand')
ffhp_airsource_htg.setDefrostOperationTimeFraction(0.0)
ffhp_airsource_htg.setFuelEnergyInputRatioDefrostAdjustmentCurve(fuelEnergyInputRatioDefrostAdjustmentCurve)
ffhp_airsource_htg.setResistiveDefrostHeaterCapacity(0.0)
ffhp_airsource_htg.setMaximumOutdoorDrybulbTemperatureforDefrostOperation(3.0)
ffhp_airsource_htg.setCyclingRatioFactorCurve(cyclingRatioFactorCurve)
ffhp_airsource_htg.setNominalAuxiliaryElectricPower(500)
ffhp_airsource_htg.setAuxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve(auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve)
ffhp_airsource_htg.setAuxiliaryElectricEnergyInputRatioFunctionofPLRCurve(auxiliaryElectricEnergyInputRatioFunctionofPLRCurve)
ffhp_airsource_htg.setStandbyElectricPower(20)
# ffhp_airsource_htg.autosizeNominalHeatingCapacity()
# ffhp_airsource_htg.autosizeDesignFlowRate()
# ffhp_airsource_htg.autosizeDesignTemperatureLift()

ffhp_airsource_clg.setName('Heat Pump Plant Loop Fuel Fired Cooling - AirSource')
ffhp_airsource_clg.setCompanionHeatingHeatPump(ffhp_airsource_htg)
ffhp_airsource_clg.setNominalCoolingCapacity(400000)
ffhp_airsource_clg.setNominalCOP(2.0)
ffhp_airsource_clg.setDesignFlowRate(0.005)
ffhp_airsource_clg.setDesignSupplyTemperature(7)
ffhp_airsource_clg.setDesignTemperatureLift(11.1)
ffhp_airsource_clg.setSizingFactor(1.0)
ffhp_airsource_clg.setFlowMode('NotModulated')
ffhp_airsource_clg.setOutdoorAirTemperatureCurveInputVariable('DryBulb')
ffhp_airsource_clg.setWaterTemperatureCurveInputVariable('EnteringEvaporator')
ffhp_airsource_clg.normalizedCapacityFunctionofTemperatureCurve.setName('CapCurveFuncTemp2')
ffhp_airsource_clg.fuelEnergyInputRatioFunctionofTemperatureCurve.setName('EIRCurveFuncTemp2')
ffhp_airsource_clg.fuelEnergyInputRatioFunctionofPLRCurve.setName('EIRCurveFuncPLR2')
ffhp_airsource_clg.setMinimumPartLoadRatio(0.2)
ffhp_airsource_clg.setMaximumPartLoadRatio(1.0)
ffhp_airsource_clg.setCyclingRatioFactorCurve(cyclingRatioFactorCurve)
ffhp_airsource_clg.setNominalAuxiliaryElectricPower(500)
ffhp_airsource_clg.setAuxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve(auxiliaryElectricEnergyInputRatioFunctionofTemperatureCurve)
ffhp_airsource_clg.setAuxiliaryElectricEnergyInputRatioFunctionofPLRCurve(auxiliaryElectricEnergyInputRatioFunctionofPLRCurve)
ffhp_airsource_clg.setStandbyElectricPower(20)
# ffhp_airsource_clg.autosizeNominalCoolingCapacity()
# ffhp_airsource_clg.autosizeDesignFlowRate()
# ffhp_airsource_clg.autosizeDesignTemperatureLift()

hw_loop.addSupplyBranchForComponent(ffhp_airsource_htg)
chw_loop.addSupplyBranchForComponent(ffhp_airsource_clg)

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
