# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 2 stories, 100m X 50m, 2 zone building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 2,
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

def make_zone_hvac_cooler(z, direct_is_first: false)
  model = z.model
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
    indirect_evap = OpenStudio::Model::EvaporativeCoolerIndirectResearchSpecial.new(model)
    zoneHVACEvaporativeCoolerUnit.setSecondEvaporativeCooler(indirect_evap)
  else
    # And an explicit Ctor:
    # ZoneHVACEvaporativeCoolerUnit(const Model& model, Schedule& availabilitySchedule, HVACComponent& supplyAirFan, HVACComponent& firstEvaporativeCooler);
    supplyAirFan = OpenStudio::Model::FanSystemModel.new(model)

    indirect_evap = OpenStudio::Model::EvaporativeCoolerIndirectResearchSpecial.new(model)
    zoneHVACEvaporativeCoolerUnit = OpenStudio::Model::ZoneHVACEvaporativeCoolerUnit.new(
      model, model.alwaysOnDiscreteSchedule, supplyAirFan, indirect_evap
    )
    # An optional Second EvaporativeCooler
    direct_evap = OpenStudio::Model::EvaporativeCoolerDirectResearchSpecial.new(model, model.alwaysOnDiscreteSchedule)
    zoneHVACEvaporativeCoolerUnit.setSecondEvaporativeCooler(direct_evap)
  end
  indirect_evap.setName("#{z.nameString} Indirect Evaporative Cooler")
  direct_evap.setName("#{z.nameString} Direct Evaporative Cooler")
  supplyAirFan.setName("#{z.nameString} Supply Fan")
  zoneHVACEvaporativeCoolerUnit.setName("#{z.nameString} Zone Evap Unit")
  # zoneHVACEvaporativeCoolerUnit.resetSecondEvaporativeCooler
  #
  # Redoing what the default constructor does for demonstration purposes
  # zoneHVACEvaporativeCoolerUnit.setDesignSupplyAirFlowRate(1.0)
  zoneHVACEvaporativeCoolerUnit.autosizeDesignSupplyAirFlowRate
  zoneHVACEvaporativeCoolerUnit.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule)
  zoneHVACEvaporativeCoolerUnit.setSupplyAirFan(zoneHVACEvaporativeCoolerUnit.supplyAirFan)
  zoneHVACEvaporativeCoolerUnit.setFanPlacement('BlowThrough')
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

z1 = zones[0]
z1.setName("Direct First Zone")
make_zone_hvac_cooler(z1, direct_is_first: true)

# Mimic SMStore8 from StripMallZoneEvapCoolerAutosized.idf
# https://github.com/NREL/EnergyPlus/blob/31e3c33467c5873371bf48b12a7318215971c315/testfiles/StripMallZoneEvapCoolerAutosized.idf#L4767-L4784
z2 = zones[1]
z2.setName("Indirect First Zone")
make_zone_hvac_cooler(z2, direct_is_first: false)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
