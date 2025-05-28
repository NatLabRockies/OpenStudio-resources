# This is a test for SurfaceProperty:LocalEnvironment and
# SurfaceProperty:SurroundingSurfaces
# Loosely adapted from SurfacePropTest_SurfLWR.idf (from E+ 9.6)

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
z.setUseIdealAirLoads(True)

# Get the first Outdoors Wall surface, sorting by azimuth to ensure consistency just in case
surfaces = sorted(
    [s for s in model.getSurfaces() if s.surfaceType() == "Wall" and s.outsideBoundaryCondition() == "Outdoors"],
    key=lambda s: s.azimuth(),
)
assert surfaces
surface = surfaces[0]

# Get its window
subSurface = surface.subSurfaces()[0]

localEnv = openstudio.model.SurfacePropertyLocalEnvironment(surface)
localEnv.setName("#{surface.nameString()} LocalEnv")

externalShadingSch = openstudio.model.ScheduleConstant(model)
localEnv.setExternalShadingFractionSchedule(externalShadingSch)
assert localEnv.externalShadingFractionSchedule().is_initialized()

###############################################################################
#                              A P I    D E M O                               #
###############################################################################

# NOTE: you can access an OptionalSurfacePropertyLocalEnvironment from any
# surface and subsurfaces
assert surface.surfacePropertyLocalEnvironment().get() == localEnv

# The API also enforces uniqueness at this level: there can be only one
# SurfacePropertyLocalEnvironment pointing to a single Surface/SubSurface
# If you try to assign a second via the SurfacePropertyLocalEnvironment(surface) ctor or calling
# SurfacePropertyLocalEnvironment.setExteriorSurface(surface) and surface
# already has one, then the existing one is **REMOVED**
assert len(model.getSurfacePropertyLocalEnvironments()) == 1

localEnv = openstudio.model.SurfacePropertyLocalEnvironment(surface)
localEnv.setName("#{surface.nameString()} LocalEnv")
assert len(model.getSurfacePropertyLocalEnvironments()) == 1
# as you can see, this one does NOT have an external shading fraction schedule
assert not localEnv.externalShadingFractionSchedule().is_initialized()

###############################################################################

s_sp = openstudio.model.SurfacePropertySurroundingSurfaces(model)
s_sp.setName("#{surface.nameString()} SrdSurfs")
# Assign it to the SurfaceProperty:LocalEnvironment
localEnv.setSurfacePropertySurroundingSurfaces(s_sp)

# If blank in E+, this is autocalculated. Here we have it explicitly
s_sp.autocalculateSkyViewFactor()
s_sp.setSkyViewFactor(0.1)

skyTempSch = openstudio.model.ScheduleConstant(model)
s_sp.setSkyTemperatureSchedule(skyTempSch)
s_sp.resetSkyTemperatureSchedule()

s_sp.autocalculateGroundViewFactor()
s_sp.setGroundViewFactor(0.0)

groundTempSch = openstudio.model.ScheduleConstant(model)
s_sp.setGroundTemperatureSchedule(groundTempSch)
s_sp.resetGroundTemperatureSchedule()

tempSch1 = openstudio.model.ScheduleRuleset(model)
tempSch1.setName("Surface Temperature")
tempSch1.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 10.0)
tempSch1_july_to_dec_rule = openstudio.model.ScheduleRule(tempSch1)
tempSch1_july_to_dec_rule.setStartDate(openstudio.Date(openstudio.MonthOfYear("July"), 1))
tempSch1_july_to_dec_rule.setEndDate(openstudio.Date(openstudio.MonthOfYear("December"), 31))
tempSch1_july_to_dec_rule.daySchedule().addValue(openstudio.Time(0, 24, 0, 0), -10)

# Add two groups
# Group 1: the explicit SurroundingSurfaceGroup approach
group1 = openstudio.model.SurroundingSurfaceGroup("SurroundingSurface1", 0.5, tempSch1)
s_sp.addSurroundingSurfaceGroup(group1)

# Group 2: via the helper
s_sp.addSurroundingSurfaceGroup("SurroundingSurface2", 0.3, tempSch1)

###############################################################################
#                              A P I    D E M O                               #
###############################################################################

# Demonstrate the api a bit more
assert s_sp.numberofSurroundingSurfaceGroups() == 2

# You can navigate up and down
assert localEnv.surfacePropertySurroundingSurfaces().get() == s_sp
assert s_sp.surfacePropertyLocalEnvironment().get() == localEnv

# Note that the gorupIndex matches on Surrounding Surface name only
assert s_sp.surroundingSurfaceGroupIndex(group1).get() == s_sp.surroundingSurfaceGroupIndex("SurroundingSurface1").get()

# Also note that API enforces uniqueness of Surrouding Surface Name
# if I try to add another group with the same surface name, it overrides the
# values
s_sp.addSurroundingSurfaceGroup("SurroundingSurface2", 0.4, tempSch1)
assert s_sp.numberofSurroundingSurfaceGroups() == 2
assert s_sp.surroundingSurfaceGroups()[1].viewFactor() == 0.4

# Save the groups
groups = s_sp.surroundingSurfaceGroups()

s_sp.removeSurroundingSurfaceGroup(1)
assert s_sp.numberofSurroundingSurfaceGroups() == 1

s_sp.addSurroundingSurfaceGroup("SurroundingSurface2", 0.4, tempSch1)
s_sp.removeAllSurroundingSurfaceGroups()
assert s_sp.numberofSurroundingSurfaceGroups() == 0

# Add back via the vector overload
s_sp.addSurroundingSurfaceGroups(groups)
assert s_sp.numberofSurroundingSurfaceGroups() == 2

g1 = s_sp.surroundingSurfaceGroups()[0]

assert g1.surroundingSurfaceName() == "SurroundingSurface1"
assert g1.viewFactor() == 0.5
assert g1.temperatureSchedule() == tempSch1

g2 = s_sp.getSurroundingSurfaceGroup(1).get()
assert g2.surroundingSurfaceName() == "SurroundingSurface2"
assert g2.viewFactor() == 0.4
assert g2.temperatureSchedule() == tempSch1

###############################################################################

# Now add one for the SubSurface as well
sslocalEnv = openstudio.model.SurfacePropertyLocalEnvironment(subSurface)
sslocalEnv.setName("#{subSurface.nameString()} LocalEnv")

ss_sp = openstudio.model.SurfacePropertySurroundingSurfaces(model)
ss_sp.setName("#{subSurface.nameString()} SrdSurfs")
# Assign it to the SurfaceProperty:LocalEnvironment
sslocalEnv.setSurfacePropertySurroundingSurfaces(ss_sp)

ss_sp.setSkyViewFactor(0.5)
ss_sp.setGroundViewFactor(0.3)
ss_sp.addSurroundingSurfaceGroup("SurroundingSurface1", 0.2, tempSch1)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
