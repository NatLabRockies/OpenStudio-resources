import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac(ashrae_sys_num="07")

unitaryAirLoopHVAC = openstudio.model.AirLoopHVAC(model)
unitaryAirLoopHVAC.setName("Unitary AirLoopHVAC")
schedule = model.alwaysOnDiscreteSchedule()
fan = openstudio.model.FanOnOff(model, schedule)

heating_curve_1 = openstudio.model.CurveCubic(model)
heating_curve_1.setCoefficient1Constant(0.758746)
heating_curve_1.setCoefficient2x(0.027626)
heating_curve_1.setCoefficient3xPOW2(0.000148716)
heating_curve_1.setCoefficient4xPOW3(0.0000034992)
heating_curve_1.setMinimumValueofx(-20.0)
heating_curve_1.setMaximumValueofx(20.0)

heating_curve_2 = openstudio.model.CurveCubic(model)
heating_curve_2.setCoefficient1Constant(0.84)
heating_curve_2.setCoefficient2x(0.16)
heating_curve_2.setCoefficient3xPOW2(0.0)
heating_curve_2.setCoefficient4xPOW3(0.0)
heating_curve_2.setMinimumValueofx(0.5)
heating_curve_2.setMaximumValueofx(1.5)

heating_curve_3 = openstudio.model.CurveCubic(model)
heating_curve_3.setCoefficient1Constant(1.19248)
heating_curve_3.setCoefficient2x(-0.0300438)
heating_curve_3.setCoefficient3xPOW2(0.00103745)
heating_curve_3.setCoefficient4xPOW3(-0.000023328)
heating_curve_3.setMinimumValueofx(-20.0)
heating_curve_3.setMaximumValueofx(20.0)

heating_curve_4 = openstudio.model.CurveQuadratic(model)
heating_curve_4.setCoefficient1Constant(1.3824)
heating_curve_4.setCoefficient2x(-0.4336)
heating_curve_4.setCoefficient3xPOW2(0.0512)
heating_curve_4.setMinimumValueofx(0.0)
heating_curve_4.setMaximumValueofx(1.0)

heating_curve_5 = openstudio.model.CurveQuadratic(model)
heating_curve_5.setCoefficient1Constant(0.75)
heating_curve_5.setCoefficient2x(0.25)
heating_curve_5.setCoefficient3xPOW2(0.0)
heating_curve_5.setMinimumValueofx(0.0)
heating_curve_5.setMaximumValueofx(1.0)

heating_coil = openstudio.model.CoilHeatingDXSingleSpeed(
    model, schedule, heating_curve_1, heating_curve_2, heating_curve_3, heating_curve_4, heating_curve_5
)

cooling_curve_1 = openstudio.model.CurveBiquadratic(model)
cooling_curve_1.setCoefficient1Constant(0.766956)
cooling_curve_1.setCoefficient2x(0.0107756)
cooling_curve_1.setCoefficient3xPOW2(-0.0000414703)
cooling_curve_1.setCoefficient4y(0.00134961)
cooling_curve_1.setCoefficient5yPOW2(-0.000261144)
cooling_curve_1.setCoefficient6xTIMESY(0.000457488)
cooling_curve_1.setMinimumValueofx(17.0)
cooling_curve_1.setMaximumValueofx(22.0)
cooling_curve_1.setMinimumValueofy(13.0)
cooling_curve_1.setMaximumValueofy(46.0)

cooling_curve_2 = openstudio.model.CurveQuadratic(model)
cooling_curve_2.setCoefficient1Constant(0.8)
cooling_curve_2.setCoefficient2x(0.2)
cooling_curve_2.setCoefficient3xPOW2(0.0)
cooling_curve_2.setMinimumValueofx(0.5)
cooling_curve_2.setMaximumValueofx(1.5)

cooling_curve_3 = openstudio.model.CurveBiquadratic(model)
cooling_curve_3.setCoefficient1Constant(0.297145)
cooling_curve_3.setCoefficient2x(0.0430933)
cooling_curve_3.setCoefficient3xPOW2(-0.000748766)
cooling_curve_3.setCoefficient4y(0.00597727)
cooling_curve_3.setCoefficient5yPOW2(0.000482112)
cooling_curve_3.setCoefficient6xTIMESY(-0.000956448)
cooling_curve_3.setMinimumValueofx(17.0)
cooling_curve_3.setMaximumValueofx(22.0)
cooling_curve_3.setMinimumValueofy(13.0)
cooling_curve_3.setMaximumValueofy(46.0)

cooling_curve_4 = openstudio.model.CurveQuadratic(model)
cooling_curve_4.setCoefficient1Constant(1.156)
cooling_curve_4.setCoefficient2x(-0.1816)
cooling_curve_4.setCoefficient3xPOW2(0.0256)
cooling_curve_4.setMinimumValueofx(0.5)
cooling_curve_4.setMaximumValueofx(1.5)

