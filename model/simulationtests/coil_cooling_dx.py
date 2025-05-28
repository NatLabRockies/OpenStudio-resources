import openstudio

from lib.baseline_model import BaselineModel

m = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone building
m.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
m.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
m.add_thermostats(heating_setpoint=19, cooling_setpoint=26)

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type()

# add design days to the model (Chicago)
m.add_design_days()


def curve_biquadratic(model, c_1constant, c_2x, c_3xPOW2, c_4y, c_5yPOW2, c_6xTIMESY, minx, maxx, miny, maxy):
    curve = openstudio.model.CurveBiquadratic(model)
    curve.setCoefficient1Constant(c_1constant)
    curve.setCoefficient2x(c_2x)
    curve.setCoefficient3xPOW2(c_3xPOW2)
    curve.setCoefficient4y(c_4y)
    curve.setCoefficient5yPOW2(c_5yPOW2)
    curve.setCoefficient6xTIMESY(c_6xTIMESY)
    curve.setMinimumValueofx(minx)
    curve.setMaximumValueofx(maxx)
    curve.setMinimumValueofy(miny)
    curve.setMaximumValueofy(maxy)
    return curve


def curve_quadratic(model, c_1constant, c_2x, c_3xPOW2, minx, maxx, miny, maxy):
    curve = openstudio.model.CurveQuadratic(model)
    curve.setCoefficient1Constant(c_1constant)
    curve.setCoefficient2x(c_2x)
    curve.setCoefficient3xPOW2(c_3xPOW2)
    curve.setMinimumValueofx(minx)
    curve.setMaximumValueofx(maxx)
    curve.setMinimumCurveOutput(miny)
    curve.setMaximumCurveOutput(maxy)
    return curve


constant_biquadratic = curve_biquadratic(m, 1, 0, 0, 0, 0, 0, -100, 100, -100, 100)

# CoilCoolingDXCurveFitSpeed
# speeds correspond to a variable speed central air conditioner
speed_1 = openstudio.model.CoilCoolingDXCurveFitSpeed(m)
speed_1.setGrossTotalCoolingCapacityFraction(1.0)
speed_1.setGrossSensibleHeatRatio(0.842150793933333)
speed_1.setGrossCoolingCOP(5.48021287249984)

cool_cap_ft = curve_biquadratic(
    m,
    1.790226088881,
    -0.0772146982404,
    0.00299548780452,
    0.0026270330994,
    -6.81238188e-005,
    -0.00062105857056,
    13.88,
    23.88,
    18.33,
    51.66,
)
cool_cap_fff = curve_quadratic(m, 1, 0, 0, 0, 2, 0, 2)
cool_eir_ft = curve_biquadratic(
    m,
    -0.1450569952,
    0.062239559472,
    -0.00190953288,
    -0.012608055432,
    0.0010591834752,
    -0.0003311985672,
    13.88,
    23.88,
    18.33,
    51.66,
)
cool_eir_fff = curve_quadratic(m, 1, 0, 0, 0, 2, 0, 2)
cool_plf_fplr = curve_quadratic(m, 0.75, 0.25, 0, 0, 1, 0.7, 1)

speed_1.setTotalCoolingCapacityModifierFunctionofTemperatureCurve(cool_cap_ft)
speed_1.setTotalCoolingCapacityModifierFunctionofAirFlowFractionCurve(cool_cap_fff)
speed_1.setEnergyInputRatioModifierFunctionofTemperatureCurve(cool_eir_ft)
speed_1.setEnergyInputRatioModifierFunctionofAirFlowFractionCurve(cool_eir_fff)
speed_1.setPartLoadFractionCorrelationCurve(cool_plf_fplr)
speed_1.setWasteHeatModifierFunctionofTemperatureCurve(constant_biquadratic)

speed_2 = openstudio.model.CoilCoolingDXCurveFitSpeed(m)
speed_2.setGrossTotalCoolingCapacityFraction(7137.87761659463 / 4015.05615933448)
speed_2.setGrossSensibleHeatRatio(0.80758872085)
speed_2.setGrossCoolingCOP(5.1989191865934)

