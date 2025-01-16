# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 8 stories, 100m X 50m, 8 zone building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 8,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

def make_zone_hvac_cooler(z, direct_is_first: false, add_secondary: true, fan_placement: 'BlowThrough')
  model = z.model
  indirect_evap = nil
  direct_evap = nil
  if direct_is_first
    # There is a default ctor
    zoneHVACEvaporativeCoolerUnit = OpenStudio::Model::ZoneHVACEvaporativeCoolerUnit.new(model)
    direct_evap = zoneHVACEvaporativeCoolerUnit.firstEvaporativeCooler
    supplyAirFan = zoneHVACEvaporativeCoolerUnit.supplyAirFan

    fan_system = OpenStudio::Model::FanSystemModel.new(model)
    zoneHVACEvaporativeCoolerUnit.setSupplyAirFan(fan_system)
    supplyAirFan.remove
    supplyAirFan = fan_system
    # An optional Second EvaporativeCooler
    if add_secondary
      indirect_evap = OpenStudio::Model::EvaporativeCoolerIndirectResearchSpecial.new(model)
      zoneHVACEvaporativeCoolerUnit.setSecondEvaporativeCooler(indirect_evap)
    end
  else
    # And an explicit Ctor:
    # ZoneHVACEvaporativeCoolerUnit(const Model& model, Schedule& availabilitySchedule, HVACComponent& supplyAirFan, HVACComponent& firstEvaporativeCooler);
    supplyAirFan = OpenStudio::Model::FanSystemModel.new(model)

    indirect_evap = OpenStudio::Model::EvaporativeCoolerIndirectResearchSpecial.new(model)
    zoneHVACEvaporativeCoolerUnit = OpenStudio::Model::ZoneHVACEvaporativeCoolerUnit.new(
      model, model.alwaysOnDiscreteSchedule, supplyAirFan, indirect_evap
    )
    # An optional Second EvaporativeCooler
    if add_secondary
      direct_evap = OpenStudio::Model::EvaporativeCoolerDirectResearchSpecial.new(model, model.alwaysOnDiscreteSchedule)
      zoneHVACEvaporativeCoolerUnit.setSecondEvaporativeCooler(direct_evap)
    end
  end
  indirect_evap.setName("#{z.nameString} Indirect Evaporative Cooler") unless indirect_evap.nil?
  direct_evap.setName("#{z.nameString} Direct Evaporative Cooler") unless direct_evap.nil?
  supplyAirFan.setName("#{z.nameString} Supply Fan")
  zoneHVACEvaporativeCoolerUnit.setName("#{z.nameString} Evap Unit")
  # zoneHVACEvaporativeCoolerUnit.resetSecondEvaporativeCooler
  #
  # Redoing what the default constructor does for demonstration purposes
  # zoneHVACEvaporativeCoolerUnit.setDesignSupplyAirFlowRate(1.0)
  zoneHVACEvaporativeCoolerUnit.autosizeDesignSupplyAirFlowRate
  zoneHVACEvaporativeCoolerUnit.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule)
  zoneHVACEvaporativeCoolerUnit.setSupplyAirFan(zoneHVACEvaporativeCoolerUnit.supplyAirFan)
  zoneHVACEvaporativeCoolerUnit.setFanPlacement(fan_placement)
  zoneHVACEvaporativeCoolerUnit.setCoolerUnitControlMethod('ZoneCoolingLoadVariableSpeedFan')
  zoneHVACEvaporativeCoolerUnit.setThrottlingRangeTemperatureDifference(1.1)
  zoneHVACEvaporativeCoolerUnit.setCoolingLoadControlThresholdHeatTransferRate(100.0)
  zoneHVACEvaporativeCoolerUnit.setShutOffRelativeHumidity(100.0)

  # Add it to a ThermalZone
  zoneHVACEvaporativeCoolerUnit.addToThermalZone(z)

  # Rename nodes for clarity
  z.zoneAirNode.setName("#{z.nameString} Zone Air Node")
  # z.returnAirModelObjects.modelObjects[0].setName("#{z.nameString} Zone Return Air Node")
  z.inletPortList.modelObjects[0].setName("#{z.nameString} Zone Air Inlet Node")
  z.exhaustPortList.modelObjects[0].setName("#{z.nameString} Zone Air Exhaust Node")
end


# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = model.getThermalZones.sort_by { |z| z.name.to_s }

configs = [
  {zone_name: "DirectFirst", direct_is_first: true, add_secondary: true},

  # Mimic SMStore8 from StripMallZoneEvapCoolerAutosized.idf
  # https://github.com/NREL/EnergyPlus/blob/31e3c33467c5873371bf48b12a7318215971c315/testfiles/StripMallZoneEvapCoolerAutosized.idf#L4767-L4784
  {zone_name: "IndirectFirst", direct_is_first: false, add_secondary: true},

  {zone_name: "DirectOnly", direct_is_first: true, add_secondary: false},

  {zone_name: "IndirectOnly", direct_is_first: false, add_secondary: false},
]
fan_placements = ["BlowThrough", "DrawThrough"]
raise "Mismatch" unless configs.size * fan_placements.size == zones.size

configs.product(fan_placements).zip(zones).each do |(config, fan_placement), z|
  z.setName("#{config[:zone_name]} #{fan_placement} Zn")
  make_zone_hvac_cooler(
    z,
    direct_is_first: config[:direct_is_first],
    add_secondary: config[:add_secondary],
    fan_placement: fan_placement
  )
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
