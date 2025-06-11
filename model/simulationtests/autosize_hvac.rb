# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 9 story, 100m X 50m, 45 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 9,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 3 })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# add windows at a 40% window-to-wall ratio
# model.add_windows({"wwr" => 0.4,
# "offset" => 1,
# "application_type" => "Above Floor"})

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = model.getThermalZones.sort_by { |z| z.name.to_s }
puts "The model has #{zones.size} thermal zones"

# Change the simulation to only run the sizing days
sim_control = model.getSimulationControl
sim_control.setRunSimulationforSizingPeriods(true)
sim_control.setRunSimulationforWeatherFileRunPeriods(false)

### schedules
s1 = model.alwaysOnDiscreteSchedule

### method to make evap-cooled dx coils
def new_evap_cooling_coil_dx_singlespeed(model)
  clg_coil = OpenStudio::Model::CoilCoolingDXSingleSpeed.new(model)
  clg_coil.setCondenserType('EvaporativelyCooled')
  clg_coil.setEvaporativeCondenserAirFlowRate(OpenStudio::OptionalDouble.new)
  clg_coil.setEvaporativeCondenserPumpRatedPowerConsumption(OpenStudio::OptionalDouble.new)
  return clg_coil
end

def new_evap_cooling_coil_dx_twospeed(model)
  clg_coil = OpenStudio::Model::CoilCoolingDXTwoSpeed.new(model)
  clg_coil.setCondenserType('EvaporativelyCooled')
  clg_coil.setLowSpeedEvaporativeCondenserEffectiveness(0.85)
  clg_coil.setHighSpeedEvaporativeCondenserEffectiveness(0.85)
  clg_coil.setLowSpeedEvaporativeCondenserAirFlowRate(OpenStudio::OptionalDouble.new)
  clg_coil.setHighSpeedEvaporativeCondenserAirFlowRate(OpenStudio::OptionalDouble.new)
  clg_coil.setLowSpeedEvaporativeCondenserPumpRatedPowerConsumption(OpenStudio::OptionalDouble.new)
  clg_coil.setHighSpeedEvaporativeCondenserPumpRatedPowerConsumption(OpenStudio::OptionalDouble.new)
  clg_coil.setRatedLowSpeedSensibleHeatRatio(OpenStudio::OptionalDouble.new)
  return clg_coil
end

def curve_biquadratic(model, c_1constant, c_2x, c_3xPOW2, c_4y, c_5yPOW2, c_6xTIMESY, minx, maxx, miny, maxy)
  curve = OpenStudio::Model::CurveBiquadratic.new(model)
  curve.setCoefficient1Constant(c_1constant)
  curve.setCoefficient2x(c_2x)
  curve.setCoefficient3xPOW2(c_3xPOW2)
  curve.setCoefficient4y(c_4y)
  curve.setCoefficient5yPOW2(c_5yPOW2)
  curve.setCoefficient6xTIMESY(c_6xTIMESY)
  curve.setMinimumValueofx(minx)
  curve.setMaximumValueofx(maxx)
  curve.setMinimumValueofy(miny)
  curve.setMaximumValueofy(maxy)
  return curve
end

def curve_quadratic(model, c_1constant, c_2x, c_3xPOW2, minx, maxx, miny = nil, maxy = nil)
  curve = OpenStudio::Model::CurveQuadratic.new(model)
  curve.setCoefficient1Constant(c_1constant)
  curve.setCoefficient2x(c_2x)
  curve.setCoefficient3xPOW2(c_3xPOW2)
  curve.setMinimumValueofx(minx)
  curve.setMaximumValueofx(maxx)
  curve.setMinimumCurveOutput(miny) if !miny.nil?
  curve.setMaximumCurveOutput(maxy) if !maxy.nil?
  return curve
end

def make_tes_coil(model)
  tes_coil = OpenStudio::Model::CoilCoolingDXSingleSpeedThermalStorage.new(model)
  tes_op_schedule = OpenStudio::Model::ScheduleConstant.new(model)
  tes_op_schedule.setValue(2) # 2 = Cooling Only Mode
  tes_coil.setOperationModeControlSchedule(tes_op_schedule)
  tes_coil.setStorageType('Ice')
  tes_coil.autosizeFluidStorageVolume # Only autosized if Storage Type is Water
  tes_coil.autosizeIceStorageCapacity
  tes_coil.autosizeRatedEvaporatorAirFlowRate

  # Obviously, don't use this in production code. We just assign all curves to
  # a constant value to avoid E+ crashing on us, while not having to actually
  # create 41 curves with potentially lots of values...
  constant_univariate = OpenStudio::Model::CurveCubic.new(model)
  constant_univariate.setName('Constant Univariate Curve')
  constant_univariate.setCoefficient1Constant(1.0)
  constant_univariate.setCoefficient4xPOW3(0.0)
  constant_univariate.setMinimumValueofx(-100.0)
  constant_univariate.setMaximumValueofx(100.0)

  constant_bivariate = OpenStudio::Model::CurveBiquadratic.new(model)
  constant_bivariate.setName('Constant Bivariate Curve')
  constant_bivariate.setCoefficient1Constant(1.0)
  constant_bivariate.setMinimumValueofx(-100.0)
  constant_bivariate.setMaximumValueofx(100.0)
  constant_bivariate.setMinimumValueofy(-100.0)
  constant_bivariate.setMaximumValueofy(100.0)

  constant_trivariate = OpenStudio::Model::CurveTriquadratic.new(model)
  constant_trivariate.setCoefficient1Constant(1.0)
  constant_trivariate.setMinimumValueofx(-100.0)
  constant_trivariate.setMaximumValueofx(100.0)
  constant_trivariate.setMinimumValueofy(-100.0)
  constant_trivariate.setMaximumValueofy(100.0)
  constant_trivariate.setMinimumValueofz(-100.0)
  constant_trivariate.setMaximumValueofz(100.0)

  object_list_to_curve = {
    'UnivariateFunctions' => constant_univariate,
    'BivariateFunctions' => constant_bivariate,
    'TrivariateFunctions' => constant_trivariate
  }

  # Scan the curve fields, assign a constant curve with the right number of
  # independent variables
  iddObject = tes_coil.iddObject
  iddObject.numFields.times do |i|
    field = iddObject.getField(i).get
    field_name = field.name
    next unless field_name.include?('Curve')

    props = field.properties
    olist = props.objectLists.first
    setter = "set#{field_name.gsub(' ', '')}"
    raise "Undefined method #{setter} for field_name=#{field_name} at index #{i}" unless tes_coil.respond_to?(setter)

    tes_coil.send(setter, object_list_to_curve[olist])
  end

  tes_coil.setCondenserType('EvaporativelyCooled')

  tes_coil.setCoolingOnlyModeAvailable(true)
  tes_coil.autosizeCoolingOnlyModeRatedTotalEvaporatorCoolingCapacity
  tes_coil.setCoolingAndChargeModeAvailable(true)
  tes_coil.autosizeCoolingAndChargeModeRatedTotalEvaporatorCoolingCapacity
  tes_coil.autosizeCoolingAndChargeModeRatedStorageChargingCapacity
  tes_coil.setCoolingAndDischargeModeAvailable(true)
  tes_coil.autosizeCoolingAndDischargeModeRatedTotalEvaporatorCoolingCapacity
  tes_coil.autosizeCoolingAndDischargeModeRatedStorageDischargingCapacity
  tes_coil.setChargeOnlyModeAvailable(true)
  tes_coil.autosizeChargeOnlyModeRatedStorageChargingCapacity
  tes_coil.setDischargeOnlyModeAvailable(true)
  tes_coil.autosizeDischargeOnlyModeRatedStorageDischargingCapacity
  tes_coil.autosizeCondenserDesignAirFlowRate
  tes_coil.autosizeEvaporativeCondenserPumpRatedPowerConsumption
  return tes_coil
end

### High level constructs

### Declare loops
storage_loop = OpenStudio::Model::PlantLoop.new(model)
hw_loop = OpenStudio::Model::PlantLoop.new(model)
cw_loop = OpenStudio::Model::PlantLoop.new(model)
chw_loop = OpenStudio::Model::PlantLoop.new(model)
swh_loop = model.add_swh_loop('Mixed')

###  water loop for Heat recovery ###
# Water use connection
swh_connection = OpenStudio::Model::WaterUseConnections.new(model)
# Water fixture definition
water_fixture_def = OpenStudio::Model::WaterUseEquipmentDefinition.new(model)
rated_flow_rate_gal_per_min = 50
rated_flow_rate_m3_per_s = OpenStudio.convert(rated_flow_rate_gal_per_min, 'gal/min', 'm^3/s').get
water_fixture_def.setPeakFlowRate(rated_flow_rate_m3_per_s)
water_fixture_def.setName("Service Water Use Def #{rated_flow_rate_gal_per_min.round(2)}gal/min")
# Target mixed water temperature
mixed_water_temp_f = 110
mixed_water_temp_sch = OpenStudio::Model::ScheduleRuleset.new(model, OpenStudio.convert(mixed_water_temp_f, 'F', 'C').get)
water_fixture_def.setTargetTemperatureSchedule(mixed_water_temp_sch)
# Water use equipment
water_fixture = OpenStudio::Model::WaterUseEquipment.new(water_fixture_def)
water_fixture.setName("Service Water Use #{rated_flow_rate_gal_per_min.round(2)}gal/min")
swh_connection.addWaterUseEquipment(water_fixture)
# Connect the water use connection to the SWH loop
swh_loop.addDemandBranchForComponent(swh_connection)

