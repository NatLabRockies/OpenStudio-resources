import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# Make a Dual Duct AirLoopHVAC
air_loop = openstudio.model.AirLoopHVAC(model, True)

fan = openstudio.model.FanVariableVolume(model)
fan.addToNode(air_loop.supplyInletNode())

oa_controller = openstudio.model.ControllerOutdoorAir(model)
oa_system = openstudio.model.AirLoopHVACOutdoorAirSystem(model, oa_controller)
oa_system.addToNode(air_loop.supplyInletNode())

# After the splitter, we will now have two supply outlet nodes
supply_outlet_nodes = air_loop.supplyOutletNodes()

heating_coil = openstudio.model.CoilHeatingGas(model)
heating_coil.addToNode(supply_outlet_nodes[0])

heating_sch = openstudio.model.ScheduleRuleset(model)
heating_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 45.0)
heating_spm = openstudio.model.SetpointManagerScheduled(model, heating_sch)
heating_spm.addToNode(supply_outlet_nodes[0])

cooling_coil = openstudio.model.CoilCoolingDXTwoSpeed(model)
cooling_coil.addToNode(supply_outlet_nodes[1])

cooling_sch = openstudio.model.ScheduleRuleset(model)
cooling_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 12.8)
cooling_spm = openstudio.model.SetpointManagerScheduled(model, cooling_sch)
cooling_spm.addToNode(supply_outlet_nodes[1])

# In order to produce more consistent results between different runs,
# we sort the zones by names (doesn't matter here, just in case)
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())
for zone in zones:
    terminal = openstudio.model.AirTerminalDualDuctVAV(model)
    air_loop.addBranchForZone(zone, terminal)


# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
