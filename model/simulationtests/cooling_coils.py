import openstudio

from lib.baseline_model import BaselineModel

m = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
m.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

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

# add ASHRAE System type 07, VAV w/ Reheat
m.add_hvac(ashrae_sys_num="07")

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(m.getThermalZones(), key=lambda z: z.nameString())

# CoilCoolingDXTwoStageWithHumidityControlMode
zone = zones[0]
zone.airLoopHVAC().get().removeBranchForZone(zone)
airloop = openstudio.model.addSystemType3(m).to_AirLoopHVAC().get()
airloop.setName("AirLoopHVAC CoilCoolingDXTwoStageWithHumidityControlMode")
airloop.addBranchForZone(zone)
coil = (
    airloop.supplyComponents(openstudio.model.CoilCoolingDXSingleSpeed.iddObjectType())[0].to_StraightComponent().get()
)
node = coil.outletModelObject().get().to_Node().get()
new_coil = openstudio.model.CoilCoolingDXTwoStageWithHumidityControlMode(m)
new_coil.addToNode(node)
coil.remove()

# CoilSystemCoolingDXHeatExchangerAssisted
zone = zones[1]
zone.airLoopHVAC().get().removeBranchForZone(zone)
airloop = openstudio.model.AirLoopHVAC(m)
airloop.setName("AirLoopHVAC Unitary with CoilSystemCoolingDXHX")
alwaysOn = m.alwaysOnDiscreteSchedule()
# Starting with E 9.0.0, Uncontrolled is deprecated and replaced with
# ConstantVolume:NoReheat
if openstudio.VersionString(openstudio.openStudioVersion()) >= openstudio.VersionString("2.7.0"):
    terminal = openstudio.model.AirTerminalSingleDuctConstantVolumeNoReheat(m, alwaysOn)
else:
    terminal = openstudio.model.AirTerminalSingleDuctUncontrolled(m, alwaysOn)

airloop.addBranchForZone(zone, terminal)
unitary = openstudio.model.AirLoopHVACUnitarySystem(m)
unitary.setFanPlacement("BlowThrough")
fan = openstudio.model.FanOnOff(m)
unitary.setSupplyFan(fan)
heating_coil = openstudio.model.CoilHeatingElectric(m)
unitary.setHeatingCoil(heating_coil)
cooling_coil = openstudio.model.CoilSystemCoolingDXHeatExchangerAssisted(m)
unitary.setCoolingCoil(cooling_coil)
unitary.addToNode(airloop.supplyOutletNode())
unitary.setControllingZoneorThermostatLocation(zone)

# CoilCoolingDXVariableSpeed
zone = zones[2]
zone.airLoopHVAC().get().removeBranchForZone(zone)
airloop = openstudio.model.addSystemType7(m).to_AirLoopHVAC().get()
airloop.setName("AirLoopHVAC Coil DX VariableSpeeds")
airloop.addBranchForZone(zone)
coil = airloop.supplyComponents(openstudio.model.CoilCoolingWater.iddObjectType())[0].to_CoilCoolingWater().get()
newcoil = openstudio.model.CoilCoolingDXVariableSpeed(m)
coildata = openstudio.model.CoilCoolingDXVariableSpeedSpeedData(m)
newcoil.addSpeed(coildata)
newcoil.addToNode(coil.airOutletModelObject().get().to_Node().get())
coil.remove()

node = newcoil.outletModelObject().get().to_Node().get()

# CoilHeatingDXVariableSpeed
newcoil = openstudio.model.CoilHeatingDXVariableSpeed(m)
coildata = openstudio.model.CoilHeatingDXVariableSpeedSpeedData(m)
newcoil.addSpeed(coildata)
newcoil.addToNode(node)

# save the OpenStudio model (.osm)
m.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