### Chilled water loop for thermal storage ###
storage_loop.setName('Storage Chilled Water Loop')
storage_loop.setMaximumLoopTemperature(98)
storage_loop.setMinimumLoopTemperature(1)
chw_temp_f = 35
chw_delta_t_r = 5 # 5F delta-T
chw_temp_c = OpenStudio.convert(chw_temp_f, 'F', 'C').get
chw_delta_t_k = OpenStudio.convert(chw_delta_t_r, 'R', 'K').get
chw_temp_sch = OpenStudio::Model::ScheduleRuleset.new(model)
chw_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), chw_temp_c)
chw_stpt_manager = OpenStudio::Model::SetpointManagerScheduled.new(model, chw_temp_sch)
chw_stpt_manager.addToNode(storage_loop.supplyOutletNode)
sizing_plant = storage_loop.sizingPlant
sizing_plant.setLoopType('Cooling')
sizing_plant.setDesignLoopExitTemperature(chw_temp_c)
sizing_plant.setLoopDesignTemperatureDifference(chw_delta_t_k)

# Chilled water pump
pri_chw_pump = OpenStudio::Model::HeaderedPumpsVariableSpeed.new(model)
pri_chw_pump.setName('Storage Chilled Water Loop Pump')
pri_chw_pump_head_ft_h2o = 15
pri_chw_pump_head_press_pa = OpenStudio.convert(pri_chw_pump_head_ft_h2o, 'ftH_{2}O', 'Pa').get
pri_chw_pump.setRatedPumpHead(pri_chw_pump_head_press_pa)
pri_chw_pump.setMotorEfficiency(0.9)
pri_chw_pump.setPumpControlType('Intermittent')
pri_chw_pump.addToNode(storage_loop.supplyInletNode)

# Cooling equipment
storage_loop.addSupplyBranchForComponent(OpenStudio::Model::DistrictCooling.new(model))

### Condenser water loop ###
cw_loop.setName('Condenser Water Loop')
cw_loop.setMaximumLoopTemperature(80)
cw_loop.setMinimumLoopTemperature(5)
cw_temp_f = 70 # CW setpoint 70F
cw_temp_sizing_f = 102 # CW sized to deliver 102F
cw_delta_t_r = 10 # 10F delta-T
cw_approach_delta_t_r = 7 # 7F approach
cw_temp_c = OpenStudio.convert(cw_temp_f, 'F', 'C').get
cw_temp_sizing_c = OpenStudio.convert(cw_temp_sizing_f, 'F', 'C').get
cw_delta_t_k = OpenStudio.convert(cw_delta_t_r, 'R', 'K').get
cw_approach_delta_t_k = OpenStudio.convert(cw_approach_delta_t_r, 'R', 'K').get
float_down_to_f = 70
float_down_to_c = OpenStudio.convert(float_down_to_f, 'F', 'C').get
cw_t_stpt_manager = OpenStudio::Model::SetpointManagerFollowOutdoorAirTemperature.new(model)
cw_t_stpt_manager.setReferenceTemperatureType('OutdoorAirWetBulb')
cw_t_stpt_manager.setMaximumSetpointTemperature(cw_temp_sizing_c)
cw_t_stpt_manager.setMinimumSetpointTemperature(float_down_to_c)
cw_t_stpt_manager.setOffsetTemperatureDifference(cw_approach_delta_t_k)
cw_t_stpt_manager.addToNode(cw_loop.supplyOutletNode)
sizing_plant = cw_loop.sizingPlant
sizing_plant.setLoopType('Condenser')
sizing_plant.setDesignLoopExitTemperature(cw_temp_sizing_c)
sizing_plant.setLoopDesignTemperatureDifference(cw_delta_t_k)

# Condenser water pump
cw_pump = OpenStudio::Model::PumpConstantSpeed.new(model)
cw_pump.setName('Condenser Water Loop Pump')
cw_pump_head_ft_h2o = 60.0
cw_pump_head_press_pa = OpenStudio.convert(cw_pump_head_ft_h2o, 'ftH_{2}O', 'Pa').get
cw_pump.setRatedPumpHead(cw_pump_head_press_pa)
cw_pump.addToNode(cw_loop.supplyInletNode)

# Heat rejection equipment
cw_loop.addSupplyBranchForComponent(OpenStudio::Model::CoolingTowerSingleSpeed.new(model))
clg_twr = OpenStudio::Model::CoolingTowerTwoSpeed.new(model)
clg_twr.autosizeFreeConvectionRegimeAirFlowRate
clg_twr.autosizeFreeConvectionRegimeUFactorTimesAreaValue
cw_loop.addSupplyBranchForComponent(clg_twr)
# Not testing the alternate autosizing approach for 2 speed cooling towers,
# but the queries were checked manually.
# clg_twr = OpenStudio::Model::CoolingTowerTwoSpeed.new(model) # Uses different sizing approach
# clg_twr.setPerformanceInputMethod('NominalCapacity')
# clg_twr.resetDesignWaterFlowRate
# clg_twr.resetHighFanSpeedUFactorTimesAreaValue
# clg_twr.resetLowFanSpeedUFactorTimesAreaValue
# clg_twr.autosizeFreeConvectionRegimeAirFlowRate
# clg_twr.setHighSpeedNominalCapacity(17265800)
# clg_twr.autosizeLowSpeedNominalCapacity
# clg_twr.autosizeFreeConvectionNominalCapacity
# cw_loop.addSupplyBranchForComponent(clg_twr)
cw_loop.addSupplyBranchForComponent(OpenStudio::Model::CoolingTowerVariableSpeed.new(model))
fluid_clr = OpenStudio::Model::FluidCoolerSingleSpeed.new(model)
fluid_clr.autosizeDesignAirFlowRate
fluid_clr.autosizeDesignAirFlowRateFanPower
fluid_clr.autosizeDesignAirFlowRateUfactorTimesAreaValue
fluid_clr.autosizeDesignWaterFlowRate
cw_loop.addSupplyBranchForComponent(fluid_clr)
fluid_clr = OpenStudio::Model::FluidCoolerTwoSpeed.new(model)
fluid_clr.autosizeHighFanSpeedUfactorTimesAreaValue
fluid_clr.autosizeLowFanSpeedUfactorTimesAreaValue
fluid_clr.autosizeLowSpeedNominalCapacity
fluid_clr.autosizeDesignWaterFlowRate
fluid_clr.autosizeHighFanSpeedAirFlowRate
fluid_clr.autosizeHighFanSpeedFanPower
fluid_clr.autosizeLowFanSpeedAirFlowRate
fluid_clr.autosizeLowFanSpeedFanPower
cw_loop.addSupplyBranchForComponent(fluid_clr)
cw_loop.addSupplyBranchForComponent(OpenStudio::Model::EvaporativeFluidCoolerSingleSpeed.new(model))
cw_loop.addSupplyBranchForComponent(OpenStudio::Model::EvaporativeFluidCoolerTwoSpeed.new(model))
fluid_clr = OpenStudio::Model::EvaporativeFluidCoolerTwoSpeed.new(model) # Uses different sizing approach
fluid_clr.setPerformanceInputMethod('StandardDesignCapacity')
fluid_clr.setHighSpeedStandardDesignCapacity(50000)
fluid_clr.setLowSpeedStandardDesignCapacity(25000)

cw_loop.addSupplyBranchForComponent(fluid_clr)
fluid_clr = OpenStudio::Model::EvaporativeFluidCoolerTwoSpeed.new(model) # Uses different sizing approach
fluid_clr.setPerformanceInputMethod('UserSpecifiedDesignCapacity')
fluid_clr.setHighSpeedUserSpecifiedDesignCapacity(50000)
fluid_clr.setLowSpeedUserSpecifiedDesignCapacity(25000)
fluid_clr.setDesignEnteringWaterTemperature(52)
fluid_clr.setDesignEnteringAirTemperature(35)
fluid_clr.setDesignEnteringAirWetbulbTemperature(25.6)
fluid_clr.resetHighFanSpeedUfactorTimesAreaValue
fluid_clr.resetLowFanSpeedUfactorTimesAreaValue
cw_loop.addSupplyBranchForComponent(fluid_clr)

### Chilled water loop ###
chw_loop.setName('Chilled Water Loop')
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

