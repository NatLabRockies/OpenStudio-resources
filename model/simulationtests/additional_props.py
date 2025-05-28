import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 01, PTAC, Residential
model.add_hvac(ashrae_sys_num="01")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# Get spaces, ordered by name to ensure consistency
spaces = sorted(model.getSpaces(), key=lambda s: s.nameString())

# create 8in concrete material
material = openstudio.model.StandardOpaqueMaterial(model)
material.setThickness(0.2032)
material.setConductivity(1.3114056)
material.setDensity(2242.8)
material.setSpecificHeat(837.4)

# create the additional properties object
additional_properties = material.additionalProperties()
additional_properties.setFeature("isNiceMaterial", True)

# create construction with the material
construction = openstudio.model.Construction(model)
construction.insertLayer(0, material)

# create the additional properties object
additional_properties = construction.additionalProperties()
additional_properties.setFeature("isNiceConstruction", True)

# update all additional properties objects
for add_props in model.getAdditionalPropertiess():
    # retrieve an additional properties object and set a new feature
    add_props.setFeature("newFeature", 1)

    # retrieve the parent object from the additional properties object
    model_object = add_props.modelObject()
    if model_object.to_StandardOpaqueMaterial().is_initialized():
        material = model_object.to_StandardOpaqueMaterial().get()
        material.setThickness(0.3)

    if model_object.to_Construction().is_initialized():
        material = openstudio.model.StandardOpaqueMaterial(model)
        material.setThickness(0.2032)
        material.setConductivity(1.3114056)
        material.setDensity(2242.8)
        material.setSpecificHeat(837.4)
        construction = model_object.to_Construction().get()
        construction.insertLayer(1, material)


unit = openstudio.model.BuildingUnit(model)
for space in spaces:
    space.setBuildingUnit(unit)


additional_properties = unit.additionalProperties()
additional_properties.setFeature("isNiceUnit", True)

if "isNiceUnit" in unit.suggestedFeatures():  # check backwards compatibility:
    unit.setFeature("hasSuggestedFeature1", True)


if "isNiceUnit" in unit.additionalProperties().suggestedFeatureNames():
    additional_properties.setFeature("hasSuggestedFeature2", True)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
