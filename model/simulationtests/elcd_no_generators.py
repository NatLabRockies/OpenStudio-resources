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

# In order to produce more consistent results between different runs,
# we sort the zones by names
# (There's only one here, but just in case this would be copy pasted somewhere
# else...)
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())
z = zones[0]

# create the distribution system
elcd = openstudio.model.ElectricLoadCenterDistribution(model)

# We set the bussType to DirectCurrentWithInverterDCStorage meaning we need
# an inverter, a storage converter, and a storage object
elcd.setElectricalBussType("DirectCurrentWithInverterDCStorage")

# create the inverter
inverter = openstudio.model.ElectricLoadCenterInverterLookUpTable(model)
inverter.setName("Default Eplus PV Inverter LookUpTable")
inverter.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule())
# inverter.setThermalZone
inverter.setRadiativeFraction(0.25)
inverter.setRatedMaximumContinuousOutputPower(14000)
inverter.setNightTareLossPower(200)
inverter.setNominalVoltageInput(368)
inverter.setEfficiencyAt10PowerAndNominalVoltage(0.839)
inverter.setEfficiencyAt20PowerAndNominalVoltage(0.897)
inverter.setEfficiencyAt30PowerAndNominalVoltage(0.916)
inverter.setEfficiencyAt50PowerAndNominalVoltage(0.931)
inverter.setEfficiencyAt75PowerAndNominalVoltage(0.934)
inverter.setEfficiencyAt100PowerAndNominalVoltage(0.93)

elcd.setInverter(inverter)

# We need a storage object (Battery or Simple)
# We will model a 200 kWh battery with 100 kW charge/discharge power
storage = openstudio.model.ElectricLoadCenterStorageSimple(model)

z.setName("#{z.name()} With Battery")
storage.setThermalZone(z)
# Showcase its attribute setters
storage.setRadiativeFractionforZoneHeatGains(0.1)
storage.setMaximumStorageCapacity(openstudio.convert(200, "kWh", "J").get())
storage.setMaximumPowerforDischarging(100000)
storage.setMaximumPowerforCharging(100000)
storage.setNominalEnergeticEfficiencyforCharging(0.8)
storage.setNominalDischargingEnergeticEfficiency(0.8)
storage.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule())
# Start at half charge
storage.setInitialStateofCharge(storage.maximumStorageCapacity() / 2.0)

# Add it to the ELCD
elcd.setElectricalStorage(storage)

# We need a storage converter
storage_conv = openstudio.model.ElectricLoadCenterStorageConverter(model)
storage_conv.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule())
storage_conv.setSimpleFixedEfficiency(0.95)
# 20 W of standby
storage_conv.setAncillaryPowerConsumedInStandby(20)
storage_conv.setThermalZone(z)
storage_conv.setRadiativeFraction(0.25)
# We used SimpleFixedEfficiency, so neither of these fields are used:
# storage_conv.setDesignMaximumContinuousInputPower
# storage_conv.setEfficiencyFunctionofPowerCurve

# Add it to the ELCD
elcd.setStorageConverter(storage_conv)

# Some parameters for the battery are set on the ELCD, including the min/max
# State of Charge (SoC). In our case we assume the SoC is bound by 0.04 / 0.96
# Meaning the lowest the battery can store is 0.04*200=0.8 kWh,
# max is 0.96*200=192 kWh and the total usable energy is 184 kWh
elcd.setMinimumStorageStateofChargeFraction(0.04)
elcd.setMaximumStorageStateofChargeFraction(0.96)
elcd.setDesignStorageControlChargePower(100000)
elcd.setDesignStorageControlDischargePower(100000)

# Try to level demand to 250 kW (peak was 326 kW with PV and no storage)
# Note: there was a bug prior to 2.4.2 that will make this fail on older
elcd.setStorageOperationScheme("FacilityDemandLeveling")
elcd.setStorageControlUtilityDemandTarget(250000)

# I had also added a convenience method called validityCheck because this
# object has many fields that depend on values selected for \choices fields
# Eg: if I had not set 'AlternatingCurrent' for buss type, the default is
# 'DirectCurrentWithInverter', elcd.validityCheck would return false and print
# a message saying the buss type requires and inverter while I didn't set one
if not elcd.validityCheck():
    raise "Electric Load Center is not valid"


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
