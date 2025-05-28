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
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())
zone = zones[0]

air_loop = openstudio.model.AirLoopHVAC(model)
supplyOutletNode = air_loop.supplyOutletNode()
sat_f = 55
sat_c = openstudio.convert(sat_f, "F", "C").get()
sat_sch = openstudio.model.ScheduleRuleset(model)
sat_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), sat_c)
stpt_manager = openstudio.model.SetpointManagerScheduled(model, sat_sch)
stpt_manager.addToNode(supplyOutletNode)

schedule = model.alwaysOnDiscreteSchedule()
fan = openstudio.model.FanOnOff(model, schedule)
supp_heating_coil = openstudio.model.CoilHeatingElectric(model, schedule)

space_cooling_coil = openstudio.model.CoilCoolingDXVariableSpeed(model)
space_cooling_coil.setName("Heat Pump ACDXCoil 1")
space_cooling_coil_speed_1 = openstudio.model.CoilCoolingDXVariableSpeedSpeedData(model)
space_cooling_coil.addSpeed(space_cooling_coil_speed_1)
space_cooling_coil.setGrossRatedTotalCoolingCapacityAtSelectedNominalSpeedLevel(32000)
space_cooling_coil.setRatedAirFlowRateAtSelectedNominalSpeedLevel(1.7)

space_heating_coil = openstudio.model.CoilHeatingDXVariableSpeed(model)
space_heating_coil.setName("Heat Pump DX Heating Coil 1")
space_heating_coil_speed_1 = openstudio.model.CoilHeatingDXVariableSpeedSpeedData(model)
space_heating_coil.addSpeed(space_heating_coil_speed_1)

dedicated_water_heating_coil = openstudio.model.CoilWaterHeatingAirToWaterHeatPumpVariableSpeed(model)
dedicated_water_heating_coil.setName("HPWHOutdoorDXCoilVS")
dedicated_water_heating_coil_speed_1 = openstudio.model.CoilWaterHeatingAirToWaterHeatPumpVariableSpeedSpeedData(model)
dedicated_water_heating_coil.addSpeed(dedicated_water_heating_coil_speed_1)

scwh_coil = openstudio.model.CoilWaterHeatingAirToWaterHeatPumpVariableSpeed(model)
scwh_coil.setName("SCWHCoil1")
scwh_coil_speed_1 = openstudio.model.CoilWaterHeatingAirToWaterHeatPumpVariableSpeedSpeedData(model)
scwh_coil.addSpeed(scwh_coil_speed_1)

scdwh_cooling_coil = openstudio.model.CoilCoolingDXVariableSpeed(model)
scdwh_cooling_coil.setName("SCDWHCoolCoil1")
scdwh_cooling_coil_speed_1 = openstudio.model.CoilCoolingDXVariableSpeedSpeedData(model)
scdwh_cooling_coil.addSpeed(scdwh_cooling_coil_speed_1)

scdwh_water_heating_coil = openstudio.model.CoilWaterHeatingAirToWaterHeatPumpVariableSpeed(model)
scdwh_water_heating_coil.setName("SCDWHWHCoil1")
scdwh_water_heating_coil_speed_1 = openstudio.model.CoilWaterHeatingAirToWaterHeatPumpVariableSpeedSpeedData(model)
scdwh_water_heating_coil.addSpeed(scdwh_water_heating_coil_speed_1)

shdwh_heating_coil = openstudio.model.CoilHeatingDXVariableSpeed(model)
shdwh_heating_coil.setName("SHDWHHeatCoil1")
shdwh_heating_coil_speed_1 = openstudio.model.CoilHeatingDXVariableSpeedSpeedData(model)
shdwh_heating_coil.addSpeed(shdwh_heating_coil_speed_1)

shdwh_water_heating_coil = openstudio.model.CoilWaterHeatingAirToWaterHeatPumpVariableSpeed(model)
shdwh_water_heating_coil.setName("SHDWHWHCoil1")
shdwh_water_heating_coil_speed_1 = openstudio.model.CoilWaterHeatingAirToWaterHeatPumpVariableSpeedSpeedData(model)
shdwh_water_heating_coil.addSpeed(shdwh_water_heating_coil_speed_1)