# Primary chilled water pump
pri_chw_pump = OpenStudio::Model::HeaderedPumpsConstantSpeed.new(model)
pri_chw_pump.setName('Chilled Water Loop Primary Pump')
pri_chw_pump_head_ft_h2o = 15
pri_chw_pump_head_press_pa = OpenStudio.convert(pri_chw_pump_head_ft_h2o, 'ftH_{2}O', 'Pa').get
pri_chw_pump.setRatedPumpHead(pri_chw_pump_head_press_pa)
pri_chw_pump.setMotorEfficiency(0.9)
pri_chw_pump.setPumpControlType('Intermittent')
pri_chw_pump.addToNode(chw_loop.supplyInletNode)
# Secondary chilled water pump
sec_chw_pump = OpenStudio::Model::HeaderedPumpsVariableSpeed.new(model)
sec_chw_pump.setName('Chilled Water Loop Secondary Pump')
sec_chw_pump_head_ft_h2o = 45
sec_chw_pump_head_press_pa = OpenStudio.convert(sec_chw_pump_head_ft_h2o, 'ftH_{2}O', 'Pa').get
sec_chw_pump.setRatedPumpHead(sec_chw_pump_head_press_pa)
sec_chw_pump.setMotorEfficiency(0.9)
# Curve makes it perform like variable speed pump
sec_chw_pump.setFractionofMotorInefficienciestoFluidStream(0)
sec_chw_pump.setCoefficient1ofthePartLoadPerformanceCurve(0)
sec_chw_pump.setCoefficient2ofthePartLoadPerformanceCurve(0.0205)
sec_chw_pump.setCoefficient3ofthePartLoadPerformanceCurve(0.4101)
sec_chw_pump.setCoefficient4ofthePartLoadPerformanceCurve(0.5753)
sec_chw_pump.setPumpControlType('Intermittent')
sec_chw_pump.addToNode(chw_loop.demandInletNode)
# Change the chilled water loop to have a two-way common pipes
chw_loop.setCommonPipeSimulation('CommonPipe')

# Cooling equipment
chiller = OpenStudio::Model::ChillerElectricEIR.new(model)
chw_loop.addSupplyBranchForComponent(chiller)
cw_loop.addDemandBranchForComponent(chiller)
swh_loop.addDemandBranchForComponent(chiller) # Heat Recovery
chiller = OpenStudio::Model::ChillerAbsorptionIndirect.new(model)
chw_loop.addSupplyBranchForComponent(chiller)
cw_loop.addDemandBranchForComponent(chiller)
swh_loop.addDemandBranchForComponent(chiller) # Heat Recovery
chiller = OpenStudio::Model::ChillerAbsorption.new(model)
chw_loop.addSupplyBranchForComponent(chiller)
cw_loop.addDemandBranchForComponent(chiller)
swh_loop.addDemandBranchForComponent(chiller) # Heat Recovery
chiller = OpenStudio::Model::ChillerElectricReformulatedEIR.new(model)
chw_loop.addSupplyBranchForComponent(chiller)
cw_loop.addDemandBranchForComponent(chiller)
swh_loop.addDemandBranchForComponent(chiller) # Heat Recovery

file_name = File.join(File.dirname(__FILE__), 'CoolSys1-Chiller-Detailed.RS0001.a205.cbor')
file_name = File.realpath(file_name)
representation_file = OpenStudio::Model::ExternalFile.getExternalFile(model, file_name)
chiller = OpenStudio::Model::ChillerElectricASHRAE205.new(representation_file.get)
chw_loop.addSupplyBranchForComponent(chiller)
cw_loop.addDemandBranchForComponent(chiller)
swh_loop.addDemandBranchForComponent(chiller) # Heat Recovery (not enabled in 22.2.0)

chw_loop.addSupplyBranchForComponent(OpenStudio::Model::DistrictCooling.new(model))
wwhp = OpenStudio::Model::HeatPumpWaterToWaterEquationFitCooling.new(model)
chw_loop.addSupplyBranchForComponent(wwhp)
cw_loop.addDemandBranchForComponent(wwhp)
chw_storage = OpenStudio::Model::ThermalStorageChilledWaterStratified.new(model)
chw_storage.setSetpointTemperatureSchedule(chw_temp_sch)
chw_loop.addSupplyBranchForComponent(chw_storage)
storage_loop.addDemandBranchForComponent(chw_storage)

# WaterSource
# TODO: I CANNOT GET autosizeReferenceCapacity to work in E+: see https://github.com/NREL/EnergyPlus/issues/8948
# Yet it is still reported... so whatever
plhp_clg = OpenStudio::Model::HeatPumpPlantLoopEIRCooling.new(model)
plhp_clg.setReferenceCapacity(400000)
# plhp_clg.autosizeReferenceCapacity
plhp_clg.autosizeSourceSideReferenceFlowRate
plhp_clg.autosizeLoadSideReferenceFlowRate
# plhp_clg.autosizeHeatRecoveryReferenceFlowRate
plhp_clg.setSizingFactor(1)
chw_loop.addSupplyBranchForComponent(plhp_clg)
# The Source Side Volume Flow Rate is reported only for WaterSource apparently
cw_loop.addDemandBranchForComponent(plhp_clg)

# AirSource w/ Heat Recovery
plhp_airsource_clg_hr = OpenStudio::Model::HeatPumpPlantLoopEIRCooling.new(model)
plhp_airsource_clg_hr.setReferenceCapacity(400000)
plhp_airsource_clg_hr.autosizeSourceSideReferenceFlowRate
plhp_airsource_clg_hr.autosizeLoadSideReferenceFlowRate
plhp_airsource_clg_hr.autosizeHeatRecoveryReferenceFlowRate
plhp_airsource_clg_hr.setSizingFactor(1)
chw_loop.addSupplyBranchForComponent(plhp_airsource_clg_hr)

ffhp_airsource_clg = OpenStudio::Model::HeatPumpAirToWaterFuelFiredCooling.new(model)
ffhp_airsource_clg.autosizeNominalCoolingCapacity
ffhp_airsource_clg.autosizeDesignFlowRate
ffhp_airsource_clg.autosizeDesignTemperatureLift
ffhp_airsource_clg.setNominalAuxiliaryElectricPower(500)
chw_loop.addSupplyBranchForComponent(ffhp_airsource_clg)

# chw_loop.addSupplyBranchForComponent(OpenStudio::Model::ChillerHeaterPerformanceElectricEIR.new(model))

### Hot water loop ###
hw_loop.setName('Hot Water Loop')
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

# Heating equipment
hw_loop.addSupplyBranchForComponent(OpenStudio::Model::BoilerHotWater.new(model))
hw_loop.addSupplyBranchForComponent(OpenStudio::Model::DistrictHeating.new(model))
hw_loop.addSupplyBranchForComponent(OpenStudio::Model::WaterHeaterMixed.new(model))
wh_strat = OpenStudio::Model::WaterHeaterStratified.new(model)
wh_strat.setTankVolume(1.89) # 500 gal
hw_loop.addSupplyBranchForComponent(wh_strat)
hp_wh = OpenStudio::Model::WaterHeaterHeatPump.new(model)
hw_loop.addSupplyBranchForComponent(hp_wh.tank)
wwhp = OpenStudio::Model::HeatPumpWaterToWaterEquationFitHeating.new(model)
hw_loop.addSupplyBranchForComponent(wwhp)
cw_loop.addDemandBranchForComponent(wwhp)
hx = OpenStudio::Model::HeatExchangerFluidToFluid.new(model)
hw_loop.addSupplyBranchForComponent(hx)
cw_loop.addDemandBranchForComponent(hx)

# WaterSource
# TODO: I CANNOT GET autosizeReferenceCapacity to work in E+: see https://github.com/NREL/EnergyPlus/issues/8948
plhp_htg = OpenStudio::Model::HeatPumpPlantLoopEIRHeating.new(model)
plhp_htg.setReferenceCapacity(80000)
# plhp_htg.autosizeReferenceCapacity()
plhp_htg.autosizeSourceSideReferenceFlowRate
plhp_htg.autosizeLoadSideReferenceFlowRate
# plhp_htg.autosizeHeatRecoveryReferenceFlowRate
plhp_htg.setSizingFactor(1.0)
hw_loop.addSupplyBranchForComponent(plhp_htg)
# The Source Side Volume Flow Rate is reported only for WaterSource apparently
cw_loop.addDemandBranchForComponent(plhp_htg)

# AirSource w/ Heat Recovery
plhp_airsource_htg_hr = OpenStudio::Model::HeatPumpPlantLoopEIRHeating.new(model)
plhp_airsource_htg_hr.setReferenceCapacity(80000)
plhp_airsource_htg_hr.autosizeSourceSideReferenceFlowRate
plhp_airsource_htg_hr.autosizeLoadSideReferenceFlowRate
plhp_airsource_htg_hr.autosizeHeatRecoveryReferenceFlowRate
plhp_airsource_htg_hr.setSizingFactor(1.0)
hw_loop.addSupplyBranchForComponent(plhp_airsource_htg_hr)

# WaterSource
plhp_clg.setCompanionHeatingHeatPump(plhp_htg)
plhp_htg.setCompanionCoolingHeatPump(plhp_clg)

# AirSource w/ Heat Recovery
plhp_airsource_clg_hr.setCompanionHeatingHeatPump(plhp_airsource_htg_hr)
plhp_airsource_htg_hr.setCompanionCoolingHeatPump(plhp_airsource_clg_hr)
# If not passing tertiary=true here, this would connect the Source Water Side
# and swich the HP to a WaterSource one
tertiary = true
chw_loop.addDemandBranchForComponent(plhp_airsource_htg_hr, tertiary)
hw_loop.addDemandBranchForComponent(plhp_airsource_clg_hr, tertiary)

ffhp_airsource_htg = OpenStudio::Model::HeatPumpAirToWaterFuelFiredHeating.new(model)
ffhp_airsource_htg.autosizeNominalHeatingCapacity
ffhp_airsource_htg.autosizeDesignFlowRate
ffhp_airsource_htg.autosizeDesignTemperatureLift
ffhp_airsource_htg.setNominalAuxiliaryElectricPower(500)
hw_loop.addSupplyBranchForComponent(ffhp_airsource_htg)

