import math

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 50m X 50m, 5 zone core/perimeter building
model.add_geometry(length=50, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=6)

# Get spaces, ordered by name to ensure consistency
spaces = sorted(model.getSpaces(), key=lambda s: s.nameString())

# collapse all spaces into one thermal zone
thermalZone = None
for space in spaces:
    if thermalZone:
        temp = space.thermalZone().get()
        space.setThermalZone(thermalZone)
        temp.remove()
    else:
        thermalZone = space.thermalZone().get()


# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# make construction for interior surfaces

# materialName = "1/2IN Gypsum"
materialName = "MAT-CC05 4 HW CONCRETE"
# materialName = "Metal Decking"

interiorMaterial = None
for material in model.getStandardOpaqueMaterials():
    if material.nameString() == materialName:
        interiorMaterial = material
        break


interiorConstruction = openstudio.model.Construction(model)
interiorConstruction.setName("Interior Partition Construction")
interiorConstruction.insertLayer(0, interiorMaterial)

# turn this on so we get ugly names and sorting order changes
# model.setFastNaming(true)

# add some interior partition surfaces
fractionOfExteriorSurfaceArea = 0.1
for space in spaces:
    interiorGroup = openstudio.model.InteriorPartitionSurfaceGroup(model)
    interiorGroup.setSpace(space)

    heights = [1, 3, 3, 1]
    lengths = [1, 3, 1, 3]
    dir_x = [1, 0, -1, 0]
    dir_y = [0, 1, 0, -1]
    x = 1
    y = 1
    interiorArea = 0
    for i in range(len(heights)):
        new_x = x + lengths[i] * dir_x[i]
        new_y = y + lengths[i] * dir_y[i]
        points = openstudio.Point3dVector()
        points.append(openstudio.Point3d(x, y, 0))
        points.append(openstudio.Point3d(new_x, new_y, 0))
        points.append(openstudio.Point3d(new_x, new_y, heights[i]))
        points.append(openstudio.Point3d(x, y, heights[i]))
        interiorSurface = openstudio.model.InteriorPartitionSurface(points, model)
        interiorSurface.setInteriorPartitionSurfaceGroup(interiorGroup)
        interiorSurface.setConverttoInternalMass(True)
        interiorSurface.setConstruction(interiorConstruction)

        x = new_x
        y = new_y
        interiorArea += interiorSurface.grossArea()

    surfaceArea = 0
    for surface in space.surfaces():
        surfaceArea += surface.grossArea()

    multiplier = fractionOfExteriorSurfaceArea * surfaceArea / interiorArea
    interiorGroup.setMultiplier(math.ceil(multiplier))


# turn this off
# model.setFastNaming(false)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 01, PTAC, Residential
model.add_hvac(ashrae_sys_num="01")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
