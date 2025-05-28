import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 03, PSZ-AC
# model.add_hvac({"ashrae_sys_num" => '03'})

# add ASHRAE System type 08, VAV w/ PFP Boxes
# DLM: this invokes weird mass conservation rules with VAV
# model.add_hvac({"ashrae_sys_num" => '08'})

# add thermostats
# model.add_thermostats({"heating_setpoint" => 24, "cooling_setpoint" => 28})

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# make interior walls air walls
air_wall = None
if openstudio.VersionString(openstudio.openStudioVersion()) > openstudio.VersionString("3.4.0"):
    air_wall = model.getConstructionAirBoundarys()[0]
else:
    for c in model.getConstructions():
        if c.nameString() == "Air_Wall":
            air_wall = c
            break


if air_wall is None:
    raise ValueError("Could not find an AirWall / ConstructionAirBoundary construction")

model.getBuilding().defaultConstructionSet().get().defaultInteriorSurfaceConstructions().get().setWallConstruction(
    air_wall
)

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# remove all infiltration
[x.remove() for x in model.getSpaceInfiltrationDesignFlowRates()]

# add zone mixing between all air walls
for s in model.getSurfaces():
    if s.construction().get().nameString() == "Air_Wall":
        a = s.adjacentSurface().get()
        zone1 = s.space().get().thermalZone().get()
        zone2 = a.space().get().thermalZone().get()
        m = openstudio.model.ZoneMixing(zone1)
        m.setSourceZone(zone2)
        m.setAirChangesperHour(0.5)  # this is based on the receiving zone volume, will not be equal mixing
        m.setDeltaTemperature(0.0)

        infil = openstudio.model.SpaceInfiltrationDesignFlowRate(model)
        infil.setSpace(s.space().get())
        infil.setSchedule(model.alwaysOnContinuousSchedule())
        infil.setDesignFlowRate(0.0)


# conserve some mass
zamfc = model.getZoneAirMassFlowConservation()
zamfc.setAdjustZoneMixingForZoneAirMassFlowBalance(True)
if openstudio.VersionString(openstudio.openStudioVersion()) <= openstudio.VersionString("3.4.0"):
    # Does nothing as of 1.9.3, removed after 3.4.0
    zamfc.setSourceZoneInfiltrationTreatment("AdjustInfiltrationFlow")


# add design days to the model (Chicago)
model.add_design_days()

# add output reports
add_out_vars = False
if add_out_vars:
    openstudio.model.OutputVariable("Zone Infiltration Current Density Volume Flow Rate", model)
    openstudio.model.OutputVariable("Zone Infiltration Standard Density Volume Flow Rate", model)
    openstudio.model.OutputVariable("Zone Infiltration Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Infiltration Air Change Rate", model)
    openstudio.model.OutputVariable("Zone Mixing Volume", model)
    openstudio.model.OutputVariable("Zone Mixing Current Density Air Volume Flow Rate", model)
    openstudio.model.OutputVariable("Zone Mixing Standard Density Air Volume Flow Rate", model)
    openstudio.model.OutputVariable("Zone Mixing Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Supply Air Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Exhaust Air Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Return Air Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Mixing Receiving Air Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Mixing Source Air Mass Flow Rate", model)
    openstudio.model.OutputVariable("Zone Infiltration Air Mass Flow Balance Status", model)
    openstudio.model.OutputVariable("Zone Mass Balance Infiltration Air Mass Flow Rate", model)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
