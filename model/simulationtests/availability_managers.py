import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 03, PSZ-AC
model.add_hvac(ashrae_sys_num="03")

schedule = openstudio.model.ScheduleRuleset(model)
day_schedule = schedule.defaultDaySchedule()
day_schedule.addValue(openstudio.Time(0, 6, 0, 0), 0.0)
day_schedule.addValue(openstudio.Time(0, 22, 0, 0), 1.0)
day_schedule.addValue(openstudio.Time(0, 24, 0, 0), 0.0)

# In order to produce consistent results, because zones and systems may not
# be in the same order in the resulting OSM on subsequent runs,
# We sort the AirLoopHVAC by the (unique in each AirLoopHVAC) thermal zone names
# We'll ensure we assign the same AVMs to the same Zone!
systems = sorted(model.getAirLoopHVACs(), key=lambda a: a.thermalZones()[0].nameString())
for i, system in enumerate(systems):
    system.setAvailabilitySchedule(schedule)
    if i == 0:
        avm = openstudio.model.AvailabilityManagerNightVentilation(model)
        ventilationTemperatureSchedule = openstudio.model.ScheduleRuleset(model)
        ventilationTemperatureSchedule.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 18.0)
        avm.setVentilationTemperatureSchedule(ventilationTemperatureSchedule)
        if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("2.3.1"):
            system.setAvailabilityManagers([avm])
        else:
            system.setAvailabilityManager(avm)

    elif i == 1:
        avm = openstudio.model.AvailabilityManagerOptimumStart(model)
        if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("2.3.1"):
            system.setAvailabilityManagers([avm])
        else:
            system.setAvailabilityManager(avm)

    elif i == 2:
        avm = openstudio.model.AvailabilityManagerHybridVentilation(model)
        if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("2.3.1"):
            system.setAvailabilityManagers([avm])
        else:
            system.setAvailabilityManager(avm)

    elif i == 3:
        system.setNightCycleControlType("CycleOnAny")


# Swap the coils so that the heating coil is before the DX to avoid frost
# conditions on the DX cooling coil
#      nmodel.getAirLoopHVACs.each do |a|
#      n  hc = a.supplyComponents(openstudio.IddObjectType("OS_Coil_Heating_Gas")[0].to_CoilHeatingGas.get
#      n  m_node = a.mixedAirNode.get
#      n  hc.addToNode(m_node)
#      nend

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
