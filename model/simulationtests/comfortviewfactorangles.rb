# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 1 zone core/perimeter building
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

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# create thermal comfort schedules
workeffsch = OpenStudio::Model::ScheduleConstant.new(model)
workeffsch.setName("Work Efficiency Schedule")
workeffsch.setValue(0.2)

# Trousers, long-sleeve shirt: 0.61 clo
cloinssch = OpenStudio::Model::ScheduleConstant.new(model)
cloinssch.setName("Clothing Insulation Schedule")
cloinssch.setValue(0.61)

airvelsch = OpenStudio::Model::ScheduleConstant.new(model)
airvelsch.setName("Air Velocity Schedule")
airvelsch.setValue(0.2)

# Office activity, typing: 117 W/person
actsch = OpenStudio::Model::ScheduleConstant.new(model)
actsch.setName("Activity Level Schedule")
actsch.setValue(117.0)

# get a construction for internal mass object
constrset = model.getBuilding.defaultConstructionSet.get
intpartconstr = constrset.interiorPartitionConstruction.get

spaces.each do |space|
  intmassdef = OpenStudio::Model::InternalMassDefinition.new(model)
  intmassdef.setSurfaceArea(50.0)
  intmassdef.setConstruction(intpartconstr)
  intmass = OpenStudio::Model::InternalMass.new(intmassdef)
  intmass.setSpace(space)

  surfaces = []
  sub_surfaces = []
  space.surfaces.each do |surface|
    surfaces << surface
    surface.subSurfaces.each do |sub_surface|
      sub_surfaces << sub_surface
    end
  end
  int_masss = []
  space.internalMass.each do |int_mass|
    int_masss << int_mass
  end

  surfaces = surfaces.uniq.sort_by { |s| s.name.to_s }
  sub_surfaces = sub_surfaces.uniq.sort_by { |ss| ss.name.to_s }
  int_masss = int_masss.uniq.sort_by { |i| i.name.to_s }

  comfortview = OpenStudio::Model::ComfortViewFactorAngles.new(model)
  (surfaces + sub_surfaces + int_masss).each do |surface|
    comfortview.addAngleFactor(surface, 1.0 / (surfaces.size + sub_surfaces.size + int_masss.size))
  end

  definition1 = OpenStudio::Model::PeopleDefinition.new(model)
  definition1.setNumberofPeople(1.0)
  definition1.setMeanRadiantTemperatureCalculationType('SurfaceWeighted')
  definition1.setThermalComfortModelType(0, 'Fanger')

  people1 = OpenStudio::Model::People.new(definition1)
  people1.setWorkEfficiencySchedule(workeffsch)
  people1.setClothingInsulationSchedule(cloinssch)
  people1.setAirVelocitySchedule(airvelsch)
  people1.setActivityLevelSchedule(actsch)
  people1.setSurfaceNameAngleFactorListName(surfaces[0])
  people1.setSpace(space)

  definition2 = OpenStudio::Model::PeopleDefinition.new(model)
  definition2.setNumberofPeople(1.0)
  definition2.setMeanRadiantTemperatureCalculationType('SurfaceWeighted')
  definition2.setThermalComfortModelType(0, 'Fanger')

  people2 = OpenStudio::Model::People.new(definition2)
  people2.setWorkEfficiencySchedule(workeffsch)
  people2.setClothingInsulationSchedule(cloinssch)
  people2.setAirVelocitySchedule(airvelsch)
  people2.setActivityLevelSchedule(actsch)
  people2.setSurfaceNameAngleFactorListName(sub_surfaces[0])
  people2.setSpace(space)

  definition3 = OpenStudio::Model::PeopleDefinition.new(model)
  definition3.setNumberofPeople(1.0)
  definition3.setMeanRadiantTemperatureCalculationType('SurfaceWeighted')
  definition3.setThermalComfortModelType(0, 'Fanger')

  people3 = OpenStudio::Model::People.new(definition3)
  people3.setWorkEfficiencySchedule(workeffsch)
  people3.setClothingInsulationSchedule(cloinssch)
  people3.setAirVelocitySchedule(airvelsch)
  people3.setActivityLevelSchedule(actsch)
  people3.setSurfaceNameAngleFactorListName(int_masss[0])
  people3.setSpace(space)

  definition4 = OpenStudio::Model::PeopleDefinition.new(model)
  definition4.setNumberofPeople(1.0)
  definition4.setMeanRadiantTemperatureCalculationType('AngleFactor')
  definition4.setThermalComfortModelType(0, 'Pierce')

  people4 = OpenStudio::Model::People.new(definition4)
  people4.setWorkEfficiencySchedule(workeffsch)
  people4.setClothingInsulationSchedule(cloinssch)
  people4.setAirVelocitySchedule(airvelsch)
  people4.setActivityLevelSchedule(actsch)
  people4.setSurfaceNameAngleFactorListName(comfortview)
  people4.setSpace(space)
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
