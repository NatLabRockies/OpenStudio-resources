import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 03, PSZ-AC
model.add_hvac(ashrae_sys_num="03")

# air_system = model.getAirLoopHVACs.first
# If we get the first airLoopHVAC from the example model using the above
# We cannot ensure we'll get the same one each time on subsequent runs
# (they may be in different order in the model)
# So we rely on ThermalZone names, and get the airLoopHVAC from there
# Sort the zones by name
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())
# Get the first zone, get its PTAC's fan.
z = zones[0]
air_system = z.airLoopHVAC().get()

oa_node = air_system.airLoopHVACOutdoorAirSystem().get().outboardOANode().get()

direct_evap = openstudio.model.EvaporativeCoolerDirectResearchSpecial(model, model.alwaysOnDiscreteSchedule())
direct_evap.addToNode(oa_node)

indirect_evap = openstudio.model.EvaporativeCoolerIndirectResearchSpecial(model)
indirect_evap.addToNode(oa_node)

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
