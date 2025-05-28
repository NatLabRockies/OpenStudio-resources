import openstudio

from lib.baseline_model import BaselineModel

m = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone core building
m.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=3, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
m.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# Add ASHRAE System type 07, VAV w/ Reheat, this creates a ChW, a HW loop and a
# Condenser Loop
m.add_hvac(ashrae_sys_num="07")

# add thermostats
m.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type()

# add design days to the model (Chicago)
m.add_design_days()

###############################################################################
#                        R E P L A C E    A T Us
###############################################################################

b = m.getBoilerHotWaters()[0]
p_hw = b.plantLoop().get()

ch = m.getChillerElectricEIRs()[0]
p_chw = ch.plantLoop().get()

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(m.getThermalZones(), key=lambda z: z.nameString())
# (There's only one here...)
z = zones[0]
a = z.airLoopHVAC().get()
a.removeBranchForZone(z)

atu = openstudio.model.AirTerminalSingleDuctInletSideMixer(m)
a.addBranchForZone(z, atu)

fan = openstudio.model.FanConstantVolume(m)
heatingCoil = openstudio.model.CoilHeatingWater(m)
p_hw.addDemandBranchForComponent(heatingCoil)
coolingCoil = openstudio.model.CoilCoolingWater(m)
p_chw.addDemandBranchForComponent(coolingCoil)
fc = openstudio.model.ZoneHVACFourPipeFanCoil(m, m.alwaysOnDiscreteSchedule(), fan, coolingCoil, heatingCoil)
fc.addToNode(atu.outletModelObject().get().to_Node().get())

# This replaces the E+ field 'Design Specification Outdoor Air'
# This will find the Thermal Zone associated, find the space, which has a space
# type, and that space type has a Design Specification Outdoor Air and it will
# write the DSOA into the field in E+.
atu.setControlForOutdoorAir(True)

atu.setPerPersonVentilationRateMode("CurrentOccupancy")

# Rename some nodes to facilitate looking at the resulting IDF
z.zoneAirNode().setName("Zone Air Node")
z.returnAirModelObjects()[0].setName("Zone Return Air Node")
atu.inletModelObject().get().setName("ATU InletSideMixer Inlet Node")
atu.outletModelObject().get().setName("ATU InletSideMixer Outlet to FC Inlet Node")
fc.outletNode().get().setName("FC Outlet Node")
z.exhaustPortList().modelObjects()[0].setName("Zone Exhaust Air Node")

# save the OpenStudio model (.osm)
m.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
