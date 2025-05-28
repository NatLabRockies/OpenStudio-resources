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

# In order to produce more consistent results between different runs,
# we sort the zones by names (only one here anyways...)
zones = sorted(m.getThermalZones(), key=lambda z: z.nameString())

# The Sizing:Zone object is translated to IDF only if:
# The thermal is translated, and it has at least one equipment / ideal air
# loads and we have design days
# Use Ideal Air Loads
for z in zones:
    z.setUseIdealAirLoads(True)

sz = zones[0].sizingZone()

# The DesignSpecification:ZoneAirDistribution is only translated if we set the
# fields that live on OS:Sizing:Zone
sz.setDesignZoneAirDistributionEffectivenessinCoolingMode(0.8)
sz.setDesignZoneAirDistributionEffectivenessinHeatingMode(0.75)

# New in 3.0.0, but we set it to the default of 0, so we can compare between
# versions, while still showing API
if openstudio.VersionString(openstudio.openStudioVersion()) > openstudio.VersionString("2.9.1"):
    sz.setDesignZoneSecondaryRecirculationFraction(0.0)
    sz.setDesignMinimumZoneVentilationEfficiency(0.0)


# save the OpenStudio model (.osm)
m.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
