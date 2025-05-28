import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=3, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# Add ASHRAE System type 07, VAV w/ Reheat, this creates a ChW, a HW loop and a
# Condenser Loop
model.add_hvac(ashrae_sys_num="07")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# In order to produce more consistent results between different runs,
# We ensure we do get the same object each time
cts = sorted(model.getCoolingTowerSingleSpeeds(), key=lambda c: c.nameString())
chillers = sorted(model.getChillerElectricEIRs(), key=lambda c: c.nameString())
boilers = sorted(model.getBoilerHotWaters(), key=lambda c: c.nameString())

condenser_loop = cts[0].plantLoop().get()
cooling_loop = chillers[0].plantLoop().get()
heating_loop = boilers[0].plantLoop().get()

# Create a central heat pump system and two modules
central_hp = openstudio.model.CentralHeatPumpSystem(model)
central_hp.setName("CentralHeatPumpSystem")

central_hp_module = openstudio.model.CentralHeatPumpSystemModule(model)
central_hp.addModule(central_hp_module)

central_hp_module2 = openstudio.model.CentralHeatPumpSystemModule(model)
central_hp.addModule(central_hp_module2)
central_hp_module2.setNumberofChillerHeaterModules(2)

# Add to to the demand side of the condenser loop
condenser_loop.addDemandBranchForComponent(central_hp)

# Supply side of the chw loop, remove chiller
[x.remove() for x in chillers]
cooling_loop.addSupplyBranchForComponent(central_hp)

# Supply side to HW loop: tertiary. Remove boiler
# Since we need to use addToTertiaryNode,
# The trick is to add it to the boiler inlet node first, then remove boiler
# n = b.inletModelObject.get.to_Node.get
# central_hp.addToTertiaryNode(n)
# b.remove
#
# This is not true anymore, this will work and add to tertiary node
# because we have already connected the central_hp to the supply side of the
# cooling loop, it knows it's trying to connect the tertiary loop
heating_loop.addSupplyBranchForComponent(central_hp)
[x.remove() for x in boilers]

###############################################################################
#         R E N A M E    E Q U I P M E N T    A N D    N O D E S
###############################################################################
# Remove pipes
[x.remove() for x in model.getPipeAdiabatics()]

# Rename loops
condenser_loop.setName("CndW Loop")
heating_loop.setName("HW Loop")
cooling_loop.setName("ChW Loop")

# There is is only one
model.getCoilCoolingWaters()[0].setName("VAV Central ChW Coil")

for coil in model.getCoilHeatingWaters():
    if not coil.airLoopHVAC().is_initialized():
        continue

    coil.setName("VAV Central HW Coil")


a = sorted(model.getAirLoopHVACs(), key=lambda c: c.nameString())[0]
for z in a.thermalZones():
    atu = z.equipment()[0].to_AirTerminalSingleDuctVAVReheat().get()
    atu.setName("#{z.name()} ATU VAV Reheat")
    atu.reheatCoil().setName("#{z.name()} ATU Reheat HW Coil")


# Rename nodes
model.rename_air_nodes()
model.rename_loop_nodes()

# central hp has a tertiary loop, so need to do it manually

# Supply = cooling
central_hp.supplyInletModelObject().get().setName(
    "#{central_hp.coolingPlantLoop().get().name()} Supply Side #{central_hp.name()} Inlet Node"
)
central_hp.supplyOutletModelObject().get().setName(
    "#{central_hp.coolingPlantLoop().get().name()} Supply Side #{central_hp.name()} Outlet Node"
)

# Demand = Source (Condenser)
central_hp.demandInletModelObject().get().setName(
    "#{central_hp.sourcePlantLoop().get().name()} Demand Side #{central_hp.name()} Inlet Node"
)
central_hp.demandOutletModelObject().get().setName(
    "#{central_hp.sourcePlantLoop().get().name()} Demand Side #{central_hp.name()} Outlet Node"
)

# tertiary = heating
central_hp.tertiaryInletModelObject().get().setName(
    "#{central_hp.heatingPlantLoop().get().name()} Supply Side #{central_hp.name()} Inlet Node"
)
central_hp.tertiaryOutletModelObject().get().setName(
    "#{central_hp.heatingPlantLoop().get().name()} Supply Side #{central_hp.name()} Outlet Node"
)

