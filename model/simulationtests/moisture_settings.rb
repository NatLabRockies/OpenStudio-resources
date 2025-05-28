# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

heat_balance_algorithm = model.getHeatBalanceAlgorithm
heat_balance_algorithm.setAlgorithm('MoisturePenetrationDepthConductionTransferFunction')

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 2,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 1,
                     'perimeter_zone_depth' => 3 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add ASHRAE System type 01, PTAC, Residential
model.add_hvac({ 'ashrae_sys_num' => '01' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 24,
                        'cooling_setpoint' => 28 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# assign material property moisture penetration depth settings to walls
model.getSurfaces.each do |surface|
  next unless surface.surfaceType.downcase == 'wall'

  surface.construction.get.to_Construction.get.layers.each do |layer|
    std_mat_ = layer.to_StandardOpaqueMaterial
    next unless std_mat_.is_initialized

    std_mat_.get.createMaterialPropertyMoisturePenetrationDepthSettings(8.9, 0.0069, 0.9066, 0.0404, 22.1121, 0.005, 140) # drywall
  end
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd, 'osm_name' => 'in.osm' })
