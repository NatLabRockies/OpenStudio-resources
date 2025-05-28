# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'
require 'json'

model = BaselineModel.new

model.add_standards(JSON.parse('{
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
  }'))

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 2,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 1,
                     'perimeter_zone_depth' => 3 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add ASHRAE System type 01, PTAC, Residential
model.add_hvac({ 'ashrae_sys_num' => '01' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# create the swh loop and uses
mixed_swh_loop = model.add_swh_loop('Mixed')
model.add_swh_end_uses(mixed_swh_loop, 'Medium Office Bldg Swh')

# remove the existing water heater
supply_components = mixed_swh_loop.supplyComponents('OS:WaterHeater:Mixed'.to_IddObjectType)
swh_water_heater = supply_components.first.to_WaterHeaterMixed.get
mixed_swh_loop.removeSupplyBranchWithComponent(swh_water_heater)

supply_components = mixed_swh_loop.supplyComponents('OS:Pipe:Adiabatic'.to_IddObjectType)
swh_pipe = supply_components.first.to_PipeAdiabatic.get
mixed_swh_loop.removeSupplyBranchWithComponent(swh_pipe)

supply_components = mixed_swh_loop.supplyComponents('OS:Pump:ConstantSpeed'.to_IddObjectType)
swh_pump = supply_components.first.to_PumpConstantSpeed.get

# storage water heating loop
storage_water_loop = OpenStudio::Model::PlantLoop.new(model)
storage_water_loop.setName('Storage Water Loop')
storage_water_loop.setMaximumLoopTemperature(60)
storage_water_loop.setMinimumLoopTemperature(10)

# Temperature schedule type limits
temp_sch_type_limits = OpenStudio::Model::ScheduleTypeLimits.new(model)
temp_sch_type_limits.setName('Temperature Schedule Type Limits')
temp_sch_type_limits.setLowerLimitValue(0.0)
temp_sch_type_limits.setUpperLimitValue(100.0)
temp_sch_type_limits.setNumericType('Continuous')
temp_sch_type_limits.setUnitType('Temperature')

# Storage water heating loop controls
storage_temp_f = 140
storage_delta_t_r = 9 # 9F delta-T
storage_temp_c = OpenStudio.convert(storage_temp_f, 'F', 'C').get
storage_delta_t_k = OpenStudio.convert(storage_delta_t_r, 'R', 'K').get
storage_temp_sch = OpenStudio::Model::ScheduleRuleset.new(model)
storage_temp_sch.setName("Hot Water Loop Temp - #{storage_temp_f}F")
storage_temp_sch.defaultDaySchedule.setName("Hot Water Loop Temp - #{storage_temp_f}F Default")
storage_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), storage_temp_c)
storage_temp_sch.setScheduleTypeLimits(temp_sch_type_limits)
storage_stpt_manager = OpenStudio::Model::SetpointManagerScheduled.new(model, storage_temp_sch)
storage_stpt_manager.addToNode(storage_water_loop.supplyOutletNode)

storage_plant = storage_water_loop.sizingPlant
storage_plant.setLoopType('Heating')
storage_plant.setDesignLoopExitTemperature(storage_temp_c)
storage_plant.setLoopDesignTemperatureDifference(storage_delta_t_k)

# Storage water heating pump
storage_pump_head_press_pa = 0.001
storage_pump_motor_efficiency = 1

storage_pump = OpenStudio::Model::PumpConstantSpeed.new(model)
storage_pump.setName('Storage Water Loop Pump')
storage_pump.setRatedPumpHead(storage_pump_head_press_pa.to_f)
storage_pump.setMotorEfficiency(storage_pump_motor_efficiency)
storage_pump.setPumpControlType('Intermittent')
storage_pump.addToNode(storage_water_loop.supplyInletNode)

storage_water_heater = OpenStudio::Model::WaterHeaterMixed.new(model)
storage_water_heater.setName('Storage Hot Water Tank')
storage_water_heater.setSetpointTemperatureSchedule(storage_temp_sch)
storage_water_heater.setHeaterMaximumCapacity(0.0)
# storage_water_heater.setDeadbandTemperatureDifference(OpenStudio.convert(3.6,'R','K').get)
# storage_water_heater.setHeaterControlType('Cycle')
# storage_water_heater.setTankVolume(OpenStudio.convert(water_heater_vol_gal,'gal','m^3').get)
storage_water_loop.addDemandBranchForComponent(storage_water_heater)

# make a solar collector and add it to the storage loop
vertices = OpenStudio::Point3dVector.new
vertices << OpenStudio::Point3d.new(0, 0, 0)
vertices << OpenStudio::Point3d.new(10, 0, 0)
vertices << OpenStudio::Point3d.new(10, 4, 0)
vertices << OpenStudio::Point3d.new(0, 4, 0)
rotation = OpenStudio.createRotation(OpenStudio::Vector3d.new(1, 0, 0), OpenStudio.degToRad(30))
vertices = rotation * vertices

group = OpenStudio::Model::ShadingSurfaceGroup.new(model)
group.setXOrigin(20)
group.setYOrigin(10)
group.setZOrigin(8)

shade = OpenStudio::Model::ShadingSurface.new(vertices, model)
shade.setShadingSurfaceGroup(group)

collector = OpenStudio::Model::SolarCollectorFlatPlatePhotovoltaicThermal.new(model)
storage_water_loop.addSupplyBranchForComponent(collector)
collector.setSurface(shade)

# We need a PV object as well, and and ELCD, and an inverted
# create the panel
panel = OpenStudio::Model::GeneratorPhotovoltaic.simple(model)
panel.setSurface(shade)
# create the inverter
inverter = OpenStudio::Model::ElectricLoadCenterInverterSimple.new(model)
# create the distribution system
elcd = OpenStudio::Model::ElectricLoadCenterDistribution.new(model)
elcd.addGenerator(panel)
elcd.setInverter(inverter)

# Assign the PV Generator to the collector
collector.setGeneratorPhotovoltaic(panel)

collector.autosizeDesignFlowRate

# Modify the Performance object
# (Here I hardset them exactly like the constructor does)
# Note: Before 3.6.0, the cast is not needed, but it is mandatory starting in 3.6.0
perf = collector.solarCollectorPerformance.to_SolarCollectorPerformancePhotovoltaicThermalSimple.get
perf.setName('Solar Collector Performance Photovoltaic Thermal Simple')
perf.setFractionOfSurfaceAreaWithActiveThermalCollector(1.0)
perf.setThermalConversionEfficiency(0.3)
perf.setFrontSurfaceEmittance(0.84)

add_out_vars = false
if add_out_vars
  collector.outputVariableNames.each do |var|
    OpenStudio::Model::OutputVariable.new(var, model)
  end
end

# add a storage tank to the swh loop
mixed_swh_loop.addSupplyBranchForComponent(storage_water_heater)

# add instantaneous swh water heater after the storage tank
swh_water_heater = OpenStudio::Model::WaterHeaterMixed.new(model)
swh_water_heater.addToNode(mixed_swh_loop.supplyOutletNode)

# add a tempering valve
tempering_valve = OpenStudio::Model::TemperingValve.new(model)
mixed_swh_loop.addSupplyBranchForComponent(tempering_valve)
tempering_valve.setStream2SourceNode(storage_water_heater.supplyOutletModelObject.get.to_Node.get)
tempering_valve.setTemperatureSetpointNode(swh_water_heater.supplyOutletModelObject.get.to_Node.get)
tempering_valve.setPumpOutletNode(swh_pump.outletModelObject.get.to_Node.get)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
