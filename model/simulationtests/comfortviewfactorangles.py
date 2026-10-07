import openstudio
from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=19, cooling_setpoint=26)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# In order to produce more consistent results between different runs,
# we sort the spaces by names
spaces = sorted(model.getSpaces(), key=lambda space: space.nameString())

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# create thermal comfort schedules
workeffsch = openstudio.model.ScheduleConstant(model)
workeffsch.setName("Work Efficiency Schedule")
workeffsch.setValue(0.2)

# Trousers, long-sleeve shirt: 0.61 clo
cloinssch = openstudio.model.ScheduleConstant(model)
cloinssch.setName("Clothing Insulation Schedule")
cloinssch.setValue(0.61)

airvelsch = openstudio.model.ScheduleConstant(model)
airvelsch.setName("Air Velocity Schedule")
airvelsch.setValue(0.2)

# Office activity, typing: 117 W/person
actsch = openstudio.model.ScheduleConstant(model)
actsch.setName("Activity Level Schedule")
actsch.setValue(117.0)

# get a construction for internal mass object
constrset = model.getBuilding().defaultConstructionSet().get()
intpartconstr = constrset.interiorPartitionConstruction().get()

for space in spaces:
    intmassdef = openstudio.model.InternalMassDefinition(model)
    intmassdef.setSurfaceArea(50.0)
    intmassdef.setConstruction(intpartconstr)
    intmass = openstudio.model.InternalMass(intmassdef)
    intmass.setSpace(space)

    surfaces = []
    sub_surfaces = []
    for surface in space.surfaces():
        surfaces.append(surface)
        for sub_surface in surface.subSurfaces():
            sub_surfaces.append(sub_surface)
    int_masss = []
    for int_mass in space.internalMass():
        int_masss.append(int_mass)

    surfaces = sorted(surfaces, key=lambda surface: surface.nameString())
    sub_surfaces = sorted(sub_surfaces, key=lambda sub_surface: sub_surface.nameString())
    int_masss = sorted(int_masss, key=lambda int_mass: int_mass.nameString())

    comfortview = openstudio.model.ComfortViewFactorAngles(model)
    for surface in surfaces + sub_surfaces + int_masss:
        comfortview.addAngleFactor(surface, 1.0 / (len(surfaces) + len(sub_surfaces) + len(int_masss)))

    definition1 = openstudio.model.PeopleDefinition(model)
    definition1.setNumberofPeople(1.0)
    definition1.setMeanRadiantTemperatureCalculationType("SurfaceWeighted")
    definition1.setThermalComfortModelType(0, "Fanger")

    people1 = openstudio.model.People(definition1)
    people1.setWorkEfficiencySchedule(workeffsch)
    people1.setClothingInsulationSchedule(cloinssch)
    people1.setAirVelocitySchedule(airvelsch)
    people1.setActivityLevelSchedule(actsch)
    people1.setSurfaceNameAngleFactorListName(surfaces[0])
    people1.setSpace(space)

    definition2 = openstudio.model.PeopleDefinition(model)
    definition2.setNumberofPeople(1.0)
    definition2.setMeanRadiantTemperatureCalculationType("SurfaceWeighted")
    definition2.setThermalComfortModelType(0, "Fanger")

    people2 = openstudio.model.People(definition2)
    people2.setWorkEfficiencySchedule(workeffsch)
    people2.setClothingInsulationSchedule(cloinssch)
    people2.setAirVelocitySchedule(airvelsch)
    people2.setActivityLevelSchedule(actsch)
    people2.setSurfaceNameAngleFactorListName(sub_surfaces[0])
    people2.setSpace(space)

    definition3 = openstudio.model.PeopleDefinition(model)
    definition3.setNumberofPeople(1.0)
    definition3.setMeanRadiantTemperatureCalculationType("SurfaceWeighted")
    definition3.setThermalComfortModelType(0, "Fanger")

    people3 = openstudio.model.People(definition3)
    people3.setWorkEfficiencySchedule(workeffsch)
    people3.setClothingInsulationSchedule(cloinssch)
    people3.setAirVelocitySchedule(airvelsch)
    people3.setActivityLevelSchedule(actsch)
    people3.setSurfaceNameAngleFactorListName(int_masss[0])
    people3.setSpace(space)

    definition4 = openstudio.model.PeopleDefinition(model)
    definition4.setNumberofPeople(1.0)
    definition4.setMeanRadiantTemperatureCalculationType("AngleFactor")
    definition4.setThermalComfortModelType(0, "Pierce")

    people4 = openstudio.model.People(definition4)
    people4.setWorkEfficiencySchedule(workeffsch)
    people4.setClothingInsulationSchedule(cloinssch)
    people4.setAirVelocitySchedule(airvelsch)
    people4.setActivityLevelSchedule(actsch)
    people4.setSurfaceNameAngleFactorListName(comfortview)
    people4.setSpace(space)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")