import re

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

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

# add schedule
sch = openstudio.model.ScheduleCompact(model, 10)
sch.setName("Transformer Output Electric Energy Schedule")

# assign the user inputs to variables
name_plate_rating = 100

# check for transformer schedule in the starting model
schedules = model.getObjectsByName("Transformer Output Electric Energy Schedule")

# if schedules.empty?
#  runner.registerAsNotApplicable("Transformer Output Electric Energy Schedule not found")
#  return true
# end

# if schedules[0].iddObject.type != openstudio.IddObjectType("OS:Schedule:Year") and
#  schedules[0].iddObject.type != openstudio.IddObjectType("OS:Schedule:Compact")
#  runner.registerError("Transformer Output Electric Energy Schedule is not a Schedule:Year or a Schedule:Compact")
#  return false
# end

# DLM: these could be inputs
name_plate_efficiency = 0.985
unit_load_at_name_plate_efficiency = 0.35

REGEX_GROUP = re.compile(r"\A[+-]?\d+?(_?\d+)*(\.\d+e?\d*)?\Z")

if name_plate_rating == 0:
    max_energy = 0

    if schedules[0].iddObject().type() == openstudio.IddObjectType("Schedule:Year"):
        for week_target in schedules[0].targets():
            if week_target.iddObject().type() != openstudio.IddObjectType("Schedule:Week:Daily"):
                continue

            for day_target in week_target.targets():
                if day_target.iddObject().type() != openstudio.IddObjectType("Schedule:Day:Interval"):
                    continue

                for eg in day_target.extensibleGroups():
                    value = eg.getDouble(1)
                    if not value.is_initialized():
                        continue
                    if value.get() <= max_energy:
                        continue

                    max_energy = value.get()

    elif schedules[0].iddObject().type() == openstudio.IddObjectType("Schedule:Compact"):
        for eg in schedules[0].extensibleGroups():
            if REGEX_GROUP.match(eg.getString(0).to_s().strip()):
                value = eg.getDouble(0)
                if value.is_initialized() and (value.get() > max_energy):
                    max_energy = value.get()

    # runner.registerInfo("Max energy is #{max_energy} J")

    minutes_per_timestep = None
    for timestep in model.getObjectsByType(openstudio.IddObjectType("Timestep")):
        timestep_per_hour = timestep.getDouble(0)
        if not timestep_per_hour.is_initialized():
            # runner.registerError("Cannot determine timesteps per hour")
            # return false
            pass

        minutes_per_timestep = 60 / timestep_per_hour.get()

    if not minutes_per_timestep:
        # runner.registerError("Cannot determine minutes per timestep")
        # return false
        pass

    seconds_per_timestep = minutes_per_timestep * 60
    max_power = max_energy / seconds_per_timestep

    # runner.registerInfo("Max power is #{max_power} W")

    name_plate_rating = max_power / unit_load_at_name_plate_efficiency


sensor = openstudio.model.EnergyManagementSystemSensor(model, "Schedule Value")
sensor.setKeyName("Transformer Output Electric Energy Schedule")
sensor.setName("TransformerOutputElectricEnergyScheduleEMSSensor")

meteredOutputVariable = openstudio.model.EnergyManagementSystemMeteredOutputVariable(model, sensor)
meteredOutputVariable.setEMSVariableName(sensor.nameString())
meteredOutputVariable.setUpdateFrequency("ZoneTimeStep")
meteredOutputVariable.setResourceType("Electricity")
meteredOutputVariable.setGroupType("Building")
meteredOutputVariable.setEndUseCategory("ExteriorEquipment")
meteredOutputVariable.setEndUseSubcategory("Transformers")
meteredOutputVariable.setUnits("J")

# add 8 lines to deal with E+ bug; can be removed in E+ 9.0
program = openstudio.model.EnergyManagementSystemProgram(model)
program.setName("DummyProgram")
program.addLine("SET N = 0")
program.addLine("SET N = 0")
program.addLine("SET N = 0")
program.addLine("SET N = 0")
program.addLine("SET N = 0")
program.addLine("SET N = 0")
program.addLine("SET N = 0")
program.addLine("SET N = 0")

pcm = openstudio.model.EnergyManagementSystemProgramCallingManager(model)
pcm.setName("DummyManager")
pcm.setCallingPoint("BeginTimestepBeforePredictor")
pcm.addProgram(program)

meter = openstudio.model.OutputMeter(model)
meter.setName("Transformer:ExteriorEquipment:Electricity")
meter.setReportingFrequency("Timestep")

transformer = openstudio.model.ElectricLoadCenterTransformer(model)
transformer.setTransformerUsage("PowerInFromGrid")
transformer.setRatedCapacity(name_plate_rating)
transformer.setPhase("3")
transformer.setConductorMaterial("Aluminum")
transformer.setFullLoadTemperatureRise(150)
transformer.setFractionofEddyCurrentLosses(0.1)
transformer.setPerformanceInputMethod("NominalEfficiency")
transformer.setNameplateEfficiency(name_plate_efficiency)
transformer.setPerUnitLoadforNameplateEfficiency(unit_load_at_name_plate_efficiency)
transformer.setReferenceTemperatureforNameplateEfficiency(75)
transformer.setConsiderTransformerLossforUtilityCost(True)
transformer.addMeter("Transformer:ExteriorEquipment:Electricity")

# add output reports
add_out_vars = False
if add_out_vars:
    # Request timeseries data for debugging
    reporting_frequency = "Timestep"
    # Enable all output Variables for the object
    for var_name in transformer.outputVariableNames():
        outputVariable = openstudio.model.OutputVariable(var_name, model)
        outputVariable.setReportingFrequency(reporting_frequency)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
