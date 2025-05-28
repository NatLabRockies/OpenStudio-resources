import json

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

model.add_standards(
    json.loads(
        """{
  "schedules": [
    {
        "name": "Medium Office Bldg Swh",
        "category": "Service Water Heating",
        "units": null,
        "day_types": "Default|SmrDsn",
        "start_date": "2014-01-01T00:00:00+00:00",
        "end_date": "2014-12-31T00:00:00+00:00",
        "type": "Hourly",
        "notes": "From DOE Reference Buildings ",
        "values": [
          0.05, 0.05, 0.05, 0.05, 0.05, 0.08, 0.07, 0.19, 0.35, 0.38, 0.39, 0.47, 0.57, 0.54, 0.34, 0.33, 0.44, 0.26, 0.21, 0.15, 0.17, 0.08, 0.05, 0.05
        ]
      },
      {
        "name": "Medium Office Bldg Swh",
        "category": "Service Water Heating",
        "units": null,
        "day_types": "Sun",
        "start_date": "2014-01-01T00:00:00+00:00",
        "end_date": "2014-12-31T00:00:00+00:00",
        "type": "Hourly",
        "notes": "From DOE Reference Buildings ",
        "values": [
          0.04, 0.04, 0.04, 0.04, 0.04, 0.07, 0.04, 0.04, 0.04, 0.04, 0.04, 0.06, 0.06, 0.09, 0.06, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.07, 0.04, 0.04
        ]
      },
      {
        "name": "Medium Office Bldg Swh",
        "category": "Service Water Heating",
        "units": null,
        "day_types": "WntrDsn|Sat",
        "start_date": "2014-01-01T00:00:00+00:00",
        "end_date": "2014-12-31T00:00:00+00:00",
        "type": "Hourly",
        "notes": "From DOE Reference Buildings ",
        "values": [
          0.05, 0.05, 0.05, 0.05, 0.05, 0.08, 0.07, 0.11, 0.15, 0.21, 0.19, 0.23, 0.2, 0.19, 0.15, 0.13, 0.14, 0.07, 0.07, 0.07, 0.07, 0.09, 0.05, 0.05
        ]
      }
    ]
  }"""
    )
)

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 01, PTAC, Residential
model.add_hvac(ashrae_sys_num="01")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# create the swh loop and uses
mixed_swh_loop = model.add_swh_loop("Mixed")

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())
for thermal_zone in zones:
    model.add_swh_end_uses(mixed_swh_loop, "Medium Office Bldg Swh")


# remove the existing water heater
supply_components = mixed_swh_loop.supplyComponents(openstudio.IddObjectType("OS:WaterHeater:Mixed"))
swh_water_heater = supply_components[0].to_WaterHeaterMixed().get()
mixed_swh_loop.removeSupplyBranchWithComponent(swh_water_heater)

supply_components = mixed_swh_loop.supplyComponents(openstudio.IddObjectType("OS:Pipe:Adiabatic"))
swh_pipe = supply_components[0].to_PipeAdiabatic().get()
mixed_swh_loop.removeSupplyBranchWithComponent(swh_pipe)

supply_components = mixed_swh_loop.supplyComponents(openstudio.IddObjectType("OS:Pump:ConstantSpeed"))
swh_pump = supply_components[0].to_PumpConstantSpeed().get()

# storage water heating loop
storage_water_loop = openstudio.model.PlantLoop(model)
storage_water_loop.setName("Storage Water Loop")
storage_water_loop.setMaximumLoopTemperature(60)
storage_water_loop.setMinimumLoopTemperature(10)

# Temperature schedule type limits
temp_sch_type_limits = openstudio.model.ScheduleTypeLimits(model)
temp_sch_type_limits.setName("Temperature Schedule Type Limits")
temp_sch_type_limits.setLowerLimitValue(0.0)
temp_sch_type_limits.setUpperLimitValue(100.0)
temp_sch_type_limits.setNumericType("Continuous")
temp_sch_type_limits.setUnitType("Temperature")

# Storage water heating loop controls
storage_temp_f = 140
storage_delta_t_r = 9  # 9F delta-T
storage_temp_c = openstudio.convert(storage_temp_f, "F", "C").get()
storage_delta_t_k = openstudio.convert(storage_delta_t_r, "R", "K").get()
storage_temp_sch = openstudio.model.ScheduleRuleset(model)
storage_temp_sch.setName("Hot Water Loop Temp - #{storage_temp_f}F")
storage_temp_sch.defaultDaySchedule().setName("Hot Water Loop Temp - #{storage_temp_f}F Default")
storage_temp_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), storage_temp_c)
storage_temp_sch.setScheduleTypeLimits(temp_sch_type_limits)
storage_stpt_manager = openstudio.model.SetpointManagerScheduled(model, storage_temp_sch)
storage_stpt_manager.addToNode(storage_water_loop.supplyOutletNode())

