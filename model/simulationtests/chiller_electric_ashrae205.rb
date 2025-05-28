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
model.add_thermostats({ 'heating_setpoint' => 19,
                        'cooling_setpoint' => 26 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac({ 'ashrae_sys_num' => '07' })

# In order to produce more consistent results between different runs,
# We ensure we do get the same object each time
cts = model.getCoolingTowerSingleSpeeds.sort_by { |c| c.name.to_s }
chillers = model.getChillerElectricEIRs.sort_by { |c| c.name.to_s }
boilers = model.getBoilerHotWaters.sort_by { |c| c.name.to_s }
condenser_loop = cts.first.plantLoop.get
cooling_loop = chillers.first.plantLoop.get
heating_loop = boilers.first.plantLoop.get
condenser_loop.setName('CndW Loop')
heating_loop.setName('HW Loop')
cooling_loop.setName('ChW Loop')

chillers.each(&:remove)

z = model.getThermalZones.min_by { |zone| zone.name.to_s }

file_name = File.join(File.dirname(__FILE__), 'CoolSys1-Chiller-Detailed.RS0001.a205.cbor')
file_name = File.realpath(file_name)
representation_file = OpenStudio::Model::ExternalFile.getExternalFile(model, file_name)

ch = OpenStudio::Model::ChillerElectricASHRAE205.new(representation_file.get)

ch.setPerformanceInterpolationMethod('Cubic')
ch.autosizeRatedCapacity
ch.setSizingFactor(1.1)

# Ambient Temperature Indicator is set via other methods
# Defaults to 'Outdoors' initially
raise if ch.ambientTemperatureIndicator != 'Outdoors'

sch = OpenStudio::Model::ScheduleConstant.new(model)
ch.setAmbientTemperatureSchedule(sch)
raise if ch.ambientTemperatureIndicator != 'Schedule'

ch.setAmbientTemperatureZone(z)
raise if ch.ambientTemperatureIndicator != 'Zone'

ch.setChilledWaterMaximumRequestedFlowRate(0.0428)
ch.setCondenserMaximumRequestedFlowRate(0.0552)
ch.setChillerFlowMode('ConstantFlow')

ch.setOilCoolerDesignFlowRate(0.001)
ch.setAuxiliaryCoolingDesignFlowRate(0.002)
ch.setEndUseSubcategory('Chiller')

cooling_loop.addSupplyBranchForComponent(ch)
condenser_loop.addDemandBranchForComponent(ch)
# Tertiary Loop = Heat Recovery, on the DEMAND side (HW)
# I'm passing tertiary = true for clarity, but it'll work if you don't because
# you already have a demand branch assigned
# TODO: as of V22.2.0-IOFreeze, Heat Recovery isn't implemented for
# ChillerElectricASHRAE205
heating_loop.addDemandBranchForComponent(ch, true)

# Extra loops: put them in series on a parallel branch of the condenser loop
# Two ways of connecting to it
# Demand Branch
ch.addDemandBranchOnOilCoolerLoop(condenser_loop)
ch.addDemandBranchOnAuxiliaryLoop(condenser_loop)
# Or
# ch.addToOilCoolerLoopNode, ch.addToAuxiliaryLoopNode
# NOTE: we're specifically disallowing this:
# ch.addToAuxiliaryLoopNode(ch.oilCoolerOutletNode.get)
# It would require too much change to the Loop and derived objects to allow the
# same component to be present TWICE on the same branch

# Lots of convenience methods
raise if ch.chilledWaterLoop.empty?
raise if ch.chilledWaterInletNode.empty?
raise if ch.chilledWaterOutletNode.empty?

raise if ch.condenserWaterLoop.empty?
raise if ch.condenserInletNode.empty?
raise if ch.condenserOutletNode.empty?

raise if ch.oilCoolerLoop.empty?
raise if ch.oilCoolerInletNode.empty?
raise if ch.oilCoolerOutletNode.empty?

raise if ch.auxiliaryLoop.empty?
raise if ch.auxiliaryInletNode.empty?
raise if ch.auxiliaryOutletNode.empty?

# raise if ch.heatRecoveryLoop.empty?
# raise if ch.heatRecoveryInletNode.empty?
# raise if ch.heatRecoveryOutletNode.empty?

# If addition to ch.removeFromPlantLoop, ch.removeFromSecondaryPlantLoop
# and ch.removeFromTertiaryPlantLoop, you also have ch.removeFromAuxiliaryLoop
# and ch.removeFromOilCoolerLoop

model.rename_loop_nodes
model.rename_air_nodes

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