ffhp_airsource_clg.setCompanionHeatingHeatPump(ffhp_airsource_htg)
ffhp_airsource_htg.setCompanionCoolingHeatPump(ffhp_airsource_clg)

# This is an Uncontrolled component, should be last
hw_loop.addSupplyBranchForComponent(OpenStudio::Model::PlantComponentTemperatureSource.new(model))
# hw_loop.addSupplyBranchForComponent(OpenStudio::Model::SolarCollectorFlatPlatePhotovoltaicThermal.new(model))
# hw_loop.addSupplyBranchForComponent(OpenStudio::Model::CoilWaterHeatingAirToWaterHeatPump.new(model))

### Air loop ###
air_loop = OpenStudio::Model::AirLoopHVAC.new(model)
air_loop.setName('Air Loop')
air_loop_sizing = air_loop.sizingSystem
air_loop_sizing.autosizeDesignOutdoorAirFlowRate
air_loop_sizing.setAllOutdoorAirinCooling(false)
air_loop_sizing.setAllOutdoorAirinHeating(false)
out_1 = air_loop.supplyOutletNode
in_1 = air_loop.supplyInletNode
sat_f = 55
sat_c = OpenStudio.convert(sat_f, 'F', 'C').get
sat_sch = OpenStudio::Model::ScheduleRuleset.new(model)
sat_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), sat_c)
sat_stpt_manager = OpenStudio::Model::SetpointManagerScheduled.new(model, sat_sch)
sat_stpt_manager.addToNode(out_1)
fan = OpenStudio::Model::FanComponentModel.new(model)
fan.addToNode(in_1)
oa_controller = OpenStudio::Model::ControllerOutdoorAir.new(model)
oa_controller.autosizeMinimumOutdoorAirFlowRate # OS has a bad default of zero, which disables autosizing
oa_system = OpenStudio::Model::AirLoopHVACOutdoorAirSystem.new(model, oa_controller)
oa_system.addToNode(in_1)

# OA equipment
erv = OpenStudio::Model::HeatExchangerAirToAirSensibleAndLatent.new(model)
if Gem::Version.new(OpenStudio.openStudioVersion) >= Gem::Version.new('3.8.0')
  erv.assignHistoricalEffectivenessCurves
end
erv.addToNode(oa_system.outboardOANode.get)
spm_oa_pretreat = OpenStudio::Model::SetpointManagerOutdoorAirPretreat.new(model)
spm_oa_pretreat.setMinimumSetpointTemperature(-99.0)
spm_oa_pretreat.setMaximumSetpointTemperature(99.0)
spm_oa_pretreat.setMinimumSetpointHumidityRatio(0.00001)
spm_oa_pretreat.setMaximumSetpointHumidityRatio(1.0)
mixed_air_node = oa_system.mixedAirModelObject.get.to_Node.get
spm_oa_pretreat.setReferenceSetpointNode(mixed_air_node)
spm_oa_pretreat.setMixedAirStreamNode(mixed_air_node)
spm_oa_pretreat.setOutdoorAirStreamNode(oa_system.outboardOANode.get)
return_air_node = oa_system.returnAirModelObject.get.to_Node.get
spm_oa_pretreat.setReturnAirStreamNode(return_air_node)
erv_outlet = erv.primaryAirOutletModelObject.get.to_Node.get
spm_oa_pretreat.addToNode(erv_outlet)

# Cooling coils
clg_coil = OpenStudio::Model::CoilCoolingWater.new(model)
clg_coil.addToNode(out_1)
chw_loop.addDemandBranchForComponent(clg_coil)
clg_coil = new_evap_cooling_coil_dx_singlespeed(model)
clg_coil.addToNode(out_1)
clg_coil = new_evap_cooling_coil_dx_twospeed(model)
clg_coil.addToNode(out_1)
evap_clr = OpenStudio::Model::EvaporativeCoolerDirectResearchSpecial.new(model, s1)
evap_clr.autosizeRecirculatingWaterPumpPowerConsumption
evap_clr.addToNode(out_1)
evap_clr = OpenStudio::Model::EvaporativeCoolerIndirectResearchSpecial.new(model)
evap_clr.autosizeRecirculatingWaterPumpPowerConsumption
evap_clr.addToNode(out_1)

# Heating coils
htg_coil = OpenStudio::Model::CoilHeatingWater.new(model)
htg_coil.addToNode(out_1)
hw_loop.addDemandBranchForComponent(htg_coil)
OpenStudio::Model::CoilHeatingElectric.new(model).addToNode(out_1)
OpenStudio::Model::CoilHeatingGas.new(model).addToNode(out_1)
htg_coil = OpenStudio::Model::CoilHeatingDXVariableSpeed.new(model)
coil_data = OpenStudio::Model::CoilHeatingDXVariableSpeedSpeedData.new(model)
htg_coil.addSpeed(coil_data)
htg_coil.addToNode(out_1)

### Dual Duct Air loop ###
air_loop_dual_duct = OpenStudio::Model::AirLoopHVAC.new(model, true)
air_loop_dual_duct.setName('Dual Duct Air Loop')

fan = OpenStudio::Model::FanVariableVolume.new(model)
fan.addToNode(air_loop_dual_duct.supplyInletNode)
oa_controller = OpenStudio::Model::ControllerOutdoorAir.new(model)
oa_system = OpenStudio::Model::AirLoopHVACOutdoorAirSystem.new(model, oa_controller)
oa_system.addToNode(air_loop_dual_duct.supplyInletNode)

supply_outlet_nodes = air_loop_dual_duct.supplyOutletNodes
heating_coil = OpenStudio::Model::CoilHeatingGas.new(model)
heating_coil.addToNode(supply_outlet_nodes[0])
heating_sch = OpenStudio::Model::ScheduleRuleset.new(model)
heating_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 45.0)
heating_spm = OpenStudio::Model::SetpointManagerScheduled.new(model, heating_sch)
heating_spm.addToNode(supply_outlet_nodes[0])
cooling_coil = new_evap_cooling_coil_dx_twospeed(model)
cooling_coil.addToNode(supply_outlet_nodes[1])
cooling_sch = OpenStudio::Model::ScheduleRuleset.new(model)
cooling_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 12.8)
cooling_spm = OpenStudio::Model::SetpointManagerScheduled.new(model, cooling_sch)
cooling_spm.addToNode(supply_outlet_nodes[1])

### Unitary airloops ###

# UnitaryHeatPumpAirToAirMultiSpeed
unitary_loop = OpenStudio::Model::AirLoopHVAC.new(model)
unitary_loop.setName('UnitaryHeatPumpAirToAirMultiSpeed Loop')
fan = OpenStudio::Model::FanConstantVolume.new(model, s1)
htg_coil = OpenStudio::Model::CoilHeatingDXMultiSpeed.new(model)
htg_stage_1 = OpenStudio::Model::CoilHeatingDXMultiSpeedStageData.new(model)
htg_stage_2 = OpenStudio::Model::CoilHeatingDXMultiSpeedStageData.new(model)
htg_stage_3 = OpenStudio::Model::CoilHeatingDXMultiSpeedStageData.new(model)
htg_stage_4 = OpenStudio::Model::CoilHeatingDXMultiSpeedStageData.new(model)
htg_coil.addStage(htg_stage_1)
htg_coil.addStage(htg_stage_2)
htg_coil.addStage(htg_stage_3)
htg_coil.addStage(htg_stage_4)
clg_coil = OpenStudio::Model::CoilCoolingDXMultiSpeed.new(model)
clg_stage_1 = OpenStudio::Model::CoilCoolingDXMultiSpeedStageData.new(model)
clg_stage_2 = OpenStudio::Model::CoilCoolingDXMultiSpeedStageData.new(model)
clg_stage_3 = OpenStudio::Model::CoilCoolingDXMultiSpeedStageData.new(model)
clg_stage_4 = OpenStudio::Model::CoilCoolingDXMultiSpeedStageData.new(model)
clg_coil.addStage(clg_stage_1)
clg_coil.addStage(clg_stage_2)
clg_coil.addStage(clg_stage_3)
clg_coil.addStage(clg_stage_4)
sup_htg_coil = OpenStudio::Model::CoilHeatingElectric.new(model, s1)
unitary = OpenStudio::Model::AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed.new(model, fan, htg_coil, clg_coil, sup_htg_coil)
unitary.setNumberofSpeedsforHeating(4)
unitary.setNumberofSpeedsforCooling(4)
unitary.addToNode(unitary_loop.supplyOutletNode)
unitary.setControllingZoneorThermostatLocation(zones[26])
term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, s1)
unitary_loop.addBranchForZone(zones[26], term)

# UnitaryHeatCoolVAVChangeoverBypass
unitary_loop = OpenStudio::Model::AirLoopHVAC.new(model)
unitary_loop.setName('UnitaryHeatCoolVAVChangeoverBypass Loop')
fan = OpenStudio::Model::FanConstantVolume.new(model, s1)
clg_coil = new_evap_cooling_coil_dx_singlespeed(model)
htg_coil = OpenStudio::Model::CoilHeatingGas.new(model, s1)
unitary = OpenStudio::Model::AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass.new(model, fan, clg_coil, htg_coil)
unitary.addToNode(unitary_loop.supplyOutletNode)
# Reheat terminal
reheat_coil = OpenStudio::Model::CoilHeatingWater.new(model)
hw_loop.addDemandBranchForComponent(reheat_coil)
term = OpenStudio::Model::AirTerminalSingleDuctVAVHeatAndCoolReheat.new(model, reheat_coil)
unitary_loop.addBranchForZone(zones[28], term)
# No reheat terminal
term = OpenStudio::Model::AirTerminalSingleDuctVAVHeatAndCoolNoReheat.new(model)
unitary_loop.addBranchForZone(zones[29], term)

