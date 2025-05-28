from pathlib import Path

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

check_all = False  # requires that you have a folder of epw files at weatherdata/EPW
if check_all:

    weather_files = Path("../../weatherdata/EPW").glob("*.epw")
    for weather_file in weather_files:
        try:
            epw_file = openstudio.EpwFile(weather_file)
            epw_design_conditions = epw_file.designConditions()
            print(f"{weather_file.name}: success")
        except Exception:
            print(f"{weather_file.name}: FAILURE")


else:

    for weather_file in [Path("../../weatherdata/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")]:
        epw_file = openstudio.EpwFile(weather_file)
        epw_design_conditions = epw_file.designConditions()
        epw_design_condition = epw_design_conditions[0]

        unit = openstudio.model.BuildingUnit(model)
        unit.setName(weather_file.name)
        unit.setFeature("Title of Design Condition", epw_design_condition.titleOfDesignCondition())
        for field in [
            "Heating Coldest Month",
            "Heating Coldest Month Wind Speed 1%",
            "Cooling Dry Bulb 0.4%",
            "Cooling Enthalpy Mean Coincident Dry Bulb 1%",
        ]:
            unit.setFeature(field, epw_design_condition.getFieldByName(field).get())


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
