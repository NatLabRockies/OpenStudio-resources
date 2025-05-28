import openstudio

from lib.baseline_model import BaselineModel
from lib.surface_visitor import SurfaceVisitor


class SurfaceNetworkBuilder(SurfaceVisitor):
    def __init__(self, model):
        refcond = openstudio.model.AirflowNetworkReferenceCrackConditions(model, 20.0, 101325.0, 0.0)
        self.interiorCrack = openstudio.model.AirflowNetworkCrack(model, 0.050, 0.65, refcond)
        self.exteriorCrack = openstudio.model.AirflowNetworkCrack(model, 0.025, 0.65, refcond)
        super().__init__(model)

    def interiorFloor(self, model, surface, adjacentSurface):
        if surface.outsideBoundaryCondition().startswith("Ground"):
            return

        # Create a surface linkage
        link = surface.getAirflowNetworkSurface(self.interiorCrack)

    def interiorRoofCeiling(self, model, surface, adjacentSurface):
        # Create a surface linkage
        link = surface.getAirflowNetworkSurface(self.interiorCrack)

    def interiorWall(self, model, surface, adjacentSurface):
        # Create a surface linkage
        link = surface.getAirflowNetworkSurface(self.interiorCrack)

    def exteriorSurface(self, model, surface):
        # Create an external node?
        if surface.outsideBoundaryCondition().startswith("Ground"):
            return

        # Create a surface linkage
        link = surface.getAirflowNetworkSurface(self.exteriorCrack)


def addSystemType3(model):
    alwaysOn = model.alwaysOnDiscreteSchedule()

    airLoopHVAC = openstudio.model.AirLoopHVAC(model)
    airLoopHVAC.setName("Packaged Rooftop Air Conditioner")
    # when an airloophvac is contructed, its constructor automatically creates a sizing:system object
    # the default sizing:system contstructor makes a system:sizing object appropriate for a multizone VAV system
    # this systems is a constant volume system with no VAV terminals, and needs different default settings

    # get the sizing:system object associated with the airloophvac
    sizingSystem = airLoopHVAC.sizingSystem()

    # set the default parameters correctly for a constant volume system with no VAV terminals
    sizingSystem.setTypeofLoadtoSizeOn("Sensible")
    sizingSystem.autosizeDesignOutdoorAirFlowRate()
    sizingSystem.setCentralHeatingMaximumSystemAirFlowRatio(1.0)
    sizingSystem.setPreheatDesignTemperature(7.0)
    sizingSystem.setPreheatDesignHumidityRatio(0.008)
    sizingSystem.setPrecoolDesignTemperature(12.8)
    sizingSystem.setPrecoolDesignHumidityRatio(0.008)
    sizingSystem.setCentralCoolingDesignSupplyAirTemperature(12.8)
    sizingSystem.setCentralHeatingDesignSupplyAirTemperature(40.0)
    sizingSystem.setSizingOption("NonCoincident")
    sizingSystem.setAllOutdoorAirinCooling(False)
    sizingSystem.setAllOutdoorAirinHeating(False)
    sizingSystem.setCentralCoolingDesignSupplyAirHumidityRatio(0.0085)
    sizingSystem.setCentralHeatingDesignSupplyAirHumidityRatio(0.0080)
    sizingSystem.setCoolingDesignAirFlowMethod("DesignDay")
    sizingSystem.setCoolingDesignAirFlowRate(0.0)
    sizingSystem.setHeatingDesignAirFlowMethod("DesignDay")
    sizingSystem.setHeatingDesignAirFlowRate(0.0)
    sizingSystem.setSystemOutdoorAirMethod("ZoneSum")

    fan = openstudio.model.FanConstantVolume(model)
    fan.setPressureRise(500)

    coilHeatingGas = openstudio.model.CoilHeatingGas(model, alwaysOn)

    coilCooling = openstudio.model.CoilCoolingDXSingleSpeed(model)

    setpointMSZR = openstudio.model.SetpointManagerSingleZoneReheat(model)

    controllerOutdoorAir = openstudio.model.ControllerOutdoorAir(model)

    outdoorAirSystem = openstudio.model.AirLoopHVACOutdoorAirSystem(model, controllerOutdoorAir)

    supplyOutletNode = airLoopHVAC.supplyOutletNode()

    outdoorAirSystem.addToNode(supplyOutletNode)
    coilCooling.addToNode(supplyOutletNode)
    coilHeatingGas.addToNode(supplyOutletNode)
    fan.addToNode(supplyOutletNode)

    # Node node1 = fan.outletModelObject()->cast<Node>();
    # setpointMSZR.addToNode(node1);

    node1 = fan.outletModelObject().get().to_Node().get()
    setpointMSZR.addToNode(node1)

    # Starting with E 9.0.0, Uncontrolled is deprecated and replaced with
    # ConstantVolume:NoReheat
    if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("2.7.0"):
        terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, alwaysOn)
    else:
        terminal = openstudio.model.AirTerminalSingleDuctUncontrolled(model, alwaysOn)

    airLoopHVAC.addBranchForHVACComponent(terminal)

    return airLoopHVAC


