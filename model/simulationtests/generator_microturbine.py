import json

import openstudio

from lib.baseline_model import BaselineModel


# Helper function to create a captsone with heat recovery
# Author: Julien Marrec
# Will create a Capstone C65 and return the mchp, mchpHR
def add_generator_mt_capstone65(model):
    # Generator:MicroTurbine,
    mchp = openstudio.model.GeneratorMicroTurbine(model)

    #    Capstone C65,            !- Name
    mchp.setName("Capstone C65")

    # And it has heat recovery
    mchpHR = openstudio.model.GeneratorMicroTurbineHeatRecovery(model, mchp)

    # Set the Rated Thermal To Electrical
    mchpHR.setRatedThermaltoElectricalPowerRatio(1.72)

    #    65000,                   !- Reference Electrical Power Output {W}
    mchp.setReferenceElectricalPowerOutput(65000)

    #    29900,                   !- Minimum Full Load Electrical Power Output {W}
    mchp.setMinimumFullLoadElectricalPowerOutput(29900)

    #    65000,                   !- Maximum Full Load Electrical Power Output {W}
    mchp.setMaximumFullLoadElectricalPowerOutput(65000)

    #    0.29,                    !- Reference Electrical Efficiency Using Lower Heating Value
    mchp.setReferenceElectricalEfficiencyUsingLowerHeatingValue(0.29)

    #    15.0,                    !- Reference Combustion Air Inlet Temperature {C}
    mchp.setReferenceCombustionAirInletTemperature(15.0)

    #    0.00638,                 !- Reference Combustion Air Inlet Humidity Ratio {kgWater/kgDryAir}
    mchp.setReferenceCombustionAirInletHumidityRatio(0.00638)

    #    0.0,                     !- Reference Elevation {m}
    # mchp.setReferenceElevation(0)

    #    Capstone C65 Power_vs_Temp_Elev,  !- Electrical Power Function of Temperature and Elevation Curve Name
    curve = mchp.electricalPowerFunctionofTemperatureandElevationCurve()
    curve = curve.to_CurveBiquadratic().get()
    # curve = openstudio.model.CurveBiquadratic(model)
    curve.setName("Capstone C65 Power_vs_Temp_Elev")
    curve.setCoefficient1Constant(1.2027697)
    curve.setCoefficient2x(-0.009671305)
    curve.setCoefficient3xPOW2(-0.000004860793)
    curve.setCoefficient4y(-0.0001542394)
    curve.setCoefficient5yPOW2(0.000000009111418)
    curve.setCoefficient6xTIMESY(0.0000008797885)  # Why is the Y upcase here?
    curve.setMinimumValueofx(-17.8)
    curve.setMaximumValueofx(50)
    curve.setMinimumValueofy(0)
    curve.setMaximumValueofy(3050)
    mchp.setElectricalPowerFunctionofTemperatureandElevationCurve(curve)

    #    Capstone C65 Efficiency_vs_Temp,  !- Electrical Efficiency Function of Temperature Curve Name
    curve = mchp.electricalEfficiencyFunctionofTemperatureCurve()
    curve = curve.to_CurveCubic().get()
    # curve = openstudio.model.CurveCubic(model)
    curve.setName("Capstone C65 Efficiency_vs_Temp")
    curve.setCoefficient1Constant(1.0402217)
    curve.setCoefficient2x(-0.0017314)
    curve.setCoefficient3xPOW2(-0.0000649704)
    curve.setCoefficient4xPOW3(0.0000005133175)
    curve.setMinimumValueofx(-20)
    curve.setMaximumValueofx(50)
    mchp.setElectricalEfficiencyFunctionofTemperatureCurve(curve)

    #    Capstone C65 Efficiency_vs_PLR,  !- Electrical Efficiency Function of Part Load Ratio Curve Name
    curve = mchp.electricalEfficiencyFunctionofPartLoadRatioCurve()
    curve = curve.to_CurveCubic().get()
    # curve = openstudio.model.CurveCubic(model)
    curve.setName("Capstone C65 Efficiency_vs_PLR")
    curve.setCoefficient1Constant(0.21529)
    curve.setCoefficient2x(2.561463)
    curve.setCoefficient3xPOW2(-3.24613)
    curve.setCoefficient4xPOW3(1.497306)
    curve.setMinimumValueofx(0.03)
    curve.setMaximumValueofx(1)
    mchp.setElectricalEfficiencyFunctionofPartLoadRatioCurve(curve)

    #    NaturalGas,              !- Fuel Type
    mchp.setFuelType("NaturalGas")

    #    50000,                   !- Fuel Higher Heating Value {kJ/kg}
    mchp.setFuelHigherHeatingValue(50000)

    #    45450,                   !- Fuel Lower Heating Value {kJ/kg}
    mchp.setFuelLowerHeatingValue(45450)

    #    300,                     !- Standby Power {W}
    mchp.setStandbyPower(300)

    #    4500,                    !- Ancillary Power {W}
    mchp.setAncillaryPower(4500)
    #    ,                        !- Ancillary Power Function of Fuel Input Curve Name
    #    Capstone C65 Heat Recovery Water Inlet Node,  !- Heat Recovery Water Inlet Node Name
    #    Capstone C65 Heat Recovery Water Outlet Node,  !- Heat Recovery Water Outlet Node Name

    #    0.4975,                  !- Reference Thermal Efficiency Using Lower Heat Value
    mchpHR.setReferenceThermalEfficiencyUsingLowerHeatValue(0.4975)

    #    60.0,                    !- Reference Inlet Water Temperature {C}
    mchpHR.setReferenceInletWaterTemperature(60)

    #    PlantControl,            !- Heat Recovery Water Flow Operating Mode
    mchpHR.setHeatRecoveryWaterFlowOperatingMode("PlantControl")

    #    0.00252362,              !- Reference Heat Recovery Water Flow Rate {m3/s}
    #    = 40 GPM
    mchpHR.setReferenceHeatRecoveryWaterFlowRate(0.00252362)

    #    ,                        !- Heat Recovery Water Flow Rate Function of Temperature and Power Curve Name
    # mchpHR.setHeatRecoveryWaterFlowRateFunctionofTemperatureandPowerCurve()

    #    Capstone C65 ThermalEff_vs_Temp_Elev,  !- Thermal Efficiency Function of Temperature and Elevation Curve Name
    curve = openstudio.model.CurveBicubic(model)
    curve.setName("Capstone C65 ThermalEff_vs_Temp_Elev")
    curve.setCoefficient1Constant(0.93553794)
    curve.setCoefficient2x(0.00541992)
    curve.setCoefficient3xPOW2(-0.000078902)
    curve.setCoefficient4y(-0.0000174338)
    curve.setCoefficient5yPOW2(-0.0000000251197)
    curve.setCoefficient6xTIMESY(-0.00000450373)
    curve.setCoefficient7xPOW3(0.00000149283)
    curve.setCoefficient8yPOW3(2.16866e-12)
    curve.setCoefficient9xPOW2TIMESY(0.0000000193982)
    curve.setCoefficient10xTIMESYPOW2(0.000000000673429)
    curve.setMinimumValueofx(-17.8)
    curve.setMaximumValueofx(48.9)
    curve.setMinimumValueofy(0)
    curve.setMaximumValueofy(3048)
    mchpHR.setThermalEfficiencyFunctionofTemperatureandElevationCurve(curve)

    #    Capstone C65 HeatRecoveryRate_vs_PLR,  !- Heat Recovery Rate Function of Part Load Ratio Curve Name
    curve = openstudio.model.CurveQuadratic(model)
    curve.setName("Capstone C65 HeatRecoveryRate_vs_PLR")
    curve.setCoefficient1Constant(0)
    curve.setCoefficient2x(1)
    curve.setCoefficient3xPOW2(0)
    curve.setMinimumValueofx(0.03)
    curve.setMaximumValueofx(1)
    mchpHR.setHeatRecoveryRateFunctionofPartLoadRatioCurve(curve)

    #    Capstone C65 HeatRecoveryRate_vs_InletTemp,  !- Heat Recovery Rate Function of Inlet Water Temperature Curve Name
    curve = openstudio.model.CurveQuadratic(model)
    curve.setName("Capstone C65 HeatRecoveryRate_vs_InletTemp")
    curve.setCoefficient1Constant(0.7516)
    curve.setCoefficient2x(0.00414)
    curve.setCoefficient3xPOW2(0)
    curve.setMinimumValueofx(29.44)
    curve.setMaximumValueofx(85)
    curve.setInputUnitTypeforX("Temperature")
    curve.setOutputUnitType("Dimensionless")
    mchpHR.setHeatRecoveryRateFunctionofInletWaterTemperatureCurve(curve)

    #    Capstone C65 HeatRecoveryRate_vs_WaterFlow,  !- Heat Recovery Rate Function of Water Flow Rate Curve Name
    curve = openstudio.model.CurveQuadratic(model)
    curve.setName("Capstone C65 HeatRecoveryRate_vs_WaterFlow")
    curve.setCoefficient1Constant(0.83)
    curve.setCoefficient2x(88.76138)
    curve.setCoefficient3xPOW2(-8541.831)
    curve.setMinimumValueofx(0.001577263)
    curve.setMaximumValueofx(0.003785432)
    curve.setInputUnitTypeforX("VolumetricFlow")
    curve.setOutputUnitType("Dimensionless")
    mchpHR.setHeatRecoveryRateFunctionofWaterFlowRateCurve(curve)

    #    0.001577263,             !- Minimum Heat Recovery Water Flow Rate {m3/s}
    mchpHR.setMinimumHeatRecoveryWaterFlowRate(0.001577263)

    #    0.003785432,             !- Maximum Heat Recovery Water Flow Rate {m3/s}
    mchpHR.setMaximumHeatRecoveryWaterFlowRate(0.003785432)

    #    82.2,                    !- Maximum Heat Recovery Water Temperature {C}
    mchpHR.setMaximumHeatRecoveryWaterTemperature(82.2)

    #    Capstone C65 Combustion Air Inlet Node,  !- Combustion Air Inlet Node Name
    #    Capstone C65 Combustion Air Outlet Node,  !- Combustion Air Outlet Node Name

    #    0.489885,                !- Reference Exhaust Air Mass Flow Rate {kg/s}
    mchp.setReferenceExhaustAirMassFlowRate(0.489885)

    #    Capstone C65 ExhAirFlowRate_vs_InletTemp,  !- Exhaust Air Flow Rate Function of Temperature Curve Name
    curve = openstudio.model.CurveCubic(model)
    curve.setName("Capstone C65 ExhAirFlowRate_vs_InletTemp")
    curve.setCoefficient1Constant(0.9837417)
    curve.setCoefficient2x(0.0000676623)
    curve.setCoefficient3xPOW2(0.0000535766)
    curve.setCoefficient4xPOW3(-0.00000212819)
    curve.setMinimumValueofx(-20)
    curve.setMaximumValueofx(50)
    curve.setInputUnitTypeforX("Temperature")
    curve.setOutputUnitType("Dimensionless")
    mchp.setExhaustAirFlowRateFunctionofTemperatureCurve(curve)

    #    Capstone C65 ExhAirFlowRate_vs_PLR,  !- Exhaust Air Flow Rate Function of Part Load Ratio Curve Name
    curve = openstudio.model.CurveCubic(model)
    curve.setName("Capstone C65 ExhAirFlowRate_vs_PLR")
    curve.setCoefficient1Constant(0.272074)
    curve.setCoefficient2x(1.313337)
    curve.setCoefficient3xPOW2(-1.0480845)
    curve.setCoefficient4xPOW3(0.46216638)
    curve.setMinimumValueofx(0.03)
    curve.setMaximumValueofx(1)
    mchp.setExhaustAirFlowRateFunctionofPartLoadRatioCurve(curve)

    #    308.9,                   !- Nominal Exhaust Air Outlet Temperature
    mchp.setNominalExhaustAirOutletTemperature(308.9)

    #    Capstone C65 ExhaustTemp_vs_InletTemp,  !- Exhaust Air Temperature Function of Temperature Curve Name
    curve = openstudio.model.CurveCubic(model)
    curve.setName("Capstone C65 ExhaustTemp_vs_InletTemp")
    curve.setCoefficient1Constant(0.9246362)
    curve.setCoefficient2x(0.0052553)
    curve.setCoefficient3xPOW2(-0.0000197367)
    curve.setCoefficient4xPOW3(-0.000000566196)
    curve.setMinimumValueofx(-20)
    curve.setMaximumValueofx(50)
    mchp.setExhaustAirTemperatureFunctionofTemperatureCurve(curve)

    #    Capstone C65 ExhaustTemp_vs_PLR;  !- Exhaust Air Temperature Function of Part Load Ratio Curve Name
    curve = openstudio.model.CurveCubic(model)
    curve.setName("Capstone C65 ExhaustTemp_vs_PLR")
    curve.setCoefficient1Constant(0.59175)
    curve.setCoefficient2x(0.87874)
    curve.setCoefficient3xPOW2(-0.880443)
    curve.setCoefficient4xPOW3(0.4107131)
    curve.setMinimumValueofx(0.03)
    curve.setMaximumValueofx(1)
    mchp.setExhaustAirTemperatureFunctionofPartLoadRatioCurve(curve)

    return mchp, mchpHR


