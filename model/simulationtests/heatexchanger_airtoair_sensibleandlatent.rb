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

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# add ASHRAE System type 03, PSZ-AC
model.add_hvac({ 'ashrae_sys_num' => '03' })

air_systems = model.getAirLoopHVACs

air_systems.each do |s|
  oa_node = s.airLoopHVACOutdoorAirSystem.get.outboardOANode.get

  hx = OpenStudio::Model::HeatExchangerAirToAirSensibleAndLatent.new(model)
  if Gem::Version.new(OpenStudio.openStudioVersion) >= Gem::Version.new('3.8.0')
    hx.assignHistoricalEffectivenessCurves
  end

  hx.addToNode(oa_node)

  spm = OpenStudio::Model::SetpointManagerMixedAir.new(model)

  outlet_node = hx.primaryAirOutletModelObject.get.to_Node.get

  spm.addToNode(outlet_node)
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
