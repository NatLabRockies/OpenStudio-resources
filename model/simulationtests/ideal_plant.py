import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 03, PSZ-AC
model.add_hvac(ashrae_sys_num="03")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

plant = openstudio.model.PlantLoop(model)
sizing = plant.sizingPlant()
sizing.setLoopType("Heating")
sizing.setDesignLoopExitTemperature(82.0)
sizing.setLoopDesignTemperatureDifference(11.0)

pump = openstudio.model.PumpVariableSpeed(model)
pump.addToNode(plant.supplyOutletNode())

source = openstudio.model.PlantComponentTemperatureSource(model)
source.setSourceTemperature(67.0)
plant.addSupplyBranchForComponent(source)

plantload = openstudio.model.LoadProfilePlant(model)
plant.addDemandBranchForComponent(plantload)

osTime = openstudio.Time(0, 24, 0, 0)
hotWaterTempSchedule = openstudio.model.ScheduleRuleset(model)
hotWaterTempSchedule.setName("Hot Water Temperature")

hotWaterTempSchedule.defaultDaySchedule().setName("Hot Water Temperature Default")
hotWaterTempSchedule.defaultDaySchedule().addValue(osTime, 67)

hotWaterSPM = openstudio.model.SetpointManagerScheduled(model, hotWaterTempSchedule)
hotWaterSPM.addToNode(plant.supplyOutletNode())

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
