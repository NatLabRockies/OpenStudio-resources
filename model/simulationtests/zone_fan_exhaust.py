import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 08, VAV w/ PFP Boxes
model.add_hvac(ashrae_sys_num="08")

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# find all the zones
north_zone = None
east_zone = None
south_zone = None
west_zone = None
core_zone = None
for zone in zones:
    if "North" in zone.nameString():
        north_zone = zone

    elif "East" in zone.nameString():
        east_zone = zone

    elif "South" in zone.nameString():
        south_zone = zone

    elif "West" in zone.nameString():
        west_zone = zone

    elif "Core" in zone.nameString():
        core_zone = zone


# add exhaust fan to north zone
# exhaust_rate = 1.71187 # calc heating design rate
# exhaust_rate = 1.61 # 5 ACH
# exhaust_rate = 0.047 # 100 cfm
exhaust_rate = 0.17

exhaust = openstudio.model.FanZoneExhaust(model)
exhaust.addToThermalZone(north_zone)
exhaust.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule())
exhaust.setMaximumFlowRate(exhaust_rate)
exhaust.setFlowFractionSchedule(model.alwaysOnContinuousSchedule())
exhaust.setBalancedExhaustFractionSchedule(model.alwaysOnContinuousSchedule())

# add mixing air from core zone to north zone
m = openstudio.model.ZoneMixing(north_zone)
m.setSourceZone(core_zone)
m.setDesignFlowRate(exhaust_rate)
m.setSchedule(model.alwaysOnContinuousSchedule())

# add mixing air from east, south, and west zones to core zone
m = openstudio.model.ZoneMixing(core_zone)
m.setSourceZone(east_zone)
m.setDesignFlowRate(exhaust_rate / 3.0)
m.setSchedule(model.alwaysOnContinuousSchedule())

m = openstudio.model.ZoneMixing(core_zone)
m.setSourceZone(south_zone)
m.setDesignFlowRate(exhaust_rate / 3.0)
m.setSchedule(model.alwaysOnContinuousSchedule())

m = openstudio.model.ZoneMixing(core_zone)
m.setSourceZone(west_zone)
m.setDesignFlowRate(exhaust_rate / 3.0)
m.setSchedule(model.alwaysOnContinuousSchedule())

# conserve some mass
zamfc = model.getZoneAirMassFlowConservation()
zamfc.setAdjustZoneMixingForZoneAirMassFlowBalance(True)
if openstudio.VersionString(openstudio.openStudioVersion()) <= openstudio.VersionString("3.4.0"):
    # Does nothing as of 1.9.3, removed after 3.4.0
    zamfc.setSourceZoneInfiltrationTreatment("AddInfiltrationFlow")


# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# add zone exhaust
for z in zones:
    # TODO: given the above comment "add zone exhaust", it looks like it's
    # missing the actual zone exhaust object...
    print(z)


# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# add output reports
add_out_vars = False
if add_out_vars:
    openstudio.model.OutputVariable("Zone Mixing Volume", model)
    openstudio.model.OutputVariable("Zone Supply Air Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Exhaust Air Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Return Air Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Mixing Receiving Air Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Mixing Source Air Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Infiltration Air Mass Flow Balance Status", model)
    openstudio.model.OutputVariable("Zone Mass Balance Infiltration Air Mass Flow Rate", model)
    openstudio.model.OutputVariable("System Node Mass Flow Rate", model)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
