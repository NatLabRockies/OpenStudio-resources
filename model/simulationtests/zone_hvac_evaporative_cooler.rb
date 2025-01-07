# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add ASHRAE System type 03, PSZ-AC
model.add_hvac({ 'ashrae_sys_num' => '03' })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })


# In order to produce more consistent results between different runs,
# we sort the zones by names
# (There's only one here, but just in case this would be copy pasted somewhere
# else...)
zones = model.getThermalZones.sort_by { |z| z.name.to_s }
z = zones[0]
air_system = z.airLoopHVAC.get

oa_node = air_system.airLoopHVACOutdoorAirSystem.get.outboardOANode.get

# Add ZoneHVACEvaporativeCoolerUnit
zoneHVACEvaporativeCoolerUnit = OpenStudio::Model::ZoneHVACEvaporativeCoolerUnit.new(model)
direct_evap = zoneHVACEvaporativeCoolerUnit.firstEvaporativeCooler
direct_evap.addToNode(oa_node)
indirect_evap = OpenStudio::Model::EvaporativeCoolerIndirectResearchSpecial.new(model)
indirect_evap.addToNode(oa_node)
zoneHVACEvaporativeCoolerUnit.setSecondEvaporativeCooler(indirect_evap)
zoneHVACEvaporativeCoolerUnit.addToThermalZone(z)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
