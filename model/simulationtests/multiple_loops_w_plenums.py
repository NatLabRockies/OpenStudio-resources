import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 07, VAV w/ Reheat
# model.add_hvac({"ashrae_sys_num" => '07'})

hvac1 = openstudio.model.addSystemType7(model).to_AirLoopHVAC().get()
hvac2 = openstudio.model.addSystemType7(model).to_AirLoopHVAC().get()

story_1_core_thermal_zone = model.getThermalZoneByName("Story 1 Core Thermal Zone").get()
story_2_core_thermal_zone = model.getThermalZoneByName("Story 2 Core Thermal Zone").get()

story_1_north_thermal_zone = model.getThermalZoneByName("Story 1 North Perimeter Thermal Zone").get()
story_1_south_thermal_zone = model.getThermalZoneByName("Story 1 South Perimeter Thermal Zone").get()
story_1_east_thermal_zone = model.getThermalZoneByName("Story 1 East Perimeter Thermal Zone").get()
story_1_west_thermal_zone = model.getThermalZoneByName("Story 1 West Perimeter Thermal Zone").get()

story_2_north_thermal_zone = model.getThermalZoneByName("Story 2 North Perimeter Thermal Zone").get()
story_2_south_thermal_zone = model.getThermalZoneByName("Story 2 South Perimeter Thermal Zone").get()
story_2_east_thermal_zone = model.getThermalZoneByName("Story 2 East Perimeter Thermal Zone").get()
story_2_west_thermal_zone = model.getThermalZoneByName("Story 2 West Perimeter Thermal Zone").get()

hvac1.addBranchForZone(story_1_north_thermal_zone)
hvac1.addBranchForZone(story_1_south_thermal_zone)
hvac1.addBranchForZone(story_1_east_thermal_zone)
hvac1.addBranchForZone(story_1_west_thermal_zone)
hvac1.addBranchForZone(story_2_north_thermal_zone)
hvac1.addBranchForZone(story_2_south_thermal_zone)
hvac1.addBranchForZone(story_2_east_thermal_zone)
hvac1.addBranchForZone(story_2_west_thermal_zone)

hvac2.multiAddBranchForZone(story_1_north_thermal_zone)
hvac2.multiAddBranchForZone(story_1_south_thermal_zone)
hvac2.multiAddBranchForZone(story_1_east_thermal_zone)
hvac2.multiAddBranchForZone(story_1_west_thermal_zone)
hvac2.multiAddBranchForZone(story_2_north_thermal_zone)
hvac2.multiAddBranchForZone(story_2_south_thermal_zone)
hvac2.multiAddBranchForZone(story_2_east_thermal_zone)
hvac2.multiAddBranchForZone(story_2_west_thermal_zone)

story_1_north_thermal_zone.setReturnPlenum(story_1_core_thermal_zone, hvac1)
story_1_south_thermal_zone.setReturnPlenum(story_1_core_thermal_zone, hvac1)
story_1_east_thermal_zone.setReturnPlenum(story_1_core_thermal_zone, hvac1)
story_1_west_thermal_zone.setReturnPlenum(story_1_core_thermal_zone, hvac1)

story_2_north_thermal_zone.setReturnPlenum(story_1_core_thermal_zone, hvac1)
story_2_south_thermal_zone.setReturnPlenum(story_1_core_thermal_zone, hvac1)
story_2_east_thermal_zone.setReturnPlenum(story_1_core_thermal_zone, hvac1)
story_2_west_thermal_zone.setReturnPlenum(story_1_core_thermal_zone, hvac1)

story_2_north_thermal_zone.setReturnPlenum(story_2_core_thermal_zone, hvac2)
story_2_south_thermal_zone.setReturnPlenum(story_2_core_thermal_zone, hvac2)
story_2_east_thermal_zone.setReturnPlenum(story_2_core_thermal_zone, hvac2)
story_2_west_thermal_zone.setReturnPlenum(story_2_core_thermal_zone, hvac2)

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
