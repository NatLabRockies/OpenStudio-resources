import json

import openstudio
import pytest
from baseline_model import VALID_ASHRAE_SYS_NUM_ARRAY, BaselineModel


def _one_zone_model() -> BaselineModel:
    model = BaselineModel()
    params = {
        "length": 100.0,
        "width": 50.0,
        "num_floors": 1,
        "floor_to_floor_height": 4.0,
        "plenum_height": 0,
        "perimeter_zone_depth": 0,
    }
    model.add_geometry(**params)
    return model


def _two_zone_model() -> BaselineModel:
    model = BaselineModel()
    params = {
        "length": 100.0,
        "width": 50.0,
        "num_floors": 2,
        "floor_to_floor_height": 4.0,
        "plenum_height": 0,
        "perimeter_zone_depth": 0,
    }
    model.add_geometry(**params)
    return model


@pytest.mark.parametrize(
    "num_floors, plenum_height, perimeter_zone_depth, expected_num_spaces",
    [
        (1, 0, 0, 1),
        (2, 0, 0, 2),
        (1, 0, 3, 5),
        (2, 0, 3, 10),
        # TODO: plenum height was not implemented in the ruby one! Damn
        # (1, 1, 0, 2),
        # (2, 1, 0, 4),
        # (1, 1, 3, 6),
        # (2, 1, 3, 12),
    ],
)
def test_add_geometry(num_floors: int, plenum_height: int, perimeter_zone_depth: int, expected_num_spaces: int):
    model = BaselineModel()
    params = {
        "length": 100.0,
        "width": 50.0,
        "num_floors": num_floors,
        "floor_to_floor_height": 4,
        "plenum_height": plenum_height,
        "perimeter_zone_depth": perimeter_zone_depth,
    }
    model.add_geometry(**params)
    assert len(model.getSpaces()) == expected_num_spaces


def test_add_windows():
    model = _one_zone_model()
    model.add_windows(**{"wwr": 0.4, "offset": 1, "application_type": "Above Floor"})
    assert len(model.getSubSurfaces()) == 4


def test_set_constructions():
    model = _one_zone_model()
    model.add_windows(**{"wwr": 0.4, "offset": 1, "application_type": "Above Floor"})
    assert not model.getSurfaces()[0].construction().is_initialized()
    assert not model.getSubSurfaces()[0].construction().is_initialized()

    model.set_constructions()
    assert model.getSurfaces()[0].construction().is_initialized()
    assert model.getSubSurfaces()[0].construction().is_initialized()


def test_add_daylighting_no_shades():
    model = _one_zone_model()
    model.add_windows(**{"wwr": 0.4, "offset": 1, "application_type": "Above Floor"})
    model.set_constructions()
    assert not model.getDaylightingControls()
    assert not model.getGlareSensors()
    assert not model.getIlluminanceMaps()
    assert not model.getBlinds()
    assert not model.getShadingControls()
    model.add_daylighting(**{"shades": False})
    assert len(model.getDaylightingControls()) == 1
    assert len(model.getGlareSensors()) == 1
    assert len(model.getIlluminanceMaps()) == 1
    assert not model.getBlinds()
    assert not model.getShadingControls()


def test_add_daylighting_with_shades():
    model = _one_zone_model()
    model.add_windows(**{"wwr": 0.4, "offset": 1, "application_type": "Above Floor"})
    model.set_constructions()
    assert not model.getDaylightingControls()
    assert not model.getGlareSensors()
    assert not model.getIlluminanceMaps()
    assert not model.getBlinds()
    assert not model.getShadingControls()

    model.add_daylighting(**{"shades": True})
    assert len(model.getDaylightingControls()) == 1
    assert len(model.getGlareSensors()) == 1
    assert len(model.getIlluminanceMaps()) == 1
    assert len(model.getBlinds()) == 1
    assert len(model.getShadingControls()) == 1


def test_add_daylighting_with_shades_throws_if_no_constructions():
    model = _one_zone_model()
    model.add_windows(**{"wwr": 0.4, "offset": 1, "application_type": "Above Floor"})
    with pytest.raises(RuntimeError, match=r".*must set constructions.*"):
        model.add_daylighting(**{"shades": True})


@pytest.mark.parametrize("ashrae_sys_num", VALID_ASHRAE_SYS_NUM_ARRAY)
def test_add_hvac(ashrae_sys_num: str):
    model = BaselineModel()
    params = {
        "length": 100.0,
        "width": 50.0,
        "num_floors": 2,
        "floor_to_floor_height": 4.0,
        "plenum_height": 0.0,
        "perimeter_zone_depth": 3.0,
    }
    model.add_geometry(**params)
    model.add_hvac(ashrae_sys_num=ashrae_sys_num)


