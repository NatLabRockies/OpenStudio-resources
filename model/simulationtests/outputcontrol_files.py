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
#                            OUTPUTCONTROL:FILES                              #
###############################################################################

outputcontrol_files = model.getOutputControlFiles()

# If you set this to false, reporting measures will fail, including
# openstudio_results
outputcontrol_files.setOutputSQLite(True)
# openstudio_results needs the tabular output since it queries it:
# "Can't find any contents in Building Area Table to get tabular units. measure can't run"
outputcontrol_files.setOutputTabular(True)

outputcontrol_files.setOutputCSV(True)
outputcontrol_files.setOutputAUDIT(True)

outputcontrol_files.setOutputJSON(False)
outputcontrol_files.setOutputMTR(False)
outputcontrol_files.setOutputESO(False)
outputcontrol_files.setOutputEIO(False)
outputcontrol_files.setOutputZoneSizing(False)
outputcontrol_files.setOutputSystemSizing(False)
outputcontrol_files.setOutputDXF(False)
outputcontrol_files.setOutputBND(False)
outputcontrol_files.setOutputRDD(False)
outputcontrol_files.setOutputMDD(False)
outputcontrol_files.setOutputMTD(False)

outputcontrol_files.setOutputSHD(False)
outputcontrol_files.setOutputDFS(False)
outputcontrol_files.setOutputGLHE(False)
outputcontrol_files.setOutputDelightIn(False)
outputcontrol_files.setOutputDelightELdmp(False)
outputcontrol_files.setOutputDelightDFdmp(False)
outputcontrol_files.setOutputEDD(False)
outputcontrol_files.setOutputDBG(False)
outputcontrol_files.setOutputPerfLog(False)
outputcontrol_files.setOutputSLN(False)
outputcontrol_files.setOutputSCI(False)
outputcontrol_files.setOutputWRL(False)
outputcontrol_files.setOutputScreen(False)
outputcontrol_files.setOutputExtShd(False)
outputcontrol_files.setOutputTarcog(False)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
