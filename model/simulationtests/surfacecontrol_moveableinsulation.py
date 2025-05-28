import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=0)

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
# we sort the zones by names (only one here anyways...)
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# Use Ideal Air Loads
for z in zones:
    z.setUseIdealAirLoads(True)

material = openstudio.model.StandardOpaqueMaterial(model)
material.setThickness(0.2032)
material.setConductivity(1.3114056)
material.setDensity(2242.8)
material.setSpecificHeat(837.4)

# Set a fractional continuous schedule, here we'll say the insulation is
# completely in place during the night (21 to 8), off during the day
scheduleRuleset = openstudio.model.ScheduleRuleset(model)
night_schedule = scheduleRuleset.defaultDaySchedule()
night_schedule.addValue(openstudio.Time(0, 8, 0, 0), 1.0)
night_schedule.addValue(openstudio.Time(0, 21, 0, 0), 0.0)
night_schedule.addValue(openstudio.Time(0, 24, 0, 0), 1.0)

# To ensure repeatability, we sort the surfaces by their name,
# and we keep only outside walls
surfaces = sorted(
    [s for s in model.getSurfaces() if s.surfaceType() == "Wall" and s.outsideBoundaryCondition() == "Outdoors"],
    key=lambda s: s.nameString(),
)
# set surface control movable insulation
for surface in surfaces:
    movableInsulation = openstudio.model.SurfaceControlMovableInsulation(surface, material)
    movableInsulation.setInsulationType("Inside")
    movableInsulation.setSchedule(scheduleRuleset)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