# UnitaryHeatPumpAirToAir
unitary_loop = OpenStudio::Model::AirLoopHVAC.new(model)
unitary_loop.setName('UnitaryHeatPumpAirToAir Loop')
fan = OpenStudio::Model::FanOnOff.new(model, s1)
clg_coil = new_evap_cooling_coil_dx_singlespeed(model)
htg_coil = OpenStudio::Model::CoilHeatingDXSingleSpeed.new(model)
sup_htg_coil = OpenStudio::Model::CoilHeatingElectric.new(model, s1)
unitary = OpenStudio::Model::AirLoopHVACUnitaryHeatPumpAirToAir.new(model, s1, fan, htg_coil, clg_coil, sup_htg_coil)
unitary.addToNode(unitary_loop.supplyOutletNode)
unitary.setControllingZone(zones[31])
term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, s1)
unitary_loop.addBranchForZone(zones[31], term)

# UnitarySystem with variable speed heat pumps
unitary_loop = OpenStudio::Model::AirLoopHVAC.new(model)
unitary_loop.setName('UnitarySystem Var Spd HP Loop')
fan = OpenStudio::Model::FanConstantVolume.new(model, s1)
clg_coil = OpenStudio::Model::CoilCoolingWaterToAirHeatPumpVariableSpeedEquationFit.new(model)
cw_loop.addDemandBranchForComponent(clg_coil)
speed_data = OpenStudio::Model::CoilCoolingWaterToAirHeatPumpVariableSpeedEquationFitSpeedData.new(model)
clg_coil.addSpeed(speed_data)
htg_coil = OpenStudio::Model::CoilHeatingWaterToAirHeatPumpVariableSpeedEquationFit.new(model)
cw_loop.addDemandBranchForComponent(htg_coil)
speed_data = OpenStudio::Model::CoilHeatingWaterToAirHeatPumpVariableSpeedEquationFitSpeedData.new(model)
htg_coil.addSpeed(speed_data)
unitary = OpenStudio::Model::AirLoopHVACUnitarySystem.new(model)
unitary.setFanPlacement('BlowThrough')
unitary.setSupplyAirFanOperatingModeSchedule(s1)
unitary.setSupplyFan(fan)
unitary.setCoolingCoil(clg_coil)
unitary.setHeatingCoil(htg_coil)
unitary.addToNode(unitary_loop.supplyOutletNode)
unitary.setControllingZoneorThermostatLocation(zones[27])
# Necessary for autosizedDOASDXCoolingCoilLeavingMinimumAirTemperature
unitary.setControlType('SingleZoneVAV')
# E+ 9.5.0-IOFreeze crashes when this is blank. https://github.com/NREL/EnergyPlus/issues/8566
unitary.setSupplyAirFlowRateMethodDuringCoolingOperation('SupplyAirFlowRate')
unitary.setSupplyAirFlowRateMethodDuringHeatingOperation('SupplyAirFlowRate')
unitary.setSupplyAirFlowRateMethodWhenNoCoolingorHeatingisRequired('SupplyAirFlowRate')
unitary.autosizeDOASDXCoolingCoilLeavingMinimumAirTemperature

term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, s1)
unitary_loop.addBranchForZone(zones[27], term)

# UnitarySystem with multi stage gas coils
unitary_loop = OpenStudio::Model::AirLoopHVAC.new(model)
unitary_loop.setName('UnitarySystem Multi Stage Gas Htg Loop')
fan = OpenStudio::Model::FanConstantVolume.new(model, s1)
clg_coil = OpenStudio::Model::CoilCoolingWater.new(model)
chw_loop.addDemandBranchForComponent(clg_coil)
htg_coil = OpenStudio::Model::CoilHeatingGasMultiStage.new(model)
heat_stage_1 = OpenStudio::Model::CoilHeatingGasMultiStageStageData.new(model)
heat_stage_2 = OpenStudio::Model::CoilHeatingGasMultiStageStageData.new(model)
htg_coil.addStage(heat_stage_1)
htg_coil.addStage(heat_stage_2)
supp_htg_coil = OpenStudio::Model::CoilHeatingElectricMultiStage.new(model)
supp_heat_stage_1 = OpenStudio::Model::CoilHeatingElectricMultiStageStageData.new(model)
supp_heat_stage_2 = OpenStudio::Model::CoilHeatingElectricMultiStageStageData.new(model)
supp_htg_coil.addStage(supp_heat_stage_1)
supp_htg_coil.addStage(supp_heat_stage_2)
unitary = OpenStudio::Model::AirLoopHVACUnitarySystem.new(model)
unitary.setFanPlacement('BlowThrough')
unitary.setSupplyAirFanOperatingModeSchedule(s1)
unitary.setSupplyFan(fan)
unitary.setCoolingCoil(clg_coil)
unitary.setHeatingCoil(htg_coil)
unitary.setSupplementalHeatingCoil(supp_htg_coil)
unitary.addToNode(unitary_loop.supplyOutletNode)
unitary.setControllingZoneorThermostatLocation(zones[30])
# Necessary for autosizedDOASDXCoolingCoilLeavingMinimumAirTemperature
unitary.setControlType('SingleZoneVAV')
unitary.autosizeDOASDXCoolingCoilLeavingMinimumAirTemperature

term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, s1)
unitary_loop.addBranchForZone(zones[30], term)

# UnitarySystem with variable speed cooling coil
unitary_loop = OpenStudio::Model::AirLoopHVAC.new(model)
unitary_loop.setName('UnitarySystem Var Spd Clg Loop')
fan = OpenStudio::Model::FanSystemModel.new(model)
htg_coil = OpenStudio::Model::CoilHeatingElectric.new(model, s1)
htg_coil.setName("#{air_loop.name} Electric Htg Coil")
sup_htg_coil = OpenStudio::Model::CoilHeatingElectric.new(model, s1)
clg_coil = OpenStudio::Model::CoilCoolingDXVariableSpeed.new(model)
clg_coil.setCondenserType('EvaporativelyCooled')
# clg_coil.autosizeEvaporativeCondenserPumpRatedPowerConsumption
clg_coil.setEvaporativeCondenserPumpRatedPowerConsumption(10.0)
clg_spd_1 = OpenStudio::Model::CoilCoolingDXVariableSpeedSpeedData.new(model)
clg_coil.addSpeed(clg_spd_1)
clg_coil.setNominalSpeedLevel(1)
unitary = OpenStudio::Model::AirLoopHVACUnitarySystem.new(model)
unitary.setSupplyFan(fan)
unitary.setHeatingCoil(htg_coil)
unitary.setCoolingCoil(clg_coil)
unitary.setSupplementalHeatingCoil(sup_htg_coil)
unitary.setMaximumSupplyAirTemperature(50)
unitary.setFanPlacement('BlowThrough')
unitary.setSupplyAirFlowRateMethodDuringCoolingOperation('SupplyAirFlowRate')
unitary.setSupplyAirFlowRateMethodDuringHeatingOperation('SupplyAirFlowRate')
unitary.setSupplyAirFlowRateMethodWhenNoCoolingorHeatingisRequired('SupplyAirFlowRate')
unitary.setSupplyAirFanOperatingModeSchedule(s1)
unitary.addToNode(unitary_loop.supplyInletNode)
unitary.setControllingZoneorThermostatLocation(zones[32])
# Necessary for autosizedDOASDXCoolingCoilLeavingMinimumAirTemperature
unitary.setControlType('SingleZoneVAV')
unitary.autosizeDOASDXCoolingCoilLeavingMinimumAirTemperature

term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, s1)
unitary_loop.addBranchForZone(zones[32], term)

# UnitarySystem with two stage DX with humidity control
unitary_loop = OpenStudio::Model::AirLoopHVAC.new(model)
unitary_loop.setName('UnitarySystem 2Spd DX Humidity Ctrl Loop')
fan = OpenStudio::Model::FanConstantVolume.new(model, s1)
clg_coil = OpenStudio::Model::CoilCoolingDXTwoStageWithHumidityControlMode.new(model)
stage_1 = clg_coil.normalModeStage1CoilPerformance
if stage_1.is_initialized
  stage_1.get.setCondenserType('EvaporativelyCooled')

end
stage_2 = clg_coil.normalModeStage1Plus2CoilPerformance
if stage_2.is_initialized
  stage_2.get.setCondenserType('EvaporativelyCooled')
