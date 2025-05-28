# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'
require_relative 'lib/surface_visitor'

class SurfaceNetworkBuilder < SurfaceVisitor
  def initialize(model)
    refcond = OpenStudio::Model::AirflowNetworkReferenceCrackConditions.new(model, 20.0, 101325.0, 0.0)
    @interiorCrack = OpenStudio::Model::AirflowNetworkCrack.new(model, 0.050, 0.65, refcond)
    @exteriorCrack = OpenStudio::Model::AirflowNetworkCrack.new(model, 0.025, 0.65, refcond)
    super(model)
  end

  def interiorFloor(model, surface, adjacentSurface)
    return if surface.outsideBoundaryCondition.start_with?('Ground')

    # Create a surface linkage
    link = surface.getAirflowNetworkSurface(@interiorCrack)
  end

  def interiorRoofCeiling(model, surface, adjacentSurface)
    # Create a surface linkage
    link = surface.getAirflowNetworkSurface.new(@interiorCrack)
  end

  def interiorWall(model, surface, adjacentSurface)
    # Create a surface linkage
    link = surface.getAirflowNetworkSurface(@interiorCrack)
  end

  def exteriorSurface(model, surface)
    # Create an external node?
    return if surface.outsideBoundaryCondition.start_with?('Ground')

    # Create a surface linkage
    link = surface.getAirflowNetworkSurface(@exteriorCrack)
  end
end

def addSystemType3(model)
  alwaysOn = model.alwaysOnDiscreteSchedule

  airLoopHVAC = OpenStudio::Model::AirLoopHVAC.new(model)
  airLoopHVAC.setName('Packaged Rooftop Air Conditioner')
  # when an airloophvac is contructed, its constructor automatically creates a sizing:system object
  # the default sizing:system contstructor makes a system:sizing object appropriate for a multizone VAV system
  # this systems is a constant volume system with no VAV terminals, and needs different default settings

  # get the sizing:system object associated with the airloophvac
  sizingSystem = airLoopHVAC.sizingSystem()

  # set the default parameters correctly for a constant volume system with no VAV terminals
  sizingSystem.setTypeofLoadtoSizeOn('Sensible')
  sizingSystem.autosizeDesignOutdoorAirFlowRate
  sizingSystem.setCentralHeatingMaximumSystemAirFlowRatio(1.0)
  sizingSystem.setPreheatDesignTemperature(7.0)
  sizingSystem.setPreheatDesignHumidityRatio(0.008)
  sizingSystem.setPrecoolDesignTemperature(12.8)
  sizingSystem.setPrecoolDesignHumidityRatio(0.008)
  sizingSystem.setCentralCoolingDesignSupplyAirTemperature(12.8)
  sizingSystem.setCentralHeatingDesignSupplyAirTemperature(40.0)
  sizingSystem.setSizingOption('NonCoincident')
  sizingSystem.setAllOutdoorAirinCooling(false)
  sizingSystem.setAllOutdoorAirinHeating(false)
  sizingSystem.setCentralCoolingDesignSupplyAirHumidityRatio(0.0085)
  sizingSystem.setCentralHeatingDesignSupplyAirHumidityRatio(0.0080)
  sizingSystem.setCoolingDesignAirFlowMethod('DesignDay')
  sizingSystem.setCoolingDesignAirFlowRate(0.0)
  sizingSystem.setHeatingDesignAirFlowMethod('DesignDay')
  sizingSystem.setHeatingDesignAirFlowRate(0.0)
  sizingSystem.setSystemOutdoorAirMethod('ZoneSum')

  fan = OpenStudio::Model::FanConstantVolume.new(model)
  fan.setPressureRise(500)

  coilHeatingGas = OpenStudio::Model::CoilHeatingGas.new(model, alwaysOn)

  coilCooling = OpenStudio::Model::CoilCoolingDXSingleSpeed.new(model)

  setpointMSZR = OpenStudio::Model::SetpointManagerSingleZoneReheat.new(model)

  controllerOutdoorAir = OpenStudio::Model::ControllerOutdoorAir.new(model)

  outdoorAirSystem = OpenStudio::Model::AirLoopHVACOutdoorAirSystem.new(model, controllerOutdoorAir)

  supplyOutletNode = airLoopHVAC.supplyOutletNode()

  outdoorAirSystem.addToNode(supplyOutletNode)
  coilCooling.addToNode(supplyOutletNode)
  coilHeatingGas.addToNode(supplyOutletNode)
  fan.addToNode(supplyOutletNode)

  # Node node1 = fan.outletModelObject()->cast<Node>();
  # setpointMSZR.addToNode(node1);

  node1 = fan.outletModelObject.get.to_Node.get
  setpointMSZR.addToNode(node1)

  # Starting with E 9.0.0, Uncontrolled is deprecated and replaced with
  # ConstantVolume:NoReheat
  if Gem::Version.new(OpenStudio.openStudioVersion) >= Gem::Version.new('2.7.0')
    terminal = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, alwaysOn)
  else
    terminal = OpenStudio::Model::AirTerminalSingleDuctUncontrolled.new(model, alwaysOn)
  end

  airLoopHVAC.addBranchForHVACComponent(terminal)

  return airLoopHVAC
