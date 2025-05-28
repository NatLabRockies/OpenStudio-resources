# This test aims to test the new 'Adiabatic Surface Construction Name' field
# added in the OS:DefaultConstructionSet

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone building
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
# we sort the zones by names
# (There's only one here, but just in case this would be copy pasted somewhere
# else...)
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())
z = zones[0]
z.setUseIdealAirLoads(True)

# create a window property frame and divider
window_property = openstudio.model.WindowPropertyFrameAndDivider(model)
window_property.setFrameWidth(0.1)
# Careful: no default, E+ defaults to 0.0 in source code
window_property.setFrameConductance(2.33)

# All these are just the IDD defaults
window_property.setFrameOutsideProjection(0.0)
window_property.setFrameInsideProjection(0.0)
window_property.setRatioOfFrameEdgeGlassConductanceToCenterOfGlassConductance(1.0)
window_property.setFrameSolarAbsorptance(0.7)
window_property.setFrameVisibleAbsorptance(0.7)
window_property.setFrameThermalHemisphericalEmissivity(0.9)
window_property.setDividerType("DividedLite")
window_property.setDividerWidth(0.0)
window_property.setNumberOfHorizontalDividers(0)
window_property.setNumberOfVerticalDividers(0)
window_property.setDividerOutsideProjection(0.0)
window_property.setDividerInsideProjection(0.0)
window_property.setDividerConductance(0.0)
window_property.setRatioOfDividerEdgeGlassConductanceToCenterOfGlassConductance(1.0)
window_property.setDividerSolarAbsorptance(0.0)
window_property.setDividerVisibleAbsorptance(0.0)
window_property.setDividerThermalHemisphericalEmissivity(0.9)
window_property.setOutsideRevealDepth(0.0)
window_property.setOutsideRevealSolarAbsorptance(0.0)
window_property.setInsideSillDepth(0.0)
window_property.setInsideSillSolarAbsorptance(0.0)
window_property.setInsideRevealDepth(0.0)
window_property.setInsideRevealSolarAbsorptance(0.0)

# This will be used to report the Assembly U-Factor, SGHC
# and VisibleTransmittance in the SQL/HTML.
# After a sucessful run, attach a sql file to your model and you can call
# SubSurface.assemblyUFactor() for eg
window_property.setNFRCProductTypeforAssemblyCalculations("CurtainWall")

# set window property on all subsurfaces
for sub_surface in model.getSubSurfaces():
    if sub_surface.subSurfaceType() != "FixedWindow":
        continue

    sub_surface.setWindowPropertyFrameAndDivider(window_property)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
