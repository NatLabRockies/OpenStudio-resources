# This file aims to test the PlantEquipmentOperation based on outdoor
# conditions: OutdoorDryBulb, OutdoorDewpoint and OutdoorRelativeHumidity
# (OutdoorWetBulb is tested in plant_op_schemes.rb)

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac(ashrae_sys_num="07")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# manually add op schemes instead of depending on os defaults

# Test the OA RH one, between 0 and 50 percent, one chiller, above two
chiller = model.getChillerElectricEIRs()[0]
chilled_plant = chiller.plantLoop().get()
chiller2 = openstudio.model.ChillerElectricEIR(model)
chilled_plant.addSupplyBranchForComponent(chiller2)

# A default constructed load scheme has a single large load range
plant_op_oa_rh = openstudio.model.PlantEquipmentOperationOutdoorRelativeHumidity(model)
plant_op_oa_rh.addEquipment(chiller)
plant_op_oa_rh.addEquipment(chiller2)
# This cuts the load range into two pieces with only chiller operating on the lower end of the range
# See PlantEquipmentOperationRangeBasedScheme for details about this api
plant_op_oa_rh.addLoadRange(50, [chiller])
chilled_plant.setPrimaryPlantEquipmentOperationScheme(plant_op_oa_rh)

# Test the plant OA Db one: below 0C, two boilers, above only one
boiler = model.getBoilerHotWaters()[0]
heating_plant = boiler.plantLoop().get()
boiler2 = openstudio.model.BoilerHotWater(model)
heating_plant.addSupplyBranchForComponent(boiler2)

plant_op_oa_db = openstudio.model.PlantEquipmentOperationOutdoorDryBulb(model)
plant_op_oa_db.addEquipment(boiler)
plant_op_oa_db.addLoadRange(0, [boiler, boiler2])
heating_plant.setPrimaryPlantEquipmentOperationScheme(plant_op_oa_db)

# Test the Plant OA Dewpoint, if the dewpoint is below 18C, no towers, above one
tower = model.getCoolingTowerSingleSpeeds()[0]
cond = tower.plantLoop().get()

plant_op_oa_dew = openstudio.model.PlantEquipmentOperationOutdoorDewpoint(model)
plant_op_oa_dew.addEquipment(tower)
plant_op_oa_dew.addLoadRange(18.0, [])
cond.setPrimaryPlantEquipmentOperationScheme(plant_op_oa_dew)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
