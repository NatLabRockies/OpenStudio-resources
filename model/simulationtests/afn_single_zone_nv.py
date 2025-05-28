import openstudio

from lib.baseline_model import BaselineModel
from lib.surface_visitor import SurfaceVisitor


class SurfaceNetworkBuilder(SurfaceVisitor):
    def __init__(self, model):
        refcond = openstudio.model.AirflowNetworkReferenceCrackConditions(model, 20.0, 101325.0, 0.0)
        self.interiorCrack = openstudio.model.AirflowNetworkCrack(model, 0.050, 0.65, refcond)
        self.exteriorCrack = openstudio.model.AirflowNetworkCrack(model, 0.025, 0.65, refcond)
        super().__init__(model)

    def interiorFloor(self, model, surface, adjacentSurface):
        if surface.outsideBoundaryCondition().startswith("Ground"):
            return

        # Create a surface linkage
        link = surface.getAirflowNetworkSurface(self.interiorCrack)

    def interiorRoofCeiling(self, model, surface, adjacentSurface):
        # Create a surface linkage
        link = surface.getAirflowNetworkSurface(self.interiorCrack)

    def interiorWall(self, model, surface, adjacentSurface):
        # Create a surface linkage
        link = surface.getAirflowNetworkSurface(self.interiorCrack)

    def exteriorSurface(self, model, surface):
        # Create an external node?
        if surface.outsideBoundaryCondition().startswith("Ground"):
            return

        # Create a surface linkage
        link = surface.getAirflowNetworkSurface(self.exteriorCrack)


model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 03, PSZ-AC
# model.add_hvac({"ashrae_sys_num" => '03'})

zone = model.getThermalZones()[0]  # There should only be one...

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

# In order to produce more consistent results between different runs,
# we sort the zones by names
# It doesn't matter here since there's only ony, but just in case
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# make an afn zone
zone = zones[0]  # There should only be one...
afnzone = zone.getAirflowNetworkZone()

# Connect up envelope
visitor = SurfaceNetworkBuilder(model)

# add output reports
add_out_vars = False
if add_out_vars:
    openstudio.model.OutputVariable("AFN Node Temperature", model)
    openstudio.model.OutputVariable("AFN Node Wind Pressure", model)
    openstudio.model.OutputVariable("AFN Linkage Node 1 to Node 2 Mass Flow Rate", model)
    openstudio.model.OutputVariable("AFN Linkage Node 1 to Node 2 Pressure Difference", model)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
