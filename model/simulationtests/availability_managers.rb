# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 1,
                     'perimeter_zone_depth' => 3 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add ASHRAE System type 03, PSZ-AC
model.add_hvac({ 'ashrae_sys_num' => '03' })

schedule = OpenStudio::Model::ScheduleRuleset.new(model)
day_schedule = schedule.defaultDaySchedule
day_schedule.addValue(OpenStudio::Time.new(0, 6, 0, 0), 0.0)
day_schedule.addValue(OpenStudio::Time.new(0, 22, 0, 0), 1.0)
day_schedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 0.0)

# In order to produce consistent results, because zones and systems may not
# be in the same order in the resulting OSM on subsequent runs,
# We sort the AirLoopHVAC by the (unique in each AirLoopHVAC) thermal zone names
# We'll ensure we assign the same AVMs to the same Zone!
systems = model.getAirLoopHVACs.sort_by { |a| a.thermalZones[0].name.to_s }
systems.each_with_index do |system, i|
  system.setAvailabilitySchedule(schedule)
  case i
  when 0
    avm = OpenStudio::Model::AvailabilityManagerNightVentilation.new(model)
    ventilationTemperatureSchedule = OpenStudio::Model::ScheduleRuleset.new(model)
    ventilationTemperatureSchedule.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 18.0)
    avm.setVentilationTemperatureSchedule(ventilationTemperatureSchedule)
    if Gem::Version.new(OpenStudio.openStudioVersion) >= Gem::Version.new('2.3.1')
      system.setAvailabilityManagers([avm])
    else
      system.setAvailabilityManager(avm)
    end

  when 1
    avm = OpenStudio::Model::AvailabilityManagerOptimumStart.new(model)
    if Gem::Version.new(OpenStudio.openStudioVersion) >= Gem::Version.new('2.3.1')
      system.setAvailabilityManagers([avm])
    else
      system.setAvailabilityManager(avm)
    end

  when 2
    avm = OpenStudio::Model::AvailabilityManagerHybridVentilation.new(model)
    if Gem::Version.new(OpenStudio.openStudioVersion) >= Gem::Version.new('2.3.1')
      system.setAvailabilityManagers([avm])
    else
      system.setAvailabilityManager(avm)
    end

  when 3
    system.setNightCycleControlType('CycleOnAny')
  end
end

# Swap the coils so that the heating coil is before the DX to avoid frost
# conditions on the DX cooling coil
#      nmodel.getAirLoopHVACs.each do |a|
#      n  hc = a.supplyComponents("OS_Coil_Heating_Gas".to_IddObjectType)[0].to_CoilHeatingGas.get
#      n  m_node = a.mixedAirNode.get
#      n  hc.addToNode(m_node)
#      nend

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
