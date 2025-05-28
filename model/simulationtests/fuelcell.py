import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 03, PSZ-AC
model.add_hvac(ashrae_sys_num="03")

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# add electric load center distribution
eld = openstudio.model.ElectricLoadCenterDistribution(model)

# add fuel cell
fuelcell = openstudio.model.GeneratorFuelCell(model)
fuelcell.powerModule().setZone(zones[0])

# Set the fuel supply that was automatically created to the same as the
# 9.0.0 ExampleFile 'Microcogeneration.idf' in order to avoid problem
# with 'LiquidGeneric' (https://github.com/NREL/energyplus/issues/6998)
# Starting in OpenStudio 2.7.0, this is done by default, but for backwards
# compatibility, and demonstration of the API, we explicitly set it
fs = fuelcell.fuelSupply()
fs.setName("NATURALGAS")
fs.resetLiquidGenericFuelLowerHeatingValue()
fs.resetLiquidGenericFuelHigherHeatingValue()
fs.resetLiquidGenericFuelMolecularWeight()
fs.resetLiquidGenericFuelCO2EmissionFactor()
fs.removeAllConstituents()
fs.setFuelType("GaseousConstituents")
fs.addConstituent("METHANE", 0.9490)
fs.addConstituent("CarbonDioxide", 0.0070)
fs.addConstituent("NITROGEN", 0.0160)
fs.addConstituent("ETHANE", 0.0250)
fs.addConstituent("PROPANE", 0.0020)
fs.addConstituent("BUTANE", 0.0006)
fs.addConstituent("PENTANE", 0.0002)
fs.addConstituent("OXYGEN", 0.0002)

# add fuel cell to electric load center distribution
eld.addGenerator(fuelcell)
eld.setGeneratorOperationSchemeType("Baseload")
eld.setElectricalBussType("AlternatingCurrent")

# get fuel cell heat exchanger
fuelcell_hx = fuelcell.heatExchanger()

# hot water system
plant = openstudio.model.PlantLoop(model)
pump = openstudio.model.PumpConstantSpeed(model)
pump.addToNode(plant.supplyInletNode())
hot_water_heater = openstudio.model.WaterHeaterMixed(model)
# tempering_valve = openstudio.model.TemperingValve(model)
plant.addSupplyBranchForComponent(hot_water_heater)
# plant.addSupplyBranchForComponent(tempering_valve)
plant.addSupplyBranchForComponent(fuelcell_hx)

hot_water_temp_sch = openstudio.model.ScheduleRuleset(model)
hot_water_temp_sch.setName("Hot_Water_Temperature")
hot_water_temp_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 55.0)
hot_water_spm = openstudio.model.SetpointManagerScheduled(model, hot_water_temp_sch)
hot_water_spm.addToNode(plant.supplyOutletNode())

water_connections = openstudio.model.WaterUseConnections(model)
plant.addDemandBranchForComponent(water_connections)
water_def = openstudio.model.WaterUseEquipmentDefinition(model)
water_equipment = openstudio.model.WaterUseEquipment(water_def)
water_connections.addWaterUseEquipment(water_equipment)

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
