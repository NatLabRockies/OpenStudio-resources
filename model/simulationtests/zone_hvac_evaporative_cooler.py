from itertools import product

import openstudio
from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 8 stories, 100m X 50m, 8 zones building
model.add_geometry(length=100, width=50, num_floors=8, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# add thermostats
model.add_thermostats(heating_setpoint=19, cooling_setpoint=26)


def make_zone_hvac_cooler(
    z: openstudio.model.ThermalZone,
    direct_is_first: bool = False,
    add_secondary: bool = True,
    fan_placement: str = "BlowThrough",
):
    model = z.model()
    indirect_evap = None
    direct_evap = None
    if direct_is_first:
        # There is a default ctor
        zoneHVACEvaporativeCoolerUnit = openstudio.model.ZoneHVACEvaporativeCoolerUnit(model)
        direct_evap = zoneHVACEvaporativeCoolerUnit.firstEvaporativeCooler()
        supplyAirFan = zoneHVACEvaporativeCoolerUnit.supplyAirFan()

        fan_system = openstudio.model.FanSystemModel(model)
        zoneHVACEvaporativeCoolerUnit.setSupplyAirFan(fan_system)
        supplyAirFan.remove()
        supplyAirFan = fan_system
        # An optional Second EvaporativeCooler
        if add_secondary:
            indirect_evap = openstudio.model.EvaporativeCoolerIndirectResearchSpecial(model)
            zoneHVACEvaporativeCoolerUnit.setSecondEvaporativeCooler(indirect_evap)
    else:
        # And an explicit Ctor:
        # ZoneHVACEvaporativeCoolerUnit(const Model& model, Schedule& availabilitySchedule, HVACComponent& supplyAirFan, HVACComponent& firstEvaporativeCooler);
        supplyAirFan = openstudio.model.FanSystemModel(model)

        indirect_evap = openstudio.model.EvaporativeCoolerIndirectResearchSpecial(model)
        zoneHVACEvaporativeCoolerUnit = openstudio.model.ZoneHVACEvaporativeCoolerUnit(
            model, model.alwaysOnDiscreteSchedule(), supplyAirFan, indirect_evap
        )
        # An optional Second EvaporativeCooler
        if add_secondary:
            direct_evap = openstudio.model.EvaporativeCoolerDirectResearchSpecial(
                model, model.alwaysOnDiscreteSchedule()
            )
            zoneHVACEvaporativeCoolerUnit.setSecondEvaporativeCooler(direct_evap)

    if indirect_evap is not None:
        indirect_evap.setName(f"{z.nameString()} Indirect Evaporative Cooler")
    if direct_evap is not None:
        direct_evap.setName(f"{z.nameString()} Direct Evaporative Cooler")

    supplyAirFan.setName(f"{z.nameString()} Supply Fan")
    zoneHVACEvaporativeCoolerUnit.setName(f"{z.nameString()} Evap Unit")
    # zoneHVACEvaporativeCoolerUnit.resetSecondEvaporativeCooler()
    #
    # Redoing what the default constructor does for demonstration purposes
    # zoneHVACEvaporativeCoolerUnit.setDesignSupplyAirFlowRate(1.0)
    zoneHVACEvaporativeCoolerUnit.autosizeDesignSupplyAirFlowRate()
    zoneHVACEvaporativeCoolerUnit.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule())
    zoneHVACEvaporativeCoolerUnit.setFanPlacement(fan_placement)
    zoneHVACEvaporativeCoolerUnit.setCoolerUnitControlMethod("ZoneCoolingLoadVariableSpeedFan")
    zoneHVACEvaporativeCoolerUnit.setThrottlingRangeTemperatureDifference(1.1)
    zoneHVACEvaporativeCoolerUnit.setCoolingLoadControlThresholdHeatTransferRate(100.0)
    zoneHVACEvaporativeCoolerUnit.setShutOffRelativeHumidity(100.0)

    # Add it to a ThermalZone
    zoneHVACEvaporativeCoolerUnit.addToThermalZone(z)

    # Rename nodes for clarity
    z.zoneAirNode().setName(f"{z.nameString()} Zone Air Node")
    # z.returnAirModelObjects.modelObjects()[0].setName("{z.nameString()} Zone Return Air Node")
    z.inletPortList().modelObjects()[0].setName(f"{z.nameString()} Zone Air Inlet Node")
    z.exhaustPortList().modelObjects()[0].setName(f"{z.nameString()} Zone Air Exhaust Node")

    return zoneHVACEvaporativeCoolerUnit


# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

configs = [
    {"zone_name": "DirectFirst", "direct_is_first": True, "add_secondary": True},
    # Mimic SMStore8 from StripMallZoneEvapCoolerAutosized.idf
    # https://github.com/NREL/EnergyPlus/blob/31e3c33467c5873371bf48b12a7318215971c315/testfiles/StripMallZoneEvapCoolerAutosized.idf#L4767-L4784
    {"zone_name": "IndirectFirst", "direct_is_first": False, "add_secondary": True},
    {"zone_name": "DirectOnly", "direct_is_first": True, "add_secondary": False},
    {"zone_name": "IndirectOnly", "direct_is_first": False, "add_secondary": False},
]
fan_placements = ["BlowThrough", "DrawThrough"]
assert len(configs) * len(fan_placements) == len(zones)

for (config, fan_placement), z in zip(product(configs, fan_placements), zones):
    z.setName(f"{config['zone_name']} {fan_placement} Zn")
    make_zone_hvac_cooler(
        z=z,
        direct_is_first=config["direct_is_first"],
        add_secondary=config["add_secondary"],
        fan_placement=fan_placement,
    )

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
