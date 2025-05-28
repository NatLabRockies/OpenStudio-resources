from pathlib import Path

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 03, PSZ-AC
model.add_hvac(ashrae_sys_num="03")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

###############################################################################

# Add output variables?
add_out_vars = False

###############################################################################

# set year to 2013
yd = model.getYearDescription()
yd.setCalendarYear(2013)

# add schedule file
file_path = Path(__file__).parent.absolute() / "lib/schedulefile.csv"
external_file = openstudio.model.ExternalFile.getExternalFile(model, str(file_path))
external_file = external_file.get()
schedule_file = openstudio.model.ScheduleFile(external_file, 3, 1)

# apply schedule to all lights
for lights in model.getLightss():
    lights.setSchedule(schedule_file)


if add_out_vars:
    # request hourly output
    var = openstudio.model.OutputVariable("Schedule Value", model)
    var.setKeyValue("Test Schedule")

    var = openstudio.model.OutputVariable("Site Day Type Index", model)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