model = BaselineModel()

model.add_standards(
    json.loads(
        """
{
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
  }
"""
    )
)

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

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

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# We are going to artificially put more than enough electrical and service hot
# water loads (the goal isn't to produce a realistic office building...)

# We transform our building into a 10 story one
for z in zones:
    z.setMultiplier(10)

# Add a shw loop with one water use connections + water use equipment
mixed_swh_loop = model.add_swh_loop("Mixed")
model.add_swh_end_uses(mixed_swh_loop, "Medium Office Bldg Swh")

# Modify it to be about 150 GPM
# with the schedule defined for defaultDay, with a sum of hourly frac = 5.367
# that's about 48 kGal/day of service water, peaking at 85.5 GPM.
# The Capstone Reference Heat Recovery Water Flow Rate = 40 GPM
gpm = 150.0
water_use_connection = (
    mixed_swh_loop.demandComponents(openstudio.IddObjectType("OS:WaterUse:Connections"))[0].to_WaterUseConnections().get()
)
water_use_equipment = water_use_connection.waterUseEquipment()[0]
water_equip_def = water_use_equipment.waterUseEquipmentDefinition()
water_equip_def.setPeakFlowRate(openstudio.convert(gpm, "gal/min", "m^3/s").get())
water_equip_def.setName("Service Water Use Def #{gpm.round(1)} gal/min")

