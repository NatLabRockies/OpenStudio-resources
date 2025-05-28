import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 2 zone building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=19, cooling_setpoint=26)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())
for i, zone in enumerate(zones):
    # create the distribution system
    elcd = openstudio.model.ElectricLoadCenterDistribution(model)
    elcd.setElectricalBussType("DirectCurrentWithInverterDCStorage")

    # create a generator
    generator = openstudio.model.GeneratorPhotovoltaic.simple(model)

    # create the inverter
    inverter = openstudio.model.ElectricLoadCenterInverterLookUpTable(model)

    nSeries = 139
    nParallel = 25
    mass = 342.0
    surfaceArea = 4.26
    if i == 0:
        # create the storage using ctor 1
        storage = openstudio.model.ElectricLoadCenterStorageLiIonNMCBattery(
            model, nSeries, nParallel, mass, surfaceArea
        )
    else:
        # create the storage using ctor 2
        storage = openstudio.model.ElectricLoadCenterStorageLiIonNMCBattery(model)
        storage.setNumberofCellsinSeries(nSeries)
        storage.setNumberofStringsinParallel(nParallel)
        storage.setBatteryMass(mass)
        storage.setBatterySurfaceArea(surfaceArea)

    storage.setThermalZone(zone)
    storage.setRadiativeFraction(0)
    storage.setLifetimeModel("KandlerSmith")
    storage.setInitialFractionalStateofCharge(0.7)
    storage.setDCtoDCChargingEfficiency(0.95)
    storage.setBatterySpecificHeatCapacity(1500)
    storage.setHeatTransferCoefficientBetweenBatteryandAmbient(7.5)
    storage.setFullyChargedCellVoltage(4.2)
    storage.setCellVoltageatEndofExponentialZone(3.53)
    storage.setCellVoltageatEndofNominalZone(3.342)
    storage.setDefaultNominalCellVoltage(3.342)
    storage.setFullyChargedCellCapacity(3.2)
    storage.setFractionofCellCapacityRemovedattheEndofExponentialZone(0.8075)
    storage.setFractionofCellCapacityRemovedattheEndofNominalZone(0.976875)
    storage.setChargeRateatWhichVoltagevsCapacityCurveWasGenerated(1)
    storage.setBatteryCellInternalElectricalResistance(0.09)

    # Add them to the ELCD
    elcd.addGenerator(generator)
    elcd.setInverter(inverter)
    elcd.setElectricalStorage(storage)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
