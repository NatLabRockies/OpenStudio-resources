import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 01, PTAC, Residential
model.add_hvac(ashrae_sys_num="01")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# set convection coefficients
convectionCoefficients = openstudio.model.SurfacePropertyConvectionCoefficientsMultipleSurface(model)
convectionCoefficients.setSurfaceType("AllExteriorWalls")
convectionCoefficients.setConvectionCoefficient1Location("Inside")
convectionCoefficients.setConvectionCoefficient1Type("Value")
convectionCoefficients.setConvectionCoefficient1(1.0)
convectionCoefficients.setConvectionCoefficient2Location("Outside")
convectionCoefficients.setConvectionCoefficient2Type("Value")
convectionCoefficients.setConvectionCoefficient2(1.0)

# set SurfacePropertyOtherSideCoefficients
groundConditions = openstudio.model.SurfacePropertyOtherSideCoefficients(model)
groundConditions.setConstantTemperature(10.0)
groundConditions.setExternalDryBulbTemperatureCoefficient(0.0)
groundConditions.setGroundTemperatureCoefficient(0.0)
groundConditions.setWindSpeedCoefficient(0.0)
groundConditions.setZoneAirTemperatureCoefficient(0.0)
groundConditions.setSinusoidalVariationofConstantTemperatureCoefficient(False)

# set SurfacePropertyOtherSideConditionsModel
roofConditions = openstudio.model.SurfacePropertyOtherSideConditionsModel(model)
print(f"initial type of modeling is {roofConditions.typeOfModeling()}.")
roofConditions.setTypeOfModeling("UndergroundPipingSystemSurface")
print(f"final type of modeling is {roofConditions.typeOfModeling()}.")

# Get spaces, ordered by name to ensure consistency
spaces = sorted(model.getSpaces(), key=lambda s: s.nameString())

# have to do this because other side coefficient surfaces do not inherit constructions?
[x.hardApplyConstructions() for x in spaces]

# change boundary conditions for ground and roofs
for surface in model.getSurfaces():
    if surface.outsideBoundaryCondition() == "Ground":
        surface.setSurfacePropertyOtherSideCoefficients(groundConditions)  # this change the boundary condition
    elif (surface.outsideBoundaryCondition() == "Outdoors") and (surface.surfaceType() == "RoofCeiling"):
        surface.setSurfacePropertyOtherSideConditionsModel(roofConditions)  # this change the boundary condition


# add output reports
add_out_vars = False
if add_out_vars:
    openstudio.model.OutputVariable("Surface Inside Face Temperature", model)
    openstudio.model.OutputVariable("Surface Outside Face Temperature", model)
    openstudio.model.OutputVariable("Surface Inside Face Convection Heat Transfer Coefficient", model)
    openstudio.model.OutputVariable("Surface Outside Face Convection Heat Transfer Coefficient", model)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
