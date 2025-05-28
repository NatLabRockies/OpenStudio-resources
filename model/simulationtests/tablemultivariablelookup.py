import openstudio

from lib.baseline_model import BaselineModel

m = BaselineModel()

# make a 1 story, 100m X 50m, 5 zone core/perimeter building
m.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=3, plenum_height=1, perimeter_zone_depth=3)

# add windows at a 40% window-to-wall ratio
m.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# Add ASHRAE System type 07, VAV w/ Reheat, this creates a ChW, a HW loop and a
# Condenser Loop
m.add_hvac(ashrae_sys_num="07")

# add thermostats
m.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

# assign constructions from a local library to the walls/windows/etc. in the model
m.set_constructions()

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
m.set_space_type()

# add design days to the model (Chicago)
m.add_design_days()

###############################################################################
#         R E P L A C E    A T Us    W/    F O U R    P I P E    B E A Ms
###############################################################################

ct = m.getCoolingTowerSingleSpeeds()[0]
p_cnd = ct.plantLoop().get()

b = m.getBoilerHotWaters()[0]
p_hw = b.plantLoop().get()

ch = m.getChillerElectricEIRs()[0]
p_chw = ch.plantLoop().get()

# Recreate the same TableMultiVariableLookup/TableLookup that is created in
# the Ctor for CoilCoolingFourPipeBeam, except with a normalization reference
# The goal being to test the NormalizationReference feature since the E+ 9.2.0
# change to TableLookup, we pick one.
norm_ref = 2.4

if openstudio.VersionString(openstudio.openStudioVersion()) > openstudio.VersionString("3.4.0"):
    coolCapModFuncOfWaterFlow = openstudio.model.TableLookup(m)

    coolCapModFuncOfWaterFlow.setName("CoolCapModFuncOfWaterFlow")
    coolCapModFuncOfWaterFlow.setOutputUnitType("Dimensionless")

    coolCapModFuncOfWaterFlow.setMinimumOutput(0.0 * norm_ref)
    coolCapModFuncOfWaterFlow.setMaximumOutput(1.04 * norm_ref)

    coolCapModFuncOfWaterFlow.setNormalizationMethod("DivisorOnly")
    coolCapModFuncOfWaterFlow.setNormalizationDivisor(norm_ref)
    values = [0.0, 0.001, 0.71, 0.85, 0.92, 0.97, 1.0, 1.04]
    values = [v * norm_ref for v in values]
    coolCapModFuncOfWaterFlow.setOutputValues(values)

    coolCapModFuncOfWaterFlowVar1 = openstudio.model.TableIndependentVariable(m)
    coolCapModFuncOfWaterFlow.addIndependentVariable(coolCapModFuncOfWaterFlowVar1)
    coolCapModFuncOfWaterFlowVar1.setName("CoolCapModFuncOfWaterFlow_IndependentVariable1")
    coolCapModFuncOfWaterFlowVar1.setInterpolationMethod("Cubic")
    coolCapModFuncOfWaterFlowVar1.setExtrapolationMethod("Constant")
    coolCapModFuncOfWaterFlowVar1.setMinimumValue(0.0)
    coolCapModFuncOfWaterFlowVar1.setMaximumValue(1.33)
    coolCapModFuncOfWaterFlowVar1.setUnitType("Dimensionless")
    coolCapModFuncOfWaterFlowVar1.setValues([0.0, 0.05, 0.33333, 0.5, 0.666667, 0.833333, 1.0, 1.333333])
else:
    coolCapModFuncOfWaterFlow = openstudio.model.TableMultiVariableLookup(m, 1)
    coolCapModFuncOfWaterFlow.setName("CoolCapModFuncOfWaterFlow")

    coolCapModFuncOfWaterFlow.setCurveType("Quadratic")
    coolCapModFuncOfWaterFlow.setInterpolationMethod("EvaluateCurveToLimits")
    coolCapModFuncOfWaterFlow.setMinimumValueofX1(0)
    coolCapModFuncOfWaterFlow.setMaximumValueofX1(1.33)
    coolCapModFuncOfWaterFlow.setInputUnitTypeforX1("Dimensionless")
    coolCapModFuncOfWaterFlow.setOutputUnitType("Dimensionless")

    coolCapModFuncOfWaterFlow.setNormalizationReference(norm_ref)

    # Quoting I/O ref for 9.1:
    # > Both the output values and minimum/maximum curve limits
    # > are normalized as applicable.
    coolCapModFuncOfWaterFlow.setMinimumTableOutput(0.0 * norm_ref)
    coolCapModFuncOfWaterFlow.setMaximumTableOutput(1.04 * norm_ref)

    coolCapModFuncOfWaterFlow.addPoint(0.0, 0.0 * norm_ref)
    coolCapModFuncOfWaterFlow.addPoint(0.05, 0.001 * norm_ref)
    coolCapModFuncOfWaterFlow.addPoint(0.33333, 0.71 * norm_ref)
    coolCapModFuncOfWaterFlow.addPoint(0.5, 0.85 * norm_ref)
    coolCapModFuncOfWaterFlow.addPoint(0.666667, 0.92 * norm_ref)
    coolCapModFuncOfWaterFlow.addPoint(0.833333, 0.97 * norm_ref)
    coolCapModFuncOfWaterFlow.addPoint(1.0, 1.0 * norm_ref)  # <= RATING POINT
    coolCapModFuncOfWaterFlow.addPoint(1.333333, 1.04 * norm_ref)


