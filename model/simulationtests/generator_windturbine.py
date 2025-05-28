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
model.add_design_days()

# In order to produce more consistent results between different runs,
# we sort the zones by names
# (There's only one here, but just in case this would be copy pasted somewhere
# else...)
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())
z = zones[0]
z.setUseIdealAirLoads(True)

# add wind turbine generators. These are from the E+ 9.4.0 GeneratorwithWindTurbine.idf
generator1 = openstudio.model.GeneratorWindTurbine(model)
generator1.setName("WT1")
generator1.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule())
generator1.setRotorType("HorizontalAxisWindTurbine")
generator1.setPowerControl("FixedSpeedVariablePitch")
generator1.setRatedRotorSpeed(41.0)
generator1.setRotorDiameter(19.2)
generator1.setOverallHeight(30.5)
generator1.setNumberofBlades(3)
generator1.setRatedPower(55000.0)
generator1.setRatedWindSpeed(11.0)
generator1.setCutInWindSpeed(3.5)
generator1.setCutOutWindSpeed(25.0)
generator1.setFractionSystemEfficiency(0.835)
generator1.setMaximumTipSpeedRatio(8.0)
generator1.setMaximumPowerCoefficient(0.5)
generator1.setAnnualLocalAverageWindSpeed(6.4)
generator1.setHeightforLocalAverageWindSpeed(50.0)
# These fields not used for HorizontalAxisWindTurbine
# generator1.setBladeChordArea( )
# generator1.setBladeDragCoefficient( )
# generator1.setBladeLiftCoefficient( )
generator1.setPowerCoefficientC1(0.5176)
generator1.setPowerCoefficientC2(116.0)
generator1.setPowerCoefficientC3(0.4)
generator1.setPowerCoefficientC4(0.0)
generator1.setPowerCoefficientC5(5.0)
generator1.setPowerCoefficientC6(21.0)

generator2 = openstudio.model.GeneratorWindTurbine(model)
generator2.setName("WT2")
generator2.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule())
generator2.setRotorType("HorizontalAxisWindTurbine")
generator2.setPowerControl("FixedSpeedFixedPitch")
generator2.setRatedRotorSpeed(59.0)
generator2.setRotorDiameter(21.0)
generator2.setOverallHeight(37.0)
generator2.setNumberofBlades(3)
generator2.setRatedPower(100000.0)
generator2.setRatedWindSpeed(14.5)
generator2.setCutInWindSpeed(3.5)
generator2.setCutOutWindSpeed(25.0)
generator2.setFractionSystemEfficiency(0.835)
generator2.setMaximumTipSpeedRatio(7.0)
generator2.setMaximumPowerCoefficient(0.23)
generator2.setAnnualLocalAverageWindSpeed(6.4)
generator2.setHeightforLocalAverageWindSpeed(50.0)
# generator2.setBladeChordArea( )
# generator2.setBladeDragCoefficient( )
# generator2.setBladeLiftCoefficient( )
generator2.setPowerCoefficientC1(0.5176)
generator2.setPowerCoefficientC2(116.0)
generator2.setPowerCoefficientC3(0.4)
generator2.setPowerCoefficientC4(0.0)
generator2.setPowerCoefficientC5(5.0)
generator2.setPowerCoefficientC6(21.0)

generator3 = openstudio.model.GeneratorWindTurbine(model)
generator3.setName("WT3")
generator3.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule())
generator3.setRotorType("VerticalAxisWindTurbine")
generator3.setPowerControl("VariableSpeedFixedPitch")
generator3.setRatedRotorSpeed(130.0)
generator3.setRotorDiameter(5.2)
generator3.setOverallHeight(11.0)
generator3.setNumberofBlades(3)
generator3.setRatedPower(10000.0)
generator3.setRatedWindSpeed(11.0)
generator3.setCutInWindSpeed(3.0)
generator3.setCutOutWindSpeed(25.0)
generator3.setFractionSystemEfficiency(0.75)
generator3.setMaximumTipSpeedRatio(5.0)
# Not used for VerticalAxisWindTurbine
# generator3.setMaximumPowerCoefficient( )
generator3.setAnnualLocalAverageWindSpeed(6.4)
generator3.setHeightforLocalAverageWindSpeed(50.0)
generator3.setBladeChordArea(2.08)
generator3.setBladeDragCoefficient(0.9)
generator3.setBladeLiftCoefficient(0.05)
# Not used for VerticalAxisWindTurbine
# generator3.setPowerCoefficientC1( )
# generator3.setPowerCoefficientC2( )
# generator3.setPowerCoefficientC3( )
# generator3.setPowerCoefficientC4( )
# generator3.setPowerCoefficientC5( )
# generator3.setPowerCoefficientC6( )

# add generators to electric load center distribution
elcd = openstudio.model.ElectricLoadCenterDistribution(model)
elcd.addGenerator(generator1)
elcd.addGenerator(generator2)
elcd.addGenerator(generator3)
elcd.setElectricalBussType("AlternatingCurrent")

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