# Rename Zone Air Nodes
for z in model.getThermalZones():
    z.zoneAirNode().setName("#{z.name()} Zone Air Node")

# Rename thermostats
for t in model.getThermostatSetpointDualSetpoints():
    t.setName("#{t.thermalZone().get().name()} ThermostatSetpointDualSetpoint")

# Rename ATU "Air Outlet Node Name", not sure how
nodes = [n for n in model.getNodes() if n.nameString().startswith("Node ")]
for n in nodes:
    if n.inletModelObject().empty():
        continue

    atu = n.inletModelObject().get().to_AirTerminalSingleDuctVAVReheat()
    if atu.is_initialized():
        atu = atu.get()
        n.setName("#{atu.name()} Air Outlet Node")

    zone = n.inletModelObject().get().to_ThermalZone()
    if zone.is_initialized():
        zone = zone.get()
        n.setName("#{zone.name()} Return Air Node")

    if n.outletModelObject().empty():
        continue

    atu = n.outletModelObject().get().to_AirTerminalSingleDuctVAVReheat()
    if atu.is_initialized():
        atu = atu.get()
        n.setName("#{atu.name()} Air Inlet Node")


for fan in model.getFanVariableVolumes():
    fan.inletModelObject().get().to_Node().get().setName("#{fan.name()} Inlet Node")
    fan.outletModelObject().get().to_Node().get().setName("#{fan.name()} Outlet Node")


########################### Request output variables ##########################

add_out_vars = False
if add_out_vars:
    freq = "Detailed"

    # CentralHeatPumpSystem outputs, implemented in the class
    for varname in central_hp.outputVariableNames():
        outvar = openstudio.model.OutputVariable(varname, model)
        outvar.setReportingFrequency(freq)

    # ChillerHeaterPerformance:Electric:EIR Outputs: one for each Unit, not
    # implemented in class (can't be static really...)
    n_chiller_heater = sum([mod.numberofChillerHeaterModules() for mod in central_hp.modules()])

    chiller_heater_perf_vars = [
        "Chiller Heater Operation Mode Unit",
        "Chiller Heater Part Load Ratio Unit",
        "Chiller Heater Cycling Ratio Unit",
        "Chiller Heater Cooling Electric Power Unit",
        "Chiller Heater Heating Electric Power Unit",
        "Chiller Heater Cooling Electric Energy Unit",
        "Chiller Heater Heating Electric Energy Unit",
        "Chiller Heater Cooling Rate Unit",
        "Chiller Heater Cooling Energy Unit",
        "Chiller Heater False Load Heat Transfer Rate Unit",
        "Chiller Heater False Load Heat Transfer Energy Unit",
        "Chiller Heater Evaporator Inlet Temperature Unit",
        "Chiller Heater Evaporator Outlet Temperature Unit",
        "Chiller Heater Evaporator Mass Flow Rate Unit",
        "Chiller Heater Condenser Heat Transfer Rate Unit",
        "Chiller Heater Condenser Heat Transfer Energy Unit",
        "Chiller Heater COP Unit",
        "Chiller Heater Capacity Temperature Modifier Multiplier Unit",
        "Chiller Heater EIR Temperature Modifier Multiplier Unit",
        "Chiller Heater EIR Part Load Modifier Multiplier Unit",
        "Chiller Heater Condenser Inlet Temperature Unit",
        "Chiller Heater Condenser Outlet Temperature Unit",
        "Chiller Heater Condenser Mass Flow Rate Unit",
    ]

    for i in range(n_chiller_heater):
        for varname in chiller_heater_perf_vars:
            outvar = openstudio.model.OutputVariable("#{varname} #{i + 1}", model)
            outvar.setReportingFrequency(freq)


# Due to this bug: https://github.com/NREL/energyplus/issues/6445
# Need to hardsize the Reference capacity of the
# chillerHeaterPerformanceElectricEIR objects
for comp in model.getChillerHeaterPerformanceElectricEIRs():
    comp.setReferenceCoolingModeEvaporatorCapacity(600000)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
