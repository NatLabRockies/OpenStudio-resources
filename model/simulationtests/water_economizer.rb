# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'
# use line below when running in ruby 2.0
# require_relative 'lib/baseline_model'

model = BaselineModel.new

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

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac({ 'ashrae_sys_num' => '07' })

plant = OpenStudio::Model::PlantLoop.new(model)
plant.setName('Economizing Plant')

sizingPlant = plant.sizingPlant
sizingPlant.setLoopType('Condenser')
sizingPlant.setDesignLoopExitTemperature(26.0)
sizingPlant.setLoopDesignTemperatureDifference(5.6)

outletNode = plant.supplyOutletNode
inletNode = plant.supplyInletNode

s = OpenStudio::Model::ScheduleConstant.new(model)
s.setValue(26.0)
spm = OpenStudio::Model::SetpointManagerScheduled.new(model, s)
spm.addToNode(outletNode)

pump = OpenStudio::Model::PumpVariableSpeed.new(model)
pump.addToNode(inletNode)

tower = OpenStudio::Model::CoolingTowerVariableSpeed.new(model)
plant.addSupplyBranchForComponent(tower)

hx = OpenStudio::Model::HeatExchangerFluidToFluid.new(model)
hx.setControlType('HeatingSetpointModulated')
plant.addDemandBranchForComponent(hx)

chiller = model.getChillerElectricEIRs.first
hx.addToNode(chiller.supplyInletModelObject.get.to_Node.get)

hx_outlet_node = hx.supplyOutletModelObject.get.to_Node.get
# hotWaterOutletNode = plant.supplyOutletNode()
osTime = OpenStudio::Time.new(0, 24, 0, 0)
hotWaterTempSchedule = OpenStudio::Model::ScheduleRuleset.new(model)
hotWaterTempSchedule.setName('Hot Water Temperature')

### Winter Design Day
hotWaterTempScheduleWinter = OpenStudio::Model::ScheduleDay.new(model)
hotWaterTempSchedule.setWinterDesignDaySchedule(hotWaterTempScheduleWinter)
hotWaterTempSchedule.winterDesignDaySchedule.setName('Hot Water Temperature Winter Design Day')
hotWaterTempSchedule.winterDesignDaySchedule.addValue(osTime, 67)

### Summer Design Day
hotWaterTempScheduleSummer = OpenStudio::Model::ScheduleDay.new(model)
hotWaterTempSchedule.setSummerDesignDaySchedule(hotWaterTempScheduleSummer)
hotWaterTempSchedule.summerDesignDaySchedule.setName('Hot Water Temperature Summer Design Day')
hotWaterTempSchedule.summerDesignDaySchedule.addValue(osTime, 67)

### All other days
hotWaterTempSchedule.defaultDaySchedule.setName('Hot Water Temperature Default')
hotWaterTempSchedule.defaultDaySchedule.addValue(osTime, 67)

hotWaterSPM = OpenStudio::Model::SetpointManagerScheduled.new(model, hotWaterTempSchedule)
hotWaterSPM.addToNode(hx_outlet_node)

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
