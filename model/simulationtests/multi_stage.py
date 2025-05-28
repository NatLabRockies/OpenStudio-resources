import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

always_on = model.alwaysOnDiscreteSchedule()

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# add thermostats
model.add_thermostats(heating_setpoint=20, cooling_setpoint=30)

# get the heating and cooling setpoint schedule to use later
thermostat = model.getThermostatSetpointDualSetpoints()[0]
heating_schedule = thermostat.heatingSetpointTemperatureSchedule().get()
cooling_schedule = thermostat.coolingSetpointTemperatureSchedule().get()

# Unitary System with CoilHeatingGasMultiStage and CoilCoolingDXMultiSpeed test
zone = zones[0]

staged_thermostat = openstudio.model.ZoneControlThermostatStagedDualSetpoint(model)
staged_thermostat.setHeatingTemperatureSetpointSchedule(heating_schedule)
staged_thermostat.setNumberofHeatingStages(2)
staged_thermostat.setCoolingTemperatureSetpointBaseSchedule(cooling_schedule)
staged_thermostat.setNumberofCoolingStages(2)
zone.setThermostat(staged_thermostat)

air_system = openstudio.model.AirLoopHVAC(model)
supply_outlet_node = air_system.supplyOutletNode()

# Modify the sizing parameters for the air system
air_loop_sizing = air_system.sizingSystem()
air_loop_sizing.setCentralHeatingDesignSupplyAirTemperature(openstudio.convert(104, "F", "C").get())

controllerOutdoorAir = openstudio.model.ControllerOutdoorAir(model)
outdoorAirSystem = openstudio.model.AirLoopHVACOutdoorAirSystem(model, controllerOutdoorAir)
outdoorAirSystem.addToNode(supply_outlet_node)

fan = openstudio.model.FanConstantVolume(model, always_on)
heat = openstudio.model.CoilHeatingGasMultiStage(model)
heat.setName("Multi Stage Gas Htg Coil")
heat_stage_1 = openstudio.model.CoilHeatingGasMultiStageStageData(model)
heat_stage_2 = openstudio.model.CoilHeatingGasMultiStageStageData(model)
heat.addStage(heat_stage_1)
heat.addStage(heat_stage_2)
cool = openstudio.model.CoilCoolingDXMultiSpeed(model)
cool.setName("Multi Stage DX Clg Coil")
cool_stage_1 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
cool_stage_2 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
cool.addStage(cool_stage_1)
cool.addStage(cool_stage_2)
supp_heat = openstudio.model.CoilHeatingElectric(model, always_on)
supp_heat.setName("Sup Elec Htg Coil")
unitary = openstudio.model.AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed(model, fan, heat, cool, supp_heat)
unitary.addToNode(supply_outlet_node)
unitary.setControllingZoneorThermostatLocation(zone)

terminal = openstudio.model.AirTerminalSingleDuctUncontrolled(model, always_on)
air_system.addBranchForZone(zone, terminal)

# Unitary System with CoilHeatingDXMultiSpeed and CoilCoolingDXMultiSpeed test
zone = zones[1]

staged_thermostat = openstudio.model.ZoneControlThermostatStagedDualSetpoint(model)
staged_thermostat.setHeatingTemperatureSetpointSchedule(heating_schedule)
staged_thermostat.setNumberofHeatingStages(2)
staged_thermostat.setCoolingTemperatureSetpointBaseSchedule(cooling_schedule)
staged_thermostat.setNumberofCoolingStages(2)
zone.setThermostat(staged_thermostat)

air_system = openstudio.model.AirLoopHVAC(model)
supply_outlet_node = air_system.supplyOutletNode()

# Modify the sizing parameters for the air system
air_loop_sizing = air_system.sizingSystem()
air_loop_sizing.setCentralHeatingDesignSupplyAirTemperature(openstudio.convert(104, "F", "C").get())

controllerOutdoorAir = openstudio.model.ControllerOutdoorAir(model)
outdoorAirSystem = openstudio.model.AirLoopHVACOutdoorAirSystem(model, controllerOutdoorAir)
outdoorAirSystem.addToNode(supply_outlet_node)

fan = openstudio.model.FanConstantVolume(model, always_on)
heat = openstudio.model.CoilHeatingDXMultiSpeed(model)
heat.setName("Multi Stage Gas Htg Coil")
heat_stage_1 = openstudio.model.CoilHeatingDXMultiSpeedStageData(model)
heat_stage_2 = openstudio.model.CoilHeatingDXMultiSpeedStageData(model)
heat.addStage(heat_stage_1)
heat.addStage(heat_stage_2)
cool = openstudio.model.CoilCoolingDXMultiSpeed(model)
cool.setName("Multi Stage DX Clg Coil")
cool_stage_1 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
cool_stage_2 = openstudio.model.CoilCoolingDXMultiSpeedStageData(model)
cool.addStage(cool_stage_1)
cool.addStage(cool_stage_2)
supp_heat = openstudio.model.CoilHeatingElectric(model, always_on)
supp_heat.setName("Sup Elec Htg Coil")
unitary = openstudio.model.AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed(model, fan, heat, cool, supp_heat)
unitary.addToNode(supply_outlet_node)
unitary.setControllingZoneorThermostatLocation(zone)

terminal = openstudio.model.AirTerminalSingleDuctUncontrolled(model, always_on)
air_system.addBranchForZone(zone, terminal)

# Put all of the other zones on a system type 3
for z in zones[2:]:
    air_system = openstudio.model.addSystemType3(model).to_AirLoopHVAC().get()
    air_system.addBranchForZone(z)


# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