end

def addSimpleSystem(model)
  alwaysOn = model.alwaysOnDiscreteSchedule

  airLoopHVAC = OpenStudio::Model::AirLoopHVAC.new(model)
  airLoopHVAC.setName('Packaged Rooftop Air Conditioner')
  # when an airloophvac is contructed, its constructor automatically creates a sizing:system object
  # the default sizing:system contstructor makes a system:sizing object appropriate for a multizone VAV system
  # this systems is a constant volume system with no VAV terminals, and needs different default settings

  # get the sizing:system object associated with the airloophvac
  sizingSystem = airLoopHVAC.sizingSystem()

  # set the default parameters correctly for a constant volume system with no VAV terminals
  sizingSystem.setTypeofLoadtoSizeOn('Sensible')
  sizingSystem.autosizeDesignOutdoorAirFlowRate
  sizingSystem.setCentralHeatingMaximumSystemAirFlowRatio(1.0)
  sizingSystem.setPreheatDesignTemperature(7.0)
  sizingSystem.setPreheatDesignHumidityRatio(0.008)
  sizingSystem.setPrecoolDesignTemperature(12.8)
  sizingSystem.setPrecoolDesignHumidityRatio(0.008)
  sizingSystem.setCentralCoolingDesignSupplyAirTemperature(12.8)
  sizingSystem.setCentralHeatingDesignSupplyAirTemperature(40.0)
  sizingSystem.setSizingOption('NonCoincident')
  sizingSystem.setAllOutdoorAirinCooling(false)
  sizingSystem.setAllOutdoorAirinHeating(false)
  sizingSystem.setCentralCoolingDesignSupplyAirHumidityRatio(0.0085)
  sizingSystem.setCentralHeatingDesignSupplyAirHumidityRatio(0.0080)
  sizingSystem.setCoolingDesignAirFlowMethod('DesignDay')
  sizingSystem.setCoolingDesignAirFlowRate(0.0)
  sizingSystem.setHeatingDesignAirFlowMethod('DesignDay')
  sizingSystem.setHeatingDesignAirFlowRate(0.0)
  # sizingSystem.setSystemOutdoorAirMethod("ZoneSum")

  fan = OpenStudio::Model::FanConstantVolume.new(model)
  fan.setPressureRise(500)

  coilHeatingGas = OpenStudio::Model::CoilHeatingGas.new(model, alwaysOn)

  coilCooling = OpenStudio::Model::CoilCoolingDXSingleSpeed.new(model)

  setpointMSZR = OpenStudio::Model::SetpointManagerSingleZoneReheat.new(model)

  # controllerOutdoorAir = OpenStudio::Model::ControllerOutdoorAir.new(model)

  # outdoorAirSystem = OpenStudio::Model::AirLoopHVACOutdoorAirSystem.new(model,controllerOutdoorAir)

  supplyOutletNode = airLoopHVAC.supplyOutletNode()

  # outdoorAirSystem.addToNode(supplyOutletNode)
  fan.addToNode(supplyOutletNode)
  coilCooling.addToNode(supplyOutletNode)
  coilHeatingGas.addToNode(supplyOutletNode)

  # Node node1 = fan.outletModelObject()->cast<Node>();
  # setpointMSZR.addToNode(node1);

  # node1 = fan.outletModelObject().get.to_Node.get
  node1 = coilHeatingGas.outletModelObject.get.to_Node.get
  setpointMSZR.addToNode(node1)

  if Gem::Version.new(OpenStudio.openStudioVersion) >= Gem::Version.new('2.7.0')
    terminal = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, alwaysOn)
  else
    terminal = OpenStudio::Model::AirTerminalSingleDuctUncontrolled.new(model, alwaysOn)
  end

  airLoopHVAC.addBranchForHVACComponent(terminal)

  return airLoopHVAC
