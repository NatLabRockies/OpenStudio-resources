# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

m = BaselineModel.new

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
m.add_geometry({ 'length' => 100,
                 'width' => 50,
                 'num_floors' => 1,
                 'floor_to_floor_height' => 3,
                 'plenum_height' => 1,
                 'perimeter_zone_depth' => 3 })

# add windows at a 40% window-to-wall ratio
m.add_windows({ 'wwr' => 0.4,
                'offset' => 1,
                'application_type' => 'Above Floor' })

# Add ASHRAE System type 07, VAV w/ Reheat, this creates a ChW, a HW loop and a
# Condenser Loop
m.add_hvac({ 'ashrae_sys_num' => '07' })

# add thermostats
m.add_thermostats({ 'heating_setpoint' => 24,
                    'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type

# add design days to the model (Chicago)
m.add_design_days

###############################################################################
#         R E P L A C E    A T Us    W/    F O U R    P I P E    B E A Ms
###############################################################################

ct = m.getCoolingTowerSingleSpeeds.first
p_cnd = ct.plantLoop.get

b = m.getBoilerHotWaters.first
p_hw = b.plantLoop.get

ch = m.getChillerElectricEIRs.first
p_chw = ch.plantLoop.get

# Recreate the same TableMultiVariableLookup/TableLookup that is created in
# the Ctor for CoilCoolingFourPipeBeam, except with a normalization reference
# The goal being to test the NormalizationReference feature since the E+ 9.2.0
# change to TableLookup, we pick one.
norm_ref = 2.4

if Gem::Version.new(OpenStudio.openStudioVersion) > Gem::Version.new('3.4.0')
  coolCapModFuncOfWaterFlow = OpenStudio::Model::TableLookup.new(m)

  coolCapModFuncOfWaterFlow.setName('CoolCapModFuncOfWaterFlow')
  coolCapModFuncOfWaterFlow.setOutputUnitType('Dimensionless')

  coolCapModFuncOfWaterFlow.setMinimumOutput(0.0 * norm_ref)
  coolCapModFuncOfWaterFlow.setMaximumOutput(1.04 * norm_ref)

  coolCapModFuncOfWaterFlow.setNormalizationMethod('DivisorOnly')
  coolCapModFuncOfWaterFlow.setNormalizationDivisor(norm_ref)
  values = [0.0, 0.001, 0.71, 0.85, 0.92, 0.97, 1.0, 1.04].map { |v| v * norm_ref }
  coolCapModFuncOfWaterFlow.setOutputValues(values)

  coolCapModFuncOfWaterFlowVar1 = OpenStudio::Model::TableIndependentVariable.new(m)
  coolCapModFuncOfWaterFlow.addIndependentVariable(coolCapModFuncOfWaterFlowVar1)
  coolCapModFuncOfWaterFlowVar1.setName('CoolCapModFuncOfWaterFlow_IndependentVariable1')
  coolCapModFuncOfWaterFlowVar1.setInterpolationMethod('Cubic')
  coolCapModFuncOfWaterFlowVar1.setExtrapolationMethod('Constant')
  coolCapModFuncOfWaterFlowVar1.setMinimumValue(0.0)
  coolCapModFuncOfWaterFlowVar1.setMaximumValue(1.33)
  coolCapModFuncOfWaterFlowVar1.setUnitType('Dimensionless')
  coolCapModFuncOfWaterFlowVar1.setValues([0.0, 0.05, 0.33333, 0.5, 0.666667, 0.833333, 1.0, 1.333333])
else
  coolCapModFuncOfWaterFlow = OpenStudio::Model::TableMultiVariableLookup.new(m, 1)
  coolCapModFuncOfWaterFlow.setName('CoolCapModFuncOfWaterFlow')

  coolCapModFuncOfWaterFlow.setCurveType('Quadratic')
  coolCapModFuncOfWaterFlow.setInterpolationMethod('EvaluateCurveToLimits')
  coolCapModFuncOfWaterFlow.setMinimumValueofX1(0)
  coolCapModFuncOfWaterFlow.setMaximumValueofX1(1.33)
  coolCapModFuncOfWaterFlow.setInputUnitTypeforX1('Dimensionless')
  coolCapModFuncOfWaterFlow.setOutputUnitType('Dimensionless')

  coolCapModFuncOfWaterFlow.setNormalizationReference(norm_ref)

  # Quoting I/O ref for 9.1:
  # > Both the output values and minimum/maximum curve limits
  # > are normalized as applicable.
  coolCapModFuncOfWaterFlow.setMinimumTableOutput(0.0 * norm_ref)
  coolCapModFuncOfWaterFlow.setMaximumTableOutput(1.04 * norm_ref)

  coolCapModFuncOfWaterFlow.addPoint(0.0, 0.0 * norm_ref)
  coolCapModFuncOfWaterFlow.addPoint(0.05, 0.001 * norm_ref)
  coolCapModFuncOfWaterFlow.addPoint(0.33333, 0.71 * norm_ref)
  coolCapModFuncOfWaterFlow.addPoint(0.5, 0.85 * norm_ref)
  coolCapModFuncOfWaterFlow.addPoint(0.666667, 0.92 * norm_ref)
  coolCapModFuncOfWaterFlow.addPoint(0.833333, 0.97 * norm_ref)
  coolCapModFuncOfWaterFlow.addPoint(1.0, 1.0 * norm_ref) # <= RATING POINT
  coolCapModFuncOfWaterFlow.addPoint(1.333333, 1.04 * norm_ref)
end

# Replace all terminals with ATUFourPipeBeams
# There is only one airLoopHVAC, so I get it here
air_loop = m.getAirLoopHVACs[0]

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = m.getThermalZones.sort_by { |z| z.name.to_s }
zones.each do |z|
  # air_loop = z.airLoopHVAC.get
  air_loop.removeBranchForZone(z)

  # Create a cooling coil, and add it to the ChW Loop
  cc = OpenStudio::Model::CoilCoolingFourPipeBeam.new(m)
  cc.setName("#{z.name} ATU FourPipeBeam Cooling Coil")
  # Set the curve with the above table
  cc.setBeamCoolingCapacityChilledWaterFlowModificationFactorCurve(coolCapModFuncOfWaterFlow)
  p_chw.addDemandBranchForComponent(cc)

  # Create a heating coil, and add it to the HW Loop
  hc = OpenStudio::Model::CoilHeatingFourPipeBeam.new(m)
  hc.setName("#{z.name} ATU FourPipeBeam Heating Coil")
  p_hw.addDemandBranchForComponent(hc)

  atu = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeFourPipeBeam.new(m, cc, hc)
  atu.setName("#{z.name} ATU FourPipeBeam")
  air_loop.addBranchForZone(z, atu.to_StraightComponent)

  z.zoneAirNode.setName("#{z.name} Zone Air Node")
end

# All setters:

# ATU
# atu.setPrimaryAirAvailabilitySchedule()
# atu.setCoolingAvailabilitySchedule()
# atu.setHeatingAvailabilitySchedule()
# atu.setCoolingCoil()
# atu.setHeatingCoil()
# atu.setDesignPrimaryAirVolumeFlowRate()
# atu.setDesignChilledWaterVolumeFlowRate()
# atu.setDesignHotWaterVolumeFlowRate()
# atu.setZoneTotalBeamLength()
# atu.setRatedPrimaryAirFlowRateperBeamLength()

# CoilCoolingFourPipeBeam
# cc.setBeamRatedCoolingCapacityperBeamLength()
# cc.setBeamRatedCoolingRoomAirChilledWaterTemperatureDifference()
# cc.setBeamRatedChilledWaterVolumeFlowRateperBeamLength()
# cc.setBeamCoolingCapacityTemperatureDifferenceModificationFactorCurve()
# cc.setBeamCoolingCapacityAirFlowModificationFactorCurve()
# cc.setBeamCoolingCapacityChilledWaterFlowModificationFactorCurve()

# CoilHeatingFourPipeBeam

###############################################################################
#         R E N A M E    E Q U I P M E N T    A N D    N O D E S
###############################################################################

# Remove pipes
m.getPipeAdiabatics.each(&:remove)

# Rename loops
p_cnd.setName('CndW Loop')
p_hw.setName('HW Loop')
p_chw.setName('ChW Loop')

m.getCoilCoolingWaters[0].setName('VAV Central ChW Coil')

m.getCoilHeatingWaters.each do |coil|
  next if !coil.airLoopHVAC.is_initialized

  coil.setName('VAV Central HW Coil')
end

# Rename nodes
m.getPlantLoops.each do |p|
  prefix = p.name.to_s

  p.supplyComponents.reverse.each do |c|
    next if c.to_Node.is_initialized

    if c.to_ConnectorMixer.is_initialized
      c.setName("#{prefix} Supply ConnectorMixer")
    elsif c.to_ConnectorSplitter.is_initialized
      c.setName("#{prefix} Supply ConnectorSplitter")
    else

      obj_type = c.iddObjectType.valueName
      obj_type_name = obj_type.gsub('OS_', '').gsub('_', '')

      if c.to_PumpVariableSpeed.is_initialized
        c.setName("#{prefix} VSD Pump")
      elsif c.to_PumpConstantSpeed.is_initialized
        c.setName("#{prefix} CstSpeed Pump")
      elsif c.to_HeaderedPumpsVariableSpeed.is_initialized
        c.setName("#{prefix} Headered VSD Pump")
      elsif c.to_HeaderedPumpsConstantSpeed.is_initialized
        c.setName("#{prefix} Headered CstSpeed Pump")
      elsif !c.to_CentralHeatPumpSystem.is_initialized
        c.setName("#{prefix} #{obj_type_name}")
      end

      method_name = "to_#{obj_type_name}"
      next if !c.respond_to?(method_name)

      actual_thing = c.method(method_name).call
      next if actual_thing.empty?

      actual_thing = actual_thing.get
      if actual_thing.respond_to?('inletModelObject') && actual_thing.inletModelObject.is_initialized
        inlet_mo = actual_thing.inletModelObject.get
        inlet_mo.setName("#{prefix} Supply Side #{actual_thing.name} Inlet Node")
      end
      if actual_thing.respond_to?('outletModelObject') && actual_thing.outletModelObject.is_initialized
        outlet_mo = actual_thing.outletModelObject.get
        outlet_mo.setName("#{prefix} Supply Side #{actual_thing.name} Outlet Node")
      end
    end
  end

  p.demandComponents.reverse.each do |c|
    next if c.to_Node.is_initialized

    if c.to_ConnectorMixer.is_initialized
      c.setName("#{prefix} Demand ConnectorMixer")
    elsif c.to_ConnectorSplitter.is_initialized
      c.setName("#{prefix} Demand ConnectorSplitter")
    else
      obj_type = c.iddObjectType.valueName
      obj_type_name = obj_type.gsub('OS_', '').gsub('_', '')
      method_name = "to_#{obj_type_name}"
      next if !c.respond_to?(method_name)

      actual_thing = c.method(method_name).call
      next if actual_thing.empty?

      actual_thing = actual_thing.get
      if actual_thing.respond_to?('inletModelObject') && actual_thing.inletModelObject.is_initialized
        inlet_mo = actual_thing.inletModelObject.get
        inlet_mo.setName("#{prefix} Demand Side #{actual_thing.name} Inlet Node")
      end
      if actual_thing.respond_to?('outletModelObject') && actual_thing.outletModelObject.is_initialized
        outlet_mo = actual_thing.outletModelObject.get
        outlet_mo.setName("#{prefix} Demand Side #{actual_thing.name} Outlet Node")
      end

      # WaterToAirComponent
      if actual_thing.respond_to?('waterInletModelObject') && actual_thing.waterInletModelObject.is_initialized
        inlet_mo = actual_thing.waterInletModelObject.get
        inlet_mo.setName("#{prefix} Demand Side #{actual_thing.name} Inlet Node")
      end
      if actual_thing.respond_to?('waterOutletModelObject') && actual_thing.waterOutletModelObject.is_initialized
        outlet_mo = actual_thing.waterOutletModelObject.get
        outlet_mo.setName("#{prefix} Demand Side #{actual_thing.name} Outlet Node")
      end

    end
  end

  node = p.supplyInletNode
  new_name = 'Supply Inlet Node'
  new_name = "#{prefix} #{new_name}"
  node.setName(new_name)

  node = p.supplyOutletNode
  new_name = 'Supply Outlet Node'
  new_name = "#{prefix} #{new_name}"
  node.setName(new_name)

  # Demand Side
  node = p.demandInletNode
  new_name = 'Demand Inlet Node'
  new_name = "#{prefix} #{new_name}"
  node.setName(new_name)

  node = p.demandOutletNode
  new_name = 'Demand Outlet Node'
  new_name = "#{prefix} #{new_name}"
  node.setName(new_name)
end

########################### Request output variables ##########################

add_out_vars = false
freq = 'Detailed'

if add_out_vars
  atu = m.getAirTerminalSingleDuctConstantVolumeFourPipeBeams[0]
  # CentralHeatPumpSystem outputs, implemented in the class
  atu.outputVariableNames.each do |varname|
    outvar = OpenStudio::Model::OutputVariable.new(varname, m)
    outvar.setReportingFrequency(freq)
  end
end

# save the OpenStudio model (.osm)
m.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                        'osm_name' => 'in.osm' })
