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

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 19,
                        'cooling_setpoint' => 26 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# In order to produce more consistent results between different runs,
# we sort the spaces by names
spaces = model.getSpaces.sort_by { |s| s.name.to_s }

# Collapse all spaces into one thermal zone
thermal_zone = spaces[0].thermalZone.get
spaces.each do |space|
  z = space.thermalZone.get
  space.setThermalZone(thermal_zone)
  z.remove if z != thermal_zone
end
thermal_zone.setName('5 spaces zone')
raise if model.getThermalZones.size != 1
raise if thermal_zone.spaces.size != spaces.size

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# create thermal comfort schedules
workeffsch = OpenStudio::Model::ScheduleConstant.new(model)
workeffsch.setValue(0.5)
cloinssch = OpenStudio::Model::ScheduleConstant.new(model)
cloinssch.setValue(0.5)
airvelsch = OpenStudio::Model::ScheduleConstant.new(model)
airvelsch.setValue(0.5)

spaces.each do |space|
  surfaces = []
  sub_surfaces = []
  space.surfaces.each do |surface|
    surfaces << surface
    surface.subSurfaces.each do |sub_surface|
      sub_surfaces << sub_surface
    end
  end

  surfaces = surfaces.uniq.sort_by { |s| s.name.to_s }
  sub_surfaces = sub_surfaces.uniq.sort_by { |s| s.name.to_s }

  comfortview = OpenStudio::Model::ComfortViewFactorAngles.new(model)
  (surfaces + sub_surfaces).each do |surface|
    comfortview.addAngleFactor(surface, 1.0 / (surfaces.size + sub_surfaces.size))
  end

  definition1 = OpenStudio::Model::PeopleDefinition.new(model)
  definition1.setNumberofPeople(1.0)
  definition1.setMeanRadiantTemperatureCalculationType('SurfaceWeighted')
  definition1.setSurfaceNameAngleFactorListName(surfaces[0])
  definition1.setThermalComfortModelType(0, 'Fanger')

  people1 = OpenStudio::Model::People.new(definition1)
  people1.setWorkEfficiencySchedule(workeffsch)
  people1.setClothingInsulationSchedule(cloinssch)
  people1.setAirVelocitySchedule(airvelsch)
  people1.setSpace(space)

  definition2 = OpenStudio::Model::PeopleDefinition.new(model)
  definition2.setNumberofPeople(1.0)
  definition2.setMeanRadiantTemperatureCalculationType('AngleFactor')
  definition2.setSurfaceNameAngleFactorListName(comfortview)
  definition2.setThermalComfortModelType(0, 'Pierce')

  people2 = OpenStudio::Model::People.new(definition2)
  people2.setWorkEfficiencySchedule(workeffsch)
  people2.setClothingInsulationSchedule(cloinssch)
  people2.setAirVelocitySchedule(airvelsch)
  people2.setSpace(space)
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
