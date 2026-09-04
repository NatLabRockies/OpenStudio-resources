# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
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

# In order to produce more consistent results between different runs,
# we sort the zones by names
thermal_zones = model.getThermalZones.sort_by { |z| z.name.to_s }
# assign mrt weighting factors to all people in a single thermal zone
thermal_zone = thermal_zones[0]

# create the zone property user view factors by surface name object
zonemrtcalc = thermal_zone.getZoneMRTCalculation

# get all spaces in the zone
spaces = thermal_zone.spaces.sort_by { |s| s.name.to_s }

# create thermal comfort schedules
workeffsch = OpenStudio::Model::ScheduleConstant.new(model)
workeffsch.setValue(0.5)
cloinssch = OpenStudio::Model::ScheduleConstant.new(model)
cloinssch.setValue(0.5)
airvelsch = OpenStudio::Model::ScheduleConstant.new(model)
airvelsch.setValue(0.5)

# get all people in the zone
peoples = []
spaces.each do |space|
  definition1 = OpenStudio::Model::PeopleDefinition.new(model)
  definition1.setNumberofPeople(1.0)
  definition1.setMeanRadiantTemperatureCalculationType("EnclosureAveraged")
  definition1.setThermalComfortModelType(0, "Fanger")

  people1 = OpenStudio::Model::People.new(definition1)
  people1.setWorkEfficiencySchedule(workeffsch)
  people1.setClothingInsulationSchedule(cloinssch)
  people1.setAirVelocitySchedule(airvelsch)
  people1.setSpace(space)
  peoples << people1

  definition2 = OpenStudio::Model::PeopleDefinition.new(model)
  definition2.setNumberofPeople(1.0)
  definition2.setMeanRadiantTemperatureCalculationType("EnclosureAveraged") # SurfaceWeighted, AngleFactor not supported?
  definition2.setThermalComfortModelType(0, "Pierce")

  people2 = OpenStudio::Model::People.new(definition2)
  people2.setWorkEfficiencySchedule(workeffsch)
  people2.setClothingInsulationSchedule(cloinssch)
  people2.setAirVelocitySchedule(airvelsch)
  people2.setSpace(space)
  peoples << people2
end

# mrt weighting factors for people
peoples = peoples.uniq.sort_by { |p| p.name.to_s }
peoples.each do |people|
  zonemrtcalc.addMRTWeightingFactor(people, 1.0 / peoples.size)
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
