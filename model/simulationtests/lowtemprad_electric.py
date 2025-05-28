import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

heatingTemperatureSched = openstudio.model.ScheduleConstant(model)

heatingTemperatureSched.setValue(10.0)

for z in zones:
    lowtempradiant = openstudio.model.ZoneHVACLowTemperatureRadiantElectric(
        model, model.alwaysOnDiscreteSchedule(), heatingTemperatureSched
    )
    lowtempradiant.setRadiantSurfaceType("Floors")
    lowtempradiant.setMaximumElectricalPowertoPanel(1000)
    lowtempradiant.setTemperatureControlType("MeanRadiantTemperature")

    lowtempradiant.addToThermalZone(z)


# add thermostats
# model.add_thermostats({"heating_setpoint" => 24,"cooling_setpoint" => 28})

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# create an internalsourceconstruction

intSourceConst = openstudio.model.ConstructionWithInternalSource(model)
intSourceConst.setSourcePresentAfterLayerNumber(3)
intSourceConst.setTemperatureCalculationRequestedAfterLayerNumber(3)
concrete_sand_gravel = openstudio.model.StandardOpaqueMaterial(
    model, "MediumRough", 0.1014984, 1.729577, 2242.585, 836.8
)
rigid_insulation_2inch = openstudio.model.StandardOpaqueMaterial(model, "Rough", 0.05, 0.02, 56.06, 1210)
gyp1 = openstudio.model.StandardOpaqueMaterial(model, "MediumRough", 0.0127, 0.7845, 1842.1221, 988)
gyp2 = openstudio.model.StandardOpaqueMaterial(model, "MediumRough", 0.01905, 0.7845, 1842.1221, 988)
finished_floor = openstudio.model.StandardOpaqueMaterial(model, "Smooth", 0.0016, 0.17, 1922.21, 1250)
layers = [
    concrete_sand_gravel,
    rigid_insulation_2inch,
    gyp1,
    gyp2,
    finished_floor,
]  # openstudio.model.MaterialVector(model)

intSourceConst.setLayers(layers)

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# find a surface that's of surface type floor and assign the surface internal source construction
for s in model.getSurfaces():
    if s.surfaceType() == "Floor":
        s.setConstruction(intSourceConst)


# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
