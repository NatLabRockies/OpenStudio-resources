import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=15, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# set HVAC for the IT equipment zone
model.add_hvac(ashrae_sys_num="07")

# In order to produce more consistent results between different runs,
# we sort the zones by names
# zones = model.getThermalZones.sort_by{|z| z.nameString}

# Get spaces, ordered by name to ensure consistency
spaces = sorted(model.getSpaces(), key=lambda s: s.nameString())

for i, space in enumerate(spaces):
    # IT equipment with default curves
    if i == 0:
        it_equipment_def = openstudio.model.ElectricEquipmentITEAirCooledDefinition(model)
        it_equipment_def.setName("IT equipment def 1")
        it_equipment_def.setWattsperUnit(50000)
        it_equipment_def.setDesignFanAirFlowRateperPowerInput(0.0001)
        it_equipment_def.setDesignEnteringAirTemperature(22.5)  # recommended SAT 18-27C, use the middle T as design
        it_equipment_def.setDesignFanPowerInputFraction(0.4)

        it_equipment = openstudio.model.ElectricEquipmentITEAirCooled(it_equipment_def)
        it_equipment.setSpace(space)
        it_equipment.setName("#{space.name()} IT equipment 1")
        it_equipment_def.setDesignPowerInputCalculationMethod("Watts/Area", it_equipment.floorArea())

    elif i == 1:
        cpu_power_curve = openstudio.model.CurveBiquadratic(model)
        cpu_power_curve.setCoefficient1Constant(-0.035289)
        cpu_power_curve.setCoefficient2x(1.0)
        cpu_power_curve.setCoefficient3xPOW2(0.0)
        cpu_power_curve.setCoefficient4y(0.0015684)
        cpu_power_curve.setCoefficient5yPOW2(0.0)
        cpu_power_curve.setCoefficient6xTIMESY(0.0)
        cpu_power_curve.setMinimumValueofx(0.0)
        cpu_power_curve.setMaximumValueofx(1.5)
        cpu_power_curve.setMinimumValueofy(-10)
        cpu_power_curve.setMaximumValueofy(99.0)

        airflow_curve = openstudio.model.CurveBiquadratic(model)
        airflow_curve.setCoefficient1Constant(-1.025)
        airflow_curve.setCoefficient2x(0.9)
        airflow_curve.setCoefficient3xPOW2(0.0)
        airflow_curve.setCoefficient4y(0.05)
        airflow_curve.setCoefficient5yPOW2(0.0)
        airflow_curve.setCoefficient6xTIMESY(0.0)
        airflow_curve.setMinimumValueofx(0.0)
        airflow_curve.setMaximumValueofx(1.5)
        airflow_curve.setMinimumValueofy(-10)
        airflow_curve.setMaximumValueofy(99.0)

        fan_power_curve = openstudio.model.CurveQuadratic(model)
        fan_power_curve.setCoefficient1Constant(0.0)
        fan_power_curve.setCoefficient2x(1.0)
        fan_power_curve.setCoefficient3xPOW2(0.0)
        fan_power_curve.setMinimumValueofx(0.0)
        fan_power_curve.setMaximumValueofx(99.0)

        it_equipment_def = openstudio.model.ElectricEquipmentITEAirCooledDefinition(
            model, cpu_power_curve, airflow_curve, fan_power_curve
        )
        it_equipment_def.setName("IT equipment def 2")
        it_equipment_def.setWattsperUnit(50000)
        it_equipment_def.setDesignFanAirFlowRateperPowerInput(0.0001)
        it_equipment_def.setDesignFanPowerInputFraction(0.4)
        it_equipment_def.setDesignEnteringAirTemperature(22.5)  # recommended SAT 18-27C, use the middle T as design
        it_equipment_def.setAirFlowCalculationMethod("FlowControlWithApproachTemperatures")

        it_equipment = openstudio.model.ElectricEquipmentITEAirCooled(it_equipment_def)
        it_equipment.setSpace(space)
        it_equipment.setName("#{space.name()} IT equipment 2")

        it_equipment.setDesignPowerInputSchedule(model.alwaysOnDiscreteSchedule())
        it_equipment.setMultiplier(2.0)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
