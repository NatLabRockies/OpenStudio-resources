import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 03, PSZ-AC
model.add_hvac(ashrae_sys_num="03")

# hot water system
plant = openstudio.model.PlantLoop(model)
pump = openstudio.model.PumpConstantSpeed(model)
pump.addToNode(plant.supplyInletNode())
hot_water_heater = openstudio.model.WaterHeaterMixed(model)
tempering_valve = openstudio.model.TemperingValve(model)
plant.addSupplyBranchForComponent(hot_water_heater)
plant.addSupplyBranchForComponent(tempering_valve)

hot_water_temp_sch = openstudio.model.ScheduleRuleset(model)
hot_water_temp_sch.setName("Hot_Water_Temperature")
hot_water_temp_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 55.0)
hot_water_spm = openstudio.model.SetpointManagerScheduled(model, hot_water_temp_sch)
hot_water_spm.addToNode(plant.supplyOutletNode())

water_connections = openstudio.model.WaterUseConnections(model)
plant.addDemandBranchForComponent(water_connections)
water_def = openstudio.model.WaterUseEquipmentDefinition(model)
water_equipment = openstudio.model.WaterUseEquipment(water_def)
water_connections.addWaterUseEquipment(water_equipment)

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
