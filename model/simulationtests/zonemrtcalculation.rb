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

# There are a number of preconditions you must meet:
# * All People objects should be assigned directly to a space,
# * All spaces should be assigned to the same Thermal Zone.
# The Sum of the MRT Weighting Factors for all People objects in the same Thermal Zone must be < 1.0
zonemrtcalc = thermal_zone.getZoneMRTCalculation

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
  definition1.setMeanRadiantTemperatureCalculationType('EnclosureAveraged')
  definition1.setThermalComfortModelType(0, 'Fanger')

  people1 = OpenStudio::Model::People.new(definition1)
  people1.setWorkEfficiencySchedule(workeffsch)
  people1.setClothingInsulationSchedule(cloinssch)
  people1.setAirVelocitySchedule(airvelsch)
  people1.setSpace(space)
  peoples << people1

  definition2 = OpenStudio::Model::PeopleDefinition.new(model)
  definition2.setNumberofPeople(1.0)
  definition2.setMeanRadiantTemperatureCalculationType('SurfaceWeighted')
  definition2.setSurfaceNameAngleFactorListName(surfaces[0])
  definition2.setThermalComfortModelType(0, 'Pierce')

  people2 = OpenStudio::Model::People.new(definition2)
  people2.setWorkEfficiencySchedule(workeffsch)
  people2.setClothingInsulationSchedule(cloinssch)
  people2.setAirVelocitySchedule(airvelsch)
  people2.setSpace(space)
  peoples << people2

  definition3 = OpenStudio::Model::PeopleDefinition.new(model)
  definition3.setNumberofPeople(1.0)
  definition3.setMeanRadiantTemperatureCalculationType('AngleFactor')
  definition3.setSurfaceNameAngleFactorListName(comfortview)
  definition3.setThermalComfortModelType(0, 'KSU')

  people3 = OpenStudio::Model::People.new(definition3)
  people3.setWorkEfficiencySchedule(workeffsch)
  people3.setClothingInsulationSchedule(cloinssch)
  people3.setAirVelocitySchedule(airvelsch)
  people3.setSpace(space)
  peoples << people3
end

# Extensible: MRT Weighting Factors for people

people_one_mrt_weighting_factor = 0.37
people_other_mrt_weighting_factor = (1 - people_one_mrt_weighting_factor) / (peoples.size - 1)
# people, mrt_weighting_factor
mrt_weighting_factor_infos = []
mrt_weighting_factor_infos << [peoples[0], people_one_mrt_weighting_factor]
peoples[1..-1].each do |people|
  mrt_weighting_factor_infos << [people, people_other_mrt_weighting_factor]
end
# # To add a group, you can use the convenience method
# bool addMRTWeightingFactor(const People&, double mRTWeightingFactor);
zonemrtcalc.addMRTWeightingFactor(mrt_weighting_factor_infos[0][0], mrt_weighting_factor_infos[0][1])

# This will in turn actually use the helper class MRTWeightingFactor
zonemrtcalc.addMRTWeightingFactor(OpenStudio::Model::MRTWeightingFactor.new(mrt_weighting_factor_infos[1][0], mrt_weighting_factor_infos[1][1]))

# NOTE: if you call addMRTWeightingFactor with a People object that is already in the list, it will update the
# MRTWeightingFactor value for that People object.

raise unless zonemrtcalc.numberofMRTWeightingFactors == 2
# This is a vector of MRTWeightingFactor
raise unless zonemrtcalc.mRTWeightingFactors.size == 2

raise unless zonemrtcalc.mRTWeightingFactorIndex(peoples[0]).get == 0
raise unless zonemrtcalc.mRTWeightingFactorIndex(peoples[1]).get == 1

first_mrt_group = zonemrtcalc.mRTWeightingFactors.first
# This returns an OptionalMRTWeightingFactor
first_mrt_group_ = zonemrtcalc.getMRTWeightingFactor(0)
raise unless first_mrt_group_.is_initialized
raise unless first_mrt_group.people == first_mrt_group_.get.people

zonemrtcalc.removeMRTWeightingFactor(0)
raise unless zonemrtcalc.numberofMRTWeightingFactors == 1
raise unless zonemrtcalc.numExtensibleGroups == 1
raise unless zonemrtcalc.mRTWeightingFactorIndex(peoples[1]).get == 0

zonemrtcalc.removeAllMRTWeightingFactors
raise unless zonemrtcalc.numberofMRTWeightingFactors == 0
raise unless zonemrtcalc.numExtensibleGroups == 0

# There is also a batch add
mrt_groups = mrt_weighting_factor_infos.map { |g| OpenStudio::Model::MRTWeightingFactor.new(g[0], g[1]) }
zonemrtcalc.addMRTWeightingFactors(mrt_groups)
raise unless zonemrtcalc.numberofMRTWeightingFactors == peoples.size

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
