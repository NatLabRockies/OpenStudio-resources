import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)

summer_design_day = openstudio.model.DesignDay(model)
summer_design_day.setName("Chicago Ohare Intl Ap Ann Clg .4% Condns DB=>MWB")
summer_design_day.setMaximumDryBulbTemperature(33.3)
summer_design_day.setDailyDryBulbTemperatureRange(10.5)
summer_design_day.setBarometricPressure(98934)
summer_design_day.setWindSpeed(5.2)
summer_design_day.setWindDirection(230)
summer_design_day.setSkyClearness(0)
summer_design_day.setRainIndicator(False)
summer_design_day.setSnowIndicator(False)
summer_design_day.setDayOfMonth(21)
summer_design_day.setMonth(7)
summer_design_day.setDayType("SummerDesignDay")
summer_design_day.setDaylightSavingTimeIndicator(False)
summer_design_day.setHumidityConditionType("Wetbulb")
# summer_design_day.setHumidityConditionDaySchedule()
summer_design_day.setWetBulbOrDewPointAtMaximumDryBulb(23.7)
# summer_design_day.setHumidityRatioAtMaximumDryBulb()
# summer_design_day.setEnthalpyAtMaximumDryBulb()
summer_design_day.setDryBulbTemperatureRangeModifierType("DefaultMultipliers")
# summer_design_day.setDryBulbTemperatureRangeModifierDaySchedule()
summer_design_day.setSolarModelIndicator("ASHRAETau")
# summer_design_day.setBeamSolarDaySchedule()
# summer_design_day.setDiffuseSolarDaySchedule()
summer_design_day.setAshraeClearSkyOpticalDepthForBeamIrradiance(0.455)
summer_design_day.setAshraeClearSkyOpticalDepthForDiffuseIrradiance(2.05)
# summer_design_day.setDailyWetBulbTemperatureRange()
# summer_design_day.setMaximumNumberWarmupDays()
summer_design_day.setBeginEnvironmentResetMode("FullResetAtBeginEnvironment")

winter_design_day = openstudio.model.DesignDay(model)
winter_design_day.setName("Chicago Ohare Intl Ap Ann Htg 99.6% Condns DB")
winter_design_day.setMaximumDryBulbTemperature(-20)
winter_design_day.setDailyDryBulbTemperatureRange(0)
winter_design_day.setBarometricPressure(98934)
winter_design_day.setWindSpeed(4.9)
winter_design_day.setWindDirection(270)
winter_design_day.setSkyClearness(0)
winter_design_day.setRainIndicator(False)
winter_design_day.setSnowIndicator(False)
winter_design_day.setDayOfMonth(21)
winter_design_day.setMonth(1)
winter_design_day.setDayType("WinterDesignDay")
winter_design_day.setDaylightSavingTimeIndicator(False)
winter_design_day.setHumidityConditionType("Wetbulb")
# winter_design_day.setHumidityConditionDaySchedule()
winter_design_day.setWetBulbOrDewPointAtMaximumDryBulb(-20)
# winter_design_day.setHumidityRatioAtMaximumDryBulb()
# winter_design_day.setEnthalpyAtMaximumDryBulb()
winter_design_day.setDryBulbTemperatureRangeModifierType("DefaultMultipliers")
# winter_design_day.setDryBulbTemperatureRangeModifierDaySchedule()
winter_design_day.setSolarModelIndicator("ASHRAEClearSky")
# winter_design_day.setBeamSolarDaySchedule()
# winter_design_day.setDiffuseSolarDaySchedule()
winter_design_day.setAshraeClearSkyOpticalDepthForBeamIrradiance(0)
winter_design_day.setAshraeClearSkyOpticalDepthForDiffuseIrradiance(0)
# winter_design_day.setDailyWetBulbTemperatureRange()
# winter_design_day.setMaximumNumberWarmupDays()
winter_design_day.setBeginEnvironmentResetMode("FullResetAtBeginEnvironment")

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
