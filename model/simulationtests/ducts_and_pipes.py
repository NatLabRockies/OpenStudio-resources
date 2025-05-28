import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac(ashrae_sys_num="07")

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(model.getThermalZones(), key=lambda z: z.nameString())

# There should be only one (the central coiling coil of the VAV sys)
coil = model.getCoilCoolingWaters()[0]
airloop = coil.airLoopHVAC().get()
plantloop = coil.plantLoop().get()

duct = openstudio.model.Duct(model)
duct.addToNode(airloop.supplyOutletNode())

pipe = openstudio.model.PipeOutdoor(model)
pipe.addToNode(plantloop.supplyOutletNode())
mat = openstudio.model.StandardOpaqueMaterial(model, "Smooth", 3.00e-03, 45.31, 7833.0, 500.0)
mat.setThermalAbsorptance(openstudio.OptionalDouble(0.9))
mat.setSolarAbsorptance(openstudio.OptionalDouble(0.5))
mat.setVisibleAbsorptance(openstudio.OptionalDouble(0.5))
const = openstudio.model.Construction(model)
const.insertLayer(0, mat)
pipe.setConstruction(const)

pipe_indoor = openstudio.model.PipeIndoor(model)
pipe_indoor.setConstruction(const)
pipe_indoor.setAmbientTemperatureZone(zones[0])
pipe_indoor.addToNode(plantloop.supplyOutletNode())

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
