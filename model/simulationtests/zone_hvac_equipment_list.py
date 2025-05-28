import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 2 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=0)

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

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

heating_schedule = openstudio.model.ScheduleConstant(model)
heating_schedule.setValue(0.75)
cooling_schedule = openstudio.model.ScheduleRuleset(model, 0.995)

for i, thermal_zone in enumerate(zones):
    htg_coil = openstudio.model.CoilHeatingDXSingleSpeed(model)
    htg_supp_coil = openstudio.model.CoilHeatingElectric(model)
    clg_coil = openstudio.model.CoilCoolingDXSingleSpeed(model)
    fan = openstudio.model.FanOnOff(model)

    air_loop_unitary = openstudio.model.AirLoopHVACUnitarySystem(model)
    air_loop_unitary.setSupplyFan(fan)
    # Be explicit about the fanPlacement. If you have a fan, you MUST supply a
    # fanPlacement. (FT currently Would default that to DrawThrough)
    air_loop_unitary.setFanPlacement("BlowThrough")
    air_loop_unitary.setHeatingCoil(htg_coil)
    air_loop_unitary.setCoolingCoil(clg_coil)
    air_loop_unitary.setSupplementalHeatingCoil(htg_supp_coil)

    air_loop = openstudio.model.AirLoopHVAC(model)
    air_supply_inlet_node = air_loop.supplyInletNode()

    air_loop_unitary.addToNode(air_supply_inlet_node)
    air_loop_unitary.setControllingZoneorThermostatLocation(thermal_zone)

    air_terminal_living = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(
        model, model.alwaysOnDiscreteSchedule()
    )
    # TODO: I don't think there's any reason to use the multiAddBranchForZone
    # method, addBranchForZone is plenty fine here.
    air_loop.multiAddBranchForZone(thermal_zone, air_terminal_living)

    if i == 0:  # test that the old methods still accept doubles:
        thermal_zone.setSequentialHeatingFraction(air_terminal_living, 0.9)
        thermal_zone.setSequentialHeatingFraction(air_terminal_living, 0.4)
    else:  # test new schedule arguments:

        thermal_zone.setSequentialHeatingFractionSchedule(air_terminal_living, heating_schedule)
        thermal_zone.setSequentialHeatingFractionSchedule(air_terminal_living, cooling_schedule)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
