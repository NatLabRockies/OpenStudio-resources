import json

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

model.add_standards(
    json.loads(
        """{
  "schedules": [
    {
        "name": "Medium Office Bldg Swh",
        "category": "Service Water Heating",
        "units": null,
        "day_types": "Default|SmrDsn",
        "start_date": "2014-01-01T00:00:00+00:00",
        "end_date": "2014-12-31T00:00:00+00:00",
        "type": "Hourly",
        "notes": "From DOE Reference Buildings ",
        "values": [
          0.05, 0.05, 0.05, 0.05, 0.05, 0.08, 0.07, 0.19, 0.35, 0.38, 0.39, 0.47, 0.57, 0.54, 0.34, 0.33, 0.44, 0.26, 0.21, 0.15, 0.17, 0.08, 0.05, 0.05
        ]
      },
      {
        "name": "Medium Office Bldg Swh",
        "category": "Service Water Heating",
        "units": null,
        "day_types": "Sun",
        "start_date": "2014-01-01T00:00:00+00:00",
        "end_date": "2014-12-31T00:00:00+00:00",
        "type": "Hourly",
        "notes": "From DOE Reference Buildings ",
        "values": [
          0.04, 0.04, 0.04, 0.04, 0.04, 0.07, 0.04, 0.04, 0.04, 0.04, 0.04, 0.06, 0.06, 0.09, 0.06, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.07, 0.04, 0.04
        ]
      },
      {
        "name": "Medium Office Bldg Swh",
        "category": "Service Water Heating",
        "units": null,
        "day_types": "WntrDsn|Sat",
        "start_date": "2014-01-01T00:00:00+00:00",
        "end_date": "2014-12-31T00:00:00+00:00",
        "type": "Hourly",
        "notes": "From DOE Reference Buildings ",
        "values": [
          0.05, 0.05, 0.05, 0.05, 0.05, 0.08, 0.07, 0.11, 0.15, 0.21, 0.19, 0.23, 0.2, 0.19, 0.15, 0.13, 0.14, 0.07, 0.07, 0.07, 0.07, 0.09, 0.05, 0.05
        ]
      }
    ]
  }"""
    )
)

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 01, PTAC, Residential
model.add_hvac(ashrae_sys_num="01")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

###############################################################################

# Switches you can use to compare with pv and storage
add_pv = True
add_storage = True
# Add output variables?
add_out_vars = False

# Need the PV section because we use a storage converter...
# there isn't a buss type with DC buss and no inverter...
if add_storage and not add_pv:
    add_pv = True

###############################################################################

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

if add_pv:

    # make a shading surface. I chose 90 m2 because I use 0.85 fraction covered
    # with active solar cells and a fixed eff of 18% and I aim to be at around
    # 14 kWhp (90 * 0.85 * 0.18 = 13.77 kWp)
    vertices = openstudio.Point3dVector()
    vertices.append(openstudio.Point3d(0, 0, 0))
    vertices.append(openstudio.Point3d(10, 0, 0))
    vertices.append(openstudio.Point3d(10, 9, 0))
    vertices.append(openstudio.Point3d(0, 9, 0))
    rotation = openstudio.createRotation(openstudio.Vector3d(1, 0, 0), openstudio.degToRad(30))
    vertices = rotation * vertices

    group = openstudio.model.ShadingSurfaceGroup(model)
    group.setXOrigin(20)
    group.setYOrigin(10)
    group.setZOrigin(8)

    shade = openstudio.model.ShadingSurface(vertices, model)
    shade.setShadingSurfaceGroup(group)

    # create the panel
    panel = openstudio.model.GeneratorPhotovoltaic.simple(model)
    panel.setSurface(shade)

    # Modify the OS:PhotovoltaicPerformance:Simple
    perf = panel.photovoltaicPerformance().to_PhotovoltaicPerformanceSimple().get()
    perf.setFractionOfSurfaceAreaWithActiveSolarCells(0.85)
    perf.setFixedEfficiency(0.18)
    # Instead of a fixed efficiency, can use a schedule: perf.setEfficiencySchedule
    # kWp of system
    # shade.netArea * perf.fractionOfSurfaceAreaWithActiveSolarCells * perf.fixedEfficiency.get
    # Very rough estimate of kWh produced by panel, based on annual irradiance of 1250 W/m^2
    # shade.netArea * perf.fractionOfSurfaceAreaWithActiveSolarCells * perf.fixedEfficiency.get * 1250

    # create the inverter
    # inverter = openstudio.model.ElectricLoadCenterInverterSimple(model)
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

    # create the distribution system
    elcd = openstudio.model.ElectricLoadCenterDistribution(model)
    elcd.addGenerator(panel)
    elcd.setInverter(inverter)

    # Baseload is the most appropriate for PV: always use if available
    elcd.setGeneratorOperationSchemeType("Baseload")

    if add_storage:
        # We set the bussType to DirectCurrentWithInverterDCStorage meaning we need
        # an inverter, a storage converter, and a storage object
        elcd.setElectricalBussType("DirectCurrentWithInverterDCStorage")
    else:
        elcd.setElectricalBussType("DirectCurrentWithInverter")

    if add_out_vars:
        # output variables
        for var in panel.outputVariableNames():
            openstudio.model.OutputVariable(var, model)

        for var in inverter.outputVariableNames():
            openstudio.model.OutputVariable(var, model)

        for var in elcd.outputVariableNames():
            openstudio.model.OutputVariable(var, model)


# We get a zone (sort by name to ensure consistency)
z = zones[0]

if add_storage:
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

    # This scheme should work in older versions
    elcd.setStorageOperationScheme("TrackFacilityElectricDemandStoreExcessOnSite")

    # I had also added a convenience method called validityCheck because this
    # object has many fields that depend on values selected for \choices fields
    # Eg: if I had not set 'AlternatingCurrent' for buss type, the default is
    # 'DirectCurrentWithInverter', elcd.validityCheck would return false and print
    # a message saying the buss type requires and inverter while I didn't set one
    if not elcd.validityCheck():
        raise "Electric Load Center is not valid"

    if add_out_vars:
        # output variables
        for var in storage.outputVariableNames():
            openstudio.model.OutputVariable(var, model)

        for var in storage_conv.outputVariableNames():
            openstudio.model.OutputVariable(var, model)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
