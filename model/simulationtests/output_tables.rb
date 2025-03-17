# frozen_string_literal: true

# This test aims to test the new **Unique** ModelObjects related to Output
# added in 3.0.0:
# * OutputDiagnostics,
# * OutputDebuggingData,
# * OutputJSON, and
# * OutputTableSummaryReports

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 19,
                        'cooling_setpoint' => 26 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# In order to produce more consistent results between different runs,
# we sort the zones by names
# (There's only one here, but just in case this would be copy pasted somewhere
# else...)
zones = model.getThermalZones.sort_by { |z| z.name.to_s }
z = zones[0]
z.setUseIdealAirLoads(true)

###############################################################################
#                            OUTPUT:TABLE:MONTHLY                             #
###############################################################################

# Factory method to creates a OutputTableMonthly from the E+ datasets/StandardReports.idf
# Please use the OutputTableMonthly::validStandardReportNames() static method
# to look up the valid names as it will throw if it cannot find it
standardReportName = OpenStudio::Model::OutputTableMonthly.validStandardReportNames.sort.reverse[0]
output_table_monthly = OpenStudio::Model::OutputTableMonthly.fromStandardReports(model, standardReportName)

# You can of course create one yourself
output_table_monthly = OpenStudio::Model::OutputTableMonthly.new(model)
output_table_monthly.setName('Fan Report')
output_table_monthly.setDigitsAfterDecimal(4)

# To add a group, you can use the convenience method
# bool addMonthlyVariableGroup(std::string variableOrMeterName, std::string aggregationType = "SumOrAverage");

groups = [
  # variableOrMeterName, SumOrAverage
  ['Fan Electricity Energy', 'SumOrAverage'],
  ['Fan Rise in Air Temperature', 'SumOrAverage'],
  ['Fan Electricity Rate', 'Maximum'],
  ['Fan Rise in Air Temperature', 'ValueWhenMaximumOrMinimum'],
]
output_table_monthly.addMonthlyVariableGroup(groups[0][0], groups[0][1])

# This will in turn actually use the helper class MonthlyVariableGroup
output_table_monthly.addMonthlyVariableGroup(OpenStudio::Model::MonthlyVariableGroup.new(groups[1][0], groups[1][1]))

raise unless output_table_monthly.numberofMonthlyVariableGroups == 2
# This is a vector of MonthlyVariableGroup
raise unless output_table_monthly.monthlyVariableGroups.size == 2
first_monthly_group = output_table_monthly.monthlyVariableGroups.first
# This returns an OptionalMonthlyVariableGroup
first_monthly_group_ = output_table_monthly.getMonthlyVariableGroup(0)
raise unless first_monthly_group_.is_initialized
# The equality operator is defined to check for both variableOrMeterName and
# aggregationType
raise unless first_monthly_group == first_monthly_group_.get
raise unless first_monthly_group.variableOrMeterName == 'Fan Electricity Energy'
raise unless first_monthly_group.aggregationType == 'SumOrAverage'

output_table_monthly.removeMonthlyVariableGroup(1)
output_table_monthly.removeAllMonthlyVariableGroups

# There is also a batch add
monthly_groups = groups.map { |g| OpenStudio::Model::MonthlyVariableGroup.new(g[0], g[1]) }
output_table_monthly.addMonthlyVariableGroups(monthly_groups)
raise unless output_table_monthly.numberofMonthlyVariableGroups == 4

###############################################################################
#                             OUTPUT:TABLE:ANNUAL                             #
###############################################################################

output_table_annual = OpenStudio::Model::OutputTableAnnual.new(model)
output_table_annual.setName("Electricity Report")
output_table_annual.setSchedule(model.alwaysOnDiscreteSchedule)
output_table_annual.setFilter("Zone 1")
output_table_annual.resetFilter

groups = [
  #variableorMeterorEMSVariableorField, aggregationType, digitsAfterDecimal
  ['Electricity:Facility', 'SumOrAverage', 3],
  ['Electricity:Facility', 'Maximum', 1],
]

output_table_annual.addAnnualVariableGroup(groups[0][0], groups[0][1], groups[0][2])

# This will in turn actually use the helper class AnnualVariableGroup
output_table_annual.addAnnualVariableGroup(OpenStudio::Model::AnnualVariableGroup.new(groups[1][0], groups[1][1], groups[1][2]))

raise unless output_table_annual.numberofAnnualVariableGroups == 2
# This is a vector of AnnualVariableGroup
raise unless output_table_annual.annualVariableGroups.size == 2
first_annual_group = output_table_annual.annualVariableGroups.first
# This returns an OptionalAnnualVariableGroup
first_annual_group_ = output_table_annual.getAnnualVariableGroup(0)
raise unless first_annual_group_.is_initialized
# The equality operator is defined to check for both variableorMeterorEMSVariableorField and
# aggregationType
raise unless first_annual_group == first_annual_group_.get
raise unless first_annual_group.variableorMeterorEMSVariableorField == 'Electricity:Facility'
raise unless first_annual_group.aggregationType == 'SumOrAverage'
raise unless first_annual_group.digitsAfterDecimal == 3

output_table_annual.removeAnnualVariableGroup(1)
output_table_annual.removeAllAnnualVariableGroups

# There is also a batch add
annual_groups = groups.map { |g| OpenStudio::Model::AnnualVariableGroup.new(g[0], g[1], g[2]) }
output_table_annual.addAnnualVariableGroups(annual_groups)
raise unless output_table_annual.numberofAnnualVariableGroups == 2

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