def addSimpleSystem(model):
    alwaysOn = model.alwaysOnDiscreteSchedule()

    airLoopHVAC = openstudio.model.AirLoopHVAC(model)
    airLoopHVAC.setName("Packaged Rooftop Air Conditioner")
    # when an airloophvac is contructed, its constructor automatically creates a sizing:system object
    # the default sizing:system contstructor makes a system:sizing object appropriate for a multizone VAV system
    # this systems is a constant volume system with no VAV terminals, and needs different default settings

    # get the sizing:system object associated with the airloophvac
    sizingSystem = airLoopHVAC.sizingSystem()

    # set the default parameters correctly for a constant volume system with no VAV terminals
    sizingSystem.setTypeofLoadtoSizeOn("Sensible")
    sizingSystem.autosizeDesignOutdoorAirFlowRate()
    sizingSystem.setCentralHeatingMaximumSystemAirFlowRatio(1.0)
    sizingSystem.setPreheatDesignTemperature(7.0)
    sizingSystem.setPreheatDesignHumidityRatio(0.008)
    sizingSystem.setPrecoolDesignTemperature(12.8)
    sizingSystem.setPrecoolDesignHumidityRatio(0.008)
    sizingSystem.setCentralCoolingDesignSupplyAirTemperature(12.8)
    sizingSystem.setCentralHeatingDesignSupplyAirTemperature(40.0)
    sizingSystem.setSizingOption("NonCoincident")
    sizingSystem.setAllOutdoorAirinCooling(False)
    sizingSystem.setAllOutdoorAirinHeating(False)
    sizingSystem.setCentralCoolingDesignSupplyAirHumidityRatio(0.0085)
    sizingSystem.setCentralHeatingDesignSupplyAirHumidityRatio(0.0080)
    sizingSystem.setCoolingDesignAirFlowMethod("DesignDay")
    sizingSystem.setCoolingDesignAirFlowRate(0.0)
    sizingSystem.setHeatingDesignAirFlowMethod("DesignDay")
    sizingSystem.setHeatingDesignAirFlowRate(0.0)
    # sizingSystem.setSystemOutdoorAirMethod("ZoneSum")

    fan = openstudio.model.FanConstantVolume(model)
    fan.setPressureRise(500)

    coilHeatingGas = openstudio.model.CoilHeatingGas(model, alwaysOn)

    coilCooling = openstudio.model.CoilCoolingDXSingleSpeed(model)

    setpointMSZR = openstudio.model.SetpointManagerSingleZoneReheat(model)

    # controllerOutdoorAir = openstudio.model.ControllerOutdoorAir(model)

    # outdoorAirSystem = openstudio.model.AirLoopHVACOutdoorAirSystem(model,controllerOutdoorAir)

    supplyOutletNode = airLoopHVAC.supplyOutletNode()

    # outdoorAirSystem.addToNode(supplyOutletNode)
    fan.addToNode(supplyOutletNode)
    coilCooling.addToNode(supplyOutletNode)
    coilHeatingGas.addToNode(supplyOutletNode)

    # Node node1 = fan.outletModelObject()->cast<Node>();
    # setpointMSZR.addToNode(node1);

    # node1 = fan.outletModelObject().get.to_Node.get
    node1 = coilHeatingGas.outletModelObject().get().to_Node().get()
    setpointMSZR.addToNode(node1)

    if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("2.7.0"):
        terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, alwaysOn)
    else:
        terminal = openstudio.model.AirTerminalSingleDuctUncontrolled(model, alwaysOn)

    airLoopHVAC.addBranchForHVACComponent(terminal)

    return airLoopHVAC


