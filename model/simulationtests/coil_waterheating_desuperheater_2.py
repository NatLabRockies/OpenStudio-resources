import openstudio

from lib.baseline_model import BaselineModel


def add_case(model, thermal_zone, defrost_sch):
    ref_case = openstudio.model.RefrigerationCase(model, defrost_sch)
    ref_case.setThermalZone(thermal_zone)
    return ref_case


# Tests a desuperheater with:
# * Heat Rejection Target: WaterHeaterMixed
# * Heating source: RefrigerationCondenserAirCooled.
#
# @param model [BaselineModel] The model in which to create it
# @param zone [openstudio.model.ThermalZone] the zone in question (has a
# PSZ-AC that we'll mess with to add an AirLoopHVACUnitary with the
# CoilCoolingDXMultiSpeed)
# @return [openstudio.model.CoilWaterHeatingDesuperheater]
def create_refrigeration_test(model, zone, defrost_sch):
    # create desuperheater object
    setpoint_temp_sch = openstudio.model.ScheduleRuleset(model, 60)
    coil_water_heating_desuperheater_multi = openstudio.model.CoilWaterHeatingDesuperheater(model, setpoint_temp_sch)
    coil_water_heating_desuperheater_multi.setRatedHeatReclaimRecoveryEfficiency(0.85)

    # Create a SHW Loop with a Mixed Water Heater
    mixed_swh_loop = model.add_swh_loop("Mixed")
    water_heater_mixed = (
        mixed_swh_loop.supplyComponents(openstudio.IddObjectType("OS:WaterHeater:Mixed"))[0].to_WaterHeaterMixed().get()
    )
    # Add it as a heat rejection target
    coil_water_heating_desuperheater_multi.addToHeatRejectionTarget(water_heater_mixed)

    # create a refrigeration system with a case and compressor
    ref_sys1 = openstudio.model.RefrigerationSystem(model)
    ref_sys1.addCase(add_case(model, zone, defrost_sch))
    ref_sys1.addCase(add_case(model, zone, defrost_sch))
    ref_sys1.addCompressor(openstudio.model.RefrigerationCompressor(model))

    # create aircooled refrigeration condenser
    refrigeration_condenser_aircooled = openstudio.model.RefrigerationCondenserAirCooled(model)

    # set it as the condenser of the refrigeration system
    ref_sys1.setRefrigerationCondenser(refrigeration_condenser_aircooled)

    # And Set it as the heating source of the Desuperheater
    coil_water_heating_desuperheater_multi.setHeatingSource(refrigeration_condenser_aircooled)

    return coil_water_heating_desuperheater_multi


model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# add ASHRAE System type 03, PSZ-AC
model.add_hvac(ashrae_sys_num="03")

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

###############################################################################
#                  (2) T E S T    R E F R I G E R A T I O N                   #
###############################################################################

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

# Tests a desuperheater with:
# * Heat Rejection Target: WaterHeaterMixed
# * Heating source: RefrigrationCondenserAirCooled.
create_refrigeration_test(model, zones[0], defrost_sch)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
