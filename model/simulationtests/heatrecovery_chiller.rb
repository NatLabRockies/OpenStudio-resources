# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# add ASHRAE System type 07, VAV w/ Reheat: this sets up the loops we want
model.add_hvac({ 'ashrae_sys_num' => '07' })

# In order to produce more consistent results between different runs,
# We ensure we do get the same object each time
cts = model.getCoolingTowerSingleSpeeds.sort_by { |c| c.name.to_s }
chillers = model.getChillerElectricEIRs.sort_by { |c| c.name.to_s }
chiller = chillers.first
boilers = model.getBoilerHotWaters.sort_by { |c| c.name.to_s }
condenser_loop = cts.first.plantLoop.get
cooling_loop = chillers.first.plantLoop.get
heating_loop = boilers.first.plantLoop.get
condenser_loop.setName('CndW Loop')
heating_loop.setName('HW Loop')
cooling_loop.setName('ChW Loop')

# We'll setup a WaterHeater:Mixed that sits on the **supply side**
# of TWO plant loops:
# * Use Side: the Heating Loop
# * Source Side: the Heat Recovery loop, on the demand side you find the
# chiller
# (Note that you could also just place the chiller on the demand side of
# the HW loop directly, but that's not what we're testing here)

heat_recovery_loop = OpenStudio::Model::PlantLoop.new(model)
heat_recovery_loop.setName('HeatRecovery Loop')
hr_pump = OpenStudio::Model::PumpVariableSpeed.new(model)
hr_pump.setName("#{heat_recovery_loop.nameString} VSD Pump")
hr_pump.addToNode(heat_recovery_loop.supplyInletNode)

hr_spm_sch = OpenStudio::Model::ScheduleRuleset.new(model)
hr_spm_sch.setName('Hot_Water_Temperature')
hr_spm_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 25.0)
hr_spm = OpenStudio::Model::SetpointManagerScheduled.new(model, hr_spm_sch)
hr_spm.addToNode(heat_recovery_loop.supplyOutletNode)

# Water Heater Mixed
water_heater_mixed = OpenStudio::Model::WaterHeaterMixed.new(model)
water_heater_mixed.setName('Heat Recovery Tank')
# The first addSupplyBranchForComponent / addToNode to a supply side will
# connect the Use Side, so heating loop here
heating_loop.addSupplyBranchForComponent(water_heater_mixed)
raise if water_heater_mixed.plantLoop.empty?

# The Second with a supply side node, if use side already connected, will
# connect the Source Side. You can also be explicit and call
# addToSourceSideNode

# pipe = OpenStudio::Model::PipeAdiabatic.new(model)
# heat_recovery_loop.addSupplyBranchForComponent(pipe)
# water_heater_mixed.addToSourceSideNode(pipe.inletModelObject.get.to_Node.get)
# pipe.remove
heat_recovery_loop.addSupplyBranchForComponent(water_heater_mixed)

raise if water_heater_mixed.plantLoop.empty?
raise if water_heater_mixed.secondaryPlantLoop.empty?
# More convenient name aliases
raise if water_heater_mixed.useSidePlantLoop.empty?
raise if water_heater_mixed.sourceSidePlantLoop.empty?
raise if water_heater_mixed.useSidePlantLoop.get != heating_loop
raise if water_heater_mixed.sourceSidePlantLoop.get != heat_recovery_loop

# Connect the chiller to the HR loop
# Since the secondary loop is already connected (condenser loop)
# and this is a node on the **demand** side of a **different** loop than the
# condenser loop, this will call `chiller.addToTertiaryNode`
heat_recovery_loop.addDemandBranchForComponent(chiller)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