end
# clg_coil
htg_coil = OpenStudio::Model::CoilHeatingDXMultiSpeed.new(model)
heat_stage_1 = OpenStudio::Model::CoilHeatingDXMultiSpeedStageData.new(model)
heat_stage_2 = OpenStudio::Model::CoilHeatingDXMultiSpeedStageData.new(model)
htg_coil.addStage(heat_stage_1)
htg_coil.addStage(heat_stage_2)
unitary = OpenStudio::Model::AirLoopHVACUnitarySystem.new(model)
unitary.setFanPlacement('BlowThrough')
unitary.setSupplyAirFanOperatingModeSchedule(s1)
unitary.setSupplyFan(fan)
unitary.setCoolingCoil(clg_coil)
unitary.setHeatingCoil(htg_coil)
unitary.addToNode(unitary_loop.supplyInletNode)
unitary.setControllingZoneorThermostatLocation(zones[33])
term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, s1)
unitary_loop.addBranchForZone(zones[33], term)

dehumidify_sch = OpenStudio::Model::ScheduleConstant.new(model)
dehumidify_sch.setValue(50)
humidistat = OpenStudio::Model::ZoneControlHumidistat.new(model)
humidistat.setHumidifyingRelativeHumiditySetpointSchedule(dehumidify_sch)
zones[33].setZoneControlHumidistat(humidistat)
humidifier = OpenStudio::Model::HumidifierSteamElectric.new(model)
humidifier.addToNode(unitary_loop.supplyOutletNode)
humidifier_steam = OpenStudio::Model::HumidifierSteamGas.new(model)
humidifier_steam.addToNode(unitary_loop.supplyOutletNode)
spm = OpenStudio::Model::SetpointManagerSingleZoneHumidityMinimum.new(model)
spm.addToNode(unitary_loop.supplyOutletNode)
spm2 = spm.clone.to_SetpointManagerSingleZoneHumidityMinimum.get
spm2.addToNode(humidifier.outletModelObject.get.to_Node.get)

# Create an  internal source construction for the radiant systems
int_src_const = OpenStudio::Model::ConstructionWithInternalSource.new(model)
int_src_const.setSourcePresentAfterLayerNumber(3)
int_src_const.setTemperatureCalculationRequestedAfterLayerNumber(3)
layers = []
layers << concrete_sand_gravel = OpenStudio::Model::StandardOpaqueMaterial.new(model, 'MediumRough', 0.1014984, 1.729577, 2242.585, 836.8)
layers << rigid_insulation_2inch = OpenStudio::Model::StandardOpaqueMaterial.new(model, 'Rough', 0.05, 0.02, 56.06, 1210)
layers << gyp1 = OpenStudio::Model::StandardOpaqueMaterial.new(model, 'MediumRough', 0.0127, 0.7845, 1842.1221, 988)
layers << gyp2 = OpenStudio::Model::StandardOpaqueMaterial.new(model, 'MediumRough', 0.01905, 0.7845, 1842.1221, 988)
layers << finished_floor = OpenStudio::Model::StandardOpaqueMaterial.new(model, 'Smooth', 0.0016, 0.17, 1922.21, 1250)
int_src_const.setLayers(layers)

# UnitarySystem with CoilCoolingDX
unitary_loop = OpenStudio::Model::AirLoopHVAC.new(model)
unitary_loop.setName('UnitarySystem CoilCoolingDX Loop')
fan = OpenStudio::Model::FanVariableVolume.new(model, s1)

speed_1 = OpenStudio::Model::CoilCoolingDXCurveFitSpeed.new(model)
speed_1.setGrossTotalCoolingCapacityFraction(1.0)
speed_1.setGrossSensibleHeatRatio(0.842150793933333)
speed_1.setGrossCoolingCOP(5.48021287249984)

constant_biquadratic = curve_biquadratic(model, 1, 0, 0, 0, 0, 0, -100, 100, -100, 100)
cool_cap_ft = curve_biquadratic(model, 1.790226088881, -0.0772146982404, 0.00299548780452, 0.0026270330994, -6.81238188e-005, -0.00062105857056, 13.88, 23.88, 18.33, 51.66)
cool_cap_fff = curve_quadratic(model, 1, 0, 0, 0, 2, 0, 2)
cool_eir_ft = curve_biquadratic(model, -0.1450569952, 0.062239559472, -0.00190953288, -0.012608055432, 0.0010591834752, -0.0003311985672, 13.88, 23.88, 18.33, 51.66)
cool_eir_fff = curve_quadratic(model, 1, 0, 0, 0, 2, 0, 2)
cool_plf_fplr = curve_quadratic(model, 0.75, 0.25, 0, 0, 1, 0.7, 1)

speed_1.setTotalCoolingCapacityModifierFunctionofTemperatureCurve(cool_cap_ft)
speed_1.setTotalCoolingCapacityModifierFunctionofAirFlowFractionCurve(cool_cap_fff)
speed_1.setEnergyInputRatioModifierFunctionofTemperatureCurve(cool_eir_ft)
speed_1.setEnergyInputRatioModifierFunctionofAirFlowFractionCurve(cool_eir_fff)
speed_1.setPartLoadFractionCorrelationCurve(cool_plf_fplr)
speed_1.setWasteHeatModifierFunctionofTemperatureCurve(constant_biquadratic)

operating_mode = OpenStudio::Model::CoilCoolingDXCurveFitOperatingMode.new(model)
operating_mode.addSpeed(speed_1)
# Nominal Evaporative Condenser Pump Power is not autosized - because it is
# unused - if it's AirCooled (default); so set it to evap cooled
operating_mode.setCondenserType('EvaporativelyCooled')
operating_mode.autosizeRatedGrossTotalCoolingCapacity
operating_mode.autosizeRatedEvaporatorAirFlowRate
operating_mode.autosizeRatedCondenserAirFlowRate
operating_mode.autosizeNominalEvaporativeCondenserPumpPower

performance = OpenStudio::Model::CoilCoolingDXCurveFitPerformance.new(model, operating_mode)
clg_coil = OpenStudio::Model::CoilCoolingDX.new(model, performance)

htg_coil = OpenStudio::Model::CoilHeatingDXSingleSpeed.new(model)

unitary = OpenStudio::Model::AirLoopHVACUnitarySystem.new(model)
unitary_loop.setName('UnitarySystem CoilCoolingDX')
unitary.setFanPlacement('BlowThrough')
unitary.setSupplyAirFanOperatingModeSchedule(s1)
unitary.setSupplyFan(fan)
unitary.setCoolingCoil(clg_coil)
unitary.setHeatingCoil(htg_coil)
unitary.addToNode(unitary_loop.supplyInletNode)
unitary.setControllingZoneorThermostatLocation(zones[38])
term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, s1)
unitary_loop.addBranchForZone(zones[38], term)

# HeatExchangerDesiccantBalancedFlowPerformanceDataType1
hx_dessicant_loop = OpenStudio::Model::AirLoopHVAC.new(model)
hx_dessicant_loop.setName('HeatExchangerDesiccantBalancedFlow Loop')

hx = OpenStudio::Model::HeatExchangerDesiccantBalancedFlow.new(model)
hxPerfDataType1 = hx.heatExchangerPerformance
hxPerfDataType1.autosizeNominalAirFlowRate
hxPerfDataType1.autosizeNominalAirFaceVelocity
# This object is problematic, try to relax the min/max boundaries...

# Instead of 21.83
hxPerfDataType1.setMaximumProcessInletAirTemperatureforTemperatureEquation(30.0)
hxPerfDataType1.setMaximumProcessInletAirTemperatureforHumidityRatioEquation(30.0)

# Instead of 2.286
hxPerfDataType1.setMinimumRegenerationAirVelocityforTemperatureEquation(1.0)
hxPerfDataType1.setMinimumRegenerationAirVelocityforHumidityRatioEquation(1.0)

# Instead of 80.0
hxPerfDataType1.setMinimumProcessInletAirRelativeHumidityforTemperatureEquation(35.0)
hxPerfDataType1.setMinimumProcessInletAirRelativeHumidityforHumidityRatioEquation(35.0)

# Add the HX on the Outdoor Air System
oa_controller = OpenStudio::Model::ControllerOutdoorAir.new(model)
oa_controller.autosizeMinimumOutdoorAirFlowRate # OS has a bad default of zero, which disables autosizing
oa_system = OpenStudio::Model::AirLoopHVACOutdoorAirSystem.new(model, oa_controller)
oa_system.addToNode(hx_dessicant_loop.supplyOutletNode)
hx.addToNode(oa_system.outboardOANode.get)

spm_oa_pretreat = OpenStudio::Model::SetpointManagerOutdoorAirPretreat.new(model)
spm_oa_pretreat.setMinimumSetpointTemperature(-99.0)
spm_oa_pretreat.setMaximumSetpointTemperature(99.0)
spm_oa_pretreat.setMinimumSetpointHumidityRatio(0.00001)
spm_oa_pretreat.setMaximumSetpointHumidityRatio(1.0)
mixed_air_node = oa_system.mixedAirModelObject.get.to_Node.get
spm_oa_pretreat.setReferenceSetpointNode(mixed_air_node)
spm_oa_pretreat.setMixedAirStreamNode(mixed_air_node)
spm_oa_pretreat.setOutdoorAirStreamNode(oa_system.outboardOANode.get)
return_air_node = oa_system.returnAirModelObject.get.to_Node.get
spm_oa_pretreat.setReturnAirStreamNode(return_air_node)
hx_outlet = hx.primaryAirOutletModelObject.get.to_Node.get
spm_oa_pretreat.addToNode(hx_outlet)

