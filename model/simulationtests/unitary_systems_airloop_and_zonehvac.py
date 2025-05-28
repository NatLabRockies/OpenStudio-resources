import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 01, PTAC, Residential
model.add_hvac(ashrae_sys_num="01")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# Get the first one
zone = zones[0]

# add AirLoopHVACUnitarySystem for air loop
air_loop_unitary = openstudio.model.AirLoopHVACUnitarySystem(model)
clg_coil = openstudio.model.CoilCoolingDXSingleSpeed(model)
air_loop_unitary.setCoolingCoil(clg_coil)
fan = openstudio.model.FanOnOff(model, model.alwaysOnDiscreteSchedule())
air_loop_unitary.setSupplyFan(fan)
air_loop_unitary.setFanPlacement("BlowThrough")
air_loop_unitary.setControllingZoneorThermostatLocation(zone)

# add AirLoopHVAC
air_loop = openstudio.model.AirLoopHVAC(model)
air_loop_unitary.addToNode(air_loop.supplyInletNode())
diffuser = openstudio.model.AirTerminalSingleDuctUncontrolled(model, model.alwaysOnDiscreteSchedule())
air_loop.addBranchForZone(zone, diffuser.to_StraightComponent())
air_loop.addBranchForZone(zone)

# add AirLoopHVACUnitarySystem for zone
htg_coil = openstudio.model.CoilHeatingGas(model)
fan = openstudio.model.FanOnOff(model, model.alwaysOnDiscreteSchedule())
zone_unitary = openstudio.model.AirLoopHVACUnitarySystem(model)
zone_unitary.setHeatingCoil(htg_coil)
zone_unitary.setSupplyFan(fan)
zone_unitary.setFanPlacement("BlowThrough")
zone_unitary.setControllingZoneorThermostatLocation(zone)
zone_unitary.addToThermalZone(zone)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
