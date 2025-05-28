# This is a test for SurfaceProperty:GroundSurfaces and
# SurfaceProperty:IncidentSolarMultiplier
# Loosely adapted from SurfacePropGroundSurfaces_LWR.idf
# and 1ZoneEvapCooler_4Win_incidentSolarMultiplier.idf (from E+ 22.2.0)

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=19, cooling_setpoint=26)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# There's only one zone here...
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())
z = zones[0]
zone_ideal_loads = openstudio.model.ZoneHVACIdealLoadsAirSystem(model)
zone_ideal_loads.addToThermalZone(z)

# Get the first Outdoors Wall surface, sorting by azimuth to ensure consistency just in case
surfaces = sorted(
    [s for s in model.getSurfaces() if s.surfaceType() == "Wall" and s.outsideBoundaryCondition() == "Outdoors"],
    key=lambda s: s.azimuth(),
)
assert surfaces
surface = surfaces[0]

# Get its window
assert surface.subSurfaces()

subSurface = surface.subSurfaces()[0]

###############################################################################
#                   SurfacePropertyIncidentSolarMultiplier                    #
###############################################################################

spism = openstudio.model.SurfacePropertyIncidentSolarMultiplier(subSurface)
spism.setIncidentSolarMultiplier(0.5)

solarMultConstSch = openstudio.model.ScheduleConstant(model)
solarMultConstSch.setName("SolarMultConstSch")
solarMultConstSch.setValue(1.0)
spism.setIncidentSolarMultiplierSchedule(solarMultConstSch)

# API DEMO
# NOTE: you can access an OptionalSurfacePropertyIncidentSolarMultiplier from any subsurface
assert subSurface.surfacePropertyIncidentSolarMultiplier().get() == spism
assert spism.subSurface() == subSurface

###############################################################################
#                        SurfacePropertyGroundSurfaces                        #
###############################################################################

localEnv = openstudio.model.SurfacePropertyLocalEnvironment(surface)
localEnv.setName("#{surface.nameString()} LocalEnv")

spigs = openstudio.model.SurfacePropertyGroundSurfaces(model)
spigs.setName("#{surface.nameString()} GndSurfs")
localEnv.setSurfacePropertyGroundSurfaces(spigs)

grassTempSch = openstudio.model.ScheduleConstant(model)
grassTempSch.setName("GndSurfs:GrassTemp")
grassTempSch.setValue(12.0)
grassReflSch = openstudio.model.ScheduleConstant(model)
grassReflSch.setName("GndSurfs:GrassRefl")
grassReflSch.setValue(0.2)

# Note: because we allow not passing any of two schedules, you have to wrap the
# schedule in an OptionalSchedule for ruby/SWIG to understand the function
# you're trying to call
# Explicit via the GroundSurfacesGroup helper
grassGroup = openstudio.model.GroundSurfaceGroup(
    "GndSurfs:Grass",
    0.3,
    openstudio.model.OptionalSchedule(grassTempSch),
    openstudio.model.OptionalSchedule(grassReflSch),
)
spigs.addGroundSurfaceGroup(grassGroup)

parkingTempSch = openstudio.model.ScheduleConstant(model)
parkingTempSch.setName("GndSurfs:ParkingTemp")
parkingTempSch.setValue(17.0)
parkingReflSch = openstudio.model.ScheduleConstant(model)
parkingReflSch.setName("GndSurfs:ParkingRefl")
parkingReflSch.setValue(0.15)

# Shorthand helper
spigs.addGroundSurfaceGroup(
    "GndSurfs:Parking",
    0.1,
    openstudio.model.OptionalSchedule(parkingTempSch),
    openstudio.model.OptionalSchedule(parkingReflSch),
)

# API DEMO

# Demonstrate the api a bit more
assert spigs.numberofGroundSurfaceGroups() == 2

# You can navigate up and down
assert spigs.surfacePropertyLocalEnvironment().get() == localEnv
assert localEnv.surfacePropertyGroundSurfaces().get() == spigs

# Note that the groupIndex matches on Ground Surface name only
assert spigs.groundSurfaceGroupIndex(grassGroup).get() == spigs.groundSurfaceGroupIndex("GndSurfs:Grass").get()

# Also note that API enforces uniqueness of Ground Surface Name
# if I try to add another group with the same surface name, it overrides the
# values
spigs.addGroundSurfaceGroup(
    "GndSurfs:Parking",
    0.2,
    openstudio.model.OptionalSchedule(parkingTempSch),
    openstudio.model.OptionalSchedule(parkingReflSch),
)
assert spigs.numberofGroundSurfaceGroups() == 2
assert spigs.groundSurfaceGroups()[1].viewFactor() == 0.2

# Save the groups
groups = spigs.groundSurfaceGroups()

spigs.removeGroundSurfaceGroup(1)
assert spigs.numberofGroundSurfaceGroups() == 1

spigs.addGroundSurfaceGroup(
    "GndSurfs:Parking",
    0.1,
    openstudio.model.OptionalSchedule(parkingTempSch),
    openstudio.model.OptionalSchedule(parkingReflSch),
)
spigs.removeAllGroundSurfaceGroups()
assert spigs.numberofGroundSurfaceGroups() == 0

# Add back via the vector overload
spigs.addGroundSurfaceGroups(groups)
assert spigs.numberofGroundSurfaceGroups() == 2

g1 = spigs.groundSurfaceGroups()[0]
assert g1.groundSurfaceName() == "GndSurfs:Grass"
assert g1.viewFactor() == 0.3
assert g1.temperatureSchedule().is_initialized()
assert g1.temperatureSchedule().get() == grassTempSch
assert g1.reflectanceSchedule().is_initialized()
assert g1.reflectanceSchedule().get() == grassReflSch

g2 = spigs.getGroundSurfaceGroup(1).get()
assert g2.groundSurfaceName() == "GndSurfs:Parking"
assert g2.viewFactor() == 0.2
assert g2.temperatureSchedule().is_initialized()
assert g2.temperatureSchedule().get() == parkingTempSch
assert g2.reflectanceSchedule().is_initialized()
assert g2.reflectanceSchedule().get() == parkingReflSch

###############################################################################

# Now add one for the SubSurface as well
sslocalEnv = openstudio.model.SurfacePropertyLocalEnvironment(subSurface)
sslocalEnv.setName("#{subSurface.nameString()} LocalEnv")

sspigs = openstudio.model.SurfacePropertyGroundSurfaces(model)
sspigs.setName("#{subSurface.nameString()} GndSurfs")
# Assign it to the SurfaceProperty:LocalEnvironment
sslocalEnv.setSurfacePropertyGroundSurfaces(sspigs)

# We don't define the schedules
sspigs.addGroundSurfaceGroup("#{subSurface.nameString()} Gnd", 0.3)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
