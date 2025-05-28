# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
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

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = model.getThermalZones.sort_by { |z| z.name.to_s }

alwaysOn = model.alwaysOnDiscreteSchedule

vrf_fluid_temperature_control = OpenStudio::Model::AirConditionerVariableRefrigerantFlowFluidTemperatureControl.new(model)
vrf_fluid_temperature_control.setAvailabilitySchedule(alwaysOn)
vrf_fluid_temperature_control.setRefrigerantType('R410a')
vrf_fluid_temperature_control.setRatedEvaporativeCapacity(40000)
vrf_fluid_temperature_control.setRatedCompressorPowerPerUnitofRatedEvaporativeCapacity(0.35)
vrf_fluid_temperature_control.setMinimumOutdoorAirTemperatureinCoolingMode(-6.0)
vrf_fluid_temperature_control.setMaximumOutdoorAirTemperatureinCoolingMode(43.0)
vrf_fluid_temperature_control.setMinimumOutdoorAirTemperatureinHeatingMode(-20.0)
vrf_fluid_temperature_control.setMaximumOutdoorAirTemperatureinHeatingMode(16.0)
vrf_fluid_temperature_control.setReferenceOutdoorUnitSuperheating(3)
vrf_fluid_temperature_control.setReferenceOutdoorUnitSubcooling(5)
vrf_fluid_temperature_control.setRefrigerantTemperatureControlAlgorithmforIndoorUnit('VariableTemp')
vrf_fluid_temperature_control.setReferenceEvaporatingTemperatureforIndoorUnit(6.0)
vrf_fluid_temperature_control.setReferenceCondensingTemperatureforIndoorUnit(44.0)
vrf_fluid_temperature_control.setVariableEvaporatingTemperatureMinimumforIndoorUnit(4.0)
vrf_fluid_temperature_control.setVariableEvaporatingTemperatureMaximumforIndoorUnit(13.0)
vrf_fluid_temperature_control.setVariableCondensingTemperatureMinimumforIndoorUnit(42.0)
vrf_fluid_temperature_control.setVariableCondensingTemperatureMaximumforIndoorUnit(46.0)
vrf_fluid_temperature_control.setOutdoorUnitFanPowerPerUnitofRatedEvaporativeCapacity(4.25E-3)
vrf_fluid_temperature_control.setOutdoorUnitFanFlowRatePerUnitofRatedEvaporativeCapacity(7.50E-5)
vrf_fluid_temperature_control.setDiameterofMainPipeConnectingOutdoorUnittotheFirstBranchJoint(0.0762)
vrf_fluid_temperature_control.setLengthofMainPipeConnectingOutdoorUnittotheFirstBranchJoint(30.0)
vrf_fluid_temperature_control.setEquivalentLengthofMainPipeConnectingOutdoorUnittotheFirstBranchJoint(36.0)
vrf_fluid_temperature_control.setHeightDifferenceBetweenOutdoorUnitandIndoorUnits(5.0)
vrf_fluid_temperature_control.setMainPipeInsulationThickness(0.02)
vrf_fluid_temperature_control.setMainPipeInsulationThermalConductivity(0.032)
vrf_fluid_temperature_control.setCrankcaseHeaterPowerperCompressor(33.0)
vrf_fluid_temperature_control.setNumberofCompressors(2)
vrf_fluid_temperature_control.setRatioofCompressorSizetoTotalCompressorCapacity(0.5)
vrf_fluid_temperature_control.setMaximumOutdoorDryBulbTemperatureforCrankcaseHeater(5.0)
vrf_fluid_temperature_control.setDefrostStrategy('Resistive')
vrf_fluid_temperature_control.setDefrostControl('Timed')
vrf_fluid_temperature_control.setDefrostTimePeriodFraction(0.058333)
vrf_fluid_temperature_control.setResistiveDefrostHeaterCapacity(0.0)
vrf_fluid_temperature_control.setMaximumOutdoorDrybulbTemperatureforDefrostOperation(5.0)
vrf_fluid_temperature_control.setCompressorMaximumDeltaPressure(4500000.0)
vrf_fluid_temperature_control.removeAllLoadingIndexes

outdoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve = OpenStudio::Model::CurveQuadratic.new(model)
outdoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve.setCoefficient1Constant(0)
outdoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve.setCoefficient2x(6.05E-1)
outdoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve.setCoefficient3xPOW2(2.50E-2)
outdoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve.setMinimumValueofx(0)
outdoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve.setMaximumValueofx(15)
vrf_fluid_temperature_control.setOutdoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve(outdoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve)

outdoorUnitCondensingTemperatureFunctionofSubcoolingCurve = OpenStudio::Model::CurveQuadratic.new(model)
outdoorUnitCondensingTemperatureFunctionofSubcoolingCurve.setCoefficient1Constant(0)
outdoorUnitCondensingTemperatureFunctionofSubcoolingCurve.setCoefficient2x(-2.91)
outdoorUnitCondensingTemperatureFunctionofSubcoolingCurve.setCoefficient3xPOW2(1.180)
outdoorUnitCondensingTemperatureFunctionofSubcoolingCurve.setMinimumValueofx(0)
outdoorUnitCondensingTemperatureFunctionofSubcoolingCurve.setMaximumValueofx(5)
vrf_fluid_temperature_control.setOutdoorUnitCondensingTemperatureFunctionofSubcoolingCurve(outdoorUnitCondensingTemperatureFunctionofSubcoolingCurve)

evaporativeCapacityMultiplierFunctionofTemperatureCurve1 = OpenStudio::Model::CurveBiquadratic.new(model)
evaporativeCapacityMultiplierFunctionofTemperatureCurve1.setCoefficient1Constant(3.19E-01)
evaporativeCapacityMultiplierFunctionofTemperatureCurve1.setCoefficient2x(-1.26E-03)
evaporativeCapacityMultiplierFunctionofTemperatureCurve1.setCoefficient3xPOW2(-2.15E-05)
evaporativeCapacityMultiplierFunctionofTemperatureCurve1.setCoefficient4y(1.20E-02)
evaporativeCapacityMultiplierFunctionofTemperatureCurve1.setCoefficient5yPOW2(1.05E-04)
evaporativeCapacityMultiplierFunctionofTemperatureCurve1.setCoefficient6xTIMESY(-8.66E-05)
evaporativeCapacityMultiplierFunctionofTemperatureCurve1.setMinimumValueofx(15)
evaporativeCapacityMultiplierFunctionofTemperatureCurve1.setMaximumValueofx(65)
evaporativeCapacityMultiplierFunctionofTemperatureCurve1.setMinimumValueofy(-30)
evaporativeCapacityMultiplierFunctionofTemperatureCurve1.setMaximumValueofy(15)

compressorPowerMultiplierFunctionofTemperatureCurve1 = OpenStudio::Model::CurveBiquadratic.new(model)
compressorPowerMultiplierFunctionofTemperatureCurve1.setCoefficient1Constant(8.79E-02)
compressorPowerMultiplierFunctionofTemperatureCurve1.setCoefficient2x(-1.72E-04)
compressorPowerMultiplierFunctionofTemperatureCurve1.setCoefficient3xPOW2(6.93E-05)
compressorPowerMultiplierFunctionofTemperatureCurve1.setCoefficient4y(-3.38E-05)
compressorPowerMultiplierFunctionofTemperatureCurve1.setCoefficient5yPOW2(-8.10E-06)
compressorPowerMultiplierFunctionofTemperatureCurve1.setCoefficient6xTIMESY(-1.04E-05)
compressorPowerMultiplierFunctionofTemperatureCurve1.setMinimumValueofx(15)
compressorPowerMultiplierFunctionofTemperatureCurve1.setMaximumValueofx(65)
compressorPowerMultiplierFunctionofTemperatureCurve1.setMinimumValueofy(-30)
compressorPowerMultiplierFunctionofTemperatureCurve1.setMaximumValueofy(15)
loadingIndex1 = OpenStudio::Model::LoadingIndex.new(model, 1500, evaporativeCapacityMultiplierFunctionofTemperatureCurve1, compressorPowerMultiplierFunctionofTemperatureCurve1)
vrf_fluid_temperature_control.addLoadingIndex(loadingIndex1)

