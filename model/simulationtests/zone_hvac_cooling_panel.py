import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

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

# In order to produce more consistent results between different runs,
# we sort the zones by names
# (There's only one here, but just in case this would be copy pasted somewhere
# else...)
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())
z = zones[0]

# Chilled Water Plant
chw_loop = openstudio.model.PlantLoop(model)
chw_loop.setName("Chilled Water Loop")
chw_loop.setMaximumLoopTemperature(98)
chw_loop.setMinimumLoopTemperature(1)
chw_temp_f = 44
chw_delta_t_r = 10.1  # 10.1F delta-T
chw_temp_c = openstudio.convert(chw_temp_f, "F", "C").get()
chw_delta_t_k = openstudio.convert(chw_delta_t_r, "R", "K").get()
chw_temp_sch = openstudio.model.ScheduleRuleset(model)
chw_temp_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), chw_temp_c)
chw_stpt_manager = openstudio.model.SetpointManagerScheduled(model, chw_temp_sch)
chw_stpt_manager.addToNode(chw_loop.supplyOutletNode())
sizing_plant = chw_loop.sizingPlant()
sizing_plant.setLoopType("Cooling")
sizing_plant.setDesignLoopExitTemperature(chw_temp_c)
sizing_plant.setLoopDesignTemperatureDifference(chw_delta_t_k)

# Primary chilled water pump
pri_chw_pump = openstudio.model.HeaderedPumpsConstantSpeed(model)
pri_chw_pump.setName("Chilled Water Loop Primary Pump")
pri_chw_pump_head_ft_h2o = 15
pri_chw_pump_head_press_pa = openstudio.convert(pri_chw_pump_head_ft_h2o, "ftH_{2}O", "Pa").get()
pri_chw_pump.setRatedPumpHead(pri_chw_pump_head_press_pa)
pri_chw_pump.setMotorEfficiency(0.9)
pri_chw_pump.setPumpControlType("Intermittent")
pri_chw_pump.addToNode(chw_loop.supplyInletNode())

# Secondary chilled water pump
sec_chw_pump = openstudio.model.HeaderedPumpsVariableSpeed(model)
sec_chw_pump.setName("Chilled Water Loop Secondary Pump")
sec_chw_pump_head_ft_h2o = 45
sec_chw_pump_head_press_pa = openstudio.convert(sec_chw_pump_head_ft_h2o, "ftH_{2}O", "Pa").get()
sec_chw_pump.setRatedPumpHead(sec_chw_pump_head_press_pa)
sec_chw_pump.setMotorEfficiency(0.9)

# Curve makes it perform like variable speed pump
sec_chw_pump.setFractionofMotorInefficienciestoFluidStream(0)
sec_chw_pump.setCoefficient1ofthePartLoadPerformanceCurve(0)
sec_chw_pump.setCoefficient2ofthePartLoadPerformanceCurve(0.0205)
sec_chw_pump.setCoefficient3ofthePartLoadPerformanceCurve(0.4101)
sec_chw_pump.setCoefficient4ofthePartLoadPerformanceCurve(0.5753)
sec_chw_pump.setPumpControlType("Intermittent")
sec_chw_pump.addToNode(chw_loop.demandInletNode())

# Change the chilled water loop to have a two-way common pipes
chw_loop.setCommonPipeSimulation("CommonPipe")

# Cooling equipment
chiller = openstudio.model.ChillerElectricEIR(model)
chw_loop.addSupplyBranchForComponent(chiller)

# Add ZoneHVACCoolingPanelRadiantConvectiveWater
zoneHVACCoolingPanelRadiantConvectiveWater = openstudio.model.ZoneHVACCoolingPanelRadiantConvectiveWater(model)
panel_coil = zoneHVACCoolingPanelRadiantConvectiveWater.coolingCoil().to_CoilCoolingWaterPanelRadiant().get()
panel_coil.setCoolingDesignCapacity(600.0)
chw_loop.addDemandBranchForComponent(panel_coil)
zoneHVACCoolingPanelRadiantConvectiveWater.addToThermalZone(z)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