end

def addSimpleSystemAFN(model)
  alwaysOn = model.alwaysOnDiscreteSchedule

  airLoopHVAC = OpenStudio::Model::AirLoopHVAC.new(model)
  airLoopHVAC.setName('Packaged Rooftop Air Conditioner')
  # when an airloophvac is contructed, its constructor automatically creates a sizing:system object
  # the default sizing:system contstructor makes a system:sizing object appropriate for a multizone VAV system
  # this systems is a constant volume system with no VAV terminals, and needs different default settings

  # get the sizing:system object associated with the airloophvac
  sizingSystem = airLoopHVAC.sizingSystem()

  # set the default parameters correctly for a constant volume system with no VAV terminals
  sizingSystem.setTypeofLoadtoSizeOn('Sensible')
  sizingSystem.autosizeDesignOutdoorAirFlowRate
  if Gem::Version.new(OpenStudio.openStudioVersion) >= Gem::Version.new('3.3.0')
    sizingSystem.setCentralHeatingMaximumSystemAirFlowRatio(1.0)
  else
    sizingSystem.setMinimumSystemAirFlowRatio(1.0)
  end
  sizingSystem.setPreheatDesignTemperature(7.0)
  sizingSystem.setPreheatDesignHumidityRatio(0.008)
  sizingSystem.setPrecoolDesignTemperature(12.8)
  sizingSystem.setPrecoolDesignHumidityRatio(0.008)
  sizingSystem.setCentralCoolingDesignSupplyAirTemperature(12.8)
  sizingSystem.setCentralHeatingDesignSupplyAirTemperature(40.0)
  sizingSystem.setSizingOption('NonCoincident')
  sizingSystem.setAllOutdoorAirinCooling(false)
  sizingSystem.setAllOutdoorAirinHeating(false)
  sizingSystem.setCentralCoolingDesignSupplyAirHumidityRatio(0.0085)
  sizingSystem.setCentralHeatingDesignSupplyAirHumidityRatio(0.0080)
  sizingSystem.setCoolingDesignAirFlowMethod('DesignDay')
  sizingSystem.setCoolingDesignAirFlowRate(0.0)
  sizingSystem.setHeatingDesignAirFlowMethod('DesignDay')
  sizingSystem.setHeatingDesignAirFlowRate(0.0)
  # sizingSystem.setSystemOutdoorAirMethod("ZoneSum")

  fan = OpenStudio::Model::FanConstantVolume.new(model)
  fan.setPressureRise(500)

  coilHeatingGas = OpenStudio::Model::CoilHeatingGas.new(model, alwaysOn)

  coilCooling = OpenStudio::Model::CoilCoolingDXSingleSpeed.new(model)

  setpointMSZR = OpenStudio::Model::SetpointManagerSingleZoneReheat.new(model)

  # controllerOutdoorAir = OpenStudio::Model::ControllerOutdoorAir.new(model)

  # outdoorAirSystem = OpenStudio::Model::AirLoopHVACOutdoorAirSystem.new(model,controllerOutdoorAir)

  supplyOutletNode = airLoopHVAC.supplyOutletNode()

  # outdoorAirSystem.addToNode(supplyOutletNode)
  fan.addToNode(supplyOutletNode)
  coilCooling.addToNode(supplyOutletNode)
  coilHeatingGas.addToNode(supplyOutletNode)

  # Node node1 = fan.outletModelObject()->cast<Node>();
  # setpointMSZR.addToNode(node1);

  # node1 = fan.outletModelObject().get.to_Node.get
  node1 = coilHeatingGas.outletModelObject.get.to_Node.get
  setpointMSZR.addToNode(node1)

  if Gem::Version.new(OpenStudio.openStudioVersion) >= Gem::Version.new('2.7.0')
    terminal = OpenStudio::Model::AirTerminalSingleDuctConstantVolumeNoReheat.new(model, alwaysOn)
  else
    terminal = OpenStudio::Model::AirTerminalSingleDuctUncontrolled.new(model, alwaysOn)
  end

  airLoopHVAC.addBranchForHVACComponent(terminal)

  # Create AFN components
  fanComponent = fan.getAirflowNetworkFan
  heatingComponent = coilHeatingGas.getAirflowNetworkEquivalentDuct(0.1, 1.0)
  coolingComponent = coilCooling.getAirflowNetworkEquivalentDuct(0.1, 1.0)
  # And all the ducts
  mainTruck = OpenStudio::Model::AirflowNetworkDuct.new(model)
  mainTruck.setDuctLength(2)
  mainTruck.setHydraulicDiameter(0.4064)
  mainTruck.setCrossSectionArea(0.1297)
  mainTruck.setSurfaceRoughness(0.0009)
  mainTruck.setCoefficientforLocalDynamicLossDuetoFitting(0.01)
  mainTruck.setDuctWallHeatTransmittanceCoefficient(0.946792)
  mainTruck.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
  mainTruck.setOutsideConvectionCoefficient(5.018)
  mainTruck.setInsideConvectionCoefficient(25.09)

  mainReturn = OpenStudio::Model::AirflowNetworkDuct.new(model)
  mainReturn.setDuctLength(1)
  mainReturn.setHydraulicDiameter(0.5)
  mainReturn.setCrossSectionArea(0.1963)
  mainReturn.setSurfaceRoughness(0.0009)
  mainReturn.setCoefficientforLocalDynamicLossDuetoFitting(0.01)
  mainReturn.setDuctWallHeatTransmittanceCoefficient(0.001226)
  mainReturn.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
  mainReturn.setOutsideConvectionCoefficient(0.0065)
  mainReturn.setInsideConvectionCoefficient(0.0325)

  airLoopReturn = OpenStudio::Model::AirflowNetworkDuct.new(model)
  airLoopReturn.setDuctLength(0.1)
  airLoopReturn.setHydraulicDiameter(1)
  airLoopReturn.setCrossSectionArea(0.7854)
  airLoopReturn.setSurfaceRoughness(0.0001)
  airLoopReturn.setCoefficientforLocalDynamicLossDuetoFitting(0)
  airLoopReturn.setDuctWallHeatTransmittanceCoefficient(0.001226)
  airLoopReturn.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
  airLoopReturn.setOutsideConvectionCoefficient(0.0065)
  airLoopReturn.setInsideConvectionCoefficient(0.0325)

  airLoopSupply = OpenStudio::Model::AirflowNetworkDuct.new(model)
  airLoopSupply.setDuctLength(0.1)
  airLoopSupply.setHydraulicDiameter(1)
  airLoopSupply.setCrossSectionArea(0.7854)
  airLoopSupply.setSurfaceRoughness(0.0001)
  airLoopSupply.setCoefficientforLocalDynamicLossDuetoFitting(0)
  airLoopSupply.setDuctWallHeatTransmittanceCoefficient(0.001226)
  airLoopSupply.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
  airLoopSupply.setOutsideConvectionCoefficient(0.0065)
  airLoopSupply.setInsideConvectionCoefficient(0.0325)

  # Build the AFN loop, first get the nodes and components we need

  splitter = airLoopHVAC.zoneSplitter
  mixer = airLoopHVAC.zoneMixer

  equipmentInletNode = splitter.inletModelObject.get.to_Node.get

  zoneSupplyRegisterNode = nil
  zoneOutletNode = mixer.inletModelObject(0).get.to_Node.get

  mainReturnNode = mixer.outletModelObject.get.to_Node.get

  mixerOutletNode = mixer.outletModelObject.get.to_Node.get
  fanInletNode = fan.inletModelObject.get.to_Node.get
  fanOutletNode = fan.outletModelObject.get.to_Node.get
  heatingInletNode = coilHeatingGas.inletModelObject.get.to_Node.get
  heatingOutletNode = coilHeatingGas.outletModelObject.get.to_Node.get

  # Now walk around the loop and make the AFN nodes
  equipmentInletNode_AFN = equipmentInletNode.getAirflowNetworkDistributionNode
  splitterNode_AFN = splitter.getAirflowNetworkDistributionNode
  zoneSupplyNode_AFN = OpenStudio::Model::AirflowNetworkDistributionNode.new(model)

  zoneSupplyRegisterNode_AFN = nil
  # zoneOutletNode_AFN = zoneOutletNode.getAirflowNetworkDistributionNode

  zoneReturnNode_AFN = OpenStudio::Model::AirflowNetworkDistributionNode.new(model)
  mixerNode_AFN = mixer.getAirflowNetworkDistributionNode
  mainReturnNode_AFN = mainReturnNode.getAirflowNetworkDistributionNode
  fanInletNode_AFN = fanInletNode.getAirflowNetworkDistributionNode
  fanOutletNode_AFN = fanOutletNode.getAirflowNetworkDistributionNode
  heatingInletNode_AFN = heatingInletNode.getAirflowNetworkDistributionNode
  heatingOutletNode_AFN = heatingOutletNode.getAirflowNetworkDistributionNode

  # Now the links

  mainLink = OpenStudio::Model::AirflowNetworkDistributionLinkage.new(model, equipmentInletNode_AFN, splitterNode_AFN, mainTruck)
  # Zone stuff goes in here
  returnMixerLink = OpenStudio::Model::AirflowNetworkDistributionLinkage.new(model, mixerNode_AFN, mainReturnNode_AFN, mainReturn)
  systemReturnLink = OpenStudio::Model::AirflowNetworkDistributionLinkage.new(model, mainReturnNode_AFN, fanInletNode_AFN, airLoopReturn)
  fanLink = OpenStudio::Model::AirflowNetworkDistributionLinkage.new(model, fanInletNode_AFN, fanOutletNode_AFN, fanComponent)
  coolingCoilLink = OpenStudio::Model::AirflowNetworkDistributionLinkage.new(model, fanOutletNode_AFN, heatingInletNode_AFN, coolingComponent)
  heatingCoilLink = OpenStudio::Model::AirflowNetworkDistributionLinkage.new(model, heatingInletNode_AFN, heatingOutletNode_AFN, heatingComponent)
  equipmentAirLoopLink = OpenStudio::Model::AirflowNetworkDistributionLinkage.new(model, heatingOutletNode_AFN, equipmentInletNode_AFN, airLoopSupply)

  return airLoopHVAC
