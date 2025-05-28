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

time_24hrs = openstudio.Time(0, 24, 0, 0)

cooling_sch = openstudio.model.ScheduleRuleset(model)
cooling_sch.setName("Air Chiller Cooling Sch")
cooling_sch.defaultDaySchedule().setName("Air Chiller Cooling Sch Default")
cooling_sch.defaultDaySchedule().addValue(time_24hrs, 5)

heating_sch = openstudio.model.ScheduleRuleset(model)
heating_sch.setName("Air Chiller Heating Sch")
heating_sch.defaultDaySchedule().setName("Air Chiller Heating Sch Default")
heating_sch.defaultDaySchedule().addValue(time_24hrs, 5)

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 20% window-to-wall ratio
model.add_windows(wwr=0.2, offset=1, application_type="Above Floor")

air_chiller1 = openstudio.model.RefrigerationAirChiller(model, defrost_sch)
air_chiller2 = openstudio.model.RefrigerationAirChiller(model, defrost_sch)

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

heating_coil1 = None
heating_coil3 = None
cooling_coil1 = None
cooling_coil3 = None
for i, z in enumerate(zones):
    if i == 0:
        schedule = model.alwaysOnDiscreteSchedule()
        fan = openstudio.model.FanOnOff(model, schedule)
        heating_coil1 = openstudio.model.CoilHeatingWater(model, schedule)
        cooling_coil1 = openstudio.model.CoilCoolingWater(model, schedule)
        four_pipe_fan_coil = openstudio.model.ZoneHVACFourPipeFanCoil(
            model, schedule, fan, cooling_coil1, heating_coil1
        )
        four_pipe_fan_coil.addToThermalZone(z)
        air_chiller1.addToThermalZone(z)

    elif i == 1:
        air_chiller2.addToThermalZone(z)
        schedule = model.alwaysOnDiscreteSchedule()
        fan = openstudio.model.FanOnOff(model, schedule)
        heating_coil3 = openstudio.model.CoilHeatingWater(model, schedule)
        cooling_coil3 = openstudio.model.CoilCoolingWater(model, schedule)
        four_pipe_fan_coil = openstudio.model.ZoneHVACFourPipeFanCoil(
            model, schedule, fan, cooling_coil3, heating_coil3
        )
        four_pipe_fan_coil.addToThermalZone(z)


# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac(ashrae_sys_num="07")

# add thermostats
model.add_thermostats(heating_setpoint=18, cooling_setpoint=32)

# In order to produce more consistent results between different runs,
# We ensure we do get the same object each time
chillers = sorted(model.getChillerElectricEIRs(), key=lambda c: c.nameString())
boilers = sorted(model.getBoilerHotWaters(), key=lambda c: c.nameString())

cooling_loop = chillers[0].plantLoop().get()
heating_loop = boilers[0].plantLoop().get()

heating_loop.addDemandBranchForComponent(heating_coil1)
cooling_loop.addDemandBranchForComponent(cooling_coil1)
heating_loop.addDemandBranchForComponent(heating_coil3)
cooling_loop.addDemandBranchForComponent(cooling_coil3)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

