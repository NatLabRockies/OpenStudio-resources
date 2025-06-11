# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

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

check_all = false # requires that you have a folder of epw files at weatherdata/EPW
if check_all

  weather_files = Dir.glob('../../weatherdata/EPW/*.epw')
  weather_files.each do |weather_file|
    epw_file = OpenStudio::EpwFile.new(weather_file)
    epw_design_conditions = epw_file.designConditions
    puts "#{File.basename(weather_file)}: success"
  rescue StandardError
    puts "#{File.basename(weather_file)}: FAILURE"
  end

else

  ['../../weatherdata/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'].each do |weather_file|
    epw_file = OpenStudio::EpwFile.new(weather_file)
    epw_design_conditions = epw_file.designConditions
    epw_design_condition = epw_design_conditions[0]

    unit = OpenStudio::Model::BuildingUnit.new(model)
    unit.setName(File.basename(weather_file).to_s)
    unit.setFeature('Title of Design Condition', epw_design_condition.titleOfDesignCondition)
    ['Heating Coldest Month', 'Heating Coldest Month Wind Speed 1%', 'Cooling Dry Bulb 0.4%', 'Cooling Enthalpy Mean Coincident Dry Bulb 1%'].each do |field|
      unit.setFeature(field.to_s, epw_design_condition.getFieldByName(field.to_s).get)
    end
  end

end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd, 'osm_name' => 'in.osm' })
