import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# add ASHRAE System type 07, VAV w/ Reheat: this sets up the loops we want
model.add_hvac(ashrae_sys_num="07")

# In order to produce more consistent results between different runs,
# We ensure we do get the same object each time
cts = sorted(model.getCoolingTowerSingleSpeeds(), key=lambda c: c.nameString())
chillers = sorted(model.getChillerElectricEIRs(), key=lambda c: c.nameString())
chiller = chillers[0]
boilers = sorted(model.getBoilerHotWaters(), key=lambda c: c.nameString())
condenser_loop = cts[0].plantLoop().get()
cooling_loop = chillers[0].plantLoop().get()
heating_loop = boilers[0].plantLoop().get()
condenser_loop.setName("CndW Loop")
heating_loop.setName("HW Loop")
cooling_loop.setName("ChW Loop")

# We'll setup a WaterHeater:Mixed that sits on the **supply side**
# of TWO plant loops:
# * Use Side: the Heating Loop
# * Source Side: the Heat Recovery loop, on the demand side you find the
# chiller
# (Note that you could also just place the chiller on the demand side of
# the HW loop directly, but that's not what we're testing here)

heat_recovery_loop = openstudio.model.PlantLoop(model)
heat_recovery_loop.setName("HeatRecovery Loop")
hr_pump = openstudio.model.PumpVariableSpeed(model)
hr_pump.setName("#{heat_recovery_loop.nameString()} VSD Pump")
hr_pump.addToNode(heat_recovery_loop.supplyInletNode())

hr_spm_sch = openstudio.model.ScheduleRuleset(model)
hr_spm_sch.setName("Hot_Water_Temperature")
hr_spm_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 25.0)
hr_spm = openstudio.model.SetpointManagerScheduled(model, hr_spm_sch)
hr_spm.addToNode(heat_recovery_loop.supplyOutletNode())

# Water Heater Mixed
water_heater_mixed = openstudio.model.WaterHeaterMixed(model)
water_heater_mixed.setName("Heat Recovery Tank")
# The first addSupplyBranchForComponent / addToNode to a supply side will
# connect the Use Side, so heating loop here
heating_loop.addSupplyBranchForComponent(water_heater_mixed)
assert water_heater_mixed.plantLoop().is_initialized()

# The Second with a supply side node, if use side already connected, will
# connect the Source Side. You can also be explicit and call
# addToSourceSideNode

# pipe = openstudio.model.PipeAdiabatic(model)
# heat_recovery_loop.addSupplyBranchForComponent(pipe)
# water_heater_mixed.addToSourceSideNode(pipe.inletModelObject.get.to_Node.get)
# pipe.remove
heat_recovery_loop.addSupplyBranchForComponent(water_heater_mixed)

assert water_heater_mixed.plantLoop().is_initialized()
assert water_heater_mixed.secondaryPlantLoop().is_initialized()
# More convenient name aliases
assert water_heater_mixed.useSidePlantLoop().is_initialized()
assert water_heater_mixed.sourceSidePlantLoop().is_initialized()
assert water_heater_mixed.useSidePlantLoop().get() == heating_loop
assert water_heater_mixed.sourceSidePlantLoop().get() == heat_recovery_loop

# Connect the chiller to the HR loop
# Since the secondary loop is already connected (condenser loop)
# and this is a node on the **demand** side of a **different** loop than the
# condenser loop, this will call `chiller.addToTertiaryNode`
heat_recovery_loop.addDemandBranchForComponent(chiller)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
