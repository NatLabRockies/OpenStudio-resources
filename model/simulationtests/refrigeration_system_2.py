import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# Schedule Ruleset
defrost_sch = openstudio.model.ScheduleRuleset(model)
defrost_sch.setName("Refrigeration Defrost Schedule")
# All other days
defrost_sch.defaultDaySchedule().setName("Refrigeration Defrost Schedule Default")
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 4, 0, 0), 0)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 4, 45, 0), 1)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 8, 0, 0), 0)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 8, 45, 0), 1)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 12, 0, 0), 0)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 12, 45, 0), 1)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 16, 0, 0), 0)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 16, 45, 0), 1)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 20, 0, 0), 0)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 20, 45, 0), 1)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 0)


def add_case(model, thermal_zone, defrost_sch):
    ref_case = openstudio.model.RefrigerationCase(model, defrost_sch)
    ref_case.setThermalZone(thermal_zone)
    return ref_case


def add_walkin(model, thermal_zone, defrost_sch):
    ref_walkin = openstudio.model.RefrigerationWalkIn(model, defrost_sch)
    zone_boundaries = ref_walkin.zoneBoundaries()
    zone_boundaries[0].setThermalZone(thermal_zone)
    return ref_walkin


# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac(ashrae_sys_num="07")

# add thermostats
model.add_thermostats(heating_setpoint=20, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

i = 0
for z in zones:
    if i == 0:
        compressor_rack = openstudio.model.RefrigerationCompressorRack(model)
        compressor_rack.addCase(add_case(model, z, defrost_sch))
        compressor_rack.addCase(add_case(model, z, defrost_sch))
        compressor_rack.addWalkin(add_walkin(model, z, defrost_sch))
        compressor_rack.addWalkin(add_walkin(model, z, defrost_sch))

    i += 1


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
