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

############   C O N D E N S E R    S I D E  ##################

cw_loop = OpenStudio::Model::PlantLoop.new(model)
cw_loop.setName('Condenser Water Loop Water Source')
cw_loop.setMaximumLoopTemperature(100)
cw_loop.setMinimumLoopTemperature(3)
cw_loop.setPlantLoopVolume(1.0)
cw_temp_sizing_f = 102 # CW sized to deliver 102F
cw_delta_t_r = 10 # 10F delta-T
cw_temp_sizing_c = OpenStudio.convert(cw_temp_sizing_f, 'F', 'C').get
cw_delta_t_k = OpenStudio.convert(cw_delta_t_r, 'R', 'K').get

sizing_plant = cw_loop.sizingPlant
sizing_plant.setLoopType('Condenser')
sizing_plant.setDesignLoopExitTemperature(cw_temp_sizing_c)
sizing_plant.setLoopDesignTemperatureDifference(cw_delta_t_k)

cw_pump = OpenStudio::Model::PumpVariableSpeed.new(model)
cw_pump.setName('Condenser Water Loop Pump Water Source')
cw_pump_head_ft_h2o = 60.0
cw_pump_head_press_pa = OpenStudio.convert(cw_pump_head_ft_h2o, 'ftH_{2}O', 'Pa').get
cw_pump.setRatedPumpHead(cw_pump_head_press_pa)
cw_pump.addToNode(cw_loop.supplyInletNode)

groundHX = OpenStudio::Model::GroundHeatExchangerVertical.new(model)
# THe default isn't the same as the E+ example file (and apparently wrong)
groundHX.setUTubeDistance(5.1225E-02)

cw_loop.addSupplyBranchForComponent(groundHX)

ground_temp = model.getSiteGroundTemperatureDeep
ground_temp.setAllMonthlyTemperatures(
  [13.03, 13.03, 13.13, 13.30, 13.43, 13.52, 13.62, 13.77, 13.78, 13.55, 13.44, 13.20]
)
spm_ground = OpenStudio::Model::SetpointManagerFollowGroundTemperature.new(model)
spm_ground.setControlVariable('Temperature')
spm_ground.setOffsetTemperatureDifference(0.0)
spm_ground.setMaximumSetpointTemperature(80.0)
spm_ground.setMinimumSetpointTemperature(10.0)
spm_ground.setReferenceGroundTemperatureObjectType('Site:GroundTemperature:Deep')
spm_ground.addToNode(cw_loop.supplyOutletNode)

###############################################################################
#                         A I R    S O U R C E    H P                         #
###############################################################################

# PlantLoopHeatPump_EIR_AirSource.idf

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

hw_loop.addSupplyBranchForComponent(plhp_airsource_htg)
chw_loop.addSupplyBranchForComponent(plhp_airsource_clg)

###############################################################

###############################################################################
#                       W A T E R    S O U R C E    H P                       #
###############################################################################

# PlantLoopHeatPump_EIR_WaterSource.idf

plhp_watersource_htg = OpenStudio::Model::HeatPumpPlantLoopEIRHeating.new(model)
plhp_watersource_clg = OpenStudio::Model::HeatPumpPlantLoopEIRCooling.new(model)

plhp_watersource_htg.setName('Heat Pump Plant Loop EIR Heating - WaterSource')
plhp_watersource_htg.setCompanionCoolingHeatPump(plhp_watersource_clg)
# No: you can't do it! We enforce the condenserType <=> secondaryPlantLoop relationship.
# Instead when you call addDemandBranchForComponent(plhp_watersource_clg)
# It will switch it to WaterSource
# plhp_watersource_htg.setCondenserType('WaterSource')
plhp_watersource_htg.setLoadSideReferenceFlowRate(0.005)
plhp_watersource_htg.setSourceSideReferenceFlowRate(0.002)
plhp_watersource_htg.setReferenceCapacity(80000)
plhp_watersource_htg.setReferenceCoefficientofPerformance(3.5)
plhp_watersource_htg.setSizingFactor(1)
plhp_watersource_htg.capacityModifierFunctionofTemperatureCurve.setName('CapCurveFuncTemp Water Source')
plhp_watersource_htg.electricInputtoOutputRatioModifierFunctionofTemperatureCurve.setName('EIRCurveFuncTemp Water Source')
plhp_watersource_htg.electricInputtoOutputRatioModifierFunctionofPartLoadRatioCurve.setName('EIRCurveFuncPLR Water Source')

plhp_watersource_clg.setName('Heat Pump Plant Loop EIR Cooling - WaterSource')
plhp_watersource_clg.setCompanionHeatingHeatPump(plhp_watersource_htg)
# plhp_watersource_clg.setCondenserType('WaterSource')
plhp_watersource_clg.setLoadSideReferenceFlowRate(0.005)
plhp_watersource_clg.setSourceSideReferenceFlowRate(0.003)
plhp_watersource_clg.setReferenceCapacity(400000)
plhp_watersource_clg.setReferenceCoefficientofPerformance(3.5)
plhp_watersource_clg.setSizingFactor(1)
plhp_watersource_clg.capacityModifierFunctionofTemperatureCurve.setName('CapCurveFuncTemp2 Water Source')
plhp_watersource_clg.electricInputtoOutputRatioModifierFunctionofTemperatureCurve.setName('EIRCurveFuncTemp2 Water Source')
plhp_watersource_clg.electricInputtoOutputRatioModifierFunctionofPartLoadRatioCurve.setName('EIRCurveFuncPLR2 Water Source')

hw_loop.addSupplyBranchForComponent(plhp_watersource_htg)
chw_loop.addSupplyBranchForComponent(plhp_watersource_clg)

# This switches them to 'WaterSource' condenser type
cw_loop.addDemandBranchForComponent(plhp_watersource_htg)
cw_loop.addDemandBranchForComponent(plhp_watersource_clg)

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
