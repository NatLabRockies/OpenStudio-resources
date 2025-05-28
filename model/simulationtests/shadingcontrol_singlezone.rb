# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

m = BaselineModel.new

# make a 3 story, 100m X 50m, 3 zone building
m.add_geometry({ 'length' => 100,
                 'width' => 50,
                 'num_floors' => 3,
                 'floor_to_floor_height' => 4,
                 'plenum_height' => 0,
                 'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
m.add_windows({ 'wwr' => 0.4,
                'offset' => 1,
                'application_type' => 'Above Floor' })

# add thermostats
m.add_thermostats({ 'heating_setpoint' => 24,
                    'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type

# add design days to the model (Chicago)
m.add_design_days

# In order to produce more consistent results between different runs,
# we sort the zones by names (only one here anyways...)
zones = m.getThermalZones.sort_by(&:nameString)
zone1 = zones[0]
zone2 = zones[1]
zone3 = zones[2]

# spaces
spaces1 = zone1.spaces.sort_by(&:nameString)
spaces2 = zone2.spaces.sort_by(&:nameString)
spaces3 = zone3.spaces.sort_by(&:nameString)

# surfaces
sub_surfaces1 = []
surfaces1 = spaces1[0].surfaces.sort_by(&:azimuth)
surfaces1.each do |surface|
  next if surface.surfaceType != 'Wall'

  sub_surfaces1 += surface.subSurfaces.sort_by(&:nameString)
end
sub_surfaces2 = []
surfaces2 = spaces2[0].surfaces.sort_by(&:azimuth)
surfaces2.each do |surface|
  next if surface.surfaceType != 'Wall'

  sub_surfaces2 += surface.subSurfaces.sort_by(&:nameString)
end
sub_surfaces3 = []
surfaces3 = spaces3[0].surfaces.sort_by(&:azimuth)
surfaces3.each do |surface|
  next if surface.surfaceType != 'Wall'

  sub_surfaces3 += surface.subSurfaces.sort_by(&:nameString)
end

# sub surfaces
sub_surface1 = sub_surfaces1[0] # zone 1
sub_surface2 = sub_surfaces1[1] # zone 1
sub_surface3 = sub_surfaces2[0] # zone 2
sub_surface4 = sub_surfaces2[1] # zone 2
sub_surface5 = sub_surfaces3[0] # zone 3
sub_surface6 = sub_surfaces3[1] # zone 3

# Use Ideal Air Loads
zones.each { |z| z.setUseIdealAirLoads(true) }

# SHADING CONTROL 1 (BLIND 1)
# SUB SURFACE 1 (ZONE 1)
# SUB SURFACE 2 (ZONE 1)
# SHADING CONTROL 2 (BLIND 1)
# SUB SURFACE 1 (ZONE 1)
# SUB SURFACE 2 (ZONE 1)
# SHADING CONTROL 3 (BLIND 2)
# SUB SURFACE 3 (ZONE 2)
# SUB SURFACE 4 (ZONE 2)
# SHADING CONTROL 4 (CONSTRUCTION 1)
# SUB SURFACE 5 (ZONE 3)
# SUB SURFACE 6 (ZONE 3)

# shading materials
blind1 = OpenStudio::Model::Blind.new(m)
blind2 = OpenStudio::Model::Blind.new(m)

# construction
simple_glazing = OpenStudio::Model::SimpleGlazing.new(m)
construction1 = OpenStudio::Model::Construction.new(m)
construction1.insertLayer(0, simple_glazing)

# shading controls
shading_control1 = OpenStudio::Model::ShadingControl.new(blind1)
shading_control2 = OpenStudio::Model::ShadingControl.new(blind1)
shading_control3 = OpenStudio::Model::ShadingControl.new(blind2)
shading_control4 = OpenStudio::Model::ShadingControl.new(construction1)

# add sub surface 1 to shading control 1
shading_control1.addSubSurface(sub_surface1)

# bulk add sub surfaces to shading control 1
sub_surfaces = OpenStudio::Model::SubSurfaceVector.new
[sub_surface2].each do |sub_surface|
  sub_surfaces << sub_surface
end
shading_control1.addSubSurfaces(sub_surfaces)

# add shading control to sub suface 1, sub surface 2
sub_surface1.addShadingControl(shading_control2)
sub_surface2.addShadingControl(shading_control2)

# bulk add shading controls to sub surface 3, sub surface 4
shading_controls = OpenStudio::Model::ShadingControlVector.new
[shading_control3].each do |shading_control|
  shading_controls << shading_control
end
sub_surface3.addShadingControls(shading_controls)
sub_surface4.addShadingControls(shading_controls)

# bulk add sub surface5, sub surface 6 to shading control 4
sub_surfaces = OpenStudio::Model::SubSurfaceVector.new
[sub_surface5, sub_surface6].each do |sub_surface|
  sub_surfaces << sub_surface
end
shading_control4.addSubSurfaces(sub_surfaces)

# save the OpenStudio model (.osm)
m.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                        'osm_name' => 'in.osm' })
