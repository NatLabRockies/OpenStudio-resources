import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# Schedule Ruleset
defrost_sch = openstudio.model.ScheduleRuleset(model)
defrost_sch.setName("Refrigeration Defrost Schedule")
# All other days
defrost_sch.defaultDaySchedule().setName("Refrigeration Defrost Schedule Default")
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 4, 0, 0), 0)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 4, 45, 0), 1)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 8, 0, 0), 0)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 8, 45, 0), 1)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 12, 0, 0), 0)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 12, 45, 0), 1)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 16, 0, 0), 0)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 16, 45, 0), 1)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 20, 0, 0), 0)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 20, 45, 0), 1)
defrost_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 0)


def add_case(model, thermal_zone, defrost_sch):
    ref_case = openstudio.model.RefrigerationCase(model, defrost_sch)
    ref_case.setThermalZone(thermal_zone)
    return ref_case


def add_walkin(model, thermal_zone, defrost_sch):
    ref_walkin = openstudio.model.RefrigerationWalkIn(model, defrost_sch)
    zone_boundaries = ref_walkin.zoneBoundaries()
    zone_boundaries[0].setThermalZone(thermal_zone)
    return ref_walkin


# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac(ashrae_sys_num="07")

# add thermostats
model.add_thermostats(heating_setpoint=20, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

boilers = sorted(model.getBoilerHotWaters(), key=lambda c: c.nameString())
heating_loop = boilers[0].plantLoop().get()

i = 0
therm_zone = None
ref_sys1 = None
cascade_condenser = None

for z in zones:
    if i == 0:
        therm_zone = z
        ref_sys1 = openstudio.model.RefrigerationSystem(model)
        ref_sys1.addCase(add_case(model, z, defrost_sch))
        ref_sys1.addWalkin(add_walkin(model, z, defrost_sch))
        ref_sys1.addCompressor(openstudio.model.RefrigerationCompressor(model))
        condenser = openstudio.model.RefrigerationCondenserAirCooled(model)
        ref_sys1.setRefrigerationCondenser(condenser)
        ref_sys1.setSuctionPipingZone(z)
        desuperheater = openstudio.model.CoilHeatingDesuperheater(model)
        desuperheater.setHeatingSource(condenser)
        air_loop = z.airLoopHVAC().get()
        coilCoolingWaters = air_loop.supplyComponents(openstudio.IddObjectType("OS:Coil:Cooling:Water"))
        setpointMMA1 = openstudio.model.SetpointManagerMixedAir(model)
        node = coilCoolingWaters[0].to_CoilCoolingWater().get().airOutletModelObject().get().to_Node().get()
        desuperheater.addToNode(node)
        node = desuperheater.outletModelObject().get().to_Node().get()
        setpointMMA1.addToNode(node)

    elif i == 1:
        ref_sys2 = openstudio.model.RefrigerationSystem(model)
        ref_sys2.addCase(add_case(model, z, defrost_sch))
        ref_case_2 = add_case(model, z, defrost_sch)
        ref_case_2.setDurationofDefrostCycle(25)
        ref_case_2.setDripDownTime(5)
        ref_case_2.setDefrost1StartTime(openstudio.Time(0, 1, 15))
        ref_case_2.setDefrost2StartTime(openstudio.Time(0, 4, 16))
        ref_case_2.setDefrost3StartTime(openstudio.Time(0, 7, 17))
        ref_case_2.setDefrost4StartTime(openstudio.Time(0, 10, 18))
        ref_case_2.setDefrost5StartTime(openstudio.Time(0, 14, 19))
        ref_case_2.setDefrost6StartTime(openstudio.Time(0, 17, 20))
        ref_case_2.setDefrost7StartTime(openstudio.Time(0, 20, 21))
        ref_case_2.setDefrost8StartTime(openstudio.Time(0, 23, 22))
        ref_case_3 = add_case(model, z, defrost_sch)
        ref_case_3.setUnitType("NumberOfDoors")
        ref_case_3.setNumberOfDoors(10)
        ref_case_3.setCaseLength(10)
        ref_case_3.setRatedTotalCoolingCapacityperDoor(2000)
        ref_case_3.setStandardCaseFanPowerperDoor(80)
        ref_case_3.setOperatingCaseFanPowerperDoor(80)
        ref_case_3.setStandardCaseLightingPowerperDoor(100)
        ref_case_3.setInstalledCaseLightingPowerperDoor(100)
        ref_case_3.setCaseAntiSweatHeaterPowerperDoor(20)
        ref_case_3.setMinimumAntiSweatHeaterPowerperDoor(20)
        ref_case_3.setCaseDefrostPowerperDoor(150)
        ref_sys2.addCase(ref_case_2)
        ref_sys2.addCase(ref_case_3)
        ref_sys2.addWalkin(add_walkin(model, z, defrost_sch))
        ref_walkin_2 = add_walkin(model, z, defrost_sch)
        ref_walkin_2.setDurationofDefrostCycle(25)
        ref_walkin_2.setDripDownTime(5)
        ref_walkin_2.setDefrost1StartTime(openstudio.Time(0, 1, 15))
        ref_walkin_2.setDefrost2StartTime(openstudio.Time(0, 4, 16))
        ref_walkin_2.setDefrost3StartTime(openstudio.Time(0, 7, 17))
        ref_walkin_2.setDefrost4StartTime(openstudio.Time(0, 10, 18))
        ref_walkin_2.setDefrost5StartTime(openstudio.Time(0, 14, 19))
        ref_walkin_2.setDefrost6StartTime(openstudio.Time(0, 17, 20))
        ref_walkin_2.setDefrost7StartTime(openstudio.Time(0, 20, 21))
        ref_walkin_2.setDefrost8StartTime(openstudio.Time(0, 23, 22))
        ref_sys2.addWalkin(ref_walkin_2)
        ref_sys2.addWalkin(add_walkin(model, z, defrost_sch))
        ref_sys2.addCompressor(openstudio.model.RefrigerationCompressor(model))
        ref_sys2.addHighStageCompressor(openstudio.model.RefrigerationCompressor(model))
        ref_sys2.setRefrigerationCondenser(openstudio.model.RefrigerationCondenserEvaporativeCooled(model))
        ref_sys2.setSuctionPipingZone(z)
        ref_sys2.setIntercoolerType("Shell-and-Coil Intercooler")
        mech_subcooler = openstudio.model.RefrigerationSubcoolerMechanical(model)
        mech_subcooler.setCapacityProvidingSystem(ref_sys1)
        ref_sys2.setMechanicalSubcooler(mech_subcooler)
        ref_sys2.setLiquidSuctionHeatExchangerSubcooler(openstudio.model.RefrigerationSubcoolerLiquidSuction(model))

    elif i == 2:
        ref_sys3 = openstudio.model.RefrigerationSystem(model)
        ref_sys3.addCase(add_case(model, z, defrost_sch))
        ref_sys3.addCase(add_case(model, z, defrost_sch))
        ref_sys3.addWalkin(add_walkin(model, z, defrost_sch))
        ref_sys3.addWalkin(add_walkin(model, z, defrost_sch))
        ref_sys3.addCompressor(openstudio.model.RefrigerationCompressor(model))
        ref_sys3.addCompressor(openstudio.model.RefrigerationCompressor(model))
        water_cooled_condenser = openstudio.model.RefrigerationCondenserWaterCooled(model)
        cooling_tower = model.getCoolingTowerSingleSpeeds()[0]
        plant = cooling_tower.plantLoop().get()
        plant.addDemandBranchForComponent(water_cooled_condenser)
        ref_sys3.setRefrigerationCondenser(water_cooled_condenser)
        ref_sys3.setSuctionPipingZone(z)

        water_tank = openstudio.model.WaterHeaterMixed(model)
        water_tank.setAmbientTemperatureIndicator("ThermalZone")
        water_tank.setAmbientTemperatureThermalZone(z)
        heating_loop.addSupplyBranchForComponent(water_tank)
        # Schedule Ruleset
        setpointTemperatureSchedule = openstudio.model.ScheduleRuleset(model)
        setpointTemperatureSchedule.setName("Setpoint Temperature Schedule")
        setpointTemperatureSchedule.defaultDaySchedule().setName("Setpoint Temperature Schedule Default")
        setpointTemperatureSchedule.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 70)

        desuperheater = openstudio.model.CoilWaterHeatingDesuperheater(model, setpointTemperatureSchedule)
        water_tank.setSetpointTemperatureSchedule(setpointTemperatureSchedule)
        desuperheater.addToHeatRejectionTarget(water_tank)
        desuperheater.setHeatingSource(water_cooled_condenser)

    elif i == 3:
        ref_sys4 = openstudio.model.RefrigerationSystem(model)
        ref_sys4.addCase(add_case(model, z, defrost_sch))
        ref_sys4.addWalkin(add_walkin(model, z, defrost_sch))
        ref_sys4.addCompressor(openstudio.model.RefrigerationCompressor(model))
        cascade_condenser = openstudio.model.RefrigerationCondenserCascade(model)
        ref_sys4.setRefrigerationCondenser(cascade_condenser)
        ref_sys4.setSuctionPipingZone(z)

        ref_sys5 = openstudio.model.RefrigerationSystem(model)
        ref_sys5.addCase(add_case(model, z, defrost_sch))
        ref_sys5.addWalkin(add_walkin(model, z, defrost_sch))
        ref_sys5.addCompressor(openstudio.model.RefrigerationCompressor(model))
        ref_sys5.addCascadeCondenserLoad(cascade_condenser)

        secondary_sys = openstudio.model.RefrigerationSecondarySystem(model)
        secondary_sys.addCase(add_case(model, z, defrost_sch))
        secondary_sys.addCase(add_case(model, z, defrost_sch))
        secondary_sys.addWalkin(add_walkin(model, z, defrost_sch))
        secondary_sys.addWalkin(add_walkin(model, z, defrost_sch))
        secondary_sys.setDistributionPipingZone(z)
        secondary_sys.setReceiverSeparatorZone(z)

        ref_sys5.addSecondarySystemLoad(secondary_sys)
        ref_sys5.setRefrigerationCondenser(openstudio.model.RefrigerationCondenserAirCooled(model))
        ref_sys5.setSuctionPipingZone(z)

    elif i == 4:
        ref_sys6 = openstudio.model.RefrigerationTranscriticalSystem(model)
        ref_sys6.addMediumTemperatureCase(add_case(model, z, defrost_sch))
        ref_sys6.addMediumTemperatureCase(add_case(model, z, defrost_sch))
        ref_sys6.addLowTemperatureCase(add_case(model, z, defrost_sch))
        ref_sys6.addLowTemperatureCase(add_case(model, z, defrost_sch))
        ref_sys6.addMediumTemperatureWalkin(add_walkin(model, z, defrost_sch))
        ref_sys6.addMediumTemperatureWalkin(add_walkin(model, z, defrost_sch))
        ref_sys6.addLowTemperatureWalkin(add_walkin(model, z, defrost_sch))
        ref_sys6.addLowTemperatureWalkin(add_walkin(model, z, defrost_sch))
        compressor1 = openstudio.model.RefrigerationCompressor(model)
        compressor1.setTranscriticalCompressorPowerCurve(
            compressor1.refrigerationCompressorPowerCurve().clone().to_CurveBicubic().get()
        )
        compressor1.setTranscriticalCompressorCapacityCurve(
            compressor1.refrigerationCompressorCapacityCurve().clone().to_CurveBicubic().get()
        )
        compressor2 = openstudio.model.RefrigerationCompressor(model)
        compressor2.setTranscriticalCompressorPowerCurve(
            compressor2.refrigerationCompressorPowerCurve().clone().to_CurveBicubic().get()
        )
        compressor2.setTranscriticalCompressorCapacityCurve(
            compressor2.refrigerationCompressorCapacityCurve().clone().to_CurveBicubic().get()
        )
        ref_sys6.addHighPressureCompressor(compressor1)
        ref_sys6.addLowPressureCompressor(compressor2)
        gas_cooler = openstudio.model.RefrigerationGasCoolerAirCooled(model)
        # gas_cooler.setAirInletNode(z)
        ref_sys6.setRefrigerationGasCooler(gas_cooler)
        ref_sys6.setMediumTemperatureSuctionPipingZone(z)
        ref_sys6.setLowTemperatureSuctionPipingZone(z)

    i += 1


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