cooling_curve_5 = openstudio.model.CurveQuadratic(model)
cooling_curve_5.setCoefficient1Constant(0.75)
cooling_curve_5.setCoefficient2x(0.25)
cooling_curve_5.setCoefficient3xPOW2(0.0)
cooling_curve_5.setMinimumValueofx(0.0)
cooling_curve_5.setMaximumValueofx(1.0)

cooling_coil = openstudio.model.CoilCoolingDXSingleSpeed(
    model, schedule, cooling_curve_1, cooling_curve_2, cooling_curve_3, cooling_curve_4, cooling_curve_5
)
supp_heating_coil = openstudio.model.CoilHeatingElectric(model, schedule)
unitary = openstudio.model.AirLoopHVACUnitaryHeatPumpAirToAir(
    model, schedule, fan, heating_coil, cooling_coil, supp_heating_coil
)

supplyOutletNode = unitaryAirLoopHVAC.supplyOutletNode()
unitary.addToNode(supplyOutletNode)

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# In order to produce more consistent results between different runs,
# We ensure we do get the same object each time
chillers = sorted(model.getChillerElectricEIRs(), key=lambda c: c.nameString())
boilers = sorted(model.getBoilerHotWaters(), key=lambda c: c.nameString())

cooling_loop = chillers[0].plantLoop().get()
heating_loop = boilers[0].plantLoop().get()

for i, z in enumerate(zones):
    if i == 0:
        schedule = model.alwaysOnDiscreteSchedule()
        fan = openstudio.model.FanOnOff(model, schedule)
        heating_coil = openstudio.model.CoilHeatingWater(model, schedule)
        cooling_coil = openstudio.model.CoilCoolingWater(model, schedule)
        four_pipe_fan_coil = openstudio.model.ZoneHVACFourPipeFanCoil(model, schedule, fan, cooling_coil, heating_coil)
        four_pipe_fan_coil.addToThermalZone(z)
        heating_loop.addDemandBranchForComponent(heating_coil)
        cooling_loop.addDemandBranchForComponent(cooling_coil)

    elif i == 1:
        schedule = model.alwaysOnDiscreteSchedule()
        fan = openstudio.model.FanOnOff(model, schedule)
        heating_coil = openstudio.model.CoilHeatingWaterToAirHeatPumpEquationFit(model)
        cooling_coil = openstudio.model.CoilCoolingWaterToAirHeatPumpEquationFit(model)
        supp_heating_coil = openstudio.model.CoilHeatingElectric(model, schedule)
        water_to_air_heat_pump = openstudio.model.ZoneHVACWaterToAirHeatPump(
            model, schedule, fan, heating_coil, cooling_coil, supp_heating_coil
        )
        water_to_air_heat_pump.addToThermalZone(z)
        heating_loop.addDemandBranchForComponent(heating_coil)
        cooling_loop.addDemandBranchForComponent(cooling_coil)

    elif i == 2:
        thermal_zone_vector = openstudio.model.ThermalZoneVector()
        thermal_zone_vector.append(z)
        hvac = openstudio.model.addSystemType1(model, thermal_zone_vector)
        schedule = model.alwaysOnDiscreteSchedule()
        fan = openstudio.model.FanOnOff(model, schedule)
        ptacs = model.getZoneHVACPackagedTerminalAirConditioners()
        fan_cv = ptacs[0].supplyAirFan()
        ptacs[0].setSupplyAirFan(fan)
        fan_cv.remove()

    elif i == 3:
        thermal_zone_vector = openstudio.model.ThermalZoneVector()
        thermal_zone_vector.append(z)
        hvac = openstudio.model.addSystemType2(model, thermal_zone_vector)
        schedule = model.alwaysOnDiscreteSchedule()
        fan = openstudio.model.FanOnOff(model, schedule)
        pthps = model.getZoneHVACPackagedTerminalHeatPumps()
        fan_cv = pthps[0].supplyAirFan()
        pthps[0].setSupplyAirFan(fan)
        fan_cv.remove()

    elif i == 4:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)

        schedule = model.alwaysOnDiscreteSchedule()
        # Starting with E 9.0.0, Uncontrolled is deprecated and replaced with
        # ConstantVolume:NoReheat
        if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("2.7.0"):
            new_terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(model, schedule)
        else:
            new_terminal = openstudio.model.AirTerminalSingleDuctUncontrolled(model, schedule)

        unitaryAirLoopHVAC.addBranchForZone(z, new_terminal.to_StraightComponent())
        unitary.setControllingZone(z)


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
