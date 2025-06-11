# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 1,
                     'perimeter_zone_depth' => 3 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

schedule = model.alwaysOnDiscreteSchedule

_chilledWaterSchedule = OpenStudio::Model::ScheduleRuleset.new(model)
_chilledWaterSchedule.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 6.7)

# Chilled Water Plant
chilledWaterPlant = OpenStudio::Model::PlantLoop.new(model)
sizingPlant = chilledWaterPlant.sizingPlant
sizingPlant.setLoopType('Cooling')
sizingPlant.setDesignLoopExitTemperature(7.22)
sizingPlant.setLoopDesignTemperatureDifference(6.67)

chilledWaterOutletNode = chilledWaterPlant.supplyOutletNode
chilledWaterInletNode = chilledWaterPlant.supplyInletNode
chilledWaterDemandOutletNode = chilledWaterPlant.demandOutletNode
chilledWaterDemandInletNode = chilledWaterPlant.demandInletNode

pump2 = OpenStudio::Model::PumpVariableSpeed.new(model)
pump2.addToNode(chilledWaterInletNode)

chiller = OpenStudio::Model::ChillerElectricReformulatedEIR.new(model)

node = chilledWaterPlant.supplySplitter.lastOutletModelObject.get.to_Node.get
chiller.addToNode(node)

pipe3 = OpenStudio::Model::PipeAdiabatic.new(model)
chilledWaterPlant.addSupplyBranchForComponent(pipe3)

pipe4 = OpenStudio::Model::PipeAdiabatic.new(model)
pipe4.addToNode(chilledWaterOutletNode)

chilledWaterSPM = OpenStudio::Model::SetpointManagerScheduled.new(model, _chilledWaterSchedule)
chilledWaterSPM.addToNode(chilledWaterOutletNode)

chilledWaterBypass = OpenStudio::Model::PipeAdiabatic.new(model)
chilledWaterDemandInlet = OpenStudio::Model::PipeAdiabatic.new(model)
chilledWaterDemandOutlet = OpenStudio::Model::PipeAdiabatic.new(model)
chilledWaterPlant.addDemandBranchForComponent(chilledWaterBypass)
chilledWaterDemandOutlet.addToNode(chilledWaterDemandOutletNode)
chilledWaterDemandInlet.addToNode(chilledWaterDemandInletNode)

# Condenser System
condenserSystem = OpenStudio::Model::PlantLoop.new(model)
sizingPlant = condenserSystem.sizingPlant
sizingPlant.setLoopType('Condenser')
sizingPlant.setDesignLoopExitTemperature(29.4)
sizingPlant.setLoopDesignTemperatureDifference(5.6)

distHeating = OpenStudio::Model::DistrictHeating.new(model)
condenserSystem.addSupplyBranchForComponent(distHeating)

distCooling = OpenStudio::Model::DistrictCooling.new(model)
condenserSystem.addSupplyBranchForComponent(distCooling)

condenserSupplyOutletNode = condenserSystem.supplyOutletNode
condenserSupplyInletNode = condenserSystem.supplyInletNode
condenserDemandOutletNode = condenserSystem.demandOutletNode
condenserDemandInletNode = condenserSystem.demandInletNode

pump3 = OpenStudio::Model::PumpVariableSpeed.new(model)
pump3.addToNode(condenserSupplyInletNode)

condenserSystem.addDemandBranchForComponent(chiller)

condenserSupplyBypass = OpenStudio::Model::PipeAdiabatic.new(model)
condenserSystem.addSupplyBranchForComponent(condenserSupplyBypass)

condenserSupplyOutlet = OpenStudio::Model::PipeAdiabatic.new(model)
condenserSupplyOutlet.addToNode(condenserSupplyOutletNode)

condenserBypass = OpenStudio::Model::PipeAdiabatic.new(model)
condenserDemandInlet = OpenStudio::Model::PipeAdiabatic.new(model)
condenserDemandOutlet = OpenStudio::Model::PipeAdiabatic.new(model)
condenserSystem.addDemandBranchForComponent(condenserBypass)
condenserDemandOutlet.addToNode(condenserDemandOutletNode)
condenserDemandInlet.addToNode(condenserDemandInletNode)

spm = OpenStudio::Model::SetpointManagerFollowOutdoorAirTemperature.new(model)
spm.addToNode(condenserSupplyOutletNode)

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = model.getThermalZones.sort_by { |z| z.name.to_s }

airLoop_3 = OpenStudio::Model::AirLoopHVAC.new(model)
airLoop_3_supplyNode = airLoop_3.supplyOutletNode

unitary_3 = OpenStudio::Model::AirLoopHVACUnitarySystem.new(model)
fan_3 = OpenStudio::Model::FanConstantVolume.new(model, schedule)
cooling_coil_3 = OpenStudio::Model::CoilCoolingWaterToAirHeatPumpEquationFit.new(model)
chilledWaterPlant.addDemandBranchForComponent(cooling_coil_3)
heating_coil_3 = OpenStudio::Model::CoilHeatingGas.new(model, schedule)
unitary_3.setControllingZoneorThermostatLocation(zones[2])
unitary_3.setFanPlacement('BlowThrough')
unitary_3.setSupplyAirFanOperatingModeSchedule(schedule)
unitary_3.setSupplyFan(fan_3)
unitary_3.setCoolingCoil(cooling_coil_3)
unitary_3.setHeatingCoil(heating_coil_3)

unitary_3.addToNode(airLoop_3_supplyNode)

air_terminal_3 = OpenStudio::Model::AirTerminalSingleDuctUncontrolled.new(model, schedule)
airLoop_3.addBranchForZone(zones[2], air_terminal_3)

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