for i, z in enumerate(zones):
    if i == 0:
        new_thermostat = openstudio.model.ThermostatSetpointDualSetpoint(model)

        new_thermostat.setHeatingSchedule(heating_sch)
        new_thermostat.setCoolingSchedule(cooling_sch)

        z.setThermostatSetpointDualSetpoint(new_thermostat)

        sizing_zone = z.sizingZone()
        sizing_zone.setZoneCoolingDesignSupplyAirTemperature(0)
        sizing_zone.setZoneHeatingDesignSupplyAirTemperature(0)

        ref_sys7 = openstudio.model.RefrigerationSystem(model)
        ref_sys7.addCompressor(openstudio.model.RefrigerationCompressor(model))
        ref_sys7.setRefrigerationCondenser(openstudio.model.RefrigerationCondenserAirCooled(model))
        ref_sys7.setSuctionPipingZone(z)
        air_chiller3 = openstudio.model.RefrigerationAirChiller(model, defrost_sch)
        air_chiller3.addToThermalZone(z)
        air_chiller3.setCapacityRatingType("EuropeanSC1Standard")
        air_chiller3.setRatedCapacity(100000.0)
        air_chiller4 = openstudio.model.RefrigerationAirChiller(model, defrost_sch)
        air_chiller4.addToThermalZone(z)
        ref_sys7.addAirChiller(air_chiller1)
        ref_sys7.addAirChiller(air_chiller3)
        ref_sys7.addAirChiller(air_chiller4)

        schedule = model.alwaysOnDiscreteSchedule()
        fan = openstudio.model.FanOnOff(model, schedule)
        heating_coil2 = openstudio.model.CoilHeatingWater(model, schedule)
        cooling_coil2 = openstudio.model.CoilCoolingWater(model, schedule)
        four_pipe_fan_coil = openstudio.model.ZoneHVACFourPipeFanCoil(
            model, schedule, fan, cooling_coil2, heating_coil2
        )
        four_pipe_fan_coil.addToThermalZone(z)
        heating_loop.addDemandBranchForComponent(heating_coil2)
        cooling_loop.addDemandBranchForComponent(cooling_coil2)

    elif i == 1:
        new_thermostat = openstudio.model.ThermostatSetpointDualSetpoint(model)

        new_thermostat.setHeatingSchedule(heating_sch)
        new_thermostat.setCoolingSchedule(cooling_sch)

        z.setThermostatSetpointDualSetpoint(new_thermostat)

        sizing_zone = z.sizingZone()
        sizing_zone.setZoneCoolingDesignSupplyAirTemperature(0)
        sizing_zone.setZoneHeatingDesignSupplyAirTemperature(0)

        ref_sys7 = openstudio.model.RefrigerationSystem(model)
        ref_sys7.addCompressor(openstudio.model.RefrigerationCompressor(model))
        ref_sys7.setRefrigerationCondenser(openstudio.model.RefrigerationCondenserAirCooled(model))
        ref_sys7.setSuctionPipingZone(z)
        air_chiller3 = openstudio.model.RefrigerationAirChiller(model, defrost_sch)
        air_chiller3.addToThermalZone(z)
        air_chiller4 = openstudio.model.RefrigerationAirChiller(model, defrost_sch)
        air_chiller4.addToThermalZone(z)
        ref_sys7.addAirChiller(air_chiller3)
        ref_sys7.addAirChiller(air_chiller4)

    elif i == 2:
        air_loop = z.airLoopHVAC().get()
        air_loop.removeBranchForZone(z)
        new_thermostat = openstudio.model.ThermostatSetpointDualSetpoint(model)

        new_thermostat.setHeatingSchedule(heating_sch)
        new_thermostat.setCoolingSchedule(cooling_sch)

        z.setThermostatSetpointDualSetpoint(new_thermostat)

        sizing_zone = z.sizingZone()
        sizing_zone.setZoneCoolingDesignSupplyAirTemperature(0)
        sizing_zone.setZoneHeatingDesignSupplyAirTemperature(0)

        ref_sys7 = openstudio.model.RefrigerationSystem(model)
        ref_sys7.addCompressor(openstudio.model.RefrigerationCompressor(model))
        ref_sys7.setRefrigerationCondenser(openstudio.model.RefrigerationCondenserAirCooled(model))
        ref_sys7.setSuctionPipingZone(z)
        air_chiller3 = openstudio.model.RefrigerationAirChiller(model, defrost_sch)
        air_chiller3.addToThermalZone(z)
        air_chiller4 = openstudio.model.RefrigerationAirChiller(model, defrost_sch)
        air_chiller4.addToThermalZone(z)
        ref_sys7.addAirChiller(air_chiller3)
        ref_sys7.addAirChiller(air_chiller4)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
