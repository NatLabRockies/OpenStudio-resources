import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 5 zone building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=3)

# NOTE: Make all spaces under a single zone
[z.remove() for z in model.getThermalZones()]
z = openstudio.model.ThermalZone(model)
z.setName("Zone with 5 Spaces")
[s.setThermalZone(z) for s in model.getSpaces()]

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

# Add ASHRAE System type 07, VAV w/ Reheat, this creates a ChW, a HW loop and a
# Condenser Loop
model.add_hvac(ashrae_sys_num="07")

assert len(model.getThermalZones()) == 1
assert len(model.getSpaces()) == 5
assert len(model.getAirLoopHVACs()) == 1
air_loop = model.getAirLoopHVACs()[0]
assert len(model.getAirTerminalSingleDuctVAVReheats()) == 1
atu = model.getAirTerminalSingleDuctVAVReheats()[0]
assert atu.setControlForOutdoorAir(True)

# In order to produce more consistent results between different runs,
# we sort the spaces by names
spaces = sorted(model.getSpaces(), key=lambda s: s.nameString())

[dsoa.remove() for dsoa in model.getDesignSpecificationOutdoorAirs()]

# Create a Design Specification Outdoor Air for each space, but the last one
for i, space in enumerate(spaces[:-1]):
    dsoa = openstudio.model.DesignSpecificationOutdoorAir(model)
    dsoa_ach = 0.1 * (i+1)
    dsoa.setOutdoorAirFlowAirChangesperHour(dsoa_ach)
    dsoa.setName(f"{space.nameString()} DSOA {dsoa_ach:.1f} ACH")
    space.setDesignSpecificationOutdoorAir(dsoa)
    print(f"For'{space.nameString()}' created '{dsoa.nameString()}'")

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
