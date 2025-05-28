# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 1 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 3,
                     'plenum_height' => 1,
                     'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# Make a Dual Duct AirLoopHVAC
air_loop = OpenStudio::Model::AirLoopHVAC.new(model, true)

fan = OpenStudio::Model::FanVariableVolume.new(model)
fan.addToNode(air_loop.supplyInletNode)

# Similar to FurnaceWithDXSystemRHcontrol.idf

enthalpy_limit_curve = OpenStudio::Model::CurveCubic.new(model)
enthalpy_limit_curve.setName('ElectronicEnthalpyCurveA')
enthalpy_limit_curve.setCoefficient1Constant(0.01342704)
enthalpy_limit_curve.setCoefficient2x(-0.00047892)
enthalpy_limit_curve.setCoefficient3xPOW2(0.000053352)
enthalpy_limit_curve.setCoefficient4xPOW3(-0.0000018103)
enthalpy_limit_curve.setMinimumValueofx(16.6)
enthalpy_limit_curve.setMaximumValueofx(29.13)

min_outdoorair_sch = OpenStudio::Model::ScheduleRuleset.new(model)
min_outdoorair_sch.setName('OAFractionSched')
min_outdoorair_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 7, 0, 0), 0.05)
min_outdoorair_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 18, 0, 0), 1.0)
min_outdoorair_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 0.05)

economizer_control_sch = OpenStudio::Model::ScheduleRuleset.new(model)
economizer_control_sch.setName('TimeOfDayEconomizerSch')
economizer_control_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 7, 0, 0), 0.0)
economizer_control_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 7, 30, 0), 1.0)
economizer_control_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 0.0)

oa_controller = OpenStudio::Model::ControllerOutdoorAir.new(model)
oa_controller.setMinimumOutdoorAirFlowRate(0.25)
oa_controller.setMaximumOutdoorAirFlowRate(1.6)
oa_controller.setEconomizerControlType('ElectronicEnthalpy')
oa_controller.setEconomizerControlActionType('ModulateFlow')
oa_controller.setEconomizerMaximumLimitDryBulbTemperature(23.0)
# oa_controller.setEconomizerMaximumLimitEnthalpy()
oa_controller.setEconomizerMaximumLimitDewpointTemperature(13.5)
oa_controller.setElectronicEnthalpyLimitCurve(enthalpy_limit_curve)
oa_controller.setEconomizerMinimumLimitDryBulbTemperature(14.0)
oa_controller.setLockoutType('NoLockout')
oa_controller.setMinimumLimitType('FixedMinimum')
oa_controller.setMinimumOutdoorAirSchedule(min_outdoorair_sch)
# oa_controller.setMinimumFractionofOutdoorAirSchedule()
# oa_controller.setMaximumFractionofOutdoorAirSchedule()
# oa_controller.setControllerMechanicalVentilation()
oa_controller.setTimeofDayEconomizerControlSchedule(economizer_control_sch)
oa_controller.setHighHumidityOutdoorAirFlowRatio(0.9)
oa_controller.setControlHighIndoorHumidityBasedOnOutdoorHumidityRatio(true)

# Add a humidistat at 50% RH to the zone
dehumidify_sch = OpenStudio::Model::ScheduleConstant.new(model)
dehumidify_sch.setValue(50)
humidistat = OpenStudio::Model::ZoneControlHumidistat.new(model)
humidistat.setHumidifyingRelativeHumiditySetpointSchedule(dehumidify_sch)

oa_system = OpenStudio::Model::AirLoopHVACOutdoorAirSystem.new(model, oa_controller)
oa_system.addToNode(air_loop.supplyInletNode)

# After the splitter, we will now have two supply outlet nodes
supply_outlet_nodes = air_loop.supplyOutletNodes

heating_coil = OpenStudio::Model::CoilHeatingGas.new(model)
heating_coil.addToNode(supply_outlet_nodes[0])

heating_sch = OpenStudio::Model::ScheduleRuleset.new(model)
heating_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 45.0)
heating_spm = OpenStudio::Model::SetpointManagerScheduled.new(model, heating_sch)
heating_spm.addToNode(supply_outlet_nodes[0])

cooling_coil = OpenStudio::Model::CoilCoolingDXTwoSpeed.new(model)
cooling_coil.addToNode(supply_outlet_nodes[1])

cooling_sch = OpenStudio::Model::ScheduleRuleset.new(model)
cooling_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 12.8)
cooling_spm = OpenStudio::Model::SetpointManagerScheduled.new(model, cooling_sch)
cooling_spm.addToNode(supply_outlet_nodes[1])

# In order to produce more consistent results between different runs,
# we sort the zones by names (doesn't matter here, just in case)
zones = model.getThermalZones.sort_by { |z| z.name.to_s }
zones.each do |zone|
  terminal = OpenStudio::Model::AirTerminalDualDuctVAV.new(model)
  air_loop.addBranchForZone(zone, terminal)

  zone.setZoneControlHumidistat(humidistat)
  oa_controller.setHumidistatControlZone(zone)
end

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
