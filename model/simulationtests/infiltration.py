# This test aims to test the new 'Adiabatic Surface Construction Name' field
# added in the OS:DefaultConstructionSet

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 5 zone building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=3)

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

# remove all infiltration
[x.remove() for x in model.getSpaceInfiltrationDesignFlowRates()]

infilSch = openstudio.model.ScheduleRuleset(model, 1)
infilSch.setName("Infiltration Schedule")

# In order to produce more consistent results between different runs,
# we sort the spaces by names
spaces = sorted(model.getSpaces(), key=lambda s: s.nameString())
spaces = [s for s in spaces if "core" not in s.nameString().lower()]

for i, space in enumerate(spaces):
    if i == 0:
        infil = openstudio.model.SpaceInfiltrationDesignFlowRate(model)
        infil.setSpace(space)
        infil.setSchedule(infilSch)

        # Use one of these, it will set the "Design Flow Rate Calculation Method"
        # infil.setDesignFlowRate(0.1)
        # infil.setFlowperSpaceFloorArea(0.02)
        # infil.setFlowperExteriorSurfaceArea(0.01)
        # infil.setFlowperExteriorWallArea(0.01);
        infil.setAirChangesperHour(0.8)

        infil.setConstantTermCoefficient(1.0)
        infil.setTemperatureTermCoefficient(0.0)
        infil.setVelocityTermCoefficient(0.0)
        infil.setVelocitySquaredTermCoefficient(0.0)

    elif i == 1:
        infil = openstudio.model.SpaceInfiltrationEffectiveLeakageArea(model)
        infil.setSpace(space)
        infil.setSchedule(infilSch)
        infil.setEffectiveAirLeakageArea(0.1)
        infil.setStackCoefficient(0.1)
        infil.setWindCoefficient(0.1)

    elif i == 2:
        infil = openstudio.model.SpaceInfiltrationFlowCoefficient(model)
        infil.setSpace(space)
        infil.setSchedule(infilSch)
        infil.setFlowCoefficient(0.02)
        infil.setStackCoefficient(0.05)
        infil.setPressureExponent(0.67)
        infil.setWindCoefficient(0.12)
        infil.setShelterFactor(0.5)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
