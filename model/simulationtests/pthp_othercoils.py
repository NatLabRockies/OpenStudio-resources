import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=3)

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

alwaysOn = model.alwaysOnDiscreteSchedule()

for i, zone in enumerate([zones[0], zones[1], zones[2]]):
    if i == 0:
        htg_coil = openstudio.model.CoilHeatingDXSingleSpeed(model)
        clg_coil = openstudio.model.CoilCoolingDXSingleSpeed(model)
        supp_htg_coil = openstudio.model.CoilHeatingElectric(model, alwaysOn)
        fan = openstudio.model.FanOnOff(model, alwaysOn)
        pthp = openstudio.model.ZoneHVACPackagedTerminalHeatPump(
            model, alwaysOn, fan, htg_coil, clg_coil, supp_htg_coil
        )
        pthp.addToThermalZone(zone)

    elif i == 1:
        htg_coil = openstudio.model.CoilHeatingDXVariableSpeed(model)
        htg_coil_data = openstudio.model.CoilHeatingDXVariableSpeedSpeedData(model)
        htg_coil.addSpeed(htg_coil_data)
        clg_coil = openstudio.model.CoilCoolingDXVariableSpeed(model)
        clg_coil_data = openstudio.model.CoilCoolingDXVariableSpeedSpeedData(model)
        clg_coil.addSpeed(clg_coil_data)
        supp_htg_coil = openstudio.model.CoilHeatingElectric(model, alwaysOn)
        fan = openstudio.model.FanOnOff(model, alwaysOn)
        pthp = openstudio.model.ZoneHVACPackagedTerminalHeatPump(
            model, alwaysOn, fan, htg_coil, clg_coil, supp_htg_coil
        )
        pthp.addToThermalZone(zone)

    elif i == 2:
        htg_coil = openstudio.model.CoilHeatingDXSingleSpeed(model)
        clg_coil = openstudio.model.CoilSystemCoolingDXHeatExchangerAssisted(model)
        supp_htg_coil = openstudio.model.CoilHeatingElectric(model, alwaysOn)
        fan = openstudio.model.FanOnOff(model, alwaysOn)
        pthp = openstudio.model.ZoneHVACPackagedTerminalHeatPump(
            model, alwaysOn, fan, htg_coil, clg_coil, supp_htg_coil
        )
        pthp.addToThermalZone(zone)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