storage_plant = storage_water_loop.sizingPlant()
storage_plant.setLoopType("Heating")
storage_plant.setDesignLoopExitTemperature(storage_temp_c)
storage_plant.setLoopDesignTemperatureDifference(storage_delta_t_k)

# Storage water heating pump
storage_pump_head_press_pa = 0.001
storage_pump_motor_efficiency = 1

storage_pump = openstudio.model.PumpConstantSpeed(model)
storage_pump.setName("Storage Water Loop Pump")
storage_pump.setRatedPumpHead(storage_pump_head_press_pa)
storage_pump.setMotorEfficiency(storage_pump_motor_efficiency)
storage_pump.setPumpControlType("Intermittent")
storage_pump.addToNode(storage_water_loop.supplyInletNode())

storage_water_heater = openstudio.model.WaterHeaterMixed(model)
storage_water_heater.setName("Storage Hot Water Tank")
storage_water_heater.setSetpointTemperatureSchedule(storage_temp_sch)
storage_water_heater.setHeaterMaximumCapacity(0.0)
# storage_water_heater.setDeadbandTemperatureDifference(openstudio.convert(3.6,'R','K').get)
# storage_water_heater.setHeaterControlType('Cycle')
# storage_water_heater.setTankVolume(openstudio.convert(water_heater_vol_gal,'gal','m^3').get)
storage_water_loop.addDemandBranchForComponent(storage_water_heater)

# make a solar collector and add it to the storage loop
vertices = openstudio.Point3dVector()
vertices.append(openstudio.Point3d(0, 0, 0))
vertices.append(openstudio.Point3d(10, 0, 0))
vertices.append(openstudio.Point3d(10, 4, 0))
vertices.append(openstudio.Point3d(0, 4, 0))
rotation = openstudio.createRotation(openstudio.Vector3d(1, 0, 0), openstudio.degToRad(30))
vertices = rotation * vertices

group = openstudio.model.ShadingSurfaceGroup(model)
group.setXOrigin(20)
group.setYOrigin(10)
group.setZOrigin(8)

shade = openstudio.model.ShadingSurface(vertices, model)
shade.setShadingSurfaceGroup(group)

collector = openstudio.model.SolarCollectorIntegralCollectorStorage(model)
storage_water_loop.addSupplyBranchForComponent(collector)
collector.setSurface(shade)

collector.setMaximumFlowRate(0.001)
# NOTE: there is no setter for bottomSurfaceBoundaryConditionsType
# (nor Boundary Condition model)

# Modify the Performance object
# (Here I hardset them exactly like the constructor does)
perf = collector.solarCollectorPerformance()
perf.setName("Solar Collector Performance Integral Collector Storage")
# Non idd defaults
perf.setGrossArea(shade.grossArea())
perf.setCollectorWaterVolume(0.1862)  # same as ctor (from HP_wICSSolarCollector.idf)
# IDD defaults
perf.setICSCollectorType("RectangularTank")
perf.setBottomHeatLossConductance(0.4)
perf.setSideHeatLossConductance(0.6)
perf.setAspectRatio(0.8)
perf.setCollectorSideHeight(0.2)
perf.setThermalMassOfAbsorberPlate(0.0)
perf.setNumberOfCovers(2)
perf.setCoverSpacing(0.05)
perf.setRefractiveIndexOfOuterCover(1.526)
perf.setExtinctionCoefficientTimesThicknessOfOuterCover(0.045)
perf.setRefractiveIndexOfInnerCover(1.37)
perf.setExtinctionCoefficientTimesThicknessOfTheInnerCover(0.008)
perf.setEmissivityOfInnerCover(0.88)
perf.setAbsorptanceOfAbsorberPlate(0.96)
perf.setEmissivityOfAbsorberPlate(0.3)

add_out_vars = False
if add_out_vars:
    for var in collector.outputVariableNames():
        openstudio.model.OutputVariable(var, model)


# add a storage tank to the swh loop
mixed_swh_loop.addSupplyBranchForComponent(storage_water_heater)

# add instantaneous swh water heater after the storage tank
swh_water_heater = openstudio.model.WaterHeaterMixed(model)
swh_water_heater.addToNode(mixed_swh_loop.supplyOutletNode())

# add a tempering valve
tempering_valve = openstudio.model.TemperingValve(model)
mixed_swh_loop.addSupplyBranchForComponent(tempering_valve)
tempering_valve.setStream2SourceNode(storage_water_heater.supplyOutletModelObject().get().to_Node().get())
tempering_valve.setTemperatureSetpointNode(swh_water_heater.supplyOutletModelObject().get().to_Node().get())
tempering_valve.setPumpOutletNode(swh_pump.outletModelObject().get().to_Node().get())

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
