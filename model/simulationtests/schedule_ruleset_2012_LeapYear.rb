# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 2,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 1,
                     'perimeter_zone_depth' => 3 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add ASHRAE System type 03, PSZ-AC
model.add_hvac({ 'ashrae_sys_num' => '03' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# set year to 2012
yd = model.getYearDescription
yd.setCalendarYear(2012)

# add schedules
summer_design_day = OpenStudio::Model::ScheduleDay.new(model)
summer_design_day.addValue(OpenStudio::Time.new(0, 24, 0, 0), 1.0)

winter_design_day = OpenStudio::Model::ScheduleDay.new(model)
winter_design_day.addValue(OpenStudio::Time.new(0, 24, 0, 0), 0.0)

schedule = OpenStudio::Model::ScheduleRuleset.new(model)
schedule.setName('Test Schedule')
schedule.setSummerDesignDaySchedule(summer_design_day)
schedule.setWinterDesignDaySchedule(winter_design_day)

summer_design_day.setName("#{schedule.nameString} Summer Design Day Schedule")
winter_design_day.setName("#{schedule.nameString} Winter Design Day Schedule")
schedule.defaultDaySchedule.setName("#{schedule.nameString} Default Day Schedule")

weekdayRule = OpenStudio::Model::ScheduleRule.new(schedule)
weekdayRule.setName("#{schedule.nameString} Weekday Rule")
weekdayRule.daySchedule.setName("#{schedule.nameString} Weekday Rule Day Schedule")
weekdayRule.setApplySunday(false)
weekdayRule.setApplyMonday(true)
weekdayRule.setApplyTuesday(true)
weekdayRule.setApplyWednesday(true)
weekdayRule.setApplyThursday(true)
weekdayRule.setApplyFriday(true)
weekdayRule.setApplySaturday(false)
weekdayRule.daySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 0.9)

weekendRule = OpenStudio::Model::ScheduleRule.new(schedule)
weekendRule.setName("#{schedule.nameString} Weekend Rule")
weekendRule.daySchedule.setName("#{schedule.nameString} Weekend Rule Day Schedule")
weekendRule.setApplySunday(true)
weekendRule.setApplyMonday(false)
weekendRule.setApplyTuesday(false)
weekendRule.setApplyWednesday(false)
weekendRule.setApplyThursday(false)
weekendRule.setApplyFriday(false)
weekendRule.setApplySaturday(true)
weekendRule.daySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 0.3)

summerRule = OpenStudio::Model::ScheduleRule.new(schedule)
summerRule.setName("#{schedule.nameString} Summer Rule")
summerRule.daySchedule.setName("#{schedule.nameString} Summer Rule Day Schedule")
summerRule.setApplySunday(true)
summerRule.setApplyMonday(true)
summerRule.setApplyTuesday(true)
summerRule.setApplyWednesday(true)
summerRule.setApplyThursday(true)
summerRule.setApplyFriday(true)
summerRule.setApplySaturday(true)
summerRule.setStartDate(OpenStudio::Date.new('May'.to_MonthOfYear, 28))
summerRule.setEndDate(OpenStudio::Date.new('August'.to_MonthOfYear, 28))
summerRule.daySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 0.1)

# apply schedule to all lights
model.getLightss.each do |lights|
  lights.setSchedule(schedule)
end

# add output reports
add_out_vars = false
if add_out_vars
  reporting_frequency = 'Timestep'
  var = OpenStudio::Model::OutputVariable.new('Schedule Value', model)
  var.setKeyValue('Test Schedule')
  var.setReportingFrequency(reporting_frequency)

  var = OpenStudio::Model::OutputVariable.new('Site Day Type Index', model)
  var.setReportingFrequency(reporting_frequency)
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