def addSimpleSystemAFN(model):
    alwaysOn = model.alwaysOnDiscreteSchedule()

    airLoopHVAC = openstudio.model.AirLoopHVAC(model)
    airLoopHVAC.setName("Packaged Rooftop Air Conditioner")
    # when an airloophvac is contructed, its constructor automatically creates a sizing:system object
    # the default sizing:system contstructor makes a system:sizing object appropriate for a multizone VAV system
    # this systems is a constant volume system with no VAV terminals, and needs different default settings

    # get the sizing:system object associated with the airloophvac
    sizingSystem = airLoopHVAC.sizingSystem()

    # set the default parameters correctly for a constant volume system with no VAV terminals
    sizingSystem.setTypeofLoadtoSizeOn("Sensible")
    sizingSystem.autosizeDesignOutdoorAirFlowRate()
    if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("3.3.0"):
        sizingSystem.setCentralHeatingMaximumSystemAirFlowRatio(1.0)
    else:
        sizingSystem.setMinimumSystemAirFlowRatio(1.0)

    sizingSystem.setPreheatDesignTemperature(7.0)
    sizingSystem.setPreheatDesignHumidityRatio(0.008)
    sizingSystem.setPrecoolDesignTemperature(12.8)
    sizingSystem.setPrecoolDesignHumidityRatio(0.008)
    sizingSystem.setCentralCoolingDesignSupplyAirTemperature(12.8)
    sizingSystem.setCentralHeatingDesignSupplyAirTemperature(40.0)
    sizingSystem.setSizingOption("NonCoincident")
    sizingSystem.setAllOutdoorAirinCooling(False)
    sizingSystem.setAllOutdoorAirinHeating(False)
    sizingSystem.setCentralCoolingDesignSupplyAirHumidityRatio(0.0085)
    sizingSystem.setCentralHeatingDesignSupplyAirHumidityRatio(0.0080)
    sizingSystem.setCoolingDesignAirFlowMethod("DesignDay")
    sizingSystem.setCoolingDesignAirFlowRate(0.0)
    sizingSystem.setHeatingDesignAirFlowMethod("DesignDay")
    sizingSystem.setHeatingDesignAirFlowRate(0.0)
    # sizingSystem.setSystemOutdoorAirMethod("ZoneSum")

    fan = openstudio.model.FanConstantVolume(model)
    fan.setPressureRise(500)

    coilHeatingGas = openstudio.model.CoilHeatingGas(model, alwaysOn)

    coilCooling = openstudio.model.CoilCoolingDXSingleSpeed(model)

    setpointMSZR = openstudio.model.SetpointManagerSingleZoneReheat(model)

    # controllerOutdoorAir = openstudio.model.ControllerOutdoorAir(model)

    # outdoorAirSystem = openstudio.model.AirLoopHVACOutdoorAirSystem(model,controllerOutdoorAir)

    supplyOutletNode = airLoopHVAC.supplyOutletNode()

    # outdoorAirSystem.addToNode(supplyOutletNode)
    fan.addToNode(supplyOutletNode)
    coilCooling.addToNode(supplyOutletNode)
    coilHeatingGas.addToNode(supplyOutletNode)

    # Node node1 = fan.outletModelObject()->cast<Node>();
    # setpointMSZR.addToNode(node1);

    # node1 = fan.outletModelObject().get.to_Node.get
    node1 = coilHeatingGas.outletModelObject().get().to_Node().get()
    setpointMSZR.addToNode(node1)

    if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("2.7.0"):
        terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, alwaysOn)
    else:
        terminal = openstudio.model.AirTerminalSingleDuctUncontrolled(model, alwaysOn)

    airLoopHVAC.addBranchForHVACComponent(terminal)

    # Create AFN components
    fanComponent = fan.getAirflowNetworkFan()
    heatingComponent = coilHeatingGas.getAirflowNetworkEquivalentDuct(0.1, 1.0)
    coolingComponent = coilCooling.getAirflowNetworkEquivalentDuct(0.1, 1.0)
    # And all the ducts
    mainTruck = openstudio.model.AirflowNetworkDuct(model)
    mainTruck.setDuctLength(2)
    mainTruck.setHydraulicDiameter(0.4064)
    mainTruck.setCrossSectionArea(0.1297)
    mainTruck.setSurfaceRoughness(0.0009)
    mainTruck.setCoefficientforLocalDynamicLossDuetoFitting(0.01)
    mainTruck.setDuctWallHeatTransmittanceCoefficient(0.946792)
    mainTruck.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
    mainTruck.setOutsideConvectionCoefficient(5.018)
    mainTruck.setInsideConvectionCoefficient(25.09)

    mainReturn = openstudio.model.AirflowNetworkDuct(model)
    mainReturn.setDuctLength(1)
    mainReturn.setHydraulicDiameter(0.5)
    mainReturn.setCrossSectionArea(0.1963)
    mainReturn.setSurfaceRoughness(0.0009)
    mainReturn.setCoefficientforLocalDynamicLossDuetoFitting(0.01)
    mainReturn.setDuctWallHeatTransmittanceCoefficient(0.001226)
    mainReturn.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
    mainReturn.setOutsideConvectionCoefficient(0.0065)
    mainReturn.setInsideConvectionCoefficient(0.0325)

    airLoopReturn = openstudio.model.AirflowNetworkDuct(model)
    airLoopReturn.setDuctLength(0.1)
    airLoopReturn.setHydraulicDiameter(1)
    airLoopReturn.setCrossSectionArea(0.7854)
    airLoopReturn.setSurfaceRoughness(0.0001)
    airLoopReturn.setCoefficientforLocalDynamicLossDuetoFitting(0)
    airLoopReturn.setDuctWallHeatTransmittanceCoefficient(0.001226)
    airLoopReturn.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
    airLoopReturn.setOutsideConvectionCoefficient(0.0065)
    airLoopReturn.setInsideConvectionCoefficient(0.0325)

    airLoopSupply = openstudio.model.AirflowNetworkDuct(model)
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

    splitter = airLoopHVAC.zoneSplitter()
    mixer = airLoopHVAC.zoneMixer()

    equipmentInletNode = splitter.inletModelObject().get().to_Node().get()

    zoneSupplyRegisterNode = None
    zoneOutletNode = mixer.inletModelObject(0).get().to_Node().get()

    mainReturnNode = mixer.outletModelObject().get().to_Node().get()

    mixerOutletNode = mixer.outletModelObject().get().to_Node().get()
    fanInletNode = fan.inletModelObject().get().to_Node().get()
    fanOutletNode = fan.outletModelObject().get().to_Node().get()
    heatingInletNode = coilHeatingGas.inletModelObject().get().to_Node().get()
    heatingOutletNode = coilHeatingGas.outletModelObject().get().to_Node().get()

    # Now walk around the loop and make the AFN nodes
    equipmentInletNode_AFN = equipmentInletNode.getAirflowNetworkDistributionNode()
    splitterNode_AFN = splitter.getAirflowNetworkDistributionNode()
    zoneSupplyNode_AFN = openstudio.model.AirflowNetworkDistributionNode(model)

    zoneSupplyRegisterNode_AFN = None
    # zoneOutletNode_AFN = zoneOutletNode.getAirflowNetworkDistributionNode

    zoneReturnNode_AFN = openstudio.model.AirflowNetworkDistributionNode(model)
    mixerNode_AFN = mixer.getAirflowNetworkDistributionNode()
    mainReturnNode_AFN = mainReturnNode.getAirflowNetworkDistributionNode()
    fanInletNode_AFN = fanInletNode.getAirflowNetworkDistributionNode()
    fanOutletNode_AFN = fanOutletNode.getAirflowNetworkDistributionNode()
    heatingInletNode_AFN = heatingInletNode.getAirflowNetworkDistributionNode()
    heatingOutletNode_AFN = heatingOutletNode.getAirflowNetworkDistributionNode()

    # Now the links

    mainLink = openstudio.model.AirflowNetworkDistributionLinkage(
        model, equipmentInletNode_AFN, splitterNode_AFN, mainTruck
    )
    # Zone stuff goes in here
    returnMixerLink = openstudio.model.AirflowNetworkDistributionLinkage(
        model, mixerNode_AFN, mainReturnNode_AFN, mainReturn
    )
    systemReturnLink = openstudio.model.AirflowNetworkDistributionLinkage(
        model, mainReturnNode_AFN, fanInletNode_AFN, airLoopReturn
    )
    fanLink = openstudio.model.AirflowNetworkDistributionLinkage(
        model, fanInletNode_AFN, fanOutletNode_AFN, fanComponent
    )
    coolingCoilLink = openstudio.model.AirflowNetworkDistributionLinkage(
        model, fanOutletNode_AFN, heatingInletNode_AFN, coolingComponent
    )
    heatingCoilLink = openstudio.model.AirflowNetworkDistributionLinkage(
        model, heatingInletNode_AFN, heatingOutletNode_AFN, heatingComponent
    )
    equipmentAirLoopLink = openstudio.model.AirflowNetworkDistributionLinkage(
        model, heatingOutletNode_AFN, equipmentInletNode_AFN, airLoopSupply
    )

    return airLoopHVAC