evaporativeCapacityMultiplierFunctionofTemperatureCurve2 = OpenStudio::Model::CurveBiquadratic.new(model)
evaporativeCapacityMultiplierFunctionofTemperatureCurve2.setCoefficient1Constant(8.12E-01)
evaporativeCapacityMultiplierFunctionofTemperatureCurve2.setCoefficient2x(-4.23E-03)
evaporativeCapacityMultiplierFunctionofTemperatureCurve2.setCoefficient3xPOW2(-4.11E-05)
evaporativeCapacityMultiplierFunctionofTemperatureCurve2.setCoefficient4y(2.97E-02)
evaporativeCapacityMultiplierFunctionofTemperatureCurve2.setCoefficient5yPOW2(2.67E-04)
evaporativeCapacityMultiplierFunctionofTemperatureCurve2.setCoefficient6xTIMESY(-2.23E-04)
evaporativeCapacityMultiplierFunctionofTemperatureCurve2.setMinimumValueofx(15)
evaporativeCapacityMultiplierFunctionofTemperatureCurve2.setMaximumValueofx(65)
evaporativeCapacityMultiplierFunctionofTemperatureCurve2.setMinimumValueofy(-30)
evaporativeCapacityMultiplierFunctionofTemperatureCurve2.setMaximumValueofy(15)

compressorPowerMultiplierFunctionofTemperatureCurve2 = OpenStudio::Model::CurveBiquadratic.new(model)
compressorPowerMultiplierFunctionofTemperatureCurve2.setCoefficient1Constant(3.26E-01)
compressorPowerMultiplierFunctionofTemperatureCurve2.setCoefficient2x(-2.20E-03)
compressorPowerMultiplierFunctionofTemperatureCurve2.setCoefficient3xPOW2(1.42E-04)
compressorPowerMultiplierFunctionofTemperatureCurve2.setCoefficient4y(2.82E-03)
compressorPowerMultiplierFunctionofTemperatureCurve2.setCoefficient5yPOW2(2.86E-05)
compressorPowerMultiplierFunctionofTemperatureCurve2.setCoefficient6xTIMESY(-3.50E-05)
compressorPowerMultiplierFunctionofTemperatureCurve2.setMinimumValueofx(15)
compressorPowerMultiplierFunctionofTemperatureCurve2.setMaximumValueofx(65)
compressorPowerMultiplierFunctionofTemperatureCurve2.setMinimumValueofy(-30)
compressorPowerMultiplierFunctionofTemperatureCurve2.setMaximumValueofy(15)
loadingIndex2 = OpenStudio::Model::LoadingIndex.new(model, 3600, evaporativeCapacityMultiplierFunctionofTemperatureCurve2, compressorPowerMultiplierFunctionofTemperatureCurve2)
vrf_fluid_temperature_control.addLoadingIndex(loadingIndex2)

evaporativeCapacityMultiplierFunctionofTemperatureCurve3 = OpenStudio::Model::CurveBiquadratic.new(model)
evaporativeCapacityMultiplierFunctionofTemperatureCurve3.setCoefficient1Constant(1.32E+00)
evaporativeCapacityMultiplierFunctionofTemperatureCurve3.setCoefficient2x(-6.20E-03)
evaporativeCapacityMultiplierFunctionofTemperatureCurve3.setCoefficient3xPOW2(-7.10E-05)
evaporativeCapacityMultiplierFunctionofTemperatureCurve3.setCoefficient4y(4.89E-02)
evaporativeCapacityMultiplierFunctionofTemperatureCurve3.setCoefficient5yPOW2(4.59E-04)
evaporativeCapacityMultiplierFunctionofTemperatureCurve3.setCoefficient6xTIMESY(-3.67E-04)
evaporativeCapacityMultiplierFunctionofTemperatureCurve3.setMinimumValueofx(15)
evaporativeCapacityMultiplierFunctionofTemperatureCurve3.setMaximumValueofx(65)
evaporativeCapacityMultiplierFunctionofTemperatureCurve3.setMinimumValueofy(-30)
evaporativeCapacityMultiplierFunctionofTemperatureCurve3.setMaximumValueofy(15)