@pytest.mark.parametrize(
    "model",
    [pytest.param(_one_zone_model(), id="one_zone"), pytest.param(_two_zone_model(), id="two_zones")],
)
def test_set_space_type(model: BaselineModel):
    assert not model.getSpaceTypes()
    assert not model.getPeopleDefinitions()
    assert not model.getLightsDefinitions()
    assert not model.getElectricEquipmentDefinitions()
    assert not model.getPeoples()
    assert not model.getLightss()
    assert not model.getElectricEquipments()
    assert not model.getDesignSpecificationOutdoorAirs()
    assert not model.getSpaceInfiltrationDesignFlowRates()

    for space in model.getSpaces():
        assert not space.people()
        assert not space.electricEquipment()
        assert not space.lights()
        assert not space.spaceInfiltrationDesignFlowRates()
        assert space.infiltrationDesignFlowRate() == 0
        assert space.numberOfPeople() == 0
        assert space.lightingPower() == 0
        assert space.electricEquipmentPower() == 0
        assert not space.designSpecificationOutdoorAir().is_initialized()

    model.set_space_type()
    assert len(model.getSpaceTypes()) == 1
    assert len(model.getPeopleDefinitions()) == 1
    assert len(model.getLightsDefinitions()) == 1
    assert len(model.getElectricEquipmentDefinitions()) == 1
    assert len(model.getPeoples()) == 1
    assert len(model.getLightss()) == 1
    assert len(model.getElectricEquipments()) == 1
    assert len(model.getDesignSpecificationOutdoorAirs()) == 1
    assert len(model.getSpaceInfiltrationDesignFlowRates()) == 1

    for space in model.getSpaces():
        assert not space.people()
        assert not space.electricEquipment()
        assert not space.lights()
        assert not space.spaceInfiltrationDesignFlowRates()
        assert space.infiltrationDesignFlowRate() > 0
        assert space.numberOfPeople() > 0
        assert space.lightingPower() > 0
        assert space.electricEquipmentPower() > 0
        assert space.designSpecificationOutdoorAir().is_initialized()


def test_add_thermostats():
    model = _one_zone_model()
    zones = model.getThermalZones()
    assert len(zones) == 1
    zone = zones[0]
    assert not zone.thermostatSetpointDualSetpoint().is_initialized()
    model.add_thermostats(heating_setpoint=18.0, cooling_setpoint=26.0)
    assert zone.thermostatSetpointDualSetpoint().is_initialized()


def test_add_thermostats_wrong_values():
    model = _one_zone_model()
    with pytest.raises(ValueError, match=r".*cannot be greater than cooling_setpoint.*"):
        model.add_thermostats(heating_setpoint=28.0, cooling_setpoint=26.0)


@pytest.fixture
def swh_standards_data():
    return json.loads(
        """
  {
  "schedules": [
    {
        "name": "Medium Office Bldg Swh",
        "category": "Service Water Heating",
        "units": null,
        "day_types": "Default|SmrDsn",
        "start_date": "2014-01-01T00:00:00+00:00",
        "end_date": "2014-12-31T00:00:00+00:00",
        "type": "Hourly",
        "notes": "From DOE Reference Buildings ",
        "values": [
          0.05, 0.05, 0.05, 0.05, 0.05, 0.08, 0.07, 0.19, 0.35, 0.38, 0.39, 0.47, 0.57, 0.54, 0.34, 0.33, 0.44, 0.26, 0.21, 0.15, 0.17, 0.08, 0.05, 0.05
        ]
      },
      {
        "name": "Medium Office Bldg Swh",
        "category": "Service Water Heating",
        "units": null,
        "day_types": "Sun",
        "start_date": "2014-01-01T00:00:00+00:00",
        "end_date": "2014-12-31T00:00:00+00:00",
        "type": "Hourly",
        "notes": "From DOE Reference Buildings ",
        "values": [
          0.04, 0.04, 0.04, 0.04, 0.04, 0.07, 0.04, 0.04, 0.04, 0.04, 0.04, 0.06, 0.06, 0.09, 0.06, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.07, 0.04, 0.04
        ]
      },
      {
        "name": "Medium Office Bldg Swh",
        "category": "Service Water Heating",
        "units": null,
        "day_types": "WntrDsn|Sat",
        "start_date": "2014-01-01T00:00:00+00:00",
        "end_date": "2014-12-31T00:00:00+00:00",
        "type": "Hourly",
        "notes": "From DOE Reference Buildings ",
        "values": [
          0.05, 0.05, 0.05, 0.05, 0.05, 0.08, 0.07, 0.11, 0.15, 0.21, 0.19, 0.23, 0.2, 0.19, 0.15, 0.13, 0.14, 0.07, 0.07, 0.07, 0.07, 0.09, 0.05, 0.05
        ]
      }
    ]
  }
"""
    )