# Replace all terminals with ATUFourPipeBeams
# There is only one airLoopHVAC, so I get it here
air_loop = m.getAirLoopHVACs()[0]

# In order to produce more consistent results between different runs,
# we sort the zones by names
zones = sorted(m.getThermalZones(), key=lambda z: z.nameString())
for z in zones:
    # air_loop = z.airLoopHVAC.get
    air_loop.removeBranchForZone(z)

    # Create a cooling coil, and add it to the ChW Loop
    cc = openstudio.model.CoilCoolingFourPipeBeam(m)
    cc.setName("#{z.name()} ATU FourPipeBeam Cooling Coil")
    # Set the curve with the above table
    cc.setBeamCoolingCapacityChilledWaterFlowModificationFactorCurve(coolCapModFuncOfWaterFlow)
    p_chw.addDemandBranchForComponent(cc)

    # Create a heating coil, and add it to the HW Loop
    hc = openstudio.model.CoilHeatingFourPipeBeam(m)
    hc.setName("#{z.name()} ATU FourPipeBeam Heating Coil")
    p_hw.addDemandBranchForComponent(hc)

    atu = openstudio.model.AirTerminalSingleDuctConstantVolumeFourPipeBeam(m, cc, hc)
    atu.setName("#{z.name()} ATU FourPipeBeam")
    air_loop.addBranchForZone(z, atu.to_StraightComponent())

    z.zoneAirNode().setName("#{z.name()} Zone Air Node")


# All setters:

# ATU
# atu.setPrimaryAirAvailabilitySchedule()
# atu.setCoolingAvailabilitySchedule()
# atu.setHeatingAvailabilitySchedule()
# atu.setCoolingCoil()
# atu.setHeatingCoil()
# atu.setDesignPrimaryAirVolumeFlowRate()
# atu.setDesignChilledWaterVolumeFlowRate()
# atu.setDesignHotWaterVolumeFlowRate()
# atu.setZoneTotalBeamLength()
# atu.setRatedPrimaryAirFlowRateperBeamLength()

# CoilCoolingFourPipeBeam
# cc.setBeamRatedCoolingCapacityperBeamLength()
# cc.setBeamRatedCoolingRoomAirChilledWaterTemperatureDifference()
# cc.setBeamRatedChilledWaterVolumeFlowRateperBeamLength()
# cc.setBeamCoolingCapacityTemperatureDifferenceModificationFactorCurve()
# cc.setBeamCoolingCapacityAirFlowModificationFactorCurve()
# cc.setBeamCoolingCapacityChilledWaterFlowModificationFactorCurve()

# CoilHeatingFourPipeBeam

###############################################################################
#         R E N A M E    E Q U I P M E N T    A N D    N O D E S
###############################################################################

# Remove pipes
[x.remove() for x in m.getPipeAdiabatics()]

# Rename loops
p_cnd.setName("CndW Loop")
p_hw.setName("HW Loop")
p_chw.setName("ChW Loop")

m.getCoilCoolingWaters()[0].setName("VAV Central ChW Coil")

for coil in m.getCoilHeatingWaters():
    if not coil.airLoopHVAC().is_initialized():
        continue

    coil.setName("VAV Central HW Coil")

m.rename_air_nodes()
m.rename_loop_nodes()

########################### Request output variables ##########################

add_out_vars = False
freq = "Detailed"

if add_out_vars:
    atu = m.getAirTerminalSingleDuctConstantVolumeFourPipeBeams()[0]
    # CentralHeatPumpSystem outputs, implemented in the class
    for varname in atu.outputVariableNames():
        outvar = openstudio.model.OutputVariable(varname, m)
        outvar.setReportingFrequency(freq)


# save the OpenStudio model (.osm)
m.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
