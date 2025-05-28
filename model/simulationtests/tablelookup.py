import openstudio

from lib.baseline_model import BaselineModel

m = BaselineModel()

# make a 1 story, 100m X 50m, 1 zone core/perimeter building
m.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=3, plenum_height=1, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
m.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# Add ASHRAE System type 02, PTHP
m.add_hvac(ashrae_sys_num="02")

# add thermostats
m.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type()

# add design days to the model (Chicago)
m.add_design_days()

# There is only one, but to be safe, sort by name
cc = sorted(m.getCoilCoolingDXSingleSpeeds(), key=lambda c: c.nameString())[0]

# wet-bulb temperature of air entering coil
tiwb = openstudio.model.TableIndependentVariable(m)
tiwb.setName("Tiwb")
tiwb.setInterpolationMethod("Cubic")
tiwb.setExtrapolationMethod("Constant")
tiwb.setMinimumValue(12.77778)
tiwb.setMaximumValue(23.88889)
tiwb.setNormalizationReferenceValue(19.44449)
tiwb.setUnitType("Temperature")
tiwb.setValues([12.77778, 15.0, 18.0, 21.0, 23.88889])

# dry-bulb temperature of outdoor air entering condenser coil
todb = openstudio.model.TableIndependentVariable(m)
todb.setName("Todb")
todb.setInterpolationMethod("Cubic")
todb.setExtrapolationMethod("Constant")
todb.setMinimumValue(18.0)
todb.setMaximumValue(46.11111)
todb.setNormalizationReferenceValue(35.0)
todb.setUnitType("Temperature")
todb.setValues([18.0, 24.0, 30.0, 36.0, 41.0, 46.11111])

hpacCoolCapFT = openstudio.model.TableLookup(m)
hpacCoolCapFT.addIndependentVariable(tiwb)
hpacCoolCapFT.addIndependentVariable(todb)
hpacCoolCapFT.setName("HPACCoolCapFT")
hpacCoolCapFT.setNormalizationMethod("AutomaticWithDivisor")
hpacCoolCapFT.setNormalizationDivisor(1.0)
hpacCoolCapFT.setMinimumOutput(0.0)
hpacCoolCapFT.setMaximumOutput(40000.0)
hpacCoolCapFT.setOutputUnitType("Dimensionless")
hpacCoolCapFT.setOutputValues(
    [
        24421.69383,
        22779.73113,
        21147.21662,
        19524.15032,
        18178.81244,
        16810.36004,
        25997.3589,
        24352.1562,
        22716.4017,
        21090.0954,
        19742.05753,
        18370.84513,
        28392.31868,
        26742.74198,
        25102.61348,
        23471.93318,
        22120.2503,
        20745.3119,
        31094.97495,
        29441.02425,
        27796.52175,
        26161.46745,
        24806.13958,
        23427.47518,
        33988.3473,
        32330.1846,
        30681.4701,
        29042.2038,
        27683.36592,
        26301.11353,
    ]
)

hpacCoolEIRFT = openstudio.model.TableLookup(m)
hpacCoolEIRFT.addIndependentVariable(tiwb)
hpacCoolEIRFT.addIndependentVariable(todb)
hpacCoolEIRFT.setName("HPACCoolEIRFT")
hpacCoolEIRFT.setNormalizationMethod("None")
hpacCoolEIRFT.setNormalizationDivisor(1.0)
hpacCoolEIRFT.setOutputUnitType("Dimensionless")
hpacCoolEIRFT.setOutputValues(
    [
        0.750374374,
        0.834785832,
        0.950729763,
        1.098206165,
        1.277215039,
        1.418073932,
        0.760275481,
        0.834979909,
        0.941216809,
        1.078986181,
        1.248288025,
        1.382495806,
        0.763612751,
        0.823902225,
        0.91572417,
        1.039078588,
        1.193965478,
        1.318296348,
        0.752843265,
        0.798280967,
        0.875251142,
        0.983753788,
        1.123788906,
        1.237943566,
        0.738279952,
        0.774156215,
        0.84156495,
        0.940506158,
        1.070979837,
        1.178583142,
    ]
)

cc.setTotalCoolingCapacityFunctionOfTemperatureCurve(hpacCoolCapFT)
cc.setEnergyInputRatioFunctionOfTemperatureCurve(hpacCoolEIRFT)

# save the OpenStudio model (.osm)
m.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
