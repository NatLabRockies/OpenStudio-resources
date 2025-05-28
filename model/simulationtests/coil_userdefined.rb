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

# Get the objects. There should generally be only one, but let's be safe
z = model.getThermalZones.min_by(&:nameString)
airLoop = model.getAirLoopHVACs.min_by(&:nameString)
# get supplyOutletNode
supplyOutletNode = airLoop.supplyOutletNode()

# make CoilUserDefined
coil = OpenStudio::Model::CoilUserDefined.new(model)
coil.setName('My CoilUserDefined')
# All of the required EMS objects are directly instiantated for you
# There is a convenience method to rename them like this object
coil.renameEMSSubComponents

raise if coil.modelSetupandSizingProgramCallingManager.nameString != 'My_CoilUserDefined_modelSetupandSizingProgramCallingManager'
raise if coil.overallSimulationProgram.nameString != 'My_CoilUserDefined_overallSimulationProgram'
raise if coil.initializationSimulationProgram.nameString != 'My_CoilUserDefined_initializationSimulationProgram'
raise if coil.airOutletTemperatureActuator.nameString != 'My_CoilUserDefined_airOutletTemperatureActuator'
raise if coil.airOutletHumidityRatioActuator.nameString != 'My_CoilUserDefined_airOutletHumidityRatioActuator'
raise if coil.airMassFlowRateActuator.nameString != 'My_CoilUserDefined_airMassFlowRateActuator'
raise if coil.plantMinimumMassFlowRateActuator.nameString != 'My_CoilUserDefined_plantMinimumMassFlowRateActuator'
raise if coil.plantMaximumMassFlowRateActuator.nameString != 'My_CoilUserDefined_plantMaximumMassFlowRateActuator'
raise if coil.plantDesignVolumeFlowRateActuator.nameString != 'My_CoilUserDefined_plantDesignVolumeFlowRateActuator'
raise if coil.plantMassFlowRateActuator.nameString != 'My_CoilUserDefined_plantMassFlowRateActuator'
raise if coil.plantOutletTemperatureActuator.nameString != 'My_CoilUserDefined_plantOutletTemperatureActuator'

coil.setAmbientZone(z)
coil.addToNode(supplyOutletNode)

coil_Air_Tout = coil.airOutletTemperatureActuator
coil_Air_Wout = coil.airOutletHumidityRatioActuator
coil_Air_MdotOut = coil.airMassFlowRateActuator

# sim program
sim_pgrm = coil.overallSimulationProgram
sim_pgrm.setName('Coil_program')
sim_pgrm_body = <<~EMS
  Set #{coil_Air_Tout.handle} = 18
  Set #{coil_Air_Wout.handle} = 0.5
  Set #{coil_Air_MdotOut.handle} = 10
EMS
sim_pgrm.setBody(sim_pgrm_body)

# init program
init_pgrm = coil.initializationSimulationProgram
init_pgrm.setName('Coil_init')
init_pgrm_body = <<~EMS
  Set dummy = 0
EMS
init_pgrm.setBody(init_pgrm_body)

# save the OpenStudio model (.osm)
model.save(OpenStudio::Path.new('in.osm'), true)