###############################################################################
# If you want to compare it to the base case (without the microturbine)
# switch this as true
base_case = False

if not base_case:

    # Create a capstone c65 object using the method added above
    mchp, mchpHR = add_generator_mt_capstone65(model)
    # Set the Heat Recovery Water Flow Operating Mode
    heatRecoveryWaterFlowOperatingMode = "PlantControl"
    # heatRecoveryWaterFlowOperatingMode = 'InternalControl'
    mchpHR.setHeatRecoveryWaterFlowOperatingMode(heatRecoveryWaterFlowOperatingMode)

    # We will assume the tracking mode is "FollowThermalLimitElectrical"
    # so we place the cogen on the supply side of the plant loop
    # We will connect the mchpHR on the same branch as the WaterHeater:Mixed right
    # before it.
    generator_operation_scheme_type = "FollowThermalLimitElectrical"
    supply_components = mixed_swh_loop.supplyComponents(openstudio.IddObjectType("OS:WaterHeater:Mixed"))
    waterheater = supply_components[0].to_WaterHeaterMixed().get()

    # Get the Use Side (demand) Inlet Node
    inlet_node = waterheater.supplyInletModelObject().get().to_Node().get()
    mchpHR.addToNode(inlet_node)

    # Create a PlantEquipmentOperationHeatingLoad, and place the cogen first in
    # line, and set the plant loop operation scheme to Sequential so the order
    # is preserved
    mixed_swh_loop.setLoadDistributionScheme("Sequential")
    # Create a PlantEquipmentOperationHeatingLoad and add the cogen first,
    operation = openstudio.model.PlantEquipmentOperationHeatingLoad(model)
    operation.addEquipment(mchpHR)
    # Then the waterheater
    operation.addEquipment(waterheater)
    operation.setName("#{mixed_swh_loop.name()} PlantEquipmentOperationHeatingLoad")
    mixed_swh_loop.setPlantEquipmentOperationHeatingLoad(operation)

    # Create an ELCD, and add the cogen on it
    elcd = openstudio.model.ElectricLoadCenterDistribution(model)
    elcd.setName("Capstone C65 ELCD")
    elcd.setGeneratorOperationSchemeType(generator_operation_scheme_type)
    elcd.addGenerator(mchp)
    elcd.setElectricalBussType("AlternatingCurrent")

    # If you want to see all available fields on the ELCD, do the following
    # elcd.resetStorageControlUtilityDemandTargetFractionSchedule
    # Note that all fields after electrical buss type don't apply here
    # since they relate to inverters and storage (+storage controller)

    # I had also added a convenience method called validityCheck because this
    # object has many fields that depend on values selected for \choices fields
    # Eg: if I had not set 'AlternatingCurrent' for buss type, the default is
    # 'DirectCurrentWithInverter', elcd.validityCheck would return false and print
    # a message saying the buss type requires and inverter while I didn't set one
    if not elcd.validityCheck():
        raise "Electric Load Center is not valid"


###############################################################################

add_out_vars = False
if add_out_vars:
    # output variables
    for var in mchp.outputVariableNames():
        openstudio.model.OutputVariable(var, model)

    for var in mchpHR.outputVariableNames():
        openstudio.model.OutputVariable(var, model)

    for var in elcd.outputVariableNames():
        openstudio.model.OutputVariable(var, model)


###############################################################################
# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
