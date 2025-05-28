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
# zones = m.getThermalZones.sort_by{|z| z.nameString}

p = m.getPerformancePrecisionTradeoffs()
p.setUseCoilDirectSolutions(True)

# save the OpenStudio model (.osm)
m.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