model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry(
    length=17.242, width=10.778, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0
)

# add windows at a 40% window-to-wall ratio
# model.add_windows({"wwr" => 0.4,
#                  "offset" => 1,
#                  "application_type" => "Above Floor"})

# add ASHRAE System type 03, PSZ-AC
# model.add_hvac({"ashrae_sys_num" => '03'})

zone = model.getThermalZones()[0]  # There should only be one...

# hvac = addSystemType3(model)
hvac = addSimpleSystemAFN(model)
hvac = hvac.to_AirLoopHVAC().get()
hvac.addBranchForZone(zone)
outlet_node = hvac.supplyOutletNode()
setpoint_manager = (
    [spm for spm in outlet_node.setpointManagers() if spm.to_SetpointManagerSingleZoneReheat().is_initialized()][0]
    .to_SetpointManagerSingleZoneReheat()
    .get()
)
setpoint_manager.setControlZone(zone)

# add ASHRAE System type 08, VAV w/ PFP Boxes
# DLM: this invokes weird mass conservation rules with VAV
# model.add_hvac({"ashrae_sys_num" => '08'})

# add thermostats
model.add_thermostats(heating_setpoint=22, cooling_setpoint=26.6)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()  # OK, yeah, this is wrong

# remove all infiltration
# model.getSpaceInfiltrationDesignFlowRates.each do |infil|
#  infil.remove
# end

