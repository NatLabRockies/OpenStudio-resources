# This file tests the different meters: OutputMeter, MeterCustom
# and MeterCustomDecrement
#
import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 2 story, 100m X 50m, 10 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=2, floor_to_floor_height=4, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add ASHRAE System type 07, VAV w/ Reheat
model.add_hvac(ashrae_sys_num="07")

reporting_frequency = "Hourly"

#      n# Create a MeterCustom to meter VAV Reheat
#      nmeter_name = "VAV Reheat"
#      nmeter_custom = openstudio.model.MeterCustom(model)
#      nmeter_custom.setName(meter_name)
#      nmeter_custom.setFuelType("Generic")
#      n
#      nvariable_name = "Heating Coil Heating Energy"
#      nmodel.getAirTerminalSingleDuctVAVReheats.each do |atu|
#      n  # Get the reheat coil
#      n  hc = atu.reheatCoil.to_CoilHeatingWater.get
#      n  # A keyvar group
#      n  meter_custom.addKeyVarGroup(hc.nameString, variable_name)
#      nend
#      n
#      n# Create an OutputMeter to output the meter to the SQL file
#      nmeter = openstudio.model.OutputMeter(model)
#      nmeter.setName(meter_name)
#      nmeter.setReportingFrequency(reporting_frequency)
#      nmeter.setCumulative(false)
#      nmeter.setMeterFileOnly(false)
#      nmeter.resetEndUseType
#      n
#      n
#      n# We will create a MeterCustomDecrement outputing the difference between
#      n# the Heating:EnergyTransfer meter and the VAV Reheat one above
#      nsource_meter_name = "Heating:EnergyTransfer"
#      nsource_meter_name="Heating:Gas"
#      nmeter_customdecrement = openstudio.model.MeterCustomDecrement(model, source_meter_name)
#      nmeter_customdecrement.setFuelType("Generic")
#      nmeter_customdecrement.setName("Heating Minus VAV Reheat")
#      n# Add one keyvar group to subtract from source meter
#      n# key is empty because it's a meter, and var is "VAV Reheat"
#      nmeter_customdecrement.addKeyVarGroup("", meter_name)
#      n
#      n# Create an OutputMeter to output the meter to the SQL file
#      nmeter = openstudio.model.OutputMeter(model)
#      nmeter.setName(meter_customdecrement.nameString)
#      nmeter.setReportingFrequency(reporting_frequency)

# Create a MeterCustom to meter VAV Reheat
meter_name = "VAV Reheat"
meter_custom = openstudio.model.MeterCustom(model)
meter_custom.setName(meter_name)
meter_custom.setFuelType("Generic")

variable_name = "Heating Coil Heating Energy"
for atu in model.getAirTerminalSingleDuctVAVReheats():
    # Get the reheat coil
    hc = atu.reheatCoil().to_CoilHeatingWater().get()
    # A keyvar group
    meter_custom.addKeyVarGroup(hc.nameString(), variable_name)


# Create an OutputMeter to output the meter to the SQL file
meter = openstudio.model.OutputMeter(model)
meter.setName(meter_name)
meter.setReportingFrequency(reporting_frequency)
meter.setCumulative(False)
meter.setMeterFileOnly(False)
meter.resetEndUseType()

# We will create a MeterCustomDecrement outputing the difference between
# the HeatingCoils:EnergyTransfer meter and the VAV Reheat one above
# Note, in this specific example, there is only one other heating coil
# (a CoilHeatingElectric).
source_meter_name = "HeatingCoils:EnergyTransfer"

meter_customdecrement = openstudio.model.MeterCustomDecrement(model, source_meter_name)
meter_customdecrement.setFuelType("Generic")
meter_customdecrement.setName("Heating Coils Minus VAV Reheat")
# Add one keyvar group to subtract from source meter
# key is empty because it's a meter, and var is "VAV Reheat"
meter_customdecrement.addKeyVarGroup("", meter_name)

# Create an OutputMeter to output the meter to the SQL file
meter = openstudio.model.OutputMeter(model)
meter.setName(meter_customdecrement.nameString())
meter.setReportingFrequency(reporting_frequency)

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
