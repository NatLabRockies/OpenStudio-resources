import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 03, PSZ-AC
model.add_hvac(ashrae_sys_num="03")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# pick out on of the zone/system pairs and add a humidifier
# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# Try out all 3 different types of humidity setpoint managers
# on three different airloops in the same model.
for i in range(3):

    zone = zones[i]

    # Add a humidistat at 50% RH to the zone
    dehumidify_sch = openstudio.model.ScheduleConstant(model)
    dehumidify_sch.setValue(50)
    humidistat = openstudio.model.ZoneControlHumidistat(model)
    humidistat.setHumidifyingRelativeHumiditySetpointSchedule(dehumidify_sch)
    zone.setZoneControlHumidistat(humidistat)

    air_system = zone.airLoopHVAC().get()
    humidifier_outlet_node = None

    if i == 0:
        # Add a humidifier after the gas heating coil and before the fan
        htg_coil = (
            air_system.supplyComponents(openstudio.model.CoilHeatingGas.iddObjectType())[0].to_CoilHeatingGas().get()
        )
        htg_coil_outlet_node = htg_coil.outletModelObject().get().to_Node().get()
        humidifier = openstudio.model.HumidifierSteamElectric(model)
        humidifier.addToNode(htg_coil_outlet_node)
        humidifier_outlet_node = humidifier.outletModelObject().get().to_Node().get()
    else:
        # Add a humidifier after all other components
        humidifier = openstudio.model.HumidifierSteamElectric(model)
        humidifier.addToNode(air_system.supplyOutletNode())
        humidifier_outlet_node = humidifier.outletModelObject().get().to_Node().get()

    # Try out all 3 different types of humidity setpoint managers
    # by adding them to the humidifier outlet node.
    if i == 0:
        spm = openstudio.model.SetpointManagerSingleZoneHumidityMinimum(model)
        spm.addToNode(humidifier_outlet_node)

    elif i == 1:
        spm = openstudio.model.SetpointManagerMultiZoneHumidityMinimum(model)
        spm.addToNode(humidifier_outlet_node)

    elif i == 2:
        spm = openstudio.model.SetpointManagerMultiZoneMinimumHumidityAverage(model)
        spm.addToNode(humidifier_outlet_node)


# add output reports
add_out_vars = False
if add_out_vars:
    # Request timeseries data for debugging
    reporting_frequency = "hourly"
    var_names = [
        "System Node Setpoint Temperature",
        "System Node Setpoint Minimum Humidity Ratio",
        "System Node Setpoint Humidity Ratio",
        "Zone Mean Air Humidity Ratio",
        "Zone Mean Air Temperature",
        "Zone Air Relative Humidity",
        "Humidifier Water Volume Flow Rate",
    ]
    for var_name in var_names:
        outputVariable = openstudio.model.OutputVariable(var_name, model)
        outputVariable.setReportingFrequency(reporting_frequency)


# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
