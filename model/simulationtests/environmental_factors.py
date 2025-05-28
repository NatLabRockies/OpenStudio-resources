# This test aims to test the new 'Adiabatic Surface Construction Name' field
# added in the OS:DefaultConstructionSet

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

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

# OutputEnvironmentalImpactFactors is the one object that will trigger the
# ForwardTranslation of EnvironmentalImpactFactors and FuelFactors
# If you do, then you **must** supply FuelFactors for **each** fuel you do use
# in your model.
# At least one FuelFactors is required for the ForwardTranslation
# (you always have at least one fuel... Electricity probably for the lights, etc).

output_env_factors = openstudio.model.OutputEnvironmentalImpactFactors(model)
output_env_factors.setReportingFrequency("Monthly")

# This one is a UniquemodelObject
env_factors = model.getEnvironmentalImpactFactors()
# Defaults from E+ IDD, captured at v9.5.0
env_factors.setDistrictHeatingEfficiency(0.3)
env_factors.setDistrictCoolingCOP(3.0)
env_factors.setSteamConversionEfficiency(0.25)
env_factors.setTotalCarbonEquivalentEmissionFactorFromN2O(80.7272)
env_factors.setTotalCarbonEquivalentEmissionFactorFromCH4(6.2727)
env_factors.setTotalCarbonEquivalentEmissionFactorFromCO2(0.2727)

fuelFactors = openstudio.model.FuelFactors(model)
# From ElectricityUSAEnvironmentalImpactFactors.idf,
# United States 1999 national average electricity emissions factors based on eGRID, 1605, AirData
alwaysOn = model.alwaysOnContinuousSchedule()
fuelFactors.setExistingFuelResourceName("Electricity")
fuelFactors.setSourceEnergyFactor(2.253)

fuelFactors.setCO2EmissionFactor(168.33317)
fuelFactors.setCO2EmissionFactorSchedule(alwaysOn)

fuelFactors.setCOEmissionFactor(4.20616e-02)
fuelFactors.setCOEmissionFactorSchedule(alwaysOn)

fuelFactors.setCH4EmissionFactor(1.39858e-03)
fuelFactors.setCH4EmissionFactorSchedule(alwaysOn)

fuelFactors.setNOxEmissionFactor(4.10753e-01)
fuelFactors.setNOxEmissionFactorSchedule(alwaysOn)

fuelFactors.setN2OEmissionFactor(2.41916e-03)
fuelFactors.setN2OEmissionFactorSchedule(alwaysOn)

fuelFactors.setSO2EmissionFactor(8.65731e-01)
fuelFactors.setSO2EmissionFactorSchedule(alwaysOn)

fuelFactors.setPMEmissionFactor(2.95827e-02)
fuelFactors.setPMEmissionFactorSchedule(alwaysOn)

fuelFactors.setPM10EmissionFactor(1.80450e-02)
fuelFactors.setPM10EmissionFactorSchedule(alwaysOn)

fuelFactors.setPM25EmissionFactor(1.15377e-02)
fuelFactors.setPM25EmissionFactorSchedule(alwaysOn)

fuelFactors.setNH3EmissionFactor(1.10837e-03)
fuelFactors.setNH3EmissionFactorSchedule(alwaysOn)

fuelFactors.setNMVOCEmissionFactor(3.72332e-03)
fuelFactors.setNMVOCEmissionFactorSchedule(alwaysOn)

fuelFactors.setHgEmissionFactor(3.36414e-06)
fuelFactors.setHgEmissionFactorSchedule(alwaysOn)

fuelFactors.setPbEmissionFactor(0.0)
fuelFactors.setPbEmissionFactorSchedule(alwaysOn)

fuelFactors.setWaterEmissionFactor(2.10074)
fuelFactors.setWaterEmissionFactorSchedule(alwaysOn)

fuelFactors.setNuclearHighLevelEmissionFactor(0.0)
fuelFactors.setNuclearHighLevelEmissionFactorSchedule(alwaysOn)

fuelFactors.setNuclearLowLevelEmissionFactor(0.0)
fuelFactors.setNuclearLowLevelEmissionFactorSchedule(alwaysOn)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
