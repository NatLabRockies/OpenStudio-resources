import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

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

# We manually create our own HVAC system
air_system = openstudio.model.addSystemType6(model).to_AirLoopHVAC().get()

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

zone = zones[0]
air_system.addBranchForZone(zone)
coil = (
    air_system.supplyComponents(openstudio.model.CoilCoolingDXTwoSpeed.iddObjectType())[0]
    .to_CoilCoolingDXTwoSpeed()
    .get()
)
unitary = openstudio.model.AirLoopHVACUnitarySystem(model)
try:
    unitary.setControlType("SetPoint")
except Exception:
    # For (much) older OS Versions where the method wasn't implemented yet
    # (I think 2.3.1 was the first where setControlType was implemented)
    unitary.setString(2, "SetPoint")

# new_coil = openstudio.model.CoilCoolingWaterToAirHeatPumpEquationFit(model)
new_coil = openstudio.model.CoilCoolingDXSingleSpeed(model)
unitary.setCoolingCoil(new_coil)
unitary.addToNode(coil.outletModelObject().get().to_Node().get())
coil.remove()

# fan = air_system.supplyComponents(openstudio.model.FanVariableVolume.iddObjectType).first.to_FanVariableVolume.get
# new_fan = openstudio.model.FanConstantVolume(model)
# new_fan.addToNode(fan.outletModelObject().get.to_Node.get)
# fan.remove

hotWaterPlant = openstudio.model.PlantLoop(model)
sizingPlant = hotWaterPlant.sizingPlant()
sizingPlant.setLoopType("Heating")
sizingPlant.setDesignLoopExitTemperature(82.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

hotWaterOutletNode = hotWaterPlant.supplyOutletNode()
hotWaterInletNode = hotWaterPlant.supplyInletNode()
hotWaterDemandOutletNode = hotWaterPlant.demandOutletNode()
hotWaterDemandInletNode = hotWaterPlant.demandInletNode()

pump = openstudio.model.PumpVariableSpeed(model)
boiler = openstudio.model.BoilerHotWater(model)

pump.addToNode(hotWaterInletNode)
node = hotWaterPlant.supplySplitter().lastOutletModelObject().get().to_Node().get()
boiler.addToNode(node)

pipe = openstudio.model.PipeAdiabatic(model)
hotWaterPlant.addSupplyBranchForComponent(pipe)

hotWaterBypass = openstudio.model.PipeAdiabatic(model)
hotWaterDemandInlet = openstudio.model.PipeAdiabatic(model)
hotWaterDemandOutlet = openstudio.model.PipeAdiabatic(model)
hotWaterPlant.addDemandBranchForComponent(hotWaterBypass)
hotWaterDemandOutlet.addToNode(hotWaterDemandOutletNode)
hotWaterDemandInlet.addToNode(hotWaterDemandInletNode)

pipe2 = openstudio.model.PipeAdiabatic(model)
pipe2.addToNode(hotWaterOutletNode)

hotWaterSchedule = openstudio.model.ScheduleRuleset(model)
hotWaterSchedule.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 67)

hotWaterSPM = openstudio.model.SetpointManagerScheduled(model, hotWaterSchedule)
hotWaterSPM.addToNode(hotWaterOutletNode)

hotWaterPlant.addDemandBranchForComponent(new_coil)

# add output reports
add_out_vars = False
if add_out_vars:
    var = openstudio.model.OutputVariable("Cooling Coil Total Cooling Rate", model)
    var.setReportingFrequency("detailed")


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
