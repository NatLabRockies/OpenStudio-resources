import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

schedule = model.alwaysOnDiscreteSchedule()

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# CoilHeatingDXSingleSpeed, CoilCoolingDXSingleSpeed
airLoop_1 = openstudio.model.AirLoopHVAC(model)
airLoop_1_supplyNode = airLoop_1.supplyOutletNode()

fan_1 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_1 = openstudio.model.CoilCoolingDXSingleSpeed(model)
heating_coil_1 = openstudio.model.CoilHeatingDXSingleSpeed(model)
unitary_1 = openstudio.model.AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass(model, fan_1, cooling_coil_1, heating_coil_1)

unitary_1.addToNode(airLoop_1_supplyNode)
terminal_1 = openstudio.model.AirTerminalSingleDuctVAVHeatAndCoolNoReheat(model)
airLoop_1.addBranchForZone(zones[0], terminal_1)

# CoilHeatingDXVariableSpeed, CoilCoolingDXVariableSpeed
airLoop_2 = openstudio.model.AirLoopHVAC(model)
airLoop_2_supplyNode = airLoop_2.supplyOutletNode()

fan_2 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_2 = openstudio.model.CoilCoolingDXVariableSpeed(model)
cooling_coil_speed_2 = openstudio.model.CoilCoolingDXVariableSpeedSpeedData(model)
cooling_coil_2.addSpeed(cooling_coil_speed_2)
heating_coil_2 = openstudio.model.CoilHeatingDXVariableSpeed(model)
heating_coil_speed_2 = openstudio.model.CoilHeatingDXVariableSpeedSpeedData(model)
heating_coil_2.addSpeed(heating_coil_speed_2)
unitary_2 = openstudio.model.AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass(model, fan_2, cooling_coil_2, heating_coil_2)

unitary_2.addToNode(airLoop_2_supplyNode)
terminal_2 = openstudio.model.AirTerminalSingleDuctVAVHeatAndCoolNoReheat(model)
airLoop_2.addBranchForZone(zones[1], terminal_2)

# CoilHeatingGas, CoilSystemCoolingDXHeatExchangerAssisted
airLoop_3 = openstudio.model.AirLoopHVAC(model)
airLoop_3_supplyNode = airLoop_3.supplyOutletNode()

fan_3 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_3 = openstudio.model.CoilSystemCoolingDXHeatExchangerAssisted(model)
heating_coil_3 = openstudio.model.CoilHeatingGas(model)
unitary_3 = openstudio.model.AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass(model, fan_3, cooling_coil_3, heating_coil_3)

unitary_3.addToNode(airLoop_3_supplyNode)
terminal_3 = openstudio.model.AirTerminalSingleDuctVAVHeatAndCoolNoReheat(model)
airLoop_3.addBranchForZone(zones[2], terminal_3)

# CoilHeatingElectric, CoilCoolingDXTwoStageWithHumidityControlMode
airLoop_4 = openstudio.model.AirLoopHVAC(model)
airLoop_4_supplyNode = airLoop_4.supplyOutletNode()

fan_4 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_4 = openstudio.model.CoilCoolingDXTwoStageWithHumidityControlMode(model)
heating_coil_4 = openstudio.model.CoilHeatingElectric(model)
unitary_4 = openstudio.model.AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass(model, fan_4, cooling_coil_4, heating_coil_4)

unitary_4.addToNode(airLoop_4_supplyNode)
terminal_4 = openstudio.model.AirTerminalSingleDuctVAVHeatAndCoolNoReheat(model)
airLoop_4.addBranchForZone(zones[3], terminal_4)

# CoilHeatingWater, CoilCoolingDXSingleSpeed
hw_loop = openstudio.model.PlantLoop(model)
hw_temp_f = 140
hw_delta_t_r = 20  # 20F delta-T
hw_temp_c = openstudio.convert(hw_temp_f, "F", "C").get()
hw_delta_t_k = openstudio.convert(hw_delta_t_r, "R", "K").get()
hw_temp_sch = openstudio.model.ScheduleRuleset(model)
hw_temp_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), hw_temp_c)
hw_stpt_manager = openstudio.model.SetpointManagerScheduled(model, hw_temp_sch)
hw_stpt_manager.addToNode(hw_loop.supplyOutletNode())

hotWaterOutletNode = hw_loop.supplyOutletNode()
hotWaterInletNode = hw_loop.supplyInletNode()

pump = openstudio.model.PumpVariableSpeed(model)
pump.addToNode(hotWaterInletNode)

boiler = openstudio.model.BoilerHotWater(model)
node = hw_loop.supplySplitter().lastOutletModelObject().get().to_Node().get()
boiler.addToNode(node)

pipe = openstudio.model.PipeAdiabatic(model)
hw_loop.addSupplyBranchForComponent(pipe)

pipe2 = openstudio.model.PipeAdiabatic(model)
pipe2.addToNode(hotWaterOutletNode)

airLoop_5 = openstudio.model.AirLoopHVAC(model)
airLoop_5_supplyNode = airLoop_5.supplyOutletNode()

fan_5 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_5 = openstudio.model.CoilCoolingDXSingleSpeed(model)
heating_coil_5 = openstudio.model.CoilHeatingWater(model)
unitary_5 = openstudio.model.AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass(model, fan_5, cooling_coil_5, heating_coil_5)

unitary_5.addToNode(airLoop_5_supplyNode)
terminal_5 = openstudio.model.AirTerminalSingleDuctVAVHeatAndCoolNoReheat(model)
airLoop_5.addBranchForZone(zones[4], terminal_5)

hw_loop.addDemandBranchForComponent(heating_coil_5)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
