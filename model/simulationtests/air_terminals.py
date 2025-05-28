import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac(ashrae_sys_num="07")

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# In order to produce more consistent results between different runs,
# We ensure we do get the same object each time
chillers = sorted(model.getChillerElectricEIRs(), key=lambda c: c.nameString())
boilers = sorted(model.getBoilerHotWaters(), key=lambda c: c.nameString())

cooling_loop = chillers[0].plantLoop().get()
heating_loop = boilers[0].plantLoop().get()

for i, z in enumerate(zones):
    if i == 0:
        print(z.nameString())
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        schedule = model.alwaysOnDiscreteSchedule()
        new_terminal = openstudio.model.AirTerminalSingleDuctVAVNoReheat(model, schedule)
        air_loop.addBranchForZone(z, new_terminal.to_StraightComponent())

    elif i == 1:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        schedule = model.alwaysOnDiscreteSchedule()
        coil = openstudio.model.CoilHeatingWater(model, schedule)
        new_terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeReheat(model, schedule, coil)
        air_loop.addBranchForZone(z, new_terminal.to_StraightComponent())

        heating_loop.addDemandBranchForComponent(coil)

    elif i == 2:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        schedule = model.alwaysOnDiscreteSchedule()
        coil = openstudio.model.CoilHeatingElectric(model, schedule)
        new_terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeReheat(model, schedule, coil)
        air_loop.addBranchForZone(z, new_terminal.to_StraightComponent())

    elif i == 3:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        schedule = model.alwaysOnDiscreteSchedule()
        coil = openstudio.model.CoilHeatingGas(model, schedule)
        new_terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeReheat(model, schedule, coil)
        air_loop.addBranchForZone(z, new_terminal.to_StraightComponent())

    elif i == 4:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        schedule = model.alwaysOnDiscreteSchedule()
        coil = openstudio.model.CoilHeatingWater(model, schedule)
        fan = openstudio.model.FanConstantVolume(model, schedule)
        new_terminal = openstudio.model.AirTerminalSingleDuctParallelPIUReheat(model, schedule, fan, coil)
        air_loop.addBranchForZone(z, new_terminal.to_StraightComponent())

        heating_loop.addDemandBranchForComponent(coil)

    elif i == 5:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        schedule = model.alwaysOnDiscreteSchedule()
        coil = openstudio.model.CoilHeatingWater(model, schedule)
        fan = openstudio.model.FanConstantVolume(model, schedule)
        new_terminal = openstudio.model.AirTerminalSingleDuctSeriesPIUReheat(model, fan, coil)
        air_loop.addBranchForZone(z, new_terminal.to_StraightComponent())

        heating_loop.addDemandBranchForComponent(coil)

    elif i == 6:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        schedule = model.alwaysOnDiscreteSchedule()
        heat_coil = openstudio.model.CoilHeatingWater(model, schedule)
        cool_coil = openstudio.model.CoilCoolingWater(model, schedule)
        new_terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeFourPipeInduction(model, heat_coil)
        new_terminal.setCoolingCoil(cool_coil)
        air_loop.addBranchForZone(z, new_terminal.to_StraightComponent())

        heating_loop.addDemandBranchForComponent(heat_coil)
        cooling_loop.addDemandBranchForComponent(cool_coil)


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