# add design days to the model (Chicago)
model.add_design_days()

# add simulation control
afn_control = model.getAirflowNetworkSimulationControl()
afn_control.setAirflowNetworkControl("MultizoneWithDistribution")

# make an afn zone
afnzone = zone.getAirflowNetworkZone()

# This is kind of lame, regetting stuff we already have above. Need to rethink how this
# is structured at some point.
splitter = hvac.zoneSplitter()
mixer = hvac.zoneMixer()
splitterNode_AFN = splitter.getAirflowNetworkDistributionNode()
mixerNode_AFN = splitter.getAirflowNetworkDistributionNode()

# This is not great either
zoneOutletNode = mixer.inletModelObject(0).get().to_Node().get()

comps = hvac.demandComponents(hvac.demandInletNode(), zone)
zoneInletNode = comps[-2].to_Node().get()

# zoneInletNode = zone.airLoopHVACTerminal.get.to_StraightComponent.get.outletModelObject.get.to_Node.get

zoneInletNode_AFN = zoneInletNode.getAirflowNetworkDistributionNode()
zoneOutletNode_AFN = zoneOutletNode.getAirflowNetworkDistributionNode()

# Make the duct elements
zoneSupply = openstudio.model.AirflowNetworkDuct(model)
zoneSupply.setDuctLength(10)
zoneSupply.setHydraulicDiameter(0.4064)
zoneSupply.setCrossSectionArea(0.1297)
zoneSupply.setSurfaceRoughness(0.0009)
zoneSupply.setCoefficientforLocalDynamicLossDuetoFitting(0.91)
zoneSupply.setDuctWallHeatTransmittanceCoefficient(0.946792)
zoneSupply.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
zoneSupply.setOutsideConvectionCoefficient(5.018)
zoneSupply.setInsideConvectionCoefficient(25.09)

