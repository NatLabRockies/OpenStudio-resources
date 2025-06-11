from pathlib import Path

import openstudio
import pandas as pd
from lib.baseline_model import BaselineModel

# This test mimics the E+ example file ThermochromicWindow.idf
THERMOCHROMIC_PATH = Path(__file__).parent / "thermochromic_spectral_data.csv"
assert THERMOCHROMIC_PATH.is_file(), f"Thermochromic spectral data file not found at '{THERMOCHROMIC_PATH}'"

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

sub_surfaces = sorted(
    [ss for ss in model.getSubSurfaces() if ss.subSurfaceType().lower() == "fixedwindow"], key=lambda ss: ss.azimuth()
)
assert len(sub_surfaces) == 4, f"Expected 4 SubSurfaces, found {len(sub_surfaces)}"

# Get the South window
sub_surface = next(ss for ss in sub_surfaces if abs(openstudio.radToDeg(ss.azimuth()) - 180.0) < 0.01)

construction = openstudio.model.Construction(model)
construction.setName("TCWindow")

mat_clear_3mm = model.getStandardGlazingByName("000_Clear 3mm").get()
air_3mm = openstudio.model.Gas(model)
air_3mm.setName("Air 3mm")
air_3mm.setGasType("Air")
air_3mm.setThickness(0.003)

t = openstudio.model.ThermochromicGlazing(model)
t.setName("TCGlazing")
# There are rules about the layers in a multi-layered window construction in E+, see this eplusout.err message from
# 25.1.0
#   ** Severe  ** CheckAndSetConstructionProperties: Error in window construction TCWINDOW--
#   **   ~~~   **   For multi-layer window constructions the following rules apply:
#   **   ~~~   **     --The first and last layer must be a solid layer (glass or shade/screen/blind),
#   **   ~~~   **     --Adjacent glass layers must be separated by one and only one gas layer,
#   **   ~~~   **     --Adjacent layers must not be of the same type,


assert construction.setLayers([mat_clear_3mm, air_3mm, t, air_3mm, mat_clear_3mm])
assert sub_surface.setConstruction(construction)

df = pd.read_csv(THERMOCHROMIC_PATH, index_col=0, dtype="float")
df.index = df.index.astype(int)
for i, (opticalDataTemperature, sub_df) in enumerate(df.groupby("opticalDataTemperature")):
    s = openstudio.model.StandardGlazing(model)
    s.setName(f"WO18RT{opticalDataTemperature:.0f}")
    s.setThickness(0.0075)

    s.resetSolarTransmittanceatNormalIncidence()
    s.resetFrontSideSolarReflectanceatNormalIncidence()
    s.resetBackSideSolarReflectanceatNormalIncidence()
    s.resetVisibleTransmittanceatNormalIncidence()
    s.resetFrontSideVisibleReflectanceatNormalIncidence()
    s.resetBackSideVisibleReflectanceatNormalIncidence()

    s.setInfraredTransmittance(0.0)
    s.setFrontSideInfraredHemisphericalEmissivity(0.44)
    s.setBackSideInfraredHemisphericalEmissivity(0.84)
    s.setConductivity(0.6)
    s.setDirtCorrectionFactorforSolarandVisibleTransmittance(1.0)
    s.setSolarDiffusing(False)

    data_set = openstudio.model.MaterialPropertyGlazingSpectralData(model)
    s.setWindowGlassSpectralDataSet(data_set)
    s.setOpticalDataType("Spectral")

    data_set.setName(f"WO18RT{opticalDataTemperature:.0f}SP")
    for _, row in sub_df.iterrows():
        data_set.addSpectralDataField(
            row["wavelength"], row["transmittance"], row["frontReflectance"], row["backReflectance"]
        )

    if i % 2 == 0:
        assert t.addThermochromicGroup(s, opticalDataTemperature)
    else:
        group = openstudio.model.ThermochromicGroup(s, opticalDataTemperature)
        assert t.addThermochromicGroup(group)

# This is a no-op, but demonstrates the API for the extensible groups
groups = t.thermochromicGroups()
assert len(df.index.unique()) == len(groups), f"Expected {len(df.index.unique())} groups, found {len(groups)}"
assert t.thermochromicGroupIndex(groups[0]).get() == 0, "Expected first group index to be 0"
assert t.removeThermochromicGroup(0)  # Remove the first group
assert t.numberofThermochromicGroups() == len(groups) - 1, "Expected one less group after removal"
t.removeAllThermochromicGroups()  # Remove all groups
assert t.numberofThermochromicGroups() == 0, "Expected no groups after removal"
# Use the vector method
assert t.addThermochromicGroups(groups)
assert len(df.index.unique()) == len(groups), f"Expected {len(df.index.unique())} groups, found {len(groups)}"

add_out_vars = False
if add_out_vars:
    freq = "Timestep"

    # These variables are actually on the Glazed Surface that uses the Construction that references this ThermochromicGlazing
    var_names = [
        "Surface Window Thermochromic Layer Temperature",
        "Surface Window Thermochromic Layer Property Specification Temperature",
    ]

    for varname in t.outputVariableNames():
        outvar = openstudio.model.OutputVariable(varname, model)
        outvar.setReportingFrequency(freq)

# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
