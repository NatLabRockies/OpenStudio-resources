import openstudio

model = openstudio.model.exampleModel()

lifeCycleCostParameters = model.getLifeCycleCostParameters()
lifeCycleCostParameters.setAnalysisType("FEMP")
lifeCycleCostParameters.setLengthOfStudyPeriodInYears(25)

for construction in model.getConstructions():
    if openstudio.VersionString(openstudio.openStudioVersion()) < openstudio.VersionString("2.9.0"):
        # At 2.9.0 and above, the ConstructionAirBoundary is used, and it's not
        # part of the m.getConstructions
        layers = construction.layers()
        if len(layers) == 1 and layers[0].to_AirWallMaterial().is_initialized():
            continue

    material_cost = openstudio.model.LifeCycleCost.createLifeCycleCost(
        "Material Cost", construction, 10.0, "CostPerArea", "Construction", 10, 0
    )
    demolition_cost = openstudio.model.LifeCycleCost.createLifeCycleCost(
        "Demolition Cost", construction, 2.0, "CostPerArea", "Replacement", 10, 10
    )
    salvage_cost = openstudio.model.LifeCycleCost.createLifeCycleCost(
        "Salvage Cost", construction, -1.0, "CostPerArea", "Replacement", 10, 10
    )
    maintenance_cost = openstudio.model.LifeCycleCost.createLifeCycleCost(
        "Maintenance Cost", construction, 1.0, "CostPerArea", "Maintenance", 1, 1
    )


# save the OpenStudio model (.osm)
model.save("in.osm", True)
