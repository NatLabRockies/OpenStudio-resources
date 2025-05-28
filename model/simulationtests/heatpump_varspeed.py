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

schedule = model.alwaysOnDiscreteSchedule()
fan = openstudio.model.FanOnOff(model, schedule)
supp_heating_coil = openstudio.model.CoilHeatingElectric(model, schedule)

heating_coil = openstudio.model.CoilHeatingDXVariableSpeed(model)
heating_coil_speed_1 = openstudio.model.CoilHeatingDXVariableSpeedSpeedData(model)
heating_coil.addSpeed(heating_coil_speed_1)

cooling_coil = openstudio.model.CoilCoolingDXVariableSpeed(model)
cooling_coil_speed_1 = openstudio.model.CoilCoolingDXVariableSpeedSpeedData(model)
cooling_coil.addSpeed(cooling_coil_speed_1)

unitary = openstudio.model.AirLoopHVACUnitaryHeatPumpAirToAir(
    model, schedule, fan, heating_coil, cooling_coil, supp_heating_coil
)
unitary.addToNode(supplyOutletNode)

terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, schedule)
air_loop.addBranchForZone(zone, terminal.to_StraightComponent())
unitary.setControllingZone(zone)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
