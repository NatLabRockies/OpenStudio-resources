import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

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

# make a shading surface
vertices = openstudio.Point3dVector()
vertices.append(openstudio.Point3d(0, 0, 0))
vertices.append(openstudio.Point3d(10, 0, 0))
vertices.append(openstudio.Point3d(10, 4, 0))
vertices.append(openstudio.Point3d(0, 4, 0))
rotation = openstudio.createRotation(openstudio.Vector3d(1, 0, 0), openstudio.degToRad(30))
vertices = rotation * vertices

group = openstudio.model.ShadingSurfaceGroup(model)
group.setXOrigin(20)
group.setYOrigin(10)
group.setZOrigin(8)

shade = openstudio.model.ShadingSurface(vertices, model)
shade.setShadingSurfaceGroup(group)

# create the panel
# This creates a panel with the Sandia parameters for one random (static) entry
# in the embedded sandia Database
# panel = openstudio.model.GeneratorPhotovoltaic.sandia(model)

# /// Factory method to creates a GeneratorPhotovoltaic object with PhotovoltaicPerformanceSandia by looking up characteristics in the embedded
# // Sandia database by its name. Please use the PhotovoltaicPerformanceSandia.sandiaModulePerformanceNames() static method
# / to look up the valid names as it will throw if it cannot find it
sandiaModulePerformanceName = next(
    reversed(sorted(openstudio.model.PhotovoltaicPerformanceSandia.sandiaModulePerformanceNames()))
)
panel = openstudio.model.GeneratorPhotovoltaic.fromSandiaDatabase(model, sandiaModulePerformanceName)

panel.setSurface(shade)

# create the inverter
inverter = openstudio.model.ElectricLoadCenterInverterSimple(model)
inverter.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule())
inverter.setRadiativeFraction(0.0)
inverter.setInverterEfficiency(1.0)

# The above CTor has already filled up the data,
# but demonstrate the API nonetheless
sandiaPerf = panel.photovoltaicPerformance().to_PhotovoltaicPerformanceSandia().get()
sandiaPerf.setName("Aleo S16 165 [2007 (E)]")
sandiaPerf = panel.photovoltaicPerformance().to_PhotovoltaicPerformanceSandia().get()
sandiaPerf.setActiveArea(1.378)
sandiaPerf.setNumberofCellsinSeries(50)  # Int
sandiaPerf.setNumberofCellsinParallel(1)  # Int
sandiaPerf.setShortCircuitCurrent(7.9)
sandiaPerf.setOpenCircuitVoltage(30.0)
sandiaPerf.setCurrentatMaximumPowerPoint(7.08)
sandiaPerf.setVoltageatMaximumPowerPoint(23.3)
sandiaPerf.setSandiaDatabaseParameteraIsc(0.0008)
sandiaPerf.setSandiaDatabaseParameteraImp(-0.0003)
sandiaPerf.setSandiaDatabaseParameterc0(0.99)
sandiaPerf.setSandiaDatabaseParameterc1(0.01)
sandiaPerf.setSandiaDatabaseParameterBVoc0(-0.11)
sandiaPerf.setSandiaDatabaseParametermBVoc(0.0)
sandiaPerf.setSandiaDatabaseParameterBVmp0(-0.115)
sandiaPerf.setSandiaDatabaseParametermBVmp(0.0)
sandiaPerf.setDiodeFactor(1.35)
sandiaPerf.setSandiaDatabaseParameterc2(-0.12)
sandiaPerf.setSandiaDatabaseParameterc3(-11.08)
sandiaPerf.setSandiaDatabaseParametera0(0.924)
sandiaPerf.setSandiaDatabaseParametera1(0.06749)
sandiaPerf.setSandiaDatabaseParametera2(-0.012549)
sandiaPerf.setSandiaDatabaseParametera3(0.0010049)
sandiaPerf.setSandiaDatabaseParametera4(-2.8797e-05)
sandiaPerf.setSandiaDatabaseParameterb0(1.0)
sandiaPerf.setSandiaDatabaseParameterb1(-0.002438)
sandiaPerf.setSandiaDatabaseParameterb2(0.0003103)
sandiaPerf.setSandiaDatabaseParameterb3(-1.246e-05)
sandiaPerf.setSandiaDatabaseParameterb4(2.11e-07)
sandiaPerf.setSandiaDatabaseParameterb5(-1.36e-09)
sandiaPerf.setSandiaDatabaseParameterDeltaTc(3.0)
sandiaPerf.setSandiaDatabaseParameterfd(1.0)
sandiaPerf.setSandiaDatabaseParametera(-3.56)
sandiaPerf.setSandiaDatabaseParameterb(-0.075)
sandiaPerf.setSandiaDatabaseParameterc4(0.995)
sandiaPerf.setSandiaDatabaseParameterc5(0.005)
sandiaPerf.setSandiaDatabaseParameterIx0(7.8)
sandiaPerf.setSandiaDatabaseParameterIxx0(4.92)
sandiaPerf.setSandiaDatabaseParameterc6(1.15)
sandiaPerf.setSandiaDatabaseParameterc7(-0.15)

panel.setNumberOfModulesInParallel(3)
panel.setNumberOfModulesInSeries(6)
panel.setRatedElectricPowerOutput(20000)
panel.setAvailabilitySchedule(model.alwaysOnDiscreteSchedule())

# create the distribution system
elcd = openstudio.model.ElectricLoadCenterDistribution(model)
elcd.setName("PV ELCD")
elcd.addGenerator(panel)
elcd.setGeneratorOperationSchemeType("Baseload")
elcd.setElectricalBussType("DirectCurrentWithInverter")
elcd.setInverter(inverter)
elcd.setDemandLimitSchemePurchasedElectricDemandLimit(0.0)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
