# This file aims to test the PlantEquipmentOperation based on the difference
# between outdoor conditions and a reference node:
# OutdoorDryBulbDifference, OutdoorDewpointDifference and OutdoorWetBulbDifference
# These three mostly apply to condenser equipment, but in order to not
# duplicate tests unceserarilly, I will apply some to chiller/boiler loops

# NOTE: All of these delta temp schemes compare based on
# (Node condition - Outdoor condition)
# Meaning if a range from 0 to 5 degC difference, means OA condition is between
# 0 to 5 LOWER than the node
# They also all expect a WATER node as the reference temperature node
# (so you can't pass model.outdoorAirNode for eg)

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

# Note there are only 3 plant loops (heating/cooling/condenser) so this test is
# reliable by using model.getCoolingTowerSingleSpeeds.first for eg

# Test the Plant OA Wetbulb Difference, between the pump outlet and OA WB
# We set reference node to the pump outlet, which is the inlet temp to the cooling
# towers. So Looking at difference between CT inlet and OA Wetbulb, we are
# controlling on the cooling tower approach

tower = model.getCoolingTowerSingleSpeeds()[0]
cond = tower.plantLoop().get()
tower2 = openstudio.model.CoolingTowerSingleSpeed(model)
cond.addSupplyBranchForComponent(tower2)

cond_pump = cond.supplyComponents(openstudio.IddObjectType("OS_Pump_VariableSpeed"))[0].to_PumpVariableSpeed().get()
cond_pump_outlet_node = cond_pump.outletModelObject().get().to_Node().get()

# NOTE: Prior to E+ 23.1.0 (OS 3.6.0), the PlantEq based on outdoor temperature
# were not working correctly in E+ and the equipment would not turn on
# see https://github.com/NREL/energyplus/pull/9727
plant_op_oa_wb_diff = openstudio.model.PlantEquipmentOperationOutdoorWetBulbDifference(model)
plant_op_oa_wb_diff.setReferenceTemperatureNode(cond_pump_outlet_node)

# Below 5, don't even try to cool, it won't work or barely and will use too
# much fan
# Between 5 and 7, run one tower, above, run both
plant_op_oa_wb_diff.addEquipment(tower)
plant_op_oa_wb_diff.addEquipment(tower2)
plant_op_oa_wb_diff.addLoadRange(7, [tower])
plant_op_oa_wb_diff.addLoadRange(5, [])

cond.setPrimaryPlantEquipmentOperationScheme(plant_op_oa_wb_diff)

# Test the OA Dewpoint diff one, we control it based on the condenser loop pump
# outlet temperature, and if there is no difference, we don't use the
# chillers...
# note: It doesn't make any sense from a desgin standpoint, but I couldn't think
# of a smarter example and there are no E+ examples for this object...
chiller = model.getChillerElectricEIRs()[0]
chilled_plant = chiller.plantLoop().get()
chiller2 = openstudio.model.ChillerElectricEIR(model)
chilled_plant.addSupplyBranchForComponent(chiller2)

plant_op_oa_dew_diff = openstudio.model.PlantEquipmentOperationOutdoorDewpointDifference(model)
plant_op_oa_dew_diff.setReferenceTemperatureNode(cond_pump_outlet_node)

plant_op_oa_dew_diff.addEquipment(chiller)
plant_op_oa_dew_diff.addEquipment(chiller2)
# This cuts the load range into two pieces with only chiller operating on the lower end of the range
# See PlantEquipmentOperationRangeBasedScheme for details about this api
plant_op_oa_dew_diff.addLoadRange(0, [])
chilled_plant.setPrimaryPlantEquipmentOperationScheme(plant_op_oa_dew_diff)

# Test the plant OA Db diff one. If the OA drybulb temperature is greater than
# 10 degC above the supply inlet temperature to the heating plant loop,
# we turn off the boilers
# Note: doesn't make a ton of sense from a design standpoint...
boiler = model.getBoilerHotWaters()[0]
heating_plant = boiler.plantLoop().get()
boiler2 = openstudio.model.BoilerHotWater(model)
heating_plant.addSupplyBranchForComponent(boiler2)

plant_op_oa_db_diff = openstudio.model.PlantEquipmentOperationOutdoorDryBulbDifference(model)
plant_op_oa_db_diff.setReferenceTemperatureNode(heating_plant.supplyInletNode())

# OA > Node + 10 <=> (Node - OA) < -10
plant_op_oa_db_diff.addLoadRange(-10, [boiler, boiler2])
heating_plant.setPrimaryPlantEquipmentOperationScheme(plant_op_oa_db_diff)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
