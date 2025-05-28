import openstudio

from lib.baseline_model import BaselineModel

m = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone core/perimeter building
m.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
m.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
m.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type()

# add design days to the model (Chicago)
m.add_design_days()

# add ASHRAE System type 03, PSZ-AC
m.add_hvac(ashrae_sys_num="03")

# In order to produce more consistent results between different runs,
# we sort the zones by names (only one here anyways...)
zones = sorted(m.getThermalZones(), key=lambda z: z.nameString())
zone = zones[0]

zv = openstudio.model.ZoneVentilationWindandStackOpenArea(m)
zv.addToThermalZone(zone)

zv.setOpeningArea(10.0)
zv.setOpeningAreaFractionSchedule(m.alwaysOnDiscreteSchedule())
zv.setOpeningEffectiveness(0.5)
zv.setEffectiveAngle(90)
zv.setHeightDifference(10)
zv.setDischargeCoefficientforOpening(0.3)

zv.setMinimumIndoorTemperature(10.0)
minIndoorTempSch = openstudio.model.ScheduleConstant(m)
minIndoorTempSch.setValue(-10.0)
zv.setMinimumIndoorTemperatureSchedule(minIndoorTempSch)

zv.setMaximumIndoorTemperature(30.0)
maxIndoorTempSch = openstudio.model.ScheduleConstant(m)
maxIndoorTempSch.setValue(30.0)
zv.setMaximumIndoorTemperatureSchedule(maxIndoorTempSch)

zv.setDeltaTemperature(3.0)
deltaTempSch = openstudio.model.ScheduleConstant(m)
deltaTempSch.setValue(3.0)
zv.setDeltaTemperatureSchedule(deltaTempSch)

zv.setMinimumOutdoorTemperature(10.0)
minOutdoorTempSch = openstudio.model.ScheduleConstant(m)
minOutdoorTempSch.setValue(-10.0)
zv.setMinimumOutdoorTemperatureSchedule(minOutdoorTempSch)

zv.setMaximumOutdoorTemperature(-20.0)
maxOutdoorTempSch = openstudio.model.ScheduleConstant(m)
maxOutdoorTempSch.setValue(20.0)
zv.setMaximumOutdoorTemperatureSchedule(maxOutdoorTempSch)

zv.setMaximumWindSpeed(15.0)

# save the OpenStudio model (.osm)
m.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
