# This tests the classes that derive from ExteriorLoadDefinition and ExteriorLoadInstance

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

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

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# Use Ideal Air Loads
for z in zones:
    z.setUseIdealAirLoads(True)

mat_roof = openstudio.model.RoofVegetation(model)
mat_roof.setName("Green Roof Material")

# Hardset all the default properties of the object
mat_roof.setHeightofPlants(0.2)
mat_roof.setLeafAreaIndex(1.0)
mat_roof.setLeafReflectivity(0.22)
mat_roof.setLeafEmissivity(0.95)
mat_roof.setMinimumStomatalResistance(180.0)
mat_roof.setSoilLayerName("Green Roof Soil")
mat_roof.setRoughness("MediumRough")
mat_roof.setThickness(0.1)
mat_roof.setConductivityofDrySoil(0.35)
mat_roof.setDensityofDrySoil(1100.0)
mat_roof.setSpecificHeatofDrySoil(1200.0)
mat_roof.setThermalAbsorptance(0.9)
mat_roof.setSolarAbsorptance(0.7)
mat_roof.setVisibleAbsorptance(0.75)
mat_roof.setSaturationVolumetricMoistureContentoftheSoilLayer(0.3)
mat_roof.setResidualVolumetricMoistureContentoftheSoilLayer(0.01)
mat_roof.setInitialVolumetricMoistureContentoftheSoilLayer(0.1)
mat_roof.setMoistureDiffusionCalculationMethod("Advanced")

# Get the existing roof construction
roof_c = model.getConstructionByName("ASHRAE_189.1-2009_ExtRoof_IEAD_ClimateZone 2-5").get()

# Insert the green roof on the outside
success = roof_c.insertLayer(0, mat_roof)
if not success:
    raise "Cannot insert the RoofVegetation material in the Roof Construction"


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
