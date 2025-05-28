# This tests the classes that derive from ExteriorLoadDefinition and ExteriorLoadInstance

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# Use Ideal Air Loads
for z in zones:
    z.setUseIdealAirLoads(True)

# Exterior Lighting
ext_light_def = openstudio.model.ExteriorLightsDefinition(model)
ext_light_def.setDesignLevel(1000)
ext_light_def.setName("Exterior Light Def 1kW")

# ScheduleNameOnly
ext_lights = openstudio.model.ExteriorLights(ext_light_def)
ext_lights.setSchedule(model.alwaysOnDiscreteSchedule())
ext_lights.setControlOption("ScheduleNameOnly")
ext_lights.setMultiplier(2.0)
ext_lights.setEndUseSubcategory("Exterior Lighting")
ext_lights.setName("24/7 Exterior Lighting 2kW")

# Astronomical Clock
ext_lights2 = openstudio.model.ExteriorLights(ext_light_def)
ext_lights2.setControlOption("AstronomicalClock")
ext_lights2.setMultiplier(1.0)
ext_lights2.setEndUseSubcategory("Exterior Lighting")
ext_lights2.setName("AstronomicalClock Exterior Lighting 1kW")

# Exterior Fuel
ext_fuel_def = openstudio.model.ExteriorFuelEquipmentDefinition(model)
ext_fuel_def.setDesignLevel(2500)
ext_fuel_def.setName("Exterior Fuel Def 2.5 kW")

ext_fuel_eq = openstudio.model.ExteriorFuelEquipment(ext_fuel_def)
ext_fuel_eq.setSchedule(model.alwaysOnDiscreteSchedule())
ext_fuel_eq.setFuelType("NaturalGas")
ext_fuel_eq.setName("Exterior Natural Gas Equipment")
ext_fuel_eq.setMultiplier(1.0)
ext_fuel_eq.setEndUseSubcategory("Exterior Gas")

# Exterior Water
ext_water_def = openstudio.model.ExteriorWaterEquipmentDefinition(model)
ext_water_def.setDesignLevel(openstudio.convert(20, "gal/min", "m^3/s").get())
ext_water_def.setName("Exterior Water Def 20 GPM")

ext_water_eq = openstudio.model.ExteriorWaterEquipment(ext_water_def)
ext_water_eq.setSchedule(model.alwaysOnDiscreteSchedule())
ext_water_eq.setName("Exterior Water Equipment")
ext_water_eq.setMultiplier(1.0)
ext_water_eq.setEndUseSubcategory("Irrigation")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
