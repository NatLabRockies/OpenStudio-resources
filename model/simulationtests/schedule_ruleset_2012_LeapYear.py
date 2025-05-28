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

# set year to 2012
yd = model.getYearDescription()
yd.setCalendarYear(2012)

# add schedules
summer_design_day = openstudio.model.ScheduleDay(model)
summer_design_day.addValue(openstudio.Time(0, 24, 0, 0), 1.0)

winter_design_day = openstudio.model.ScheduleDay(model)
winter_design_day.addValue(openstudio.Time(0, 24, 0, 0), 0.0)

schedule = openstudio.model.ScheduleRuleset(model)
schedule.setName("Test Schedule")
schedule.setSummerDesignDaySchedule(summer_design_day)
schedule.setWinterDesignDaySchedule(winter_design_day)

weekdayRule = openstudio.model.ScheduleRule(schedule)
weekdayRule.setApplySunday(False)
weekdayRule.setApplyMonday(True)
weekdayRule.setApplyTuesday(True)
weekdayRule.setApplyWednesday(True)
weekdayRule.setApplyThursday(True)
weekdayRule.setApplyFriday(True)
weekdayRule.setApplySaturday(False)
weekdayRule.daySchedule().addValue(openstudio.Time(0, 24, 0, 0), 0.9)

weekendRule = openstudio.model.ScheduleRule(schedule)
weekendRule.setApplySunday(True)
weekendRule.setApplyMonday(False)
weekendRule.setApplyTuesday(False)
weekendRule.setApplyWednesday(False)
weekendRule.setApplyThursday(False)
weekendRule.setApplyFriday(False)
weekendRule.setApplySaturday(True)
weekendRule.daySchedule().addValue(openstudio.Time(0, 24, 0, 0), 0.3)

summerRule = openstudio.model.ScheduleRule(schedule)
summerRule.setApplySunday(True)
summerRule.setApplyMonday(True)
summerRule.setApplyTuesday(True)
summerRule.setApplyWednesday(True)
summerRule.setApplyThursday(True)
summerRule.setApplyFriday(True)
summerRule.setApplySaturday(True)
summerRule.setStartDate(openstudio.Date(openstudio.MonthOfYear("May"), 28))
summerRule.setEndDate(openstudio.Date(openstudio.MonthOfYear("August"), 28))
summerRule.daySchedule().addValue(openstudio.Time(0, 24, 0, 0), 0.1)

# apply schedule to all lights
for lights in model.getLightss():
    lights.setSchedule(schedule)


# add output reports
add_out_vars = False
if add_out_vars:
    # request hourly output
    var = openstudio.model.OutputVariable("Schedule Value", model)
    var.setKeyValue("Test Schedule")

    var = openstudio.model.OutputVariable("Site Day Type Index", model)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