# Heating -> Cooling -> Fan
htg_coil = OpenStudio::Model::CoilHeatingElectric.new(model)
htg_coil.addToNode(hx_dessicant_loop.supplyOutletNode)
clg_coil = OpenStudio::Model::CoilCoolingDXSingleSpeed.new(model)
clg_coil.addToNode(hx_dessicant_loop.supplyOutletNode)
fan = OpenStudio::Model::FanVariableVolume.new(model)
fan.addToNode(hx_dessicant_loop.supplyOutletNode)
sat_stpt_manager = sat_stpt_manager.clone(model).to_SetpointManagerScheduled.get
sat_stpt_manager.addToNode(hx_dessicant_loop.supplyOutletNode)

term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, s1)
hx_dessicant_loop.addBranchForZone(zones[40], term)

spm_max_hum = OpenStudio::Model::SetpointManagerSingleZoneHumidityMaximum.new(model)
spm_max_hum.setControlZone(zones[40])
spm_max_hum.addToNode(hx_outlet)
dehumidify_sch = OpenStudio::Model::ScheduleConstant.new(model)
dehumidify_sch.setValue(45)
humidistat = OpenStudio::Model::ZoneControlHumidistat.new(model)
humidistat.setHumidifyingRelativeHumiditySetpointSchedule(dehumidify_sch)
zones[40].setZoneControlHumidistat(humidistat)

# TES Coil CoilCoolingDXSingleSpeedThermalStorage
tes_air_loop_unitary = OpenStudio::Model::AirLoopHVACUnitarySystem.new(model)
tes_coil = make_tes_coil(model)
fan = OpenStudio::Model::FanOnOff.new(model)
tes_air_loop_unitary.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule)
tes_air_loop_unitary.setCoolingCoil(tes_coil)
tes_air_loop_unitary.setSupplyFan(fan)
tes_air_loop = OpenStudio::Model::AirLoopHVAC.new(model)
tes_air_loop_unitary.addToNode(tes_air_loop.supplyInletNode)
tes_air_loop_unitary.setControllingZoneorThermostatLocation(zones[43])
tes_atu = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, s1)
tes_air_loop.addBranchForZone(zones[43], tes_atu)
tes_air_loop.setName('AirLoop with TES Coil')

