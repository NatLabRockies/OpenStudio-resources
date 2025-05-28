import openstudio

from lib.baseline_model import BaselineModel

m = BaselineModel()

# make a 3 story, 100m X 50m, 3 zone building
m.add_geometry(length=100, width=50, num_floors=3, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
m.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
m.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type()

# add design days to the model (Chicago)
m.add_design_days()

# In order to produce more consistent results between different runs,
# we sort the zones by names (only one here anyways...)
zones = sorted(m.getThermalZones(), key=lambda z: z.nameString())
zone1 = zones[0]
zone2 = zones[1]
zone3 = zones[2]

# spaces
spaces1 = sorted(zone1.spaces(), key=lambda s: s.nameString())
spaces2 = sorted(zone2.spaces(), key=lambda s: s.nameString())
spaces3 = sorted(zone3.spaces(), key=lambda s: s.nameString())

# surfaces
sub_surfaces1 = []
surfaces1 = sorted(spaces1[0].surfaces(), key=lambda s: s.azimuth())
for surface in surfaces1:
    if surface.surfaceType() != "Wall":
        continue

    sub_surfaces1 += sorted(surface.subSurfaces(), key=lambda ss: ss.nameString())

sub_surfaces2 = []
surfaces2 = sorted(spaces2[0].surfaces(), key=lambda s: s.azimuth())
for surface in surfaces2:
    if surface.surfaceType() != "Wall":
        continue

    sub_surfaces2 += sorted(surface.subSurfaces(), key=lambda ss: ss.nameString())

sub_surfaces3 = []
surfaces3 = sorted(spaces3[0].surfaces(), key=lambda s: s.azimuth())
for surface in surfaces3:
    if surface.surfaceType() != "Wall":
        continue

    sub_surfaces3 += sorted(surface.subSurfaces(), key=lambda ss: ss.nameString())


# sub surfaces
sub_surface1 = sub_surfaces1[0]  # zone 1
sub_surface2 = sub_surfaces1[1]  # zone 1
sub_surface3 = sub_surfaces2[0]  # zone 2
sub_surface4 = sub_surfaces2[1]  # zone 2
sub_surface5 = sub_surfaces3[0]  # zone 3
sub_surface6 = sub_surfaces3[1]  # zone 3

# Use Ideal Air Loads
for z in zones:
    z.setUseIdealAirLoads(True)

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
blind1 = openstudio.model.Blind(m)
blind2 = openstudio.model.Blind(m)

# construction
simple_glazing = openstudio.model.SimpleGlazing(m)
construction1 = openstudio.model.Construction(m)
construction1.insertLayer(0, simple_glazing)

# shading controls
shading_control1 = openstudio.model.ShadingControl(blind1)
shading_control2 = openstudio.model.ShadingControl(blind1)
shading_control3 = openstudio.model.ShadingControl(blind2)
shading_control4 = openstudio.model.ShadingControl(construction1)

# add sub surface 1 to shading control 1
shading_control1.addSubSurface(sub_surface1)

# bulk add sub surfaces to shading control 1
sub_surfaces = openstudio.model.SubSurfaceVector()
for sub_surface in [sub_surface2]:
    sub_surfaces.append(sub_surface)

shading_control1.addSubSurfaces(sub_surfaces)

# add shading control to sub suface 1, sub surface 2
sub_surface1.addShadingControl(shading_control2)
sub_surface2.addShadingControl(shading_control2)

# bulk add shading controls to sub surface 3, sub surface 4
shading_controls = openstudio.model.ShadingControlVector()
for shading_control in [shading_control3]:
    shading_controls.append(shading_control)

sub_surface3.addShadingControls(shading_controls)
sub_surface4.addShadingControls(shading_controls)

# bulk add sub surface5, sub surface 6 to shading control 4
sub_surfaces = openstudio.model.SubSurfaceVector()
for sub_surface in [sub_surface5, sub_surface6]:
    sub_surfaces.append(sub_surface)

shading_control4.addSubSurfaces(sub_surfaces)

# save the OpenStudio model (.osm)
m.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