def test_set_standards_data(swh_standards_data):
    schedule_name = "Medium Office Bldg Swh"

    model = BaselineModel()
    with pytest.raises(ValueError, match=r".*must call add_standards first.*"):
        model.add_schedule(schedule_name=schedule_name)
    model.add_standards(standards=swh_standards_data)
    model.add_schedule(schedule_name=schedule_name)
    assert len(model.getScheduleRulesets()) == 1
    sch_ruleset = model.getScheduleRulesets()[0]
    assert len(sch_ruleset.scheduleRules()) == 2
    sch_rule1 = sch_ruleset.scheduleRules()[0]
    sch_rule2 = sch_ruleset.scheduleRules()[1]

    assert not sch_rule1.applyAllDays()
    assert not sch_rule2.applyAllDays()

    assert sch_rule1.applySunday() or sch_rule1.applySaturday()
    if sch_rule1.applySunday():
        assert not sch_rule1.applySaturday()
        assert sch_rule2.applySaturday()
        assert not sch_rule2.applySunday()
    else:
        assert sch_rule1.applySaturday()
        assert not sch_rule2.applySaturday()
        assert sch_rule2.applySunday()


@pytest.mark.parametrize("water_heater_type", ["Mixed", "Stratified"])
@pytest.mark.parametrize("water_heater_fuel", ["Electricity", "Natural Gas"])
def test_add_water_heater(water_heater_type: str, water_heater_fuel: str):
    model = BaselineModel()
    water_heater = model.add_water_heater(water_heater_type=water_heater_type, water_heater_fuel=water_heater_fuel)
    if water_heater_type == "Mixed":
        assert isinstance(water_heater, openstudio.model.WaterHeaterMixed)
    else:
        assert isinstance(water_heater, openstudio.model.WaterHeaterStratified)
    actual_fuel_type = "Electricity" if water_heater_fuel == "Electricity" else "NaturalGas"

    assert water_heater.heaterFuelType() == actual_fuel_type
    # Mixed returns optional here
    assert openstudio.OptionalString(water_heater.offCycleParasiticFuelType()).get() == actual_fuel_type
    assert openstudio.OptionalString(water_heater.onCycleParasiticFuelType()).get() == actual_fuel_type


@pytest.mark.parametrize("water_heater_type", ["Mixed", "Stratified"])
def test_add_swh_loop(water_heater_type: str):
    model = BaselineModel()
    swh_loop = model.add_swh_loop(water_heater_type=water_heater_type)
    assert isinstance(swh_loop, openstudio.model.PlantLoop)
    if water_heater_type == "Mixed":
        assert len(model.getWaterHeaterMixeds()) == 1
        assert not model.getWaterHeaterStratifieds()
    else:
        assert not model.getWaterHeaterMixeds()
        assert len(model.getWaterHeaterStratifieds()) == 1


def test_add_swh_end_uses(swh_standards_data):
    schedule_name = "Medium Office Bldg Swh"

    model = BaselineModel()
    model.add_standards(standards=swh_standards_data)
    swh_loop = openstudio.model.PlantLoop(model)
    model.add_swh_end_uses(swh_loop=swh_loop, flow_rate_fraction_schedule=schedule_name)


def test_rename_loop_nodes():
    model = BaselineModel()
    p = openstudio.model.PlantLoop(model)
    p.setName("HW Loop")
    b = openstudio.model.BoilerHotWater(model)
    b.setName("Boiler")
    p.addSupplyBranchForComponent(b)
    pump = openstudio.model.PumpVariableSpeed(model)
    pump.setName("Pump")
    pump.addToNode(p.supplyInletNode())
    hx = openstudio.model.HeatExchangerFluidToFluid(model)
    p.addDemandBranchForComponent(hx)
    hx.setName("HX")
    model.rename_loop_nodes()
    loop_nodes = p.supplyComponents(openstudio.IddObjectType("OS:Node"))
    node_names = [x.nameString() for x in loop_nodes]
    assert node_names == [
        "HW Loop Supply Inlet Node",
        "HW Loop Supply Side HW Loop VSD Pump Outlet Node",
        "HW Loop Supply Side Boiler Inlet Node",
        "HW Loop Supply Side Boiler Outlet Node",
        "HW Loop Supply Outlet Node",
    ]

    loop_nodes = p.demandComponents(openstudio.IddObjectType("OS:Node"))
    node_names = [x.nameString() for x in loop_nodes]
    assert node_names == [
        "HW Loop Demand Inlet Node",
        "HW Loop Demand Side HX Inlet Node",
        "HW Loop Demand Side HX Outlet Node",
        "HW Loop Demand Outlet Node",
    ]


def test_rename_air_nodes():
    model = _one_zone_model()
    model.add_hvac(ashrae_sys_num="07")
    assert len(model.getAirLoopHVACs()) == 1
    a = model.getAirLoopHVACs()[0]
    model.rename_air_nodes()
    loop_nodes = a.supplyComponents(openstudio.IddObjectType("OS:Node"))
    node_names = [x.nameString() for x in loop_nodes]
    for expected_node_name in [
        "VAV with Reheat Supply Inlet Node",
        "VAV with Reheat Mixed Air Node",
        "VAV with Reheat Supply Outlet Node",
    ]:
        assert expected_node_name in node_names
