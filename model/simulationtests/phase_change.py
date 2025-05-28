import openstudio

from lib.baseline_model import BaselineModel

model = BaselineModel()

heat_balance_algorithm = model.getHeatBalanceAlgorithm()
heat_balance_algorithm.setAlgorithm("ConductionFiniteDifference")

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry(length=100, width=50, num_floors=1, floor_to_floor_height=4, plenum_height=0, perimeter_zone_depth=0)

# add windows at a 40% window-to-wall ratio
model.add_windows(wwr=0.4, offset=1, application_type="Above Floor")

# add thermostats
model.add_thermostats(heating_setpoint=24, cooling_setpoint=28)

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

# adjust material that throws because of heat_balance_algorithm.setAlgorithm('ConductionFiniteDifference')
for material in model.getMaterials():
    if "Metal Decking" in material.nameString():
        # ** Severe  ** InitialInitHeatBalFiniteDiff: Found Material that is too thin and/or too highly conductive, material name = METAL DECKING
        # **   ~~~   ** High conductivity Material layers are not well supported by Conduction Finite Difference, material conductivity = 45.006 [W/m-K]
        # **   ~~~   ** Material thermal diffusivity = 1.401E-005 [m2/s]
        # **   ~~~   ** Material with this thermal diffusivity should have thickness > 8.69672E-002 [m]
        # **   ~~~   ** Material may be too thin to be modeled well, thickness = 1.50000E-003 [m]
        # **   ~~~   ** Material with this thermal diffusivity should have thickness > 3.00000E-003 [m]
        material.setThickness(0.09)


# assign material property phase change properties
for surface in model.getSurfaces():
    if surface.surfaceType().lower() == "wall":

        for layer in surface.construction().get().to_Construction().get().layers():
            if not layer.to_StandardOpaqueMaterial().is_initialized():
                continue

            opt_phase_change = layer.to_StandardOpaqueMaterial().get().createMaterialPropertyPhaseChange()
            if opt_phase_change.is_initialized():

                # These from CondFD1ZonePurchAirAutoSizeWithPCM.idf for E1 - 3 / 4 IN PLASTER OR GYP BOARD.
                phase_change = opt_phase_change.get()
                phase_change.setTemperatureCoefficientforThermalConductivity(0)
                phase_change.removeAllTemperatureEnthalpys()
                phase_change.addTemperatureEnthalpy(-20, 0.01)
                phase_change.addTemperatureEnthalpy(22, 18260)
                phase_change.addTemperatureEnthalpy(22.1, 32000)
                phase_change.addTemperatureEnthalpy(60, 71000)

    elif surface.surfaceType().lower() == "floor":

        for layer in surface.construction().get().to_Construction().get().layers():
            if not layer.to_StandardOpaqueMaterial().is_initialized():
                continue

            opt_phase_change_hysteresis = (
                layer.to_StandardOpaqueMaterial().get().createMaterialPropertyPhaseChangeHysteresis()
            )
            if opt_phase_change_hysteresis.is_initialized():

                # These from 1ZoneUncontrolledWithHysteresisPCM.idf for C5 - 4 IN HW CONCRETE.
                phase_change_hysteresis = opt_phase_change_hysteresis.get()
                phase_change_hysteresis.setLatentHeatduringtheEntirePhaseChangeProcess(10000)
                phase_change_hysteresis.setLiquidStateThermalConductivity(1.5)
                phase_change_hysteresis.setLiquidStateDensity(2200)
                phase_change_hysteresis.setLiquidStateSpecificHeat(2000)
                phase_change_hysteresis.setHighTemperatureDifferenceofMeltingCurve(1)
                phase_change_hysteresis.setPeakMeltingTemperature(23)
                phase_change_hysteresis.setLowTemperatureDifferenceofMeltingCurve(1)
                phase_change_hysteresis.setSolidStateThermalConductivity(1.8)
                phase_change_hysteresis.setSolidStateDensity(2300)
                phase_change_hysteresis.setSolidStateSpecificHeat(2000)
                phase_change_hysteresis.setHighTemperatureDifferenceofFreezingCurve(1)
                phase_change_hysteresis.setPeakFreezingTemperature(20)
                phase_change_hysteresis.setLowTemperatureDifferenceofFreezingCurve(1)


# save the OpenStudio model (.osm)
model.save_openstudio_osm(osm_save_directory=None, osm_name="in.osm")