coil_system = openstudio.model.CoilSystemIntegratedHeatPumpAirSource(
    model,
    space_cooling_coil,
    space_heating_coil,
    dedicated_water_heating_coil,
    scwh_coil,
    scdwh_cooling_coil,
    scdwh_water_heating_coil,
    shdwh_heating_coil,
    shdwh_water_heating_coil,
)

coil_system.setIndoorTemperatureLimitForSCWHMode(23.0)
coil_system.setAmbientTemperatureLimitForSCWHMode(28.0)
coil_system.setIndoorTemperatureAboveWhichWHHasHigherPriority(20.0)
coil_system.setAmbientTemperatureAboveWhichWHHasHigherPriority(16.0)
coil_system.setFlagtoIndicateLoadControlInSCWHMode(0)
coil_system.setMinimumSpeedLevelForSCWHMode(1)
coil_system.setMaximumWaterFlowVolumeBeforeSwitchingfromSCDWHtoSCWHMode(3.0)
coil_system.setMinimumSpeedLevelForSCDWHMode(1)
coil_system.setMaximumRunningTimeBeforeAllowingElectricResistanceHeatUseDuringSHDWHMode(600.0)
coil_system.setMinimumSpeedLevelForSHDWHMode(1)

unitary = openstudio.model.AirLoopHVACUnitaryHeatPumpAirToAir(
    model, schedule, fan, coil_system, coil_system, supp_heating_coil
)
unitary.addToNode(supplyOutletNode)

terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, schedule)
air_loop.addBranchForZone(zone, terminal.to_StraightComponent())
unitary.setControllingZone(zone)

heat_pump_water_heater = openstudio.model.WaterHeaterHeatPump(model)
heat_pump_water_heater.setCondenserWaterFlowRate(0.00016)
heat_pump_water_heater.setEvaporatorAirFlowRate(0.2685)
heat_pump_water_heater.setFanPlacement("BlowThrough")
fan = heat_pump_water_heater.fan().to_FanOnOff().get()
fan.setMaximumFlowRate(0.2685)
heat_pump_water_heater.setDXCoil(coil_system)
heat_pump_water_heater.addToThermalZone(zone)

tank = heat_pump_water_heater.tank().to_WaterHeaterMixed().get()
setpoint_temperature_schedule = tank.setpointTemperatureSchedule().get().to_ScheduleRuleset().get()
setpoint_temperature_schedule.defaultDaySchedule().clearValues()
setpoint_temperature_schedule.defaultDaySchedule().addValue(
    openstudio.Time(0, 24, 0, 0), 50.0
)  # tank setpoint must be less than heat pump cut-in

hw_loop = openstudio.model.PlantLoop(model)
hw_loop.setMinimumLoopTemperature(10)
hw_temp_f = 140
hw_delta_t_r = 20  # 20F delta-T
hw_temp_c = openstudio.convert(hw_temp_f, "F", "C").get()
hw_delta_t_k = openstudio.convert(hw_delta_t_r, "R", "K").get()
hw_temp_sch = openstudio.model.ScheduleRuleset(model)
hw_temp_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), hw_temp_c)
hw_stpt_manager = openstudio.model.SetpointManagerScheduled(model, hw_temp_sch)
hw_stpt_manager.addToNode(hw_loop.supplyOutletNode())
sizing_plant = hw_loop.sizingPlant()
sizing_plant.setLoopType("Heating")
sizing_plant.setDesignLoopExitTemperature(hw_temp_c)
sizing_plant.setLoopDesignTemperatureDifference(hw_delta_t_k)

hw_pump = openstudio.model.PumpVariableSpeed(model)
hw_pump_head_ft_h2o = 60
hw_pump_head_press_pa = openstudio.convert(hw_pump_head_ft_h2o, "ftH_{2}O", "Pa").get()
hw_pump.setRatedPumpHead(hw_pump_head_press_pa)
hw_pump.setPumpControlType("Intermittent")
hw_pump.addToNode(hw_loop.supplyInletNode())

boiler = openstudio.model.BoilerHotWater(model)
hw_loop.addSupplyBranchForComponent(boiler)
hw_loop.addSupplyBranchForComponent(tank)

htg_coil = openstudio.model.CoilHeatingWater(model)
htg_coil.addToNode(supplyOutletNode)
hw_loop.addDemandBranchForComponent(htg_coil)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
