import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# Add a hot water plant to supply the water to air heat pump
# This could be baked into HVAC templates in the future
hotWaterPlant = openstudio.model.PlantLoop(model)
hotWaterPlant.setName("Hot Water Plant")

sizingPlant = hotWaterPlant.sizingPlant()
sizingPlant.setLoopType("Heating")
sizingPlant.setDesignLoopExitTemperature(60.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

hotWaterOutletNode = hotWaterPlant.supplyOutletNode()
hotWaterInletNode = hotWaterPlant.supplyInletNode()

heatingPump = openstudio.model.PumpVariableSpeed(model)
heatingPump.addToNode(hotWaterInletNode)

# create a chilled water plant
chilledWaterPlant = openstudio.model.PlantLoop(model)
chilledWaterPlant.setName("Chilled Water Plant")

sizingPlant = chilledWaterPlant.sizingPlant()
sizingPlant.setLoopType("Cooling")
sizingPlant.setDesignLoopExitTemperature(10.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

chilledWaterOutletNode = chilledWaterPlant.supplyOutletNode()
chilledWaterInletNode = chilledWaterPlant.supplyInletNode()

coolingPump = openstudio.model.PumpVariableSpeed(model)
coolingPump.addToNode(chilledWaterInletNode)

distHeating = openstudio.model.DistrictHeating(model)
hotWaterPlant.addSupplyBranchForComponent(distHeating)

distCooling = openstudio.model.DistrictCooling(model)
chilledWaterPlant.addSupplyBranchForComponent(distCooling)

pipe_h = openstudio.model.PipeAdiabatic(model)
hotWaterPlant.addSupplyBranchForComponent(pipe_h)

pipe_h1 = openstudio.model.PipeAdiabatic(model)
pipe_h1.addToNode(hotWaterOutletNode)

pipe_c = openstudio.model.PipeAdiabatic(model)
chilledWaterPlant.addSupplyBranchForComponent(pipe_c)

pipe_c1 = openstudio.model.PipeAdiabatic(model)
pipe_c1.addToNode(chilledWaterOutletNode)

## Make a Hot Water temperature schedule

osTime = openstudio.Time(0, 24, 0, 0)

hotWaterTempSchedule = openstudio.model.ScheduleRuleset(model)
hotWaterTempSchedule.setName("Hot Water Temperature")
### Winter Design Day
hotWaterTempScheduleWinter = openstudio.model.ScheduleDay(model)
hotWaterTempSchedule.setWinterDesignDaySchedule(hotWaterTempScheduleWinter)
hotWaterTempSchedule.winterDesignDaySchedule().setName("Hot Water Temperature Winter Design Day")
hotWaterTempSchedule.winterDesignDaySchedule().addValue(osTime, 24)
### Summer Design Day
hotWaterTempScheduleSummer = openstudio.model.ScheduleDay(model)
hotWaterTempSchedule.setSummerDesignDaySchedule(hotWaterTempScheduleSummer)
hotWaterTempSchedule.summerDesignDaySchedule().setName("Hot Water Temperature Summer Design Day")
hotWaterTempSchedule.summerDesignDaySchedule().addValue(osTime, 24)
### All other days
hotWaterTempSchedule.defaultDaySchedule().setName("Hot Water Temperature Default")
hotWaterTempSchedule.defaultDaySchedule().addValue(osTime, 24)

hotWaterSPM = openstudio.model.SetpointManagerScheduled(model, hotWaterTempSchedule)
hotWaterSPM.addToNode(hotWaterOutletNode)

## Make a Chilled Water temperature schedule

chilledWaterTempSchedule = openstudio.model.ScheduleRuleset(model)
chilledWaterTempSchedule.setName("Chilled Water Temperature")
### Winter Design Day
chilledWaterTempScheduleWinter = openstudio.model.ScheduleDay(model)
chilledWaterTempSchedule.setWinterDesignDaySchedule(chilledWaterTempScheduleWinter)
chilledWaterTempSchedule.winterDesignDaySchedule().setName("Chilled Water Temperature Winter Design Day")
chilledWaterTempSchedule.winterDesignDaySchedule().addValue(osTime, 24)
### Summer Design Day
chilledWaterTempScheduleSummer = openstudio.model.ScheduleDay(model)
chilledWaterTempSchedule.setSummerDesignDaySchedule(chilledWaterTempScheduleSummer)
chilledWaterTempSchedule.summerDesignDaySchedule().setName("Chilled Water Temperature Summer Design Day")
chilledWaterTempSchedule.summerDesignDaySchedule().addValue(osTime, 24)
### All other days
chilledWaterTempSchedule.defaultDaySchedule().setName("Chilled Water Temperature Default")
chilledWaterTempSchedule.defaultDaySchedule().addValue(osTime, 24)

chilledWaterSPM = openstudio.model.SetpointManagerScheduled(model, chilledWaterTempSchedule)
chilledWaterSPM.addToNode(chilledWaterOutletNode)

heatingControlTemperatureSched = openstudio.model.ScheduleConstant(model)
coolingControlTemperatureSched = openstudio.model.ScheduleConstant(model)

heatingControlTemperatureSched.setValue(10.0)
coolingControlTemperatureSched.setValue(15.0)

for z in zones:
    heat_coil = openstudio.model.CoilHeatingLowTempRadiantVarFlow(model, heatingControlTemperatureSched)
    cool_coil = openstudio.model.CoilCoolingLowTempRadiantVarFlow(model, coolingControlTemperatureSched)

    lowtempradiant = openstudio.model.ZoneHVACLowTempRadiantVarFlow(
        model, model.alwaysOnDiscreteSchedule(), heat_coil, cool_coil
    )
    lowtempradiant.setRadiantSurfaceType("Floors")
    lowtempradiant.setHydronicTubingInsideDiameter(0.154)
    lowtempradiant.setTemperatureControlType("MeanRadiantTemperature")

    lowtempradiant.addToThermalZone(z)

    hotWaterPlant.addDemandBranchForComponent(heat_coil)
    chilledWaterPlant.addDemandBranchForComponent(cool_coil)


# add thermostats
# model.add_thermostats({"heating_setpoint" => 24,"cooling_setpoint" => 28})

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# create an internalsourceconstruction

intSourceConst = openstudio.model.ConstructionWithInternalSource(model)
intSourceConst.setSourcePresentAfterLayerNumber(3)
intSourceConst.setTemperatureCalculationRequestedAfterLayerNumber(3)
concrete_sand_gravel = openstudio.model.StandardOpaqueMaterial(
    model, "MediumRough", 0.1014984, 1.729577, 2242.585, 836.8
)
rigid_insulation_2inch = openstudio.model.StandardOpaqueMaterial(model, "Rough", 0.05, 0.02, 56.06, 1210)
gyp1 = openstudio.model.StandardOpaqueMaterial(model, "MediumRough", 0.0127, 0.7845, 1842.1221, 988)
gyp2 = openstudio.model.StandardOpaqueMaterial(model, "MediumRough", 0.01905, 0.7845, 1842.1221, 988)
finished_floor = openstudio.model.StandardOpaqueMaterial(model, "Smooth", 0.0016, 0.17, 1922.21, 1250)
layers = [
    concrete_sand_gravel,
    rigid_insulation_2inch,
    gyp1,
    gyp2,
    finished_floor,
]  # openstudio.model.MaterialVector(model)

intSourceConst.setLayers(layers)

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# find a surface that's of surface type floor and assign the surface internal source construction
for s in model.getSurfaces():
    if s.surfaceType() == "Floor":
        s.setConstruction(intSourceConst)


# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