### Zone HVAC and Terminals ###
# Add one of every single kind of Zone HVAC equipment supported by OS
zones.each_with_index do |zn, zone_index|
  # puts "Adding stuff to #{zn.name}, index #{zone_index}"
  case zone_index
  when 1
    OpenStudio::Model::ZoneHVACBaseboardConvectiveElectric.new(model).addToThermalZone(zn)
  when 2
    ideal = OpenStudio::Model::ZoneHVACIdealLoadsAirSystem.new(model)
    ideal.autosizeMaximumHeatingAirFlowRate
    ideal.autosizeMaximumSensibleHeatingCapacity
    ideal.setHeatingLimit('NoLimit')
    ideal.autosizeMaximumCoolingAirFlowRate
    ideal.autosizeMaximumTotalCoolingCapacity
    ideal.setCoolingLimit('NoLimit')
    ideal.addToThermalZone(zn)
  when 3

  when 4
    hightempradiant = OpenStudio::Model::ZoneHVACHighTemperatureRadiant.new(model)
    radiant_heating_schedule = OpenStudio::Model::ScheduleConstant.new(model)
    radiant_heating_schedule.setValue(24.0)
    hightempradiant.setHeatingSetpointTemperatureSchedule(radiant_heating_schedule)
    hightempradiant.addToThermalZone(zn)
  when 5
    fan = OpenStudio::Model::FanOnOff.new(model, s1)
    fan.setName('ZoneHVACPackagedTerminalHeatPump Fan On Off')
    htg_coil = OpenStudio::Model::CoilHeatingDXSingleSpeed.new(model)
    clg_coil = new_evap_cooling_coil_dx_singlespeed(model)
    sup_htg_coil = OpenStudio::Model::CoilHeatingElectric.new(model, s1)
    OpenStudio::Model::ZoneHVACPackagedTerminalHeatPump.new(model, s1, fan, htg_coil, clg_coil, sup_htg_coil).addToThermalZone(zn)
  when 6
    fan = OpenStudio::Model::FanConstantVolume.new(model, s1)
    htg_coil = OpenStudio::Model::CoilHeatingGas.new(model, s1)
    clg_coil = new_evap_cooling_coil_dx_singlespeed(model)
    ptac = OpenStudio::Model::ZoneHVACPackagedTerminalAirConditioner.new(model, s1, fan, htg_coil, clg_coil)
    ptac.setSupplyAirFanOperatingModeSchedule(s1)
    ptac.addToThermalZone(zn)
  when 7
    vrf = OpenStudio::Model::AirConditionerVariableRefrigerantFlow.new(model)
    vrf.autosizeResistiveDefrostHeaterCapacity
    # E+ now throws when the CoolingEIRLowPLR has a curve minimum value of x which
    # is higher than the Minimum Heat Pump Part-Load Ratio.
    # The curve has a min of 0.5 here, so set the MinimumHeatPumpPartLoadRatio to
    # the same value
    vrf.setMinimumHeatPumpPartLoadRatio(0.5)

    term = OpenStudio::Model::ZoneHVACTerminalUnitVariableRefrigerantFlow.new(model)
    # Add a supplemental heating coil since
    # 'Maximum Supply Air Temperature from Supplemental Heater' can be autosized
    suppl_hc = OpenStudio::Model::CoilHeatingElectric.new(model)
    term.setSupplementalHeatingCoil(suppl_hc)
    term.addToThermalZone(zn)
    vrf.addTerminal(term)
  when 8
    fan = OpenStudio::Model::FanOnOff.new(model, s1)
    fan.setName('ZoneHVACWaterToAirHeatPump Fan On Off')
    sup_htg_coil = OpenStudio::Model::CoilHeatingElectric.new(model, s1)
    htg_coil = OpenStudio::Model::CoilHeatingWaterToAirHeatPumpEquationFit.new(model)
    cw_loop.addDemandBranchForComponent(htg_coil)
    clg_coil = OpenStudio::Model::CoilCoolingWaterToAirHeatPumpEquationFit.new(model)
    cw_loop.addDemandBranchForComponent(clg_coil)
    OpenStudio::Model::ZoneHVACWaterToAirHeatPump.new(model, s1, fan, htg_coil, clg_coil, sup_htg_coil).addToThermalZone(zn)
  when 9
    fan = OpenStudio::Model::FanConstantVolume.new(model, s1)
    htg_coil = OpenStudio::Model::CoilHeatingWater.new(model)
    hw_loop.addDemandBranchForComponent(htg_coil)
    OpenStudio::Model::ZoneHVACUnitHeater.new(model, s1, fan, htg_coil).addToThermalZone(zn)
  when 10
    supply_fan = OpenStudio::Model::FanOnOff.new(model)
    supply_fan.setName('ZoneHVACEnergyRecoveryVentilator Supply Fan')
    exhaust_fan = OpenStudio::Model::FanOnOff.new(model)
    exhaust_fan.setName('ZoneHVACEnergyRecoveryVentilator Exhaust Fan')
    erv_controller = OpenStudio::Model::ZoneHVACEnergyRecoveryVentilatorController.new(model)
    heat_exchanger = OpenStudio::Model::HeatExchangerAirToAirSensibleAndLatent.new(model)
    zone_hvac = OpenStudio::Model::ZoneHVACEnergyRecoveryVentilator.new(model, heat_exchanger, supply_fan, exhaust_fan)
    zone_hvac.setVentilationRateperUnitFloorArea(0.001)
    zone_hvac.setController(erv_controller)
    zone_hvac.addToThermalZone(zn)
  when 11
    fan = OpenStudio::Model::FanOnOff.new(model)
    fan.setName('ZoneHVACEnergyRecoveryVentilator Fan')
    OpenStudio::Model::ZoneHVACUnitVentilator.new(model, fan).addToThermalZone(zn)
  when 12
    OpenStudio::Model::ZoneHVACBaseboardRadiantConvectiveElectric.new(model).addToThermalZone(zn)
  when 13
    obj = OpenStudio::Model::ZoneHVACBaseboardRadiantConvectiveWater.new(model)
    obj.addToThermalZone(zn)
    hw_loop.addDemandBranchForComponent(obj.heatingCoil)

    htg_coil = OpenStudio::Model::CoilHeatingWaterBaseboard.new(model)
    hw_loop.addDemandBranchForComponent(htg_coil)
    OpenStudio::Model::ZoneHVACBaseboardConvectiveWater.new(model, s1, htg_coil).addToThermalZone(zn)
  when 14
    # Make all floors in the spaces in this zone use the internal source construction
    zn.spaces.each do |space|
      space.surfaces.each do |s|
        s.setConstruction(int_src_const) if s.surfaceType == 'Floor'
      end
    end

    zn_temp_sch = OpenStudio::Model::ScheduleConstant.new(model)
    zn_temp_sch.setValue(OpenStudio.convert(65.0, 'F', 'C').get)
    low_temp_rad = OpenStudio::Model::ZoneHVACLowTemperatureRadiantElectric.new(model, s1, zn_temp_sch)
    low_temp_rad.setRadiantSurfaceType('Floors')
    low_temp_rad.addToThermalZone(zn)
  when 15
    # Make all floors in the spaces in this zone use the internal source construction
    zn.spaces.each do |space|
      space.surfaces.each do |s|
        s.setConstruction(int_src_const) if s.surfaceType == 'Floor'
      end
    end

    htg_temp_sch = OpenStudio::Model::ScheduleConstant.new(model)
    htg_temp_sch.setValue(10.0)
    clg_temp_sch = OpenStudio::Model::ScheduleConstant.new(model)
    clg_temp_sch.setValue(15.0)
    htg_coil = OpenStudio::Model::CoilHeatingLowTempRadiantVarFlow.new(model, htg_temp_sch)
    hw_loop.addDemandBranchForComponent(htg_coil)
    clg_coil = OpenStudio::Model::CoilCoolingLowTempRadiantVarFlow.new(model, clg_temp_sch)
    chw_loop.addDemandBranchForComponent(clg_coil)
    low_temp_rad = OpenStudio::Model::ZoneHVACLowTempRadiantVarFlow.new(model, s1, htg_coil, clg_coil)
    low_temp_rad.setRadiantSurfaceType('Floors')
    low_temp_rad.addToThermalZone(zn)

  when 16
    # hp_wh.addToThermalZone(zn)
  when 17
    rht_coil = OpenStudio::Model::CoilHeatingWater.new(model)
    hw_loop.addDemandBranchForComponent(rht_coil)
    term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeReheat.new(model, s1, rht_coil)
    air_loop.addBranchForZone(zn, term)
  when 18
    fan = OpenStudio::Model::FanConstantVolume.new(model, s1)
    rht_coil = OpenStudio::Model::CoilHeatingWater.new(model)
    hw_loop.addDemandBranchForComponent(rht_coil)
    term = OpenStudio::Model::AirTerminalSingleDuctSeriesPIUReheat.new(model, fan, rht_coil)
    air_loop.addBranchForZone(zn, term)
  when 19
    fan = OpenStudio::Model::FanConstantVolume.new(model, s1)
    rht_coil = OpenStudio::Model::CoilHeatingWater.new(model)
    hw_loop.addDemandBranchForComponent(rht_coil)
    term = OpenStudio::Model::AirTerminalSingleDuctParallelPIUReheat.new(model, s1, fan, rht_coil)
    air_loop.addBranchForZone(zn, term)
  when 20
    htg_coil = OpenStudio::Model::CoilHeatingWater.new(model)
    hw_loop.addDemandBranchForComponent(htg_coil)
    clg_coil = OpenStudio::Model::CoilCoolingWater.new(model)
    chw_loop.addDemandBranchForComponent(clg_coil)
    term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeFourPipeInduction.new(model, htg_coil)
    term.setCoolingCoil(clg_coil)
    air_loop.addBranchForZone(zn, term)
  when 21
    clg_coil = OpenStudio::Model::CoilCoolingCooledBeam.new(model)
    chw_loop.addDemandBranchForComponent(clg_coil)
    term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeCooledBeam.new(model, s1, clg_coil)
    air_loop.addBranchForZone(zn, term)
  when 22
    term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, s1)
    air_loop.addBranchForZone(zn, term)

    # Make this zone sizing account for DOAS
    # to check the Sizing:Zone autosizing methods
    zn.sizingZone.setAccountforDedicatedOutdoorAirSystem(true)

    fan = OpenStudio::Model::FanOnOff.new(model, s1)
    fan.setName('ZoneHVACFourPipeFanCoil Fan On Off')
    clg_coil = OpenStudio::Model::CoilCoolingWater.new(model, s1)
    chw_loop.addDemandBranchForComponent(clg_coil)
    htg_coil = OpenStudio::Model::CoilHeatingWater.new(model)
    hw_loop.addDemandBranchForComponent(htg_coil)
    OpenStudio::Model::ZoneHVACFourPipeFanCoil.new(model, s1, fan, clg_coil, htg_coil).addToThermalZone(zn)
  when 23
    term = OpenStudio::Model::AirTerminalSingleDuctVAVNoReheat.new(model, s1)
    air_loop.addBranchForZone(zn, term)
  when 24
    rht_coil = OpenStudio::Model::CoilHeatingWater.new(model)
    hw_loop.addDemandBranchForComponent(rht_coil)
    term = OpenStudio::Model::AirTerminalSingleDuctVAVReheat.new(model, s1, rht_coil)
    air_loop.addBranchForZone(zn, term)
  when 25
    term = OpenStudio::Model::AirTerminalDualDuctVAV.new(model)
    air_loop_dual_duct.addBranchForZone(zn, term)
  when 34
    term = OpenStudio::Model::AirTerminalDualDuctConstantVolume.new(model)
    air_loop_dual_duct.addBranchForZone(zn, term)
  when 35
    term = OpenStudio::Model::AirTerminalDualDuctVAVOutdoorAir.new(model)
    air_loop_dual_duct.addBranchForZone(zn, term)
  when 36
    # 2.5.2 and onwards
    clg_coil = OpenStudio::Model::CoilCoolingFourPipeBeam.new(model)
    chw_loop.addDemandBranchForComponent(clg_coil)

    htg_coil = OpenStudio::Model::CoilHeatingFourPipeBeam.new(model)
    hw_loop.addDemandBranchForComponent(htg_coil)

    term = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeFourPipeBeam.new(model, clg_coil, htg_coil)
    air_loop.addBranchForZone(zn, term)

  when 37
    # Make all floors in the spaces in this zone use the internal source construction
    zn.spaces.each do |space|
      space.surfaces.each do |s|
        s.setConstruction(int_src_const) if s.surfaceType == 'Floor'
      end
    end

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
    coolingHighControlTempSched.setValue(26.0)
    coolingLowControlTempSched.setValue(22.0)
    heatingHighWaterTempSched.setValue(50.0)
    heatingLowWaterTempSched.setValue(30.0)
    heatingHighControlTempSched.setValue(21.0)
    heatingLowControlTempSched.setValue(15.0)

    testCC = OpenStudio::Model::CoilCoolingLowTempRadiantConstFlow.new(model, coolingHighWaterTempSched, coolingLowWaterTempSched, coolingHighControlTempSched, coolingLowControlTempSched)
    testHC = OpenStudio::Model::CoilHeatingLowTempRadiantConstFlow.new(model, heatingHighWaterTempSched, heatingLowWaterTempSched, heatingHighControlTempSched, heatingLowControlTempSched)

    low_temp_cst_rad = OpenStudio::Model::ZoneHVACLowTempRadiantConstFlow.new(model, s1, testHC, testCC)
    low_temp_cst_rad.setRadiantSurfaceType('Floors')
    low_temp_cst_rad.addToThermalZone(zn)

  when 39
    zoneHVACCoolingPanelRadiantConvectiveWater = OpenStudio::Model::ZoneHVACCoolingPanelRadiantConvectiveWater.new(model)
    panel_coil = zoneHVACCoolingPanelRadiantConvectiveWater.coolingCoil.to_CoilCoolingWaterPanelRadiant.get

    chw_loop.addDemandBranchForComponent(panel_coil)
    zoneHVACCoolingPanelRadiantConvectiveWater.addToThermalZone(zn)

  when 41
    vrf = OpenStudio::Model::AirConditionerVariableRefrigerantFlowFluidTemperatureControl.new(model)
    vrf.autosizeRatedEvaporativeCapacity
    vrf.autosizeResistiveDefrostHeaterCapacity
    coolingCoil = OpenStudio::Model::CoilCoolingDXVariableRefrigerantFlowFluidTemperatureControl.new(model)
    heatingCoil = OpenStudio::Model::CoilHeatingDXVariableRefrigerantFlowFluidTemperatureControl.new(model)
    fan = OpenStudio::Model::FanVariableVolume.new(model)
    term = OpenStudio::Model::ZoneHVACTerminalUnitVariableRefrigerantFlow.new(model, coolingCoil, heatingCoil, fan)
    term.addToThermalZone(zn)
    vrf.addTerminal(term)

  when 42
    vrf = OpenStudio::Model::AirConditionerVariableRefrigerantFlowFluidTemperatureControlHR.new(model)
    vrf.autosizeRatedEvaporativeCapacity
    vrf.autosizeResistiveDefrostHeaterCapacity
    coolingCoil = OpenStudio::Model::CoilCoolingDXVariableRefrigerantFlowFluidTemperatureControl.new(model)
    heatingCoil = OpenStudio::Model::CoilHeatingDXVariableRefrigerantFlowFluidTemperatureControl.new(model)
    fan = OpenStudio::Model::FanVariableVolume.new(model)
    term = OpenStudio::Model::ZoneHVACTerminalUnitVariableRefrigerantFlow.new(model, coolingCoil, heatingCoil, fan)
    term.addToThermalZone(zn)
    vrf.addTerminal(term)

  when 44
    zoneHVACEvaporativeCoolerUnit = OpenStudio::Model::ZoneHVACEvaporativeCoolerUnit.new(model)
    zoneHVACEvaporativeCoolerUnit.autosizeDesignSupplyAirFlowRate
    zoneHVACEvaporativeCoolerUnit.addToThermalZone(zn)

  when 26, 27, 28, 29, 30, 31, 32, 33, 38, 40, 43
    # Previously used for the unitary systems, dehum, etc
  when 0
    # This wasn't assigned yet and is for grabs
    puts "Nothing added to #{zn.name}, index #{zone_index}"
  else
    raise "Nothing added to #{zn.name}, index #{zone_index}"
    # Do nothing
  end
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
