import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

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

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# NOTE: if you using this as an example for an actual project, you
# should change the curves to match a water cooled VRF...
# You should also control the Condenser Loop more carefully (the loop gets
# below freezing point...)
# This watercooled VRF example has +50% site EUI compared to vrf.rb example
vrf = openstudio.model.AirConditionerVariableRefrigerantFlow(model)

# E+ now throws when the CoolingEIRLowPLR has a curve minimum value of x which
# is higher than the Minimum Heat Pump Part-Load Ratio.
# The curve has a min of 0.5 here, so set the MinimumHeatPumpPartLoadRatio to
# the same value
vrf.setMinimumHeatPumpPartLoadRatio(0.5)

# Has to be DryBulbTemperature or you get a severe as WetBulbTemperature isn't
# supported for water-cooled VRFs
vrf.setHeatingPerformanceCurveOutdoorTemperatureType("DryBulbTemperature")

# Weirdly named, but that's the max inlet water temperature in heating mode
vrf.setMaximumOutdoorTemperatureinHeatingMode(60)

for z in zones:
    vrf_terminal = openstudio.model.ZoneHVACTerminalUnitVariableRefrigerantFlow(model)
    # Also test the supplemental heat capability that was added in 3.0.0 (#3687)
    supHC = openstudio.model.CoilHeatingElectric(model)
    vrf_terminal.setSupplementalHeatingCoil(supHC)
    vrf_terminal.autosizeMaximumSupplyAirTemperaturefromSupplementalHeater()
    vrf_terminal.setMaximumOutdoorDryBulbTemperatureforSupplementalHeaterOperation(21.0)
    vrf_terminal.addToThermalZone(z)
    vrf.addTerminal(vrf_terminal)


# Create a dummy loop to connect the VRF to
# (Controls could be better)
condenserSystem = openstudio.model.PlantLoop(model)
condenserSystem.setName("CW Loop")
sizingPlant = condenserSystem.sizingPlant()
sizingPlant.setLoopType("Condenser")
sizingPlant.setDesignLoopExitTemperature(29.4)
sizingPlant.setLoopDesignTemperatureDifference(5.6)

# Connect VRF to demand side of plant loop
# We do not hardcode the condenserType, so in the FT it will see that it's
# connected to a PlantLoop and set it to WaterCooled appropriately.
condenserSystem.addDemandBranchForComponent(vrf)
# condenserSystem.setCondenserType("WaterCooled")

# Set up supply side of the CW Loop
pump = openstudio.model.PumpVariableSpeed(model)
pump.addToNode(condenserSystem.supplyInletNode())

boiler = openstudio.model.BoilerHotWater(model)
condenserSystem.addSupplyBranchForComponent(boiler)

ct = openstudio.model.CoolingTowerSingleSpeed(model)
condenserSystem.addSupplyBranchForComponent(ct)

boilerWaterSchedule = openstudio.model.ScheduleRuleset(model, 60)
boilerWaterSchedule.setName("Boiler Water Schedule 60C")
lowWaterSchedule = openstudio.model.ScheduleRuleset(model, 20)
lowWaterSchedule.setName("Low Water Schedule 20C")
highWaterSchedule = openstudio.model.ScheduleRuleset(model, 30)
highWaterSchedule.setName("High Water Schedule 30C")

# This will set the Plant Loop Demand Calculation Scheme to "DualSetpoint"
# It means you can ONLY use SPM:DualSetpoint on that loop
loop_spm = openstudio.model.SetpointManagerScheduledDualSetpoint(model)
loop_spm.setControlVariable("Temperature")
loop_spm.setLowSetpointSchedule(lowWaterSchedule)
loop_spm.setHighSetpointSchedule(highWaterSchedule)
loop_spm.addToNode(condenserSystem.supplyOutletNode())

boiler_spm = openstudio.model.SetpointManagerScheduledDualSetpoint(model)
boiler_spm.setControlVariable("Temperature")
boiler_spm.setLowSetpointSchedule(lowWaterSchedule)
boiler_spm.setHighSetpointSchedule(boilerWaterSchedule)
boiler_spm.addToNode(boiler.outletModelObject().get().to_Node().get())

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