cool_cap_ft = curve_biquadratic(
    m,
    1.189356223401,
    -0.0251898606522,
    0.0018013099626,
    0.004151872233,
    -4.332993588e-005,
    -0.0006851085138,
    13.88,
    23.88,
    18.33,
    51.66,
)
cool_cap_fff = curve_quadratic(m, 1, 0, 0, 0, 2, 0, 2)
cool_eir_ft = curve_biquadratic(
    m,
    1.21042990764,
    -0.076844452176,
    0.00151658244,
    -0.002526115752,
    0.0007214803488,
    -0.0001603816524,
    13.88,
    23.88,
    18.33,
    51.66,
)
cool_eir_fff = curve_quadratic(m, 1, 0, 0, 0, 2, 0, 2)
cool_plf_fplr = curve_quadratic(m, 0.75, 0.25, 0, 0, 1, 0.7, 1)

speed_2.setTotalCoolingCapacityModifierFunctionofTemperatureCurve(cool_cap_ft)
speed_2.setTotalCoolingCapacityModifierFunctionofAirFlowFractionCurve(cool_cap_fff)
speed_2.setEnergyInputRatioModifierFunctionofTemperatureCurve(cool_eir_ft)
speed_2.setEnergyInputRatioModifierFunctionofAirFlowFractionCurve(cool_eir_fff)
speed_2.setPartLoadFractionCorrelationCurve(cool_plf_fplr)
speed_2.setWasteHeatModifierFunctionofTemperatureCurve(constant_biquadratic)

speed_3 = openstudio.model.CoilCoolingDXCurveFitSpeed(m)
speed_3.setGrossTotalCoolingCapacityFraction(11152.9337759291 / 4015.05615933448)
speed_3.setGrossSensibleHeatRatio(0.7039025016)
speed_3.setGrossCoolingCOP(4.64414572911775)

cool_cap_ft = curve_biquadratic(
    m,
    -0.300216325722,
    0.1194562230534,
    -0.001862843184,
    0.000730227277800001,
    -3.753475524e-005,
    -0.00043911348696,
    13.88,
    23.88,
    18.33,
    51.66,
)
cool_cap_fff = curve_quadratic(m, 1, 0, 0, 0, 2, 0, 2)
cool_eir_ft = curve_biquadratic(
    m,
    0.70183064548,
    -0.049235917464,
    0.00126482472,
    0.031408426368,
    0.0003622673484,
    -0.0011050729236,
    13.88,
    23.88,
    18.33,
    51.66,
)
cool_eir_fff = curve_quadratic(m, 1, 0, 0, 0, 2, 0, 2)
cool_plf_fplr = curve_quadratic(m, 0.75, 0.25, 0, 0, 1, 0.7, 1)

speed_3.setTotalCoolingCapacityModifierFunctionofTemperatureCurve(cool_cap_ft)
speed_3.setTotalCoolingCapacityModifierFunctionofAirFlowFractionCurve(cool_cap_fff)
speed_3.setEnergyInputRatioModifierFunctionofTemperatureCurve(cool_eir_ft)
speed_3.setEnergyInputRatioModifierFunctionofAirFlowFractionCurve(cool_eir_fff)
speed_3.setPartLoadFractionCorrelationCurve(cool_plf_fplr)
speed_3.setWasteHeatModifierFunctionofTemperatureCurve(constant_biquadratic)

speed_4 = openstudio.model.CoilCoolingDXCurveFitSpeed(m)
speed_4.setGrossTotalCoolingCapacityFraction(12937.4031800778 / 4015.05615933448)
speed_4.setGrossSensibleHeatRatio(0.712483430089655)
speed_4.setGrossCoolingCOP(4.0695894950265)

cool_cap_ft = curve_biquadratic(
    m,
    0.962249880784,
    -0.0039087090378,
    0.00132934689648,
    0.0016072565382,
    -8.342352e-008,
    -0.00065486142576,
    13.88,
    23.88,
    18.33,
    51.66,
)
cool_cap_fff = curve_quadratic(m, 1, 0, 0, 0, 2, 0, 2)
cool_eir_ft = curve_biquadratic(
    m,
    -0.74798782608,
    0.099914996016,
    -0.00272789532,
    0.026966547,
    0.0002513297808,
    -0.0006019728516,
    13.88,
    23.88,
    18.33,
    51.66,
)
cool_eir_fff = curve_quadratic(m, 1, 0, 0, 0, 2, 0, 2)
cool_plf_fplr = curve_quadratic(m, 0.75, 0.25, 0, 0, 1, 0.7, 1)

speed_4.setTotalCoolingCapacityModifierFunctionofTemperatureCurve(cool_cap_ft)
speed_4.setTotalCoolingCapacityModifierFunctionofAirFlowFractionCurve(cool_cap_fff)
speed_4.setEnergyInputRatioModifierFunctionofTemperatureCurve(cool_eir_ft)
speed_4.setEnergyInputRatioModifierFunctionofAirFlowFractionCurve(cool_eir_fff)
speed_4.setPartLoadFractionCorrelationCurve(cool_plf_fplr)
speed_4.setWasteHeatModifierFunctionofTemperatureCurve(constant_biquadratic)

# CoilCoolingDXCurveFitOperatingMode
operating_mode = openstudio.model.CoilCoolingDXCurveFitOperatingMode(m)
operating_mode.setRatedGrossTotalCoolingCapacity(4015.05615933448)
operating_mode.setMaximumCyclingRate(3)
operating_mode.setRatioofInitialMoistureEvaporationRateandSteadyStateLatentCapacity(1.5)
operating_mode.setLatentCapacityTimeConstant(45)
operating_mode.setNominalTimeforCondensateRemovaltoBegin(1000)

operating_mode.addSpeed(speed_1)
operating_mode.addSpeed(speed_2)
operating_mode.addSpeed(speed_3)
operating_mode.addSpeed(speed_4)
operating_mode.setNominalSpeedNumber(1)

# CoilCoolingDXCurveFitPerformance
performance = openstudio.model.CoilCoolingDXCurveFitPerformance(m, operating_mode)

# CoilCoolingDX
coil = openstudio.model.CoilCoolingDX(m, performance)

# FanOnOff
fan = openstudio.model.FanOnOff(m)
fan.setFanEfficiency(0.75)
fan.setPressureRise(476.748000740096)
fan.setMotorEfficiency(1.0)
fan.setMotorInAirstreamFraction(1.0)

# AirLoopHVACUnitarySystem
air_loop_unitary = openstudio.model.AirLoopHVACUnitarySystem(m)
air_loop_unitary.setAvailabilitySchedule(m.alwaysOnDiscreteSchedule())
air_loop_unitary.setCoolingCoil(coil)
air_loop_unitary.setSupplyAirFlowRateDuringHeatingOperation(0.0)
air_loop_unitary.setSupplyFan(fan)
air_loop_unitary.setFanPlacement("BlowThrough")
air_loop_unitary.setSupplyAirFanOperatingModeSchedule(m.alwaysOffDiscreteSchedule())
air_loop_unitary.setSupplyAirFlowRateMethodDuringCoolingOperation("SupplyAirFlowRate")
air_loop_unitary.setSupplyAirFlowRateMethodDuringHeatingOperation("SupplyAirFlowRate")
air_loop_unitary.setMaximumSupplyAirTemperature(48.888889)
air_loop_unitary.setSupplyAirFlowRateWhenNoCoolingorHeatingisRequired(0)

# AirLoopHVAC
air_loop = openstudio.model.AirLoopHVAC(m)
air_supply_inlet_node = air_loop.supplyInletNode()
air_loop_unitary.addToNode(air_supply_inlet_node)

# Add to zone
# In order to produce more consistent results between different runs,
# we sort the zones by names
# (There's only one here, but just in case this would be copy pasted somewhere
# else...)
zones = sorted(m.getThermalZones(), key=lambda z: z.nameString())
z = zones[0]
atu = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(m, m.alwaysOnDiscreteSchedule())
air_loop_unitary.setControllingZoneorThermostatLocation(z)
air_loop.addBranchForZone(z, atu)

# save the OpenStudio model (.osm)
m.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
