# frozen_string_literal: true

# This test aims to test the new **Unique** ModelObjects related to Output
# added in 3.5.0:
# * OutputControlTableStyle
# * OutputSQLite
# * OutputSchedules
# * OutputConstructions

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
#                             OUTPUTCONTROL:TABLE:STYLE                       #
###############################################################################

outputcontrol_table_style = model.getOutputControlTableStyle
outputcontrol_table_style.setColumnSeparator('HTML')
outputcontrol_table_style.setUnitConversion('InchPound')

###############################################################################
#                                 OUTPUT:SQLITE                               #
###############################################################################

output_sqlite = model.getOutputSQLite
output_sqlite.setOptionType('SimpleAndTabular')
output_sqlite.setUnitConversionforTabularData('None')

###############################################################################
#                              OUTPUT:SCHEDULES                               #
###############################################################################

output_schedules = model.getOutputSchedules
output_schedules.setKeyField('Timestep')

###############################################################################
#                            OUTPUT:CONSTRUCTIONS                             #
###############################################################################

output_constructions = model.getOutputConstructions
output_constructions.setReportConstructions(true)
output_constructions.setReportMaterials(true)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
