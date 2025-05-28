import openstudio

from lib.baseline_model import BaselineModel

# use line below when running in ruby 2.0
# require_relative 'lib/baseline_model'

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac(ashrae_sys_num="07")

plant = openstudio.model.PlantLoop(model)
plant.setName("Economizing Plant")

sizingPlant = plant.sizingPlant()
sizingPlant.setLoopType("Condenser")
sizingPlant.setDesignLoopExitTemperature(26.0)
sizingPlant.setLoopDesignTemperatureDifference(5.6)

outletNode = plant.supplyOutletNode()
inletNode = plant.supplyInletNode()

s = openstudio.model.ScheduleConstant(model)
s.setValue(26.0)
spm = openstudio.model.SetpointManagerScheduled(model, s)
spm.addToNode(outletNode)

pump = openstudio.model.PumpVariableSpeed(model)
pump.addToNode(inletNode)

tower = openstudio.model.CoolingTowerVariableSpeed(model)
plant.addSupplyBranchForComponent(tower)

hx = openstudio.model.HeatExchangerFluidToFluid(model)
hx.setControlType("HeatingSetpointModulated")
plant.addDemandBranchForComponent(hx)

chiller = model.getChillerElectricEIRs()[0]
hx.addToNode(chiller.supplyInletModelObject().get().to_Node().get())

hx_outlet_node = hx.supplyOutletModelObject().get().to_Node().get()
# hotWaterOutletNode = plant.supplyOutletNode()
osTime = openstudio.Time(0, 24, 0, 0)
hotWaterTempSchedule = openstudio.model.ScheduleRuleset(model)
hotWaterTempSchedule.setName("Hot Water Temperature")

### Winter Design Day
hotWaterTempScheduleWinter = openstudio.model.ScheduleDay(model)
hotWaterTempSchedule.setWinterDesignDaySchedule(hotWaterTempScheduleWinter)
hotWaterTempSchedule.winterDesignDaySchedule().setName("Hot Water Temperature Winter Design Day")
hotWaterTempSchedule.winterDesignDaySchedule().addValue(osTime, 67)

### Summer Design Day
hotWaterTempScheduleSummer = openstudio.model.ScheduleDay(model)
hotWaterTempSchedule.setSummerDesignDaySchedule(hotWaterTempScheduleSummer)
hotWaterTempSchedule.summerDesignDaySchedule().setName("Hot Water Temperature Summer Design Day")
hotWaterTempSchedule.summerDesignDaySchedule().addValue(osTime, 67)

### All other days
hotWaterTempSchedule.defaultDaySchedule().setName("Hot Water Temperature Default")
hotWaterTempSchedule.defaultDaySchedule().addValue(osTime, 67)

hotWaterSPM = openstudio.model.SetpointManagerScheduled(model, hotWaterTempSchedule)
hotWaterSPM.addToNode(hx_outlet_node)

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
