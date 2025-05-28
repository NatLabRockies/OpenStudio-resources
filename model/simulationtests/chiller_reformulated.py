import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

schedule = model.alwaysOnDiscreteSchedule()

_chilledWaterSchedule = openstudio.model.ScheduleRuleset(model)
_chilledWaterSchedule.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 6.7)

# Chilled Water Plant
chilledWaterPlant = openstudio.model.PlantLoop(model)
sizingPlant = chilledWaterPlant.sizingPlant()
sizingPlant.setLoopType("Cooling")
sizingPlant.setDesignLoopExitTemperature(7.22)
sizingPlant.setLoopDesignTemperatureDifference(6.67)

chilledWaterOutletNode = chilledWaterPlant.supplyOutletNode()
chilledWaterInletNode = chilledWaterPlant.supplyInletNode()
chilledWaterDemandOutletNode = chilledWaterPlant.demandOutletNode()
chilledWaterDemandInletNode = chilledWaterPlant.demandInletNode()

pump2 = openstudio.model.PumpVariableSpeed(model)
pump2.addToNode(chilledWaterInletNode)

chiller = openstudio.model.ChillerElectricReformulatedEIR(model)

node = chilledWaterPlant.supplySplitter().lastOutletModelObject().get().to_Node().get()
chiller.addToNode(node)

pipe3 = openstudio.model.PipeAdiabatic(model)
chilledWaterPlant.addSupplyBranchForComponent(pipe3)

pipe4 = openstudio.model.PipeAdiabatic(model)
pipe4.addToNode(chilledWaterOutletNode)

chilledWaterSPM = openstudio.model.SetpointManagerScheduled(model, _chilledWaterSchedule)
chilledWaterSPM.addToNode(chilledWaterOutletNode)

chilledWaterBypass = openstudio.model.PipeAdiabatic(model)
chilledWaterDemandInlet = openstudio.model.PipeAdiabatic(model)
chilledWaterDemandOutlet = openstudio.model.PipeAdiabatic(model)
chilledWaterPlant.addDemandBranchForComponent(chilledWaterBypass)
chilledWaterDemandOutlet.addToNode(chilledWaterDemandOutletNode)
chilledWaterDemandInlet.addToNode(chilledWaterDemandInletNode)

# Condenser System
condenserSystem = openstudio.model.PlantLoop(model)
sizingPlant = condenserSystem.sizingPlant()
sizingPlant.setLoopType("Condenser")
sizingPlant.setDesignLoopExitTemperature(29.4)
sizingPlant.setLoopDesignTemperatureDifference(5.6)

distHeating = openstudio.model.DistrictHeating(model)
condenserSystem.addSupplyBranchForComponent(distHeating)

distCooling = openstudio.model.DistrictCooling(model)
condenserSystem.addSupplyBranchForComponent(distCooling)

condenserSupplyOutletNode = condenserSystem.supplyOutletNode()
condenserSupplyInletNode = condenserSystem.supplyInletNode()
condenserDemandOutletNode = condenserSystem.demandOutletNode()
condenserDemandInletNode = condenserSystem.demandInletNode()

pump3 = openstudio.model.PumpVariableSpeed(model)
pump3.addToNode(condenserSupplyInletNode)

condenserSystem.addDemandBranchForComponent(chiller)

condenserSupplyBypass = openstudio.model.PipeAdiabatic(model)
condenserSystem.addSupplyBranchForComponent(condenserSupplyBypass)

condenserSupplyOutlet = openstudio.model.PipeAdiabatic(model)
condenserSupplyOutlet.addToNode(condenserSupplyOutletNode)

condenserBypass = openstudio.model.PipeAdiabatic(model)
condenserDemandInlet = openstudio.model.PipeAdiabatic(model)
condenserDemandOutlet = openstudio.model.PipeAdiabatic(model)
condenserSystem.addDemandBranchForComponent(condenserBypass)
condenserDemandOutlet.addToNode(condenserDemandOutletNode)
condenserDemandInlet.addToNode(condenserDemandInletNode)

spm = openstudio.model.SetpointManagerFollowOutdoorAirTemperature(model)
spm.addToNode(condenserSupplyOutletNode)

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

airLoop_3 = openstudio.model.AirLoopHVAC(model)
airLoop_3_supplyNode = airLoop_3.supplyOutletNode()

unitary_3 = openstudio.model.AirLoopHVACUnitarySystem(model)
fan_3 = openstudio.model.FanConstantVolume(model, schedule)
cooling_coil_3 = openstudio.model.CoilCoolingWaterToAirHeatPumpEquationFit(model)
chilledWaterPlant.addDemandBranchForComponent(cooling_coil_3)
heating_coil_3 = openstudio.model.CoilHeatingGas(model, schedule)
unitary_3.setControllingZoneorThermostatLocation(zones[2])
unitary_3.setFanPlacement("BlowThrough")
unitary_3.setSupplyAirFanOperatingModeSchedule(schedule)
unitary_3.setSupplyFan(fan_3)
unitary_3.setCoolingCoil(cooling_coil_3)
unitary_3.setHeatingCoil(heating_coil_3)

unitary_3.addToNode(airLoop_3_supplyNode)

air_terminal_3 = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)
airLoop_3.addBranchForZone(zones[2], air_terminal_3)

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
