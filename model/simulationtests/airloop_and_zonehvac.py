import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

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

zone = zones[0]

# add unitary AirLoopHVACUnitarySystem
air_loop_unitary = openstudio.model.AirLoopHVACUnitarySystem(model)
htg_coil = openstudio.model.CoilHeatingGas(model)
air_loop_unitary.setHeatingCoil(htg_coil)
fan = openstudio.model.FanOnOff(model, model.alwaysOnDiscreteSchedule())
air_loop_unitary.setSupplyFan(fan)
air_loop_unitary.setFanPlacement("BlowThrough")
air_loop_unitary.setControllingZoneorThermostatLocation(zone)

# add AirLoopHVAC
air_loop = openstudio.model.AirLoopHVAC(model)
air_loop_unitary.addToNode(air_loop.supplyInletNode())

alwaysOn = model.alwaysOnDiscreteSchedule()

# Starting with E+ 9.0.0 (in OS 2.7.0), Uncontrolled is deprecated
# and replaced with ConstantVolume:NoReheat
if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("2.7.0"):
    diffuser = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, alwaysOn)
else:
    diffuser = openstudio.model.AirTerminalSingleDuctUncontrolled(model, alwaysOn)


air_loop.addBranchForZone(zone, diffuser.to_StraightComponent())
air_loop.addBranchForZone(zone)

# add ZoneHVACPackagedTerminalAirConditioner
clg_coil = openstudio.model.CoilCoolingDXSingleSpeed(model)
fan = openstudio.model.FanOnOff(model, model.alwaysOnDiscreteSchedule())
htg_coil = openstudio.model.CoilHeatingElectric(model, model.alwaysOffDiscreteSchedule())
ptac = openstudio.model.ZoneHVACPackagedTerminalAirConditioner(
    model, model.alwaysOnDiscreteSchedule(), fan, htg_coil, clg_coil
)
ptac.addToThermalZone(zone)

# add ZoneHVACDehumidifierDX
humidistat = openstudio.model.ZoneControlHumidistat(model)
zone.setZoneControlHumidistat(humidistat)
zone_hvac = openstudio.model.ZoneHVACDehumidifierDX(model)
zone_hvac.addToThermalZone(zone)

# Explicitly Set Load Distribution scheme (in 2.7.0 and above only)
# to the same historical default of "SequentialLoad"
if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("2.7.0"):
    zone.setLoadDistributionScheme("SequentialLoad")


# remove airloop
air_loop.remove()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
