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

# Get spaces, ordered by name to ensure consistency
spaces = sorted(model.getSpaces(), key=lambda s: s.nameString())

# Use Ideal Air Loads
for z in zones:
    z.setUseIdealAirLoads(True)

for i, space in enumerate(spaces):
    if i == 0:
        steam_def = openstudio.model.SteamEquipmentDefinition(model)
        steam_def.setDesignLevel(1000)
        steam_def.setName("Steam Equipment Def 1kW")
        steam_def.setFractionLatent(0.5)
        steam_def.setFractionRadiant(0.3)
        steam_def.setFractionLost(0.0)

        steam_eq = openstudio.model.SteamEquipment(steam_def)
        steam_eq.setSchedule(model.alwaysOnDiscreteSchedule())
        steam_eq.setMultiplier(1.0)
        steam_eq.setEndUseSubcategory("Laundry")
        steam_eq.setSpace(space)
        steam_eq.setName("#{space.name()} Steam Equipment")

    elif i == 1:
        gas_def = openstudio.model.GasEquipmentDefinition(model)
        gas_def.setWattsperSpaceFloorArea(10)
        gas_def.setName("Gas Equipment Def 10W/m2")
        gas_def.setFractionLatent(0.0)
        gas_def.setFractionRadiant(0.3)
        gas_def.setFractionLost(0.0)
        gas_def.setCarbonDioxideGenerationRate(0)

        gas_eq = openstudio.model.GasEquipment(gas_def)
        gas_eq.setSchedule(model.alwaysOnDiscreteSchedule())
        gas_eq.setMultiplier(1.0)
        gas_eq.setEndUseSubcategory("Cooking")
        gas_eq.setSpace(space)
        gas_eq.setName("#{space.name()} Gas Equipment")

    elif i == 2:
        hw_def = openstudio.model.HotWaterEquipmentDefinition(model)
        # (Unusual to set dishwashing as per person, but I want to showcase the
        # ability to do so...)
        hw_def.setWattsperPerson(10)
        hw_def.setName("HotWater Equipment Def 10W/p")
        hw_def.setFractionLatent(0.2)
        hw_def.setFractionRadiant(0.1)
        hw_def.setFractionLost(0.5)

        hw_eq = openstudio.model.HotWaterEquipment(hw_def)
        hw_eq.setSchedule(model.alwaysOnDiscreteSchedule())
        hw_eq.setMultiplier(1.0)
        hw_eq.setEndUseSubcategory("Dishwashing")

        hw_eq.setSpace(space)
        hw_eq.setName("#{space.name()} HotWater Equipment")

    elif i == 3:
        other_def = openstudio.model.OtherEquipmentDefinition(model)
        other_def.setDesignLevel(6766)
        other_def.setName("Other Equipment Def")
        other_def.setFractionLatent(0)
        other_def.setFractionRadiant(0.3)
        other_def.setFractionLost(0.0)
        # TODO: this isn't implemented in openstudio...
        # other_def.setCarbonDioxideGenerationRate(1.2E-7)

        other_eq = openstudio.model.OtherEquipment(other_def)
        other_eq.setSchedule(model.alwaysOnDiscreteSchedule())
        other_eq.setMultiplier(1.0)
        other_eq.setEndUseSubcategory("Propane stuff")
        if openstudio.VersionString(openstudio.openStudioVersion()) < openstudio.VersionString("3.0.0"):
            other_eq.setFuelType("PropaneGas")
        else:
            other_eq.setFuelType("Propane")

        other_eq.setSpace(space)
        other_eq.setName("#{space.name()} Other Equipment")

    elif i == 4:
        luminaire_def = openstudio.model.LuminaireDefinition(model)
        luminaire_def.setLightingPower(40)
        luminaire_def.setName("A Luminaire")
        luminaire_def.setFractionRadiant(0.3)
        luminaire_def.setFractionVisible(0.7)
        luminaire_def.setReturnAirFractionFunctionofPlenumTemperatureCoefficient1(0.0)
        luminaire_def.setReturnAirFractionFunctionofPlenumTemperatureCoefficient2(0.0)

        luminaire_eq = openstudio.model.Luminaire(luminaire_def)
        luminaire_eq.setSchedule(model.alwaysOnDiscreteSchedule())
        luminaire_eq.setMultiplier(1.0)
        luminaire_eq.setEndUseSubcategory("Luminaires")

        luminaire_eq.setSpace(space)
        luminaire_eq.setName("#{space.name()} Luminaire")


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
