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

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# We manually create our own HVAC system
air_system = OpenStudio::Model.addSystemType6(model).to_AirLoopHVAC.get

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = model.getThermalZones.sort_by { |z| z.name.to_s }

zone = zones.first
air_system.addBranchForZone(zone)
coil = air_system.supplyComponents(OpenStudio::Model::CoilCoolingDXTwoSpeed.iddObjectType).first.to_CoilCoolingDXTwoSpeed.get
unitary = OpenStudio::Model::AirLoopHVACUnitarySystem.new(model)
begin
  unitary.setControlType('SetPoint')
rescue StandardError
  # For (much) older OS Versions where the method wasn't implemented yet
  # (I think 2.3.1 was the first where setControlType was implemented)
  unitary.setString(2, 'SetPoint')
end

# new_coil = OpenStudio::Model::CoilCoolingWaterToAirHeatPumpEquationFit.new(model)
new_coil = OpenStudio::Model::CoilCoolingDXSingleSpeed.new(model)
unitary.setCoolingCoil(new_coil)
unitary.addToNode(coil.outletModelObject.get.to_Node.get)
coil.remove

# fan = air_system.supplyComponents(OpenStudio::Model::FanVariableVolume::iddObjectType).first.to_FanVariableVolume.get
# new_fan = OpenStudio::Model::FanConstantVolume.new(model)
# new_fan.addToNode(fan.outletModelObject().get.to_Node.get)
# fan.remove

hotWaterPlant = OpenStudio::Model::PlantLoop.new(model)
sizingPlant = hotWaterPlant.sizingPlant
sizingPlant.setLoopType('Heating')
sizingPlant.setDesignLoopExitTemperature(82.0)
sizingPlant.setLoopDesignTemperatureDifference(11.0)

hotWaterOutletNode = hotWaterPlant.supplyOutletNode
hotWaterInletNode = hotWaterPlant.supplyInletNode
hotWaterDemandOutletNode = hotWaterPlant.demandOutletNode
hotWaterDemandInletNode = hotWaterPlant.demandInletNode

pump = OpenStudio::Model::PumpVariableSpeed.new(model)
boiler = OpenStudio::Model::BoilerHotWater.new(model)

pump.addToNode(hotWaterInletNode)
node = hotWaterPlant.supplySplitter.lastOutletModelObject.get.to_Node.get
boiler.addToNode(node)

pipe = OpenStudio::Model::PipeAdiabatic.new(model)
hotWaterPlant.addSupplyBranchForComponent(pipe)

hotWaterBypass = OpenStudio::Model::PipeAdiabatic.new(model)
hotWaterDemandInlet = OpenStudio::Model::PipeAdiabatic.new(model)
hotWaterDemandOutlet = OpenStudio::Model::PipeAdiabatic.new(model)
hotWaterPlant.addDemandBranchForComponent(hotWaterBypass)
hotWaterDemandOutlet.addToNode(hotWaterDemandOutletNode)
hotWaterDemandInlet.addToNode(hotWaterDemandInletNode)

pipe2 = OpenStudio::Model::PipeAdiabatic.new(model)
pipe2.addToNode(hotWaterOutletNode)

hotWaterSchedule = OpenStudio::Model::ScheduleRuleset.new(model)
hotWaterSchedule.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 67)

hotWaterSPM = OpenStudio::Model::SetpointManagerScheduled.new(model, hotWaterSchedule)
hotWaterSPM.addToNode(hotWaterOutletNode)

hotWaterPlant.addDemandBranchForComponent(new_coil)

# add output reports
add_out_vars = false
if add_out_vars
  var = OpenStudio::Model::OutputVariable.new('Cooling Coil Total Cooling Rate', model)
  var.setReportingFrequency('detailed')
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
