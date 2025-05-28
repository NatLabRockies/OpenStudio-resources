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

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac(ashrae_sys_num="07")

# In order to produce more consistent results between different runs,
# We ensure we do get the same object each time
boilers = sorted(model.getBoilerHotWaters(), key=lambda c: c.nameString())
heating_loop = boilers[0].plantLoop().get()
heating_loop.setName("HW Loop")
cc = sorted(model.getCoilCoolingWaters(), key=lambda c: c.nameString())[0]

a = cc.airLoopHVAC().get()
a_temp_spm = openstudio.model.SetpointManagerSystemNodeResetTemperature(model)
a_temp_spm.setName("Supply Air Temp Setpoint Manager")
a_temp_spm.setControlVariable("Temperature")
a_temp_spm.setSetpointatLowReferenceTemperature(16.7)
a_temp_spm.setSetpointatHighReferenceTemperature(12.8)
a_temp_spm.setLowReferenceTemperature(20.0)
a_temp_spm.setHighReferenceTemperature(23.3)
a_temp_spm.setReferenceNode(a.supplyInletNode())
a_temp_spm.addToNode(a.supplyOutletNode())

# This is only allowed on an AirLoopHVAC, not a PlantLoop
a_hum_spm = openstudio.model.SetpointManagerSystemNodeResetHumidity(model)
a_hum_spm.setName("Dehumidification Setpoint Manager")
a_hum_spm.setControlVariable("MaximumHumidityRatio")
a_hum_spm.setSetpointatLowReferenceHumidityRatio(0.00924)
a_hum_spm.setSetpointatHighReferenceHumidityRatio(0.00600)
a_hum_spm.setLowReferenceHumidityRatio(0.00850)
a_hum_spm.setHighReferenceHumidityRatio(0.01000)
a_hum_spm.setReferenceNode(a.supplyInletNode())
a_hum_spm.addToNode(cc.airOutletModelObject().get().to_Node().get())
# Also need to switch the controller water coil to enable dehumidification
cc.controllerWaterCoil().get().setControlVariable("TemperatureAndHumidityRatio")

# You're better off using a SetpointManagerOutdoorAirReset for this specific
# application FYI, but this is a demonstration
p_temp_spm = openstudio.model.SetpointManagerSystemNodeResetTemperature(model)
p_temp_spm.setName("Hot Water Loop Setpoint Manager")
p_temp_spm.setControlVariable("Temperature")
p_temp_spm.setSetpointatLowReferenceTemperature(80.0)
p_temp_spm.setSetpointatHighReferenceTemperature(65.6)
p_temp_spm.setLowReferenceTemperature(-6.7)
p_temp_spm.setHighReferenceTemperature(10.0)
p_temp_spm.setReferenceNode(model.outdoorAirNode())
p_temp_spm.addToNode(heating_loop.supplyOutletNode())

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