compressorPowerMultiplierFunctionofTemperatureCurve3 = OpenStudio::Model::CurveBiquadratic.new(model)
compressorPowerMultiplierFunctionofTemperatureCurve3.setCoefficient1Constant(6.56E-01)
compressorPowerMultiplierFunctionofTemperatureCurve3.setCoefficient2x(-3.71E-03)
compressorPowerMultiplierFunctionofTemperatureCurve3.setCoefficient3xPOW2(2.07E-04)
compressorPowerMultiplierFunctionofTemperatureCurve3.setCoefficient4y(1.05E-02)
compressorPowerMultiplierFunctionofTemperatureCurve3.setCoefficient5yPOW2(7.36E-05)
compressorPowerMultiplierFunctionofTemperatureCurve3.setCoefficient6xTIMESY(-1.57E-04)
compressorPowerMultiplierFunctionofTemperatureCurve3.setMinimumValueofx(15)
compressorPowerMultiplierFunctionofTemperatureCurve3.setMaximumValueofx(65)
compressorPowerMultiplierFunctionofTemperatureCurve3.setMinimumValueofy(-30)
compressorPowerMultiplierFunctionofTemperatureCurve3.setMaximumValueofy(15)
loadingIndex3 = OpenStudio::Model::LoadingIndex.new(model, 6000, evaporativeCapacityMultiplierFunctionofTemperatureCurve3, compressorPowerMultiplierFunctionofTemperatureCurve3)
vrf_fluid_temperature_control.addLoadingIndex(loadingIndex3)

zones.each_with_index do |z, i|
  coolingCoil = OpenStudio::Model::CoilCoolingDXVariableRefrigerantFlowFluidTemperatureControl.new(model)
  coolingCoil.setAvailabilitySchedule(alwaysOn)
  coolingCoil.autosizeRatedTotalCoolingCapacity
  coolingCoil.autosizeRatedSensibleHeatRatio
  coolingCoil.setIndoorUnitReferenceSuperheating(5.0)

  indoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve = OpenStudio::Model::CurveQuadratic.new(model)
  indoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve.setCoefficient1Constant(0)
  indoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve.setCoefficient2x(0.843)
  indoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve.setCoefficient3xPOW2(0)
  indoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve.setMinimumValueofx(0)
  indoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve.setMaximumValueofx(15)
  coolingCoil.setIndoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve(indoorUnitEvaporatingTemperatureFunctionofSuperheatingCurve)

  heatingCoil = OpenStudio::Model::CoilHeatingDXVariableRefrigerantFlowFluidTemperatureControl.new(model)
  heatingCoil.setAvailabilitySchedule(alwaysOn)
  heatingCoil.autosizeRatedTotalHeatingCapacity
  heatingCoil.setIndoorUnitReferenceSubcooling(5.0)
  indoorUnitCondensingTemperatureFunctionofSubcoolingCurve = OpenStudio::Model::CurveQuadratic.new(model)
  indoorUnitCondensingTemperatureFunctionofSubcoolingCurve.setCoefficient1Constant(-1.85)
  indoorUnitCondensingTemperatureFunctionofSubcoolingCurve.setCoefficient2x(0.411)
  indoorUnitCondensingTemperatureFunctionofSubcoolingCurve.setCoefficient3xPOW2(0.0196)
  indoorUnitCondensingTemperatureFunctionofSubcoolingCurve.setMinimumValueofx(0)
  indoorUnitCondensingTemperatureFunctionofSubcoolingCurve.setMaximumValueofx(20)
  heatingCoil.setIndoorUnitCondensingTemperatureFunctionofSubcoolingCurve(indoorUnitCondensingTemperatureFunctionofSubcoolingCurve)

  fan = OpenStudio::Model::FanVariableVolume.new(model)
  fan.setAvailabilitySchedule(alwaysOn)
  fan.setFanTotalEfficiency(0.6045)
  fan.setPressureRise(1017.592)
  fan.autosizeMaximumFlowRate
  fan.setFanPowerMinimumFlowRateInputMethod('FixedFlowRate')
  fan.setFanPowerMinimumFlowFraction(0.0)
  fan.setFanPowerMinimumAirFlowRate(0.0)
  fan.setMotorEfficiency(0.93)
  fan.setMotorInAirstreamFraction(1.0)
  fan.setFanPowerCoefficient1(0.0407598940)
  fan.setFanPowerCoefficient2(0.08804497)
  fan.setFanPowerCoefficient3(-0.072926120)
  fan.setFanPowerCoefficient4(0.9437398230)
  fan.setFanPowerCoefficient5(0.0)

  vrf_terminal = OpenStudio::Model::ZoneHVACTerminalUnitVariableRefrigerantFlow.new(model, coolingCoil, heatingCoil, fan)

  vrf_terminal.addToThermalZone(z)
  vrf_fluid_temperature_control.addTerminal(vrf_terminal)
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
