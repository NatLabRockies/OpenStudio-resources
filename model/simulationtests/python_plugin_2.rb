# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'
require 'tmpdir'
require 'erb'

model = BaselineModel.new

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 3 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

# Add a PythonPlugin:Variable (all OS SDK PythonPluginVariable objects are
# translated to a single E+ PythonPlugin:Variables (extensible object))
py_var = OpenStudio::Model::PythonPluginVariable.new(model)
py_var.setName('AverageBuildingTemp')

# Add a PythonPlugin:OutputVariable for that variable
py_out_var = OpenStudio::Model::PythonPluginOutputVariable.new(py_var)
py_out_var.setName('Averaged Building Temperature')
py_out_var.setTypeofDatainVariable('Averaged')
py_out_var.setUpdateFrequency('ZoneTimestep')
py_out_var.setUnits('C')

# Add a regular Output:Variable that references it
out_var = OpenStudio::Model::OutputVariable.new('PythonPlugin:OutputVariable', model)
out_var.setKeyValue(py_out_var.nameString)
out_var.setReportingFrequency('Timestep')

# Add output variables for Zone Mean Air Temperature, so we can compare
outputVariable = OpenStudio::Model::OutputVariable.new('Zone Mean Air Temperature', model)
outputVariable.setReportingFrequency('Timestep')

# Trend Variable: while this is a fully functioning object, you're probably
# best just using a storage variable on the Python side (eg: a list)
py_trend_var = OpenStudio::Model::PythonPluginTrendVariable.new(py_var)
py_trend_var.setName('Running Averaged Building Temperature')
n_timesteps = 24 * model.getTimestep.numberOfTimestepsPerHour
py_trend_var.setNumberofTimestepstobeLogged(n_timesteps)

py_var2 = OpenStudio::Model::PythonPluginVariable.new(model)
py_var2.setName('RunningAverageBuildingTemp')

py_out_trend_var = OpenStudio::Model::PythonPluginOutputVariable.new(py_var2)
py_out_trend_var.setName('Running Averaged Building Temperature')
py_out_trend_var.setTypeofDatainVariable('Averaged')
py_out_trend_var.setUpdateFrequency('ZoneTimestep')
py_out_trend_var.setUnits('C')

out_trend_var = OpenStudio::Model::OutputVariable.new('PythonPlugin:OutputVariable', model)
out_trend_var.setReportingFrequency('Timestep')

pluginClassName = 'AverageZoneTemps'

# get the python plugin program (erb template)
pluginTemplatePath = File.join(File.dirname(__FILE__), 'lib/python_plugin_program.py')
in_py = ''
File.open(pluginTemplatePath, 'r') do |file|
  in_py = file.read
end

dataPath = File.join(File.dirname(__FILE__), 'lib/python_plugin_program.csv')
OpenStudio::Model::ExternalFile.getExternalFile(model, dataPath)

# configure plugin template with variable values
renderer = ERB.new(in_py)
out_py = renderer.result(binding)

# Write it to a temporary directory so we don't pollute the current directory
# ExternalFile will copy it
pluginPath = File.join(Dir.tmpdir, 'python_plugin_program.py')
File.open(pluginPath, 'w') do |file|
  file << out_py
end

# create the external file object
external_file = OpenStudio::Model::ExternalFile.getExternalFile(model, pluginPath)
external_file = external_file.get

# create the python plugin instance object
python_plugin_instance = OpenStudio::Model::PythonPluginInstance.new(external_file, pluginClassName)
python_plugin_instance.setRunDuringWarmupDays(false)

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd, 'osm_name' => 'in.osm' })