zoneReturn = openstudio.model.AirflowNetworkDuct(model)
zoneReturn.setDuctLength(3)
zoneReturn.setHydraulicDiameter(0.5)
zoneReturn.setCrossSectionArea(0.1963)
zoneReturn.setSurfaceRoughness(0.0009)
zoneReturn.setCoefficientforLocalDynamicLossDuetoFitting(0.01)
zoneReturn.setDuctWallHeatTransmittanceCoefficient(0.001226)
zoneReturn.setOverallMoistureTransmittanceCoefficientfromAirtoAir(0.0000001)
zoneReturn.setOutsideConvectionCoefficient(0.0065)
zoneReturn.setInsideConvectionCoefficient(0.0325)

zoneConnectionDuct = openstudio.model.AirflowNetworkDuct(model)
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
zoneSupplyLink = openstudio.model.AirflowNetworkDistributionLinkage(
    model, splitterNode_AFN, zoneInletNode_AFN, zoneSupply
)
zoneSupplyConnectionLink = openstudio.model.AirflowNetworkDistributionLinkage(
    model, zoneInletNode_AFN, afnzone, zoneConnectionDuct
)
zoneReturnConnectionLink = openstudio.model.AirflowNetworkDistributionLinkage(
    model, afnzone, zoneOutletNode_AFN, zoneConnectionDuct
)
zoneSupplyLink = openstudio.model.AirflowNetworkDistributionLinkage(
    model, zoneOutletNode_AFN, mixerNode_AFN, zoneReturn
)

# Connect up envelope
visitor = SurfaceNetworkBuilder(model)

# add output reports
add_out_vars = False
if add_out_vars:
    openstudio.model.OutputVariable("AFN Node Temperature", model)
    openstudio.model.OutputVariable("AFN Node Wind Pressure", model)
    openstudio.model.OutputVariable("AFN Linkage Node 1 to Node 2 Mass Flow Rate", model)
    openstudio.model.OutputVariable("AFN Linkage Node 1 to Node 2 Pressure Difference", model)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
