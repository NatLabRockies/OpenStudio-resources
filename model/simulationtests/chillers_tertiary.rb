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

# ChillerAbsorptionIndirect: on the DEMAND side of a Tertiary Loop (HW/Steam)
chiller_abs_indirect = OpenStudio::Model::ChillerAbsorptionIndirect.new(model)
chiller_abs_indirect.setName('Chiller AbsInd')
cooling_loop.addSupplyBranchForComponent(chiller_abs_indirect)
condenser_loop.addDemandBranchForComponent(chiller_abs_indirect)
# Since the secondary loop is already connected (condenser loop)
# and this is a node on the **demand** side of a **different** loop than the
# condenser loop, this will call `chiller_abs_indirect.addToTertiaryNode`
heating_loop.addDemandBranchForComponent(chiller_abs_indirect)
chiller_abs_indirect.setCondenserInletTemperatureLowerLimit(0.01)

# ChillerAbsorption: on the DEMAND side of a Tertiary Loop (HW/Steam)
chiller_absorption = OpenStudio::Model::ChillerAbsorption.new(model)
chiller_absorption.setName('Chiller Abs')
cooling_loop.addSupplyBranchForComponent(chiller_absorption)
condenser_loop.addDemandBranchForComponent(chiller_absorption)
# Connect Generator Inlet/Outlet Nodes
heating_loop.addDemandBranchForComponent(chiller_absorption)

# ChillerElectricEIR: on the DEMAND side of a Tertiary Loop (Heat Recovery)
# Makes sense: the HR isn't "active" is responding to HR load
# Sys 07 so already water-cooled
chiller_eir = chillers.first
chiller_eir.setName('Chiller EIR')
heating_loop.addDemandBranchForComponent(chiller_eir)

model.rename_loop_nodes
model.rename_air_nodes

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
