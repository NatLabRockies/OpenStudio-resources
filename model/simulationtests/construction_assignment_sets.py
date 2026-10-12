# This tests the translation of the DefaultConstructionSets at every level (Space, SpaceType, BuildingStory, Building, Building SpaceType)
# to the E+ ConstructionAssignmentSets referenced by the E+ Space and Building objects.
# Every level gets its own uniquely named constructions, and the post-run check in model_tests.rb verifies that E+ resolved the same
# construction for every surface as when all constructions are written to the surfaces

import openstudio
from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 40m X 20m, 10 zone core/perimeter building
model.add_geometry(length=40, width=20, num_floors=2, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=19, cooling_setpoint=26)

# assign constructions from a local library to the walls/windows/etc. in the model: this is the Building level DefaultConstructionSet
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

building = model.getBuilding()
building_dcs = building.defaultConstructionSet().get()
building_space_type = building.spaceType().get()

base_ext_wall = building_dcs.defaultExteriorSurfaceConstructions().get().wallConstruction().get()
base_ext_roof = building_dcs.defaultExteriorSurfaceConstructions().get().roofCeilingConstruction().get()
base_ground_floor = building_dcs.defaultGroundContactSurfaceConstructions().get().floorConstruction().get()
base_window = building_dcs.defaultExteriorSubSurfaceConstructions().get().fixedWindowConstruction().get()


def make_construction(base, name):
    """Clone a construction under a unique name, so we can tell which level it was resolved from."""
    construction = base.clone(model).to_Construction().get()
    construction.setName(name)
    return construction


def make_dcs(name, ext_wall=None, ext_roof=None, ground_floor=None, window=None):
    """Make a partial DefaultConstructionSet, only filling the slots that are passed."""
    dcs = openstudio.model.DefaultConstructionSet(model)
    dcs.setName(name)
    if ext_wall is not None or ext_roof is not None:
        ext = openstudio.model.DefaultSurfaceConstructions(model)
        ext.setName(f"{name} Exterior Surface Constructions")
        if ext_wall is not None:
            ext.setWallConstruction(make_construction(base_ext_wall, ext_wall))
        if ext_roof is not None:
            ext.setRoofCeilingConstruction(make_construction(base_ext_roof, ext_roof))
        dcs.setDefaultExteriorSurfaceConstructions(ext)
    if ground_floor is not None:
        ground = openstudio.model.DefaultSurfaceConstructions(model)
        ground.setName(f"{name} Ground Contact Surface Constructions")
        ground.setFloorConstruction(make_construction(base_ground_floor, ground_floor))
        dcs.setDefaultGroundContactSurfaceConstructions(ground)
    if window is not None:
        ext_sub = openstudio.model.DefaultSubSurfaceConstructions(model)
        ext_sub.setName(f"{name} Exterior SubSurface Constructions")
        construction = make_construction(base_window, window)
        ext_sub.setFixedWindowConstruction(construction)
        ext_sub.setOperableWindowConstruction(construction)
        dcs.setDefaultExteriorSubSurfaceConstructions(ext_sub)
    return dcs


def get_space(name):
    return model.getSpaceByName(name).get()


# Building SpaceType: the Building set doesn't have a Ground Floor anymore, so it comes from the Building SpaceType set (all spaces have a
# defaulted SpaceType, except those using the Shared SpaceType below, for which the Building SpaceType is still the last level searched)
building_dcs.defaultGroundContactSurfaceConstructions().get().resetFloorConstruction()
building_space_type.setDefaultConstructionSet(make_dcs("Building SpaceType DCS", ground_floor="Building SpaceType Ground Floor"))

# BuildingStory: Story 1 exterior walls, shared by all the Story 1 spaces
model.getBuildingStoryByName("Story 1").get().setDefaultConstructionSet(make_dcs("Story 1 DCS", ext_wall="Story 1 Exterior Wall"))

# SpaceType: shared by spaces on both stories. On Story 1, its exterior wall wins over the Story 1 one
shared_space_type = building_space_type.clone(model).to_SpaceType().get()
shared_space_type.setName("Shared SpaceType")
shared_space_type.setDefaultConstructionSet(
    make_dcs("Shared SpaceType DCS", ext_wall="Shared SpaceType Exterior Wall", ext_roof="Shared SpaceType Exterior Roof")
)
for space_name in ["Story 1 North Perimeter Space", "Story 2 North Perimeter Space", "Story 2 South Perimeter Space"]:
    get_space(space_name).setSpaceType(shared_space_type)

# Space: only the windows, the exterior walls fall through to the Story 1 set, and the ground floor to the Building SpaceType one
get_space("Story 1 West Perimeter Space").setDefaultConstructionSet(make_dcs("Story 1 West Space DCS", window="Story 1 West Space Window"))

# Two spaces in the same zone, with different sets: when the E+ Spaces are not translated, they are combined
east_space = get_space("Story 2 East Perimeter Space")
east_space.setDefaultConstructionSet(make_dcs("Story 2 East Space DCS", ext_wall="Story 2 East Space Exterior Wall"))
east_zone = east_space.thermalZone().get()
core_zone = get_space("Story 2 Core Space").thermalZone().get()
east_space.setThermalZone(core_zone)
east_zone.remove()
core_zone.setName("Story 2 Core and East Thermal Zone")

# Use Ideal Air Loads
for z in sorted(model.getThermalZones(), key=lambda z: z.nameString()):
    z.setUseIdealAirLoads(True)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
