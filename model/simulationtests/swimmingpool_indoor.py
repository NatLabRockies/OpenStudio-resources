import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=19, cooling_setpoint=26)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# Add ASHRAE System type 07, VAV w/ Reheat, this creates a ChW, a HW loop and a
# Condenser Loop
model.add_hvac(ashrae_sys_num="07")

boilers = sorted(model.getBoilerHotWaters(), key=lambda c: c.nameString())

heating_loop = boilers[0].plantLoop().get()

core_zone = model.getThermalZoneByName("Story 1 Core Thermal Zone").get()
floor_surface = [s for s in core_zone.spaces()[0].surfaces() if s.surfaceType() == "Floor"][0]

# Create a SwimmingPoolIndoor. This mimics the 5ZoneSwimmingPool E+ example
swimmingPoolIndoor = openstudio.model.SwimmingPoolIndoor(model, floor_surface)

# Average Depth {m}
swimmingPoolIndoor.setAverageDepth(1.5)

# Activity Factor Schedule Name
poolActivitySchedule = openstudio.model.ScheduleRuleset(model)
poolActivitySchedule.setName("PoolActivitySched")
poolActivityScheduleDay = poolActivitySchedule.defaultDaySchedule()
poolActivityScheduleDay.addValue(openstudio.Time(0, 6, 0, 0), 0.1)
poolActivityScheduleDay.addValue(openstudio.Time(0, 20, 0, 0), 0.5)
poolActivityScheduleDay.addValue(openstudio.Time(0, 24, 0, 0), 0.1)
swimmingPoolIndoor.setActivityFactorSchedule(poolActivitySchedule)

# Make-up Water Supply Schedule Name
poolMakeUpWaterSchedule = openstudio.model.ScheduleRuleset(model, 16.67)
poolMakeUpWaterSchedule.setName("MakeUpWaterSched")
swimmingPoolIndoor.setMakeupWaterSupplySchedule(poolMakeUpWaterSchedule)

# Cover Schedule Name
poolCoverSchedule = openstudio.model.ScheduleRuleset(model)
poolCoverSchedule.setName("PoolCoverSched")
poolCoverScheduleDay = poolCoverSchedule.defaultDaySchedule()
poolCoverScheduleDay.addValue(openstudio.Time(0, 6, 0, 0), 0.5)
poolCoverScheduleDay.addValue(openstudio.Time(0, 20, 0, 0), 0.0)
poolCoverScheduleDay.addValue(openstudio.Time(0, 24, 0, 0), 0.5)
swimmingPoolIndoor.setCoverSchedule(poolCoverSchedule)

# Cover Evaporation Factor
swimmingPoolIndoor.setCoverEvaporationFactor(0.8)

# Cover Convection Factor
swimmingPoolIndoor.setCoverConvectionFactor(0.2)

# Cover Short-Wavelength Radiation Factor
swimmingPoolIndoor.setCoverShortWavelengthRadiationFactor(0.9)

# Cover Long-Wavelength Radiation Factor
swimmingPoolIndoor.setCoverLongWavelengthRadiationFactor(0.5)

# Pool Heating System Maximum Water Flow Rate {m3/s}
swimmingPoolIndoor.setPoolHeatingSystemMaximumWaterFlowRate(0.1)

# Pool Miscellaneous Equipment Power {W/(m3/s)}
swimmingPoolIndoor.setPoolMiscellaneousEquipmentPower(0.6)

# Setpoint Temperature Schedule
poolSetpointTempSchedule = openstudio.model.ScheduleRuleset(model, 27.0)
poolSetpointTempSchedule.setName("PoolSetpointTempSched")
swimmingPoolIndoor.setSetpointTemperatureSchedule(poolSetpointTempSchedule)

# Maximum Number of People
swimmingPoolIndoor.setMaximumNumberofPeople(15.0)

# People Schedule
poolOccupancySchedule = openstudio.model.ScheduleRuleset(model)
poolOccupancySchedule.setName("PoolOccupancySched")
poolOccupancyScheduleDay = poolOccupancySchedule.defaultDaySchedule()
poolOccupancyScheduleDay.addValue(openstudio.Time(0, 6, 0, 0), 0.0)
poolOccupancyScheduleDay.addValue(openstudio.Time(0, 9, 0, 0), 1.0)
poolOccupancyScheduleDay.addValue(openstudio.Time(0, 11, 0, 0), 0.5)
poolOccupancyScheduleDay.addValue(openstudio.Time(0, 13, 0, 0), 1.0)
poolOccupancyScheduleDay.addValue(openstudio.Time(0, 16, 0, 0), 0.5)
poolOccupancyScheduleDay.addValue(openstudio.Time(0, 20, 0, 0), 1.0)
poolOccupancyScheduleDay.addValue(openstudio.Time(0, 24, 0, 0), 0.0)
swimmingPoolIndoor.setPeopleSchedule(poolOccupancySchedule)

# People Heat Gain Schedule
poolOccHeatGainSched = openstudio.model.ScheduleRuleset(model, 300.0)
poolOccHeatGainSched.setName("PoolOccHeatGainSched")
swimmingPoolIndoor.setPeopleHeatGainSchedule(poolOccHeatGainSched)

# Connect the pool to the heating loop
heating_loop.addDemandBranchForComponent(swimmingPoolIndoor)

###

# add output reports
add_out_vars = False
if add_out_vars:

    freq = "Detailed"

    # Outputs implemented in the class
    for varname in swimmingPoolIndoor.outputVariableNames():
        outvar = openstudio.model.OutputVariable(varname, model)
        outvar.setReportingFrequency(freq)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
