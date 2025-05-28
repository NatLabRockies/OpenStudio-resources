import openstudio

from lib.baseline_model import BaselineModel

m = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone core/perimeter building
m.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
m.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
m.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type()

# add design days to the model (Chicago)
m.add_design_days()

# add ASHRAE System type 03, PSZ-AC
m.add_hvac(ashrae_sys_num="03")

# In order to produce more consistent results between different runs,
# we sort the zones by names (only one here anyways...)
zones = sorted(m.getThermalZones(), key=lambda z: z.nameString())

# CoilSystemCoolingDXHeatExchangerAssisted
zone = zones[0]
airloop = zone.airLoopHVAC().get()
airloop.setName("AirLoopHVAC CoilSystemDXHX")

# create a CoilSystem object, that creates both a DX Cooling Coil and a HX
hx = openstudio.model.HeatExchangerDesiccantBalancedFlow(m)
hx.setName("CoilSystemDXHX HX")
coil_system = openstudio.model.CoilSystemCoolingDXHeatExchangerAssisted(m, hx)
coil_system.setName("CoilSystemDXHX")
dx_coil = coil_system.coolingCoil().to_CoilCoolingDXSingleSpeed().get()
dx_coil.setName("CoilSystemDXHX CoolingCoil")

# Note JM 2019-03-13: At this point in time
# CoilSystemCoolingDXHeatExchangerAssisted is NOT allowed on a Branch directly
# and should be placed inside one of the Unitary systems
# cf https://github.com/NREL/energyplus/issues/7222
unitary = openstudio.model.AirLoopHVACUnitarySystem(m)
unitary.setCoolingCoil(coil_system)
unitary.setControllingZoneorThermostatLocation(zone)

# Replace the default CoilCoolingWater with the Unitary, then remove the default one
coil = (
    airloop.supplyComponents(openstudio.model.CoilCoolingDXSingleSpeed.iddObjectType())[0]
    .to_CoilCoolingDXSingleSpeed()
    .get()
)
# Note that we connect the CoilSystem, NOT the underlying CoilCoolingDXSingleSpeed
unitary.addToNode(coil.outletModelObject().get().to_Node().get())
coil.remove()

# Rename some nodes and such, for ease of debugging
airloop.supplyInletNode().setName("#{airloop.name()} Supply Inlet Node")
airloop.supplyOutletNode().setName("#{airloop.name()} Supply Outlet Node")
airloop.mixedAirNode().get().setName("#{airloop.name()} Mixed Air Node")
# coil_system.outletModelObject.get.to_Node.get.setName("#{airloop.nameString} HX Outlet to Heating Coil Inlet Node")
unitary.outletNode().get().setName("#{airloop.name()} Unitary Outlet to Heating Coil Node")

heating_coil = airloop.supplyComponents(openstudio.model.CoilHeatingGas.iddObjectType())[0].to_CoilHeatingGas().get()
heating_coil.outletModelObject().get().setName("#{airloop.name()} Heating Coil Outlet to Fan Inlet Node")

# save the OpenStudio model (.osm)
m.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
