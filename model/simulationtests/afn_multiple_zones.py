import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 2 zone building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 08, VAV w/ PFP Boxes
# DLM: this invokes weird mass conservation rules with VAV
# model.add_hvac({"ashrae_sys_num" => '08'})

# add thermostats
# model.add_thermostats({"heating_setpoint" => 24, "cooling_setpoint" => 28})

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# remove all infiltration
[x.remove() for x in model.getSpaceInfiltrationDesignFlowRates()]

# add design days to the model (Chicago)
model.add_design_days()

# add simulation control
afn_control = model.getAirflowNetworkSimulationControl()
afn_control.setAirflowNetworkControl("MultizoneWithoutDistribution")

zones = model.getThermalZones()

surfaces = []
adjacent_surfaces = []
sub_surfaces = []

spaces = list(zones[0].spaces()) + list(zones[1].spaces())
for space in spaces:
    for surface in space.surfaces():
        if surface.outsideBoundaryCondition().startswith("Outdoors") and surface.surfaceType().startswith("Wall"):
            surfaces.append(surface)
        elif surface.adjacentSurface().is_initialized():
            adjacent_surfaces.append(surface)

    for surface in space.surfaces():
        for sub_surface in surface.subSurfaces():
            sub_surfaces.append(sub_surface)


# In order to produce more consistent results between different runs,
# we sort the objects by names
surfaces = sorted(surfaces, key=lambda s: s.nameString())
adjacent_surfaces = sorted(adjacent_surfaces, key=lambda s: s.nameString())
sub_surfaces = sorted(sub_surfaces, key=lambda ss: ss.nameString())

# make afn zones
afnzone1 = zones[0].getAirflowNetworkZone()
afnzone1.setMinimumVentingOpenFactor(0.1)
afnzone2 = zones[1].getAirflowNetworkZone()
afnzone2.setMinimumVentingOpenFactor(0.2)

# Simple Opening
simpleOpening = openstudio.model.AirflowNetworkSimpleOpening(model, 1.0, 0.65, 0.5, 0.5)
afnsurf1 = sub_surfaces[0].getAirflowNetworkSurface(simpleOpening)
afnsurf1.setWindowDoorOpeningFactorOrCrackFactor(0.1)

# Detailed Opening
data = openstudio.model.DetailedOpeningFactorDataVector()
data.append(openstudio.model.DetailedOpeningFactorData(0.0, 0.01, 0.0, 0.0, 0.0))
data.append(openstudio.model.DetailedOpeningFactorData(1.0, 0.5, 1.0, 1.0, 0.0))
detailedOpening = openstudio.model.AirflowNetworkDetailedOpening(model, 1.0, data)
afnsurf2 = sub_surfaces[1].getAirflowNetworkSurface(detailedOpening)
afnsurf2.setWindowDoorOpeningFactorOrCrackFactor(0.2)

# Horizontal Opening
adjacent_surface = adjacent_surfaces[0]

p = openstudio.Point3dVector()
p.append(openstudio.Point3d(0, 0, 0))
p.append(openstudio.Point3d(1, 0, 0))
p.append(openstudio.Point3d(1, 1, 0))
p.append(openstudio.Point3d(0, 1, 0))
sub_surface = openstudio.model.SubSurface(p, model)
sub_surface.setSurface(adjacent_surface)
sub_surface.setSubSurfaceType("Door")

adjacent_sub_surface = openstudio.model.SubSurface(list(reversed(sub_surface.vertices())), model)
adjacent_sub_surface.setSurface(adjacent_surface.adjacentSurface().get())
adjacent_sub_surface.setSubSurfaceType("Door")
sub_surface.setAdjacentSubSurface(adjacent_sub_surface)

horizontalOpening = openstudio.model.AirflowNetworkHorizontalOpening(model, 0.5, 0.65, 90.0, 0.5)
horizontalOpeningSurface = sub_surface
horizontalOpeningSurface.getAirflowNetworkSurface(horizontalOpening)

# Effective Leakage Area
effectiveLeakageArea = openstudio.model.AirflowNetworkEffectiveLeakageArea(model, 1.0, 1.0, 4.0, 0.65)
surfaces[0].getAirflowNetworkSurface(effectiveLeakageArea)
effectiveLeakageArea = openstudio.model.AirflowNetworkEffectiveLeakageArea(model, 2.0, 1.0, 4.0, 0.65)
surfaces[4].getAirflowNetworkSurface(effectiveLeakageArea)

# Specified Flow Rate
specifiedFlowRate = openstudio.model.AirflowNetworkSpecifiedFlowRate(model, 10.0)
surfaces[1].getAirflowNetworkSurface(specifiedFlowRate)

# add output reports
add_out_vars = False
if add_out_vars:
    openstudio.model.OutputVariable("AFN Node Temperature", model)
    openstudio.model.OutputVariable("AFN Node Wind Pressure", model)
    openstudio.model.OutputVariable("AFN Linkage Node 1 to Node 2 Mass Flow Rate", model)
    openstudio.model.OutputVariable("AFN Linkage Node 1 to Node 2 Pressure Difference", model)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