end

model = BaselineModel.new

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry({ 'length' => 17.242,
                     'width' => 10.778,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
# model.add_windows({"wwr" => 0.4,
#                  "offset" => 1,
#                  "application_type" => "Above Floor"})

# add ASHRAE System type 03, PSZ-AC
# model.add_hvac({"ashrae_sys_num" => '03'})

zone = model.getThermalZones[0] # There should only be one...

# hvac = addSystemType3(model)
hvac = addSimpleSystemAFN(model)
hvac = hvac.to_AirLoopHVAC.get
hvac.addBranchForZone(zone)
outlet_node = hvac.supplyOutletNode
setpoint_manager = outlet_node.setpointManagers.select { |spm| spm.to_SetpointManagerSingleZoneReheat.is_initialized }.first.to_SetpointManagerSingleZoneReheat.get
setpoint_manager.setControlZone(zone)

# add ASHRAE System type 08, VAV w/ PFP Boxes
# DLM: this invokes weird mass conservation rules with VAV
# model.add_hvac({"ashrae_sys_num" => '08'})

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 22, 'cooling_setpoint' => 26.6 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type # OK, yeah, this is wrong

# remove all infiltration
# model.getSpaceInfiltrationDesignFlowRates.each do |infil|
#  infil.remove
# end

# add design days to the model (Chicago)
model.add_design_days

# add simulation control
afn_control = model.getAirflowNetworkSimulationControl
afn_control.setAirflowNetworkControl('MultizoneWithDistribution')

# make an afn zone
afnzone = zone.getAirflowNetworkZone

# This is kind of lame, regetting stuff we already have above. Need to rethink how this
# is structured at some point.
splitter = hvac.zoneSplitter
mixer = hvac.zoneMixer
splitterNode_AFN = splitter.getAirflowNetworkDistributionNode
mixerNode_AFN = splitter.getAirflowNetworkDistributionNode

# This is not great either
zoneOutletNode = mixer.inletModelObject(0).get.to_Node.get

comps = hvac.demandComponents(hvac.demandInletNode, zone)
zoneInletNode = comps[-2].to_Node.get

# zoneInletNode = zone.airLoopHVACTerminal.get.to_StraightComponent.get.outletModelObject.get.to_Node.get

zoneInletNode_AFN = zoneInletNode.getAirflowNetworkDistributionNode
zoneOutletNode_AFN = zoneOutletNode.getAirflowNetworkDistributionNode

# Make the duct elements
zoneSupply = OpenStudio::Model::AirflowNetworkDuct.new(model)
zoneSupply.setDuctLength(10)
zoneSupply.setHydraulicDiameter(0.4064)
zoneSupply.setCrossSectionArea(0.1297)
zoneSupply.setSurfaceRoughness(0.0009)
zoneSupply.setCoefficientforLocalDynamicLossDuetoFitting(0.91)
zoneSupply.setDuctWallHeatTransmittanceCoefficient(0.946792)
zoneSupply.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
zoneSupply.setOutsideConvectionCoefficient(5.018)
zoneSupply.setInsideConvectionCoefficient(25.09)

zoneReturn = OpenStudio::Model::AirflowNetworkDuct.new(model)
zoneReturn.setDuctLength(3)
zoneReturn.setHydraulicDiameter(0.5)
zoneReturn.setCrossSectionArea(0.1963)
zoneReturn.setSurfaceRoughness(0.0009)
zoneReturn.setCoefficientforLocalDynamicLossDuetoFitting(0.01)
zoneReturn.setDuctWallHeatTransmittanceCoefficient(0.001226)
zoneReturn.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
zoneReturn.setOutsideConvectionCoefficient(0.0065)
zoneReturn.setInsideConvectionCoefficient(0.0325)

zoneConnectionDuct = OpenStudio::Model::AirflowNetworkDuct.new(model)
zoneConnectionDuct.setDuctLength(0.1)
zoneConnectionDuct.setHydraulicDiameter(1)
zoneConnectionDuct.setCrossSectionArea(0.7854)
zoneConnectionDuct.setSurfaceRoughness(0.0001)
zoneConnectionDuct.setCoefficientforLocalDynamicLossDuetoFitting(0)
zoneConnectionDuct.setDuctWallHeatTransmittanceCoefficient(0.001226)
zoneConnectionDuct.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
zoneConnectionDuct.setOutsideConvectionCoefficient(0.0065)
zoneConnectionDuct.setInsideConvectionCoefficient(0.0325)

# And now the linkages
zoneSupplyLink = OpenStudio::Model::AirflowNetworkDistributionLinkage.new(model, splitterNode_AFN, zoneInletNode_AFN, zoneSupply)
zoneSupplyConnectionLink = OpenStudio::Model::AirflowNetworkDistributionLinkage.new(model, zoneInletNode_AFN, afnzone, zoneConnectionDuct)
zoneReturnConnectionLink = OpenStudio::Model::AirflowNetworkDistributionLinkage.new(model, afnzone, zoneOutletNode_AFN, zoneConnectionDuct)
zoneSupplyLink = OpenStudio::Model::AirflowNetworkDistributionLinkage.new(model, zoneOutletNode_AFN, mixerNode_AFN, zoneReturn)

# Connect up envelope
visitor = SurfaceNetworkBuilder.new(model)

# add output reports
add_out_vars = false
if add_out_vars
  OpenStudio::Model::OutputVariable.new('AFN Node Temperature', model)
  OpenStudio::Model::OutputVariable.new('AFN Node Wind Pressure', model)
  OpenStudio::Model::OutputVariable.new('AFN Linkage Node 1 to Node 2 Mass Flow Rate', model)
  OpenStudio::Model::OutputVariable.new('AFN Linkage Node 1 to Node 2 Pressure Difference', model)
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
