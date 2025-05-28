# frozen_string_literal: true

# This is a test for SurfaceProperty:LocalEnvironment and
# SurfaceProperty:SurroundingSurfaces
# Loosely adapted from SurfacePropTest_SurfLWR.idf (from E+ 9.6)

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 19,
                        'cooling_setpoint' => 26 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# There's only one zone here...
zones = model.getThermalZones.sort_by { |z| z.name.to_s }
z = zones[0]
z.setUseIdealAirLoads(true)

# Get the first Outdoors Wall surface, sorting by azimuth to ensure consistency just in case
surfaces = model.getSurfaces.select { |s| (s.outsideBoundaryCondition == 'Outdoors') && (s.surfaceType == 'Wall') }.sort_by(&:azimuth)
surface = surfaces[0]

# Get its window
subSurface = surface.subSurfaces[0]

localEnv = OpenStudio::Model::SurfacePropertyLocalEnvironment.new(surface)
localEnv.setName("#{surface.nameString} LocalEnv")

externalShadingSch = OpenStudio::Model::ScheduleConstant.new(model)
localEnv.setExternalShadingFractionSchedule(externalShadingSch)
raise if localEnv.externalShadingFractionSchedule.empty?

###############################################################################
#                              A P I    D E M O                               #
###############################################################################

# NOTE: you can access an OptionalSurfacePropertyLocalEnvironment from any
# surface and subsurfaces
raise if surface.surfacePropertyLocalEnvironment.get != localEnv

# The API also enforces uniqueness at this level: there can be only one
# SurfacePropertyLocalEnvironment pointing to a single Surface/SubSurface
# If you try to assign a second via the SurfacePropertyLocalEnvironment(surface) ctor or calling
# SurfacePropertyLocalEnvironment::setExteriorSurface(surface) and surface
# already has one, then the existing one is **REMOVED**
raise if model.getSurfacePropertyLocalEnvironments.size != 1

localEnv = OpenStudio::Model::SurfacePropertyLocalEnvironment.new(surface)
localEnv.setName("#{surface.nameString} LocalEnv")
raise if model.getSurfacePropertyLocalEnvironments.size != 1
# as you can see, this one does NOT have an external shading fraction schedule
raise if !localEnv.externalShadingFractionSchedule.empty?

###############################################################################

s_sp = OpenStudio::Model::SurfacePropertySurroundingSurfaces.new(model)
s_sp.setName("#{surface.nameString} SrdSurfs")
# Assign it to the SurfaceProperty:LocalEnvironment
localEnv.setSurfacePropertySurroundingSurfaces(s_sp)

# If blank in E+, this is autocalculated. Here we have it explicitly
s_sp.autocalculateSkyViewFactor
s_sp.setSkyViewFactor(0.1)

skyTempSch = OpenStudio::Model::ScheduleConstant.new(model)
s_sp.setSkyTemperatureSchedule(skyTempSch)
s_sp.resetSkyTemperatureSchedule

s_sp.autocalculateGroundViewFactor
s_sp.setGroundViewFactor(0.0)

groundTempSch = OpenStudio::Model::ScheduleConstant.new(model)
s_sp.setGroundTemperatureSchedule(groundTempSch)
s_sp.resetGroundTemperatureSchedule

tempSch1 = OpenStudio::Model::ScheduleRuleset.new(model)
tempSch1.setName('Surface Temperature')
tempSch1.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 10.0)
tempSch1_july_to_dec_rule = OpenStudio::Model::ScheduleRule.new(tempSch1)
tempSch1_july_to_dec_rule.setStartDate(OpenStudio::Date.new('July'.to_MonthOfYear, 1))
tempSch1_july_to_dec_rule.setEndDate(OpenStudio::Date.new('December'.to_MonthOfYear, 31))
tempSch1_july_to_dec_rule.daySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), -10)

# Add two groups
# Group 1: the explicit SurroundingSurfaceGroup approach
group1 = OpenStudio::Model::SurroundingSurfaceGroup.new('SurroundingSurface1', 0.5, tempSch1)
s_sp.addSurroundingSurfaceGroup(group1)

# Group 2: via the helper
s_sp.addSurroundingSurfaceGroup('SurroundingSurface2', 0.3, tempSch1)

###############################################################################
#                              A P I    D E M O                               #
###############################################################################

# Demonstrate the api a bit more
raise if s_sp.numberofSurroundingSurfaceGroups != 2

# You can navigate up and down
raise if localEnv.surfacePropertySurroundingSurfaces.get != s_sp
raise if s_sp.surfacePropertyLocalEnvironment.get != localEnv

# Note that the gorupIndex matches on Surrounding Surface name only
raise if s_sp.surroundingSurfaceGroupIndex(group1).get != s_sp.surroundingSurfaceGroupIndex('SurroundingSurface1').get

# Also note that API enforces uniqueness of Surrouding Surface Name
# if I try to add another group with the same surface name, it overrides the
# values
s_sp.addSurroundingSurfaceGroup('SurroundingSurface2', 0.4, tempSch1)
raise if s_sp.numberofSurroundingSurfaceGroups != 2
raise if s_sp.surroundingSurfaceGroups[1].viewFactor != 0.4

# Save the groups
groups = s_sp.surroundingSurfaceGroups

s_sp.removeSurroundingSurfaceGroup(1)
raise if s_sp.numberofSurroundingSurfaceGroups != 1

s_sp.addSurroundingSurfaceGroup('SurroundingSurface2', 0.4, tempSch1)
s_sp.removeAllSurroundingSurfaceGroups
raise if s_sp.numberofSurroundingSurfaceGroups != 0

# Add back via the vector overload
s_sp.addSurroundingSurfaceGroups(groups)
raise if s_sp.numberofSurroundingSurfaceGroups != 2

g1 = s_sp.surroundingSurfaceGroups[0]

raise if g1.surroundingSurfaceName != 'SurroundingSurface1'
raise if g1.viewFactor != 0.5
raise if g1.temperatureSchedule != tempSch1

g2 = s_sp.getSurroundingSurfaceGroup(1).get
raise if g2.surroundingSurfaceName != 'SurroundingSurface2'
raise if g2.viewFactor != 0.4
raise if g2.temperatureSchedule != tempSch1

###############################################################################

# Now add one for the SubSurface as well
sslocalEnv = OpenStudio::Model::SurfacePropertyLocalEnvironment.new(subSurface)
sslocalEnv.setName("#{subSurface.nameString} LocalEnv")

ss_sp = OpenStudio::Model::SurfacePropertySurroundingSurfaces.new(model)
ss_sp.setName("#{subSurface.nameString} SrdSurfs")
# Assign it to the SurfaceProperty:LocalEnvironment
sslocalEnv.setSurfacePropertySurroundingSurfaces(ss_sp)

ss_sp.setSkyViewFactor(0.5)
ss_sp.setGroundViewFactor(0.3)
ss_sp.addSurroundingSurfaceGroup('SurroundingSurface1', 0.2, tempSch1)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
