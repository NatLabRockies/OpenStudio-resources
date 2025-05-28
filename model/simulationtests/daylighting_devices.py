import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

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

thermal_zones = sorted(model.getThermalZones(), key=lambda tz: tz.nameString())
thermal_zone = thermal_zones[0]
thermal_zone.setUseIdealAirLoads(True)
spaces = sorted(thermal_zone.spaces(), key=lambda s: s.nameString())

windows = []
for space in spaces:
    surfaces = sorted(space.surfaces(), key=lambda s: s.azimuth())
    for surface in surfaces:
        sub_surfaces = sorted(surface.subSurfaces(), key=lambda ss: ss.nameString())
        for sub_surface in sub_surfaces:
            if sub_surface.subSurfaceType() != "FixedWindow":
                continue

            windows.append(sub_surface)


window1 = windows[1]  # azimuth is 180 degrees
window2 = windows[2]

###############################################################################
#                          DaylightingDeviceTubular                           #
###############################################################################

material = openstudio.model.StandardOpaqueMaterial(model)
material.setThickness(0.2032)
material.setConductivity(1.3114056)
material.setDensity(2242.8)
material.setSpecificHeat(837.4)
construction = openstudio.model.Construction(model)
construction.insertLayer(0, material)

# Azimuth here is 180 degrees as well
points = openstudio.Point3dVector()
points.append(openstudio.Point3d(0, 1, 0.2))
points.append(openstudio.Point3d(0, 0, 0.2))
points.append(openstudio.Point3d(1, 0, 0.2))
points.append(openstudio.Point3d(1, 1, 0.2))
dome = openstudio.model.SubSurface(points, model)
dome.setName("Dome")
dome.setSubSurfaceType("TubularDaylightDome")
dome.setSurface(window1.surface().get())

points = openstudio.Point3dVector()
points.append(openstudio.Point3d(0, 1, 0.1))
points.append(openstudio.Point3d(0, 0, 0.1))
points.append(openstudio.Point3d(1, 0, 0.1))
points.append(openstudio.Point3d(1, 1, 0.1))
diffuser = openstudio.model.SubSurface(points, model)
diffuser.setName("Diffuser")
diffuser.setSubSurfaceType("TubularDaylightDiffuser")
diffuser.setSurface(window1.surface().get())

tubular = openstudio.model.DaylightingDeviceTubular(dome, diffuser, construction)
tubular.setDiameter(1.1)
tubular.setTotalLength(1.4)
tubular.setEffectiveThermalResistance(0.28)

transition_zone = openstudio.model.TransitionZone(thermal_zone, 1)
tubular.addTransitionZone(transition_zone)

###############################################################################
#                         DaylightingDeviceLightWell                          #
###############################################################################

sub_surface = window1

light_well = openstudio.model.DaylightingDeviceLightWell(sub_surface)
light_well.setHeightofWell(1.2)
light_well.setPerimeterofBottomofWell(12.0)
light_well.setAreaofBottomofWell(9.0)
light_well.setVisibleReflectanceofWellWalls(0.7)

###############################################################################
#                           DaylightingDeviceShelf                            #
###############################################################################

sub_surface = window2

#### Outside Shelf
# This shading sf must have a construction as  it's used as an outside shelf
projectionFactor = 0.7
# Note that E+ will fatal is the width of the wndow and outside shelf do not
# match
offsetFraction = 0
shadingSurface = sub_surface.addOverhangByProjectionFactor(projectionFactor, offsetFraction).get()
shadingSurface.setName("Outside Shelf Shading Surface")
shadingMat = openstudio.model.StandardOpaqueMaterial(model)
shadingMat.setName("C12 - 2 IN HW CONCRETE - PAINTED WHITE")
shadingMat.setRoughness("MediumRough")
shadingMat.setThickness(openstudio.convert(2, "in", "m").get())
shadingMat.setConductivity(1.729577)
shadingMat.setDensity(2242.585)
shadingMat.setSpecificHeat(836.8)
shadingMat.setThermalAbsorptance(0.9)
shadingMat.setSolarAbsorptance(0.3)
shadingMat.setVisibleAbsorptance(0.3)

shadingConstruction = openstudio.model.Construction([shadingMat])
shadingConstruction.setName("Outside Shelf Construction")

shadingSurface.setConstruction(shadingConstruction)

#### Inside shelf
partitionGroup = openstudio.model.InteriorPartitionSurfaceGroup(model)
partitionGroup.setSpace(sub_surface.space().get())

# We'll mimic what the add addOverhangByProjectionFactor does to create a
# symetrical (w/ respect to window plane) inside shelf
# so in the end it looks like this from the side
# out    in
#  v     v
# ___ | ___
#     ^
#    window
vertices = sub_surface.vertices()
transformation = openstudio.Transformation.alignFace(vertices)
faceVertices = transformation.inverse() * vertices

# new coordinate system has z' in direction of outward normal, y' is up
xmin = min([x.x() for x in faceVertices])
xmax = max([x.x() for x in faceVertices])
ymin = min([x.y() for x in faceVertices])
ymax = max([x.y() for x in faceVertices])

if (xmin > xmax) or (ymin > ymax):
    raise ValueError("Not expected")

offset = offsetFraction * (ymax - ymin)
depth = projectionFactor * (offset + (ymax - ymin))

interiorVertices = openstudio.Point3dVector()
# Make them counterclockwise order
interiorVertices.append(
    openstudio.Point3d(xmax + offset, ymax + offset, -depth)
)  # Inverse of the shading surface (+depth)
interiorVertices.append(
    openstudio.Point3d(xmin - offset, ymax + offset, -depth)
)  # Inverse of the shading surface (+depth)
interiorVertices.append(openstudio.Point3d(xmin - offset, ymax + offset, 0))
interiorVertices.append(openstudio.Point3d(xmax + offset, ymax + offset, 0))

interiorPts = transformation * interiorVertices

inside_shelf = openstudio.model.InteriorPartitionSurface(interiorPts, model)
inside_shelf.setName("Inside Shelf Partition Surface")
inside_shelf.setInteriorPartitionSurfaceGroup(partitionGroup)

#### Shelf itself
shelf = openstudio.model.DaylightingDeviceShelf(sub_surface)
shelf.setName("DaylightingDeviceShelf")
shelf.setInsideShelf(inside_shelf)
shelf.setOutsideShelf(shadingSurface)
# Will be automacilly calculated
shelf.resetViewFactortoOutsideShelf()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
