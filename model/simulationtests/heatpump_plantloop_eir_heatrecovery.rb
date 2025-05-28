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

# PlantLoopHeatPump_EIR_AirSource_Hospital_wSixPipeHeatRecovery.idf

plhp_airsource_htg = OpenStudio::Model::HeatPumpPlantLoopEIRHeating.new(model)
plhp_airsource_clg = OpenStudio::Model::HeatPumpPlantLoopEIRCooling.new(model)

plhp_airsource_htg.setName('Heat Pump Plant Loop EIR Heating - AirSource')
plhp_airsource_htg.setCompanionCoolingHeatPump(plhp_airsource_clg)
# This is already the default, since it's not connected to any secondary plant loop
# plhp_airsource_htg.setCondenserType('AirSource')

plhp_airsource_htg.setLoadSideReferenceFlowRate(0.005)
plhp_airsource_htg.setSourceSideReferenceFlowRate(2.0)
plhp_airsource_htg.setReferenceCapacity(80000)
# plhp_airsource_htg.autosizeReferenceCapacity()
# plhp_airsource_htg.autosizeSourceSideReferenceFlowRate()
# plhp_airsource_htg.autosizeLoadSideReferenceFlowRate()

plhp_airsource_htg.setReferenceCoefficientofPerformance(3.5)
plhp_airsource_htg.setSizingFactor(1)
plhp_airsource_htg.capacityModifierFunctionofTemperatureCurve.setName('CapCurveFuncTemp Air Source')
plhp_airsource_htg.electricInputtoOutputRatioModifierFunctionofTemperatureCurve.setName('EIRCurveFuncTemp Air Source')
plhp_airsource_htg.electricInputtoOutputRatioModifierFunctionofPartLoadRatioCurve.setName('EIRCurveFuncPLR Air Source')

plhp_airsource_clg.setName('Heat Pump Plant Loop EIR Cooling - AirSource')
plhp_airsource_clg.setCompanionHeatingHeatPump(plhp_airsource_htg)
# plhp_airsource_clg.setCondenserType('AirSource')

plhp_airsource_clg.setLoadSideReferenceFlowRate(0.005)
plhp_airsource_clg.setSourceSideReferenceFlowRate(20.0)
plhp_airsource_clg.setReferenceCapacity(400000)
# plhp_airsource_clg.autosizeReferenceCapacity()
# plhp_airsource_clg.autosizeSourceSideReferenceFlowRate()
# plhp_airsource_clg.autosizeLoadSideReferenceFlowRate()

plhp_airsource_clg.setReferenceCoefficientofPerformance(3.5)
plhp_airsource_clg.setSizingFactor(1)
plhp_airsource_clg.capacityModifierFunctionofTemperatureCurve.setName('CapCurveFuncTemp2 Air Source')
plhp_airsource_clg.electricInputtoOutputRatioModifierFunctionofTemperatureCurve.setName('EIRCurveFuncTemp2 Air Source')
plhp_airsource_clg.electricInputtoOutputRatioModifierFunctionofPartLoadRatioCurve.setName('EIRCurveFuncPLR2 Air Source')

# Note: Heat Recovery is ONLY available for 'AirSource' HeatPumpPlantLoopEIRs
tertiary = true
hw_loop.addSupplyBranchForComponent(plhp_airsource_htg)
# If not passing tertiary=true here, this would connect the Source Water Side
# and swich the HP to a WaterSource one
chw_loop.addDemandBranchForComponent(plhp_airsource_htg, tertiary)

chw_loop.addSupplyBranchForComponent(plhp_airsource_clg)
hw_loop.addDemandBranchForComponent(plhp_airsource_clg, tertiary)

[plhp_airsource_htg, plhp_airsource_clg].each do |plhp|
  raise unless plhp.condenserType == 'AirSource'
  raise unless plhp.sourceSideWaterLoop.empty?
  raise if plhp.loadSideWaterLoop.empty?
  raise if plhp.heatRecoveryLoop.empty?
end

###############################################################

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
