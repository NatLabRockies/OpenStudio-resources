# frozen_string_literal: true

# This is a test for SurfaceProperty:GroundSurfaces and
# SurfaceProperty:IncidentSolarMultiplier
# Loosely adapted from SurfacePropGroundSurfaces_LWR.idf
# and 1ZoneEvapCooler_4Win_incidentSolarMultiplier.idf (from E+ 22.2.0)

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
zone_ideal_loads = OpenStudio::Model::ZoneHVACIdealLoadsAirSystem.new(model)
zone_ideal_loads.addToThermalZone(z)

# Get the first Outdoors Wall surface, sorting by azimuth to ensure consistency just in case
surfaces = model.getSurfaces.select { |s| (s.outsideBoundaryCondition == 'Outdoors') && (s.surfaceType == 'Wall') }.sort_by(&:azimuth)
raise if surfaces.empty?

surface = surfaces[0]

# Get its window
raise if surface.subSurfaces.empty?

subSurface = surface.subSurfaces[0]

###############################################################################
#                   SurfacePropertyIncidentSolarMultiplier                    #
###############################################################################

spism = OpenStudio::Model::SurfacePropertyIncidentSolarMultiplier.new(subSurface)
spism.setIncidentSolarMultiplier(0.5)

solarMultConstSch = OpenStudio::Model::ScheduleConstant.new(model)
solarMultConstSch.setName('SolarMultConstSch')
solarMultConstSch.setValue(1.0)
spism.setIncidentSolarMultiplierSchedule(solarMultConstSch)

# API DEMO
# NOTE: you can access an OptionalSurfacePropertyIncidentSolarMultiplier from any subsurface
raise if subSurface.surfacePropertyIncidentSolarMultiplier.get != spism
raise if spism.subSurface != subSurface

###############################################################################
#                        SurfacePropertyGroundSurfaces                        #
###############################################################################

localEnv = OpenStudio::Model::SurfacePropertyLocalEnvironment.new(surface)
localEnv.setName("#{surface.nameString} LocalEnv")

spigs = OpenStudio::Model::SurfacePropertyGroundSurfaces.new(model)
spigs.setName("#{surface.nameString} GndSurfs")
localEnv.setSurfacePropertyGroundSurfaces(spigs)

grassTempSch = OpenStudio::Model::ScheduleConstant.new(model)
grassTempSch.setName('GndSurfs:GrassTemp')
grassTempSch.setValue(12.0)
grassReflSch = OpenStudio::Model::ScheduleConstant.new(model)
grassReflSch.setName('GndSurfs:GrassRefl')
grassReflSch.setValue(0.2)

# NOTE: because we allow not passing any of two schedules, you have to wrap the
# schedule in an OptionalSchedule for ruby/SWIG to understand the function
# you're trying to call
# Explicit via the GroundSurfacesGroup helper
grassGroup = OpenStudio::Model::GroundSurfaceGroup.new(
  'GndSurfs:Grass', 0.3,
  OpenStudio::Model::OptionalSchedule.new(grassTempSch),
  OpenStudio::Model::OptionalSchedule.new(grassReflSch)
)
spigs.addGroundSurfaceGroup(grassGroup)

parkingTempSch = OpenStudio::Model::ScheduleConstant.new(model)
parkingTempSch.setName('GndSurfs:ParkingTemp')
parkingTempSch.setValue(17.0)
parkingReflSch = OpenStudio::Model::ScheduleConstant.new(model)
parkingReflSch.setName('GndSurfs:ParkingRefl')
parkingReflSch.setValue(0.15)

# Shorthand helper
spigs.addGroundSurfaceGroup('GndSurfs:Parking', 0.1,
                            OpenStudio::Model::OptionalSchedule.new(parkingTempSch),
                            OpenStudio::Model::OptionalSchedule.new(parkingReflSch))

# API DEMO

# Demonstrate the api a bit more
raise if spigs.numberofGroundSurfaceGroups != 2

# You can navigate up and down
raise if spigs.surfacePropertyLocalEnvironment.get != localEnv
raise if localEnv.surfacePropertyGroundSurfaces.get != spigs

# Note that the groupIndex matches on Ground Surface name only
raise if spigs.groundSurfaceGroupIndex(grassGroup).get != spigs.groundSurfaceGroupIndex('GndSurfs:Grass').get

# Also note that API enforces uniqueness of Ground Surface Name
# if I try to add another group with the same surface name, it overrides the
# values
spigs.addGroundSurfaceGroup('GndSurfs:Parking', 0.2,
                            OpenStudio::Model::OptionalSchedule.new(parkingTempSch),
                            OpenStudio::Model::OptionalSchedule.new(parkingReflSch))
raise if spigs.numberofGroundSurfaceGroups != 2
raise if spigs.groundSurfaceGroups[1].viewFactor != 0.2

# Save the groups
groups = spigs.groundSurfaceGroups

spigs.removeGroundSurfaceGroup(1)
raise if spigs.numberofGroundSurfaceGroups != 1

spigs.addGroundSurfaceGroup('GndSurfs:Parking', 0.1,
                            OpenStudio::Model::OptionalSchedule.new(parkingTempSch),
                            OpenStudio::Model::OptionalSchedule.new(parkingReflSch))
spigs.removeAllGroundSurfaceGroups
raise if spigs.numberofGroundSurfaceGroups != 0

# Add back via the vector overload
spigs.addGroundSurfaceGroups(groups)
raise if spigs.numberofGroundSurfaceGroups != 2

g1 = spigs.groundSurfaceGroups[0]
raise if g1.groundSurfaceName != 'GndSurfs:Grass'
raise if g1.viewFactor != 0.3
raise if g1.temperatureSchedule.empty?
raise if g1.temperatureSchedule.get != grassTempSch
raise if g1.reflectanceSchedule.empty?
raise if g1.reflectanceSchedule.get != grassReflSch

g2 = spigs.getGroundSurfaceGroup(1).get
raise if g2.groundSurfaceName != 'GndSurfs:Parking'
raise if g2.viewFactor != 0.2
raise if g2.temperatureSchedule.empty?
raise if g2.temperatureSchedule.get != parkingTempSch
raise if g2.reflectanceSchedule.empty?
raise if g2.reflectanceSchedule.get != parkingReflSch

###############################################################################

# Now add one for the SubSurface as well
sslocalEnv = OpenStudio::Model::SurfacePropertyLocalEnvironment.new(subSurface)
sslocalEnv.setName("#{subSurface.nameString} LocalEnv")

sspigs = OpenStudio::Model::SurfacePropertyGroundSurfaces.new(model)
sspigs.setName("#{subSurface.nameString} GndSurfs")
# Assign it to the SurfaceProperty:LocalEnvironment
sslocalEnv.setSurfacePropertyGroundSurfaces(sspigs)

# We don't define the schedules
sspigs.addGroundSurfaceGroup("#{subSurface.nameString} Gnd", 0.3)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
