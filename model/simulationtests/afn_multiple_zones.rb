# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'

model = BaselineModel.new

# make a 2 story, 100m X 50m, 2 zone building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 2,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add ASHRAE System type 08, VAV w/ PFP Boxes
# DLM: this invokes weird mass conservation rules with VAV
# model.add_hvac({"ashrae_sys_num" => '08'})

# add thermostats
# model.add_thermostats({"heating_setpoint" => 24, "cooling_setpoint" => 28})

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# remove all infiltration
model.getSpaceInfiltrationDesignFlowRates.each(&:remove)

# add design days to the model (Chicago)
model.add_design_days

# add simulation control
afn_control = model.getAirflowNetworkSimulationControl
afn_control.setAirflowNetworkControl('MultizoneWithoutDistribution')

zones = model.getThermalZones

surfaces = []
adjacent_surfaces = []
sub_surfaces = []

spaces = zones[0].spaces + zones[1].spaces
spaces.each do |space|
  space.surfaces.each do |surface|
    if surface.outsideBoundaryCondition.start_with?('Outdoors') && surface.surfaceType.start_with?('Wall')
      surfaces << surface
    elsif surface.adjacentSurface.is_initialized
      adjacent_surfaces << surface
    end
  end

  space.surfaces.each do |surface|
    surface.subSurfaces.each do |sub_surface|
      sub_surfaces << sub_surface
    end
  end
end

# In order to produce more consistent results between different runs,
# we sort the objects by names
surfaces = surfaces.sort_by { |s| s.name.to_s }
adjacent_surfaces = adjacent_surfaces.sort_by { |as| as.name.to_s }
sub_surfaces = sub_surfaces.sort_by { |ss| ss.name.to_s }

# make afn zones
afnzone1 = zones[0].getAirflowNetworkZone
afnzone2 = zones[1].getAirflowNetworkZone
afnzone1.setMinimumVentingOpenFactor(0.1)
afnzone2.setMinimumVentingOpenFactor(0.2)

# Simple Opening
simpleOpening = OpenStudio::Model::AirflowNetworkSimpleOpening.new(model, 1.0, 0.65, 0.5, 0.5)
afnsurf1 = sub_surfaces[0].getAirflowNetworkSurface(simpleOpening)
afnsurf1.setWindowDoorOpeningFactorOrCrackFactor(0.1)

# Detailed Opening
data = OpenStudio::Model::DetailedOpeningFactorDataVector.new
data << OpenStudio::Model::DetailedOpeningFactorData.new(0.0, 0.01, 0.0, 0.0, 0.0)
data << OpenStudio::Model::DetailedOpeningFactorData.new(1.0, 0.5, 1.0, 1.0, 0.0)
detailedOpening = OpenStudio::Model::AirflowNetworkDetailedOpening.new(model, 1.0, data)
afnsurf2 = sub_surfaces[1].getAirflowNetworkSurface(detailedOpening)
afnsurf2.setWindowDoorOpeningFactorOrCrackFactor(0.2)

# Horizontal Opening
adjacent_surface = adjacent_surfaces[0]

p = OpenStudio::Point3dVector.new
p << OpenStudio::Point3d.new(0, 0, 0)
p << OpenStudio::Point3d.new(1, 0, 0)
p << OpenStudio::Point3d.new(1, 1, 0)
p << OpenStudio::Point3d.new(0, 1, 0)
sub_surface = OpenStudio::Model::SubSurface.new(p, model)
sub_surface.setSurface(adjacent_surface)
sub_surface.setSubSurfaceType('Door')

adjacent_sub_surface = OpenStudio::Model::SubSurface.new(sub_surface.vertices.reverse, model)
adjacent_sub_surface.setSurface(adjacent_surface.adjacentSurface.get)
adjacent_sub_surface.setSubSurfaceType('Door')
sub_surface.setAdjacentSubSurface(adjacent_sub_surface)

horizontalOpening = OpenStudio::Model::AirflowNetworkHorizontalOpening.new(model, 0.5, 0.65, 90.0, 0.5)
horizontalOpeningSurface = sub_surface
horizontalOpeningSurface.getAirflowNetworkSurface(horizontalOpening)

# Effective Leakage Area
effectiveLeakageArea = OpenStudio::Model::AirflowNetworkEffectiveLeakageArea.new(model, 1.0, 1.0, 4.0, 0.65)
surfaces[0].getAirflowNetworkSurface(effectiveLeakageArea)
effectiveLeakageArea = OpenStudio::Model::AirflowNetworkEffectiveLeakageArea.new(model, 2.0, 1.0, 4.0, 0.65)
surfaces[4].getAirflowNetworkSurface(effectiveLeakageArea)

# Specified Flow Rate
specifiedFlowRate = OpenStudio::Model::AirflowNetworkSpecifiedFlowRate.new(model, 10.0)
surfaces[1].getAirflowNetworkSurface(specifiedFlowRate)

# add output reports
add_out_vars = false
if add_out_vars
  OpenStudio::Model::OutputVariable.new('AFN Node Temperature', model)
  OpenStudio::Model::OutputVariable.new('AFN Node Wind Pressure', model)
  OpenStudio::Model::OutputVariable.new('AFN Linkage Node 1 to Node 2 Mass Flow Rate', model)
  OpenStudio::Model::OutputVariable.new('AFN Linkage Node 1 to Node 2 Pressure Difference', model)
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
