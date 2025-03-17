# This test aims to test the new **Unique** ModelObjects related to Output
# added in 3.0.0:
# * OutputDiagnostics,
# * OutputDebuggingData,
# * OutputJSON, and
# * OutputTableSummaryReports

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

###############################################################################
#                            OUTPUT:TABLE:MONTHLY                             #
###############################################################################

# Factory method to creates a OutputTableMonthly from the E+ datasets/StandardReports.idf
# Please use the OutputTableMonthly.validStandardReportNames() static method
# to look up the valid names as it will throw if it cannot find it
standardReportName = next(reversed(sorted(openstudio.model.OutputTableMonthly.validStandardReportNames())))
output_table_monthly = openstudio.model.OutputTableMonthly.fromStandardReports(model, standardReportName)

# You can of course create one yourself
output_table_monthly = openstudio.model.OutputTableMonthly(model)
output_table_monthly.setName("Fan Report")
output_table_monthly.setDigitsAfterDecimal(4)

# To add a group, you can use the convenience method
# bool addMonthlyVariableGroup(std.string variableOrMeterName, std.string aggregationType = "SumOrAverage");

groups = [
    # variableOrMeterName, SumOrAverage
    ("Fan Electricity Energy", "SumOrAverage"),
    ("Fan Rise in Air Temperature", "SumOrAverage"),
    ("Fan Electricity Rate", "Maximum"),
    ("Fan Rise in Air Temperature", "ValueWhenMaximumOrMinimum"),
]
output_table_monthly.addMonthlyVariableGroup(groups[0][0], groups[0][1])

# This will in turn actually use the helper class MonthlyVariableGroup
output_table_monthly.addMonthlyVariableGroup(openstudio.model.MonthlyVariableGroup(groups[1][0], groups[1][1]))

assert output_table_monthly.numberofMonthlyVariableGroups() == 2
# This is a vector of MonthlyVariableGroup
assert len(output_table_monthly.monthlyVariableGroups()) == 2
first_monthly_group = output_table_monthly.monthlyVariableGroups()[0]
# This returns an OptionalMonthlyVariableGroup
first_monthly_group_ = output_table_monthly.getMonthlyVariableGroup(0)
assert first_monthly_group_.is_initialized()
# The equality operator is defined to check for both variableOrMeterName and
# aggregationType
assert first_monthly_group == first_monthly_group_.get()
assert first_monthly_group.variableOrMeterName() == "Fan Electricity Energy"
assert first_monthly_group.aggregationType() == "SumOrAverage"

output_table_monthly.removeMonthlyVariableGroup(1)
output_table_monthly.removeAllMonthlyVariableGroups()

# There is also a batch add
monthly_groups = [openstudio.model.MonthlyVariableGroup(g[0], g[1]) for g in groups]
output_table_monthly.addMonthlyVariableGroups(monthly_groups)
assert output_table_monthly.numberofMonthlyVariableGroups() == 4

###############################################################################
#                             OUTPUT:TABLE:ANNUAL                             #
###############################################################################

output_table_annual = openstudio.model.OutputTableAnnual(model)
output_table_annual.setName("Electricity Report")
output_table_annual.setSchedule(model.alwaysOnDiscreteSchedule())
output_table_annual.setFilter("Zone 1")
output_table_annual.resetFilter()

groups = [
    # variableorMeterorEMSVariableorField, aggregationType, digitsAfterDecimal
    ("Electricity:Facility", "SumOrAverage", 3),
    ("Electricity:Facility", "Maximum", 1),
]

output_table_annual.addAnnualVariableGroup(groups[0][0], groups[0][1], groups[0][2])

# This will in turn actually use the helper class AnnualVariableGroup
output_table_annual.addAnnualVariableGroup(
    openstudio.model.AnnualVariableGroup(groups[1][0], groups[1][1], groups[1][2])
)

assert output_table_annual.numberofAnnualVariableGroups() == 2
# This is a vector of AnnualVariableGroup
assert len(output_table_annual.annualVariableGroups()) == 2
first_annual_group = output_table_annual.annualVariableGroups()[0]
# This returns an OptionalAnnualVariableGroup
first_annual_group_ = output_table_annual.getAnnualVariableGroup(0)
assert first_annual_group_.is_initialized()
# The equality operator is defined to check for both variableorMeterorEMSVariableorField and
# aggregationType
assert first_annual_group == first_annual_group_.get()
assert first_annual_group.variableorMeterorEMSVariableorField() == "Electricity:Facility"
assert first_annual_group.aggregationType() == "SumOrAverage"
assert first_annual_group.digitsAfterDecimal() == 3

output_table_annual.removeAnnualVariableGroup(1)
output_table_annual.removeAllAnnualVariableGroups()

# There is also a batch add
annual_groups = [openstudio.model.AnnualVariableGroup(g[0], g[1], g[2]) for g in groups]
output_table_annual.addAnnualVariableGroups(annual_groups)
assert output_table_annual.numberofAnnualVariableGroups() == 2

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
