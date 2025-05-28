import tempfile
from pathlib import Path

import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=3)

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type()

# add design days to the model (Chicago)
model.add_design_days()

zone_names = sorted([x.nameString() for x in model.getThermalZones()])

zone_names_str_list = '["' + '", "'.join(zone_names) + '"]'

# Add a PythonPlugin:Variable (all OS SDK PythonPluginVariable objects are
# translated to a single E+ PythonPlugin:Variables (extensible object))
py_var = openstudio.model.PythonPluginVariable(model)
py_var.setName("AverageBuildingTemp")

# Add a PythonPlugin:OutputVariable for that variable
py_out_var = openstudio.model.PythonPluginOutputVariable(py_var)
py_out_var.setName("Averaged Building Temperature")
py_out_var.setTypeofDatainVariable("Averaged")
py_out_var.setUpdateFrequency("ZoneTimestep")
py_out_var.setUnits("C")

# Add a regular Output:Variable that references it
out_var = openstudio.model.OutputVariable("PythonPlugin:OutputVariable", model)
out_var.setKeyValue(py_out_var.nameString())
out_var.setReportingFrequency("Timestep")

# Add output variables for Zone Mean Air Temperature, so we can compare
outputVariable = openstudio.model.OutputVariable("Zone Mean Air Temperature", model)
outputVariable.setReportingFrequency("Timestep")

# Trend Variable: while this is a fully functioning object, you're probably
# best just using a storage variable on the Python side (eg: a list)
py_trend_var = openstudio.model.PythonPluginTrendVariable(py_var)
py_trend_var.setName("Running Averaged Building Temperature")
n_timesteps = 24 * model.getTimestep().numberOfTimestepsPerHour()
py_trend_var.setNumberofTimestepstobeLogged(n_timesteps)

py_var2 = openstudio.model.PythonPluginVariable(model)
py_var2.setName("RunningAverageBuildingTemp")

py_out_trend_var = openstudio.model.PythonPluginOutputVariable(py_var2)
py_out_trend_var.setName("Running Averaged Building Temperature")
py_out_trend_var.setTypeofDatainVariable("Averaged")
py_out_trend_var.setUpdateFrequency("ZoneTimestep")
py_out_trend_var.setUnits("C")

out_trend_var = openstudio.model.OutputVariable("PythonPlugin:OutputVariable", model)
out_trend_var.setReportingFrequency("Timestep")

pluginClassName = "AverageZoneTemps"

python_plugin_file_content = f"""from pyenergyplus.plugin import EnergyPlusPlugin

class {pluginClassName}(EnergyPlusPlugin):

    def __init__(self):
        super().__init__()
        self.do_setup = True

    def on_end_of_zone_timestep_before_zone_reporting(self, state) -> int:
        if self.do_setup:
            self.data['zone_volumes'] = []
            self.data['zone_temps'] = []
            zone_names = {zone_names_str_list}
            for zone_name in zone_names:
                handle = self.api.exchange.get_internal_variable_handle(state, 'Zone Air Volume', zone_name)
                zone_volume = self.api.exchange.get_internal_variable_value(state, handle)
                self.data['zone_volumes'].append(zone_volume)
                self.data['zone_temps'].append(
                    self.api.exchange.get_variable_handle(state, 'Zone Mean Air Temperature', zone_name)
                )
            self.data['avg_temp_variable'] = self.api.exchange.get_global_handle(state, '{py_var.nameString()}')
            self.data['trend'] = self.api.exchange.get_trend_handle(state, '{py_trend_var.nameString()}')
            self.data['running_avg_temp_variable'] = self.api.exchange.get_global_handle(state, '{py_var2.nameString()}')
            self.do_setup = False
        zone_temps = list()
        for t_handle in self.data['zone_temps']:
            zone_temps.append(self.api.exchange.get_variable_value(state, t_handle))
        numerator = 0.0
        denominator = 0.0
        for i in range(len(self.data['zone_volumes'])):
            numerator += self.data['zone_volumes'][i] * zone_temps[i]
            denominator += self.data['zone_volumes'][i]
        average_temp = numerator / denominator
        self.api.exchange.set_global_value(state, self.data['avg_temp_variable'], average_temp)

        past_daily_avg_temp = self.api.exchange.get_trend_average(state, self.data['trend'], {n_timesteps})
        self.api.exchange.set_global_value(state, self.data['running_avg_temp_variable'], past_daily_avg_temp)
        return 0
"""

# Write it to a temporary directory so we don't pollute the current directory
# ExternalFile will copy it
pluginPath = Path(tempfile.gettempdir()) / "python_plugin_program.py"
pluginPath.write_text(python_plugin_file_content)

# create the external file object
external_file = openstudio.model.ExternalFile.getExternalFile(model, str(pluginPath))
external_file = external_file.get()

# create the python plugin instance object
python_plugin_instance = openstudio.model.PythonPluginInstance(external_file, pluginClassName)
python_plugin_instance.setRunDuringWarmupDays(False)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
