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

vrf = openstudio.model.AirConditionerVariableRefrigerantFlow(model)
# E+ now throws when the CoolingEIRLowPLR has a curve minimum value of x which
# is higher than the Minimum Heat Pump Part-Load Ratio.
# The curve has a min of 0.5 here, so set the MinimumHeatPumpPartLoadRatio to
# the same value
vrf.setMinimumHeatPumpPartLoadRatio(0.5)

for z in zones:
    vrf_terminal = openstudio.model.ZoneHVACTerminalUnitVariableRefrigerantFlow(model)
    vrf_terminal.addToThermalZone(z)
    vrf.addTerminal(vrf_terminal)


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
