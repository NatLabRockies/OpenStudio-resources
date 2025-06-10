# frozen_string_literal: true

require 'openstudio'
require_relative 'lib/baseline_model'
require 'csv'
require 'pathname'

# This test mimics the E+ example file ThermochromicWindow.idf
THERMOCHROMIC_PATH = Pathname.new(__dir__) / 'thermochromic_spectral_data.csv'
raise "Thermochromic data file not found at #{THERMOCHROMIC_PATH}" unless THERMOCHROMIC_PATH.exist?

# Create a new baseline model
model = BaselineModel.new

# make a 1 story, 100m X 50m, 1 zone building
model.add_geometry({ 'length' => 100,
                     'width' => 50,
                     'num_floors' => 1,
                     'floor_to_floor_height' => 4,
                     'plenum_height' => 0,
                     'perimeter_zone_depth' => 0 })

# add windows at a 40% window-to-wall ratio
model.add_windows({ 'wwr' => 0.4,
                    'offset' => 1,
                    'application_type' => 'Above Floor' })

# add thermostats
model.add_thermostats({ 'heating_setpoint' => 19,
                        'cooling_setpoint' => 26 })

# assign constructions from a local library to the walls/windows/etc. in the model
model.set_constructions

# set whole building space type; simplified 90.1-2004 Large Office Whole Building
model.set_space_type

# add design days to the model (Chicago)
model.add_design_days

sub_surfaces = model.getSubSurfaces.select { |ss| ss.subSurfaceType.downcase == 'fixedwindow' }.sort_by(&:azimuth)
raise "Expected 4 SubSurfaces, found #{sub_surfaces.size}" unless sub_surfaces.size == 4

# Get the South window (azimuth near 180 degrees)
sub_surface = sub_surfaces.find do |ss|
  (OpenStudio.radToDeg(ss.azimuth) - 180.0).abs < 0.01
end

construction = OpenStudio::Model::Construction.new(model)
construction.setName('TCWindow')

mat_clear_3mm = model.getStandardGlazingByName('000_Clear 3mm').get
air_3mm = OpenStudio::Model::Gas.new(model)
air_3mm.setName('Air 3mm')
air_3mm.setGasType('Air')
air_3mm.setThickness(0.003)

t = OpenStudio::Model::ThermochromicGlazing.new(model)
t.setName('TCGlazing')

raise 'Failed to set construction layers' unless construction.setLayers([mat_clear_3mm, air_3mm, t, air_3mm, mat_clear_3mm])
raise 'Failed to assign construction to sub_surface' unless sub_surface.setConstruction(construction)

# Read CSV and convert all fields to float, group by opticalDataTemperature
data = CSV.read(THERMOCHROMIC_PATH, headers: true, converters: :float)

# Group rows by opticalDataTemperature column
groups = data.group_by { |row| row['opticalDataTemperature'].to_i }

groups.each_with_index do |(opticalDataTemperature, rows), i|
  s = OpenStudio::Model::StandardGlazing.new(model)
  s.setName("WO18RT#{opticalDataTemperature}")
  s.setThickness(0.0075)

  s.resetSolarTransmittanceatNormalIncidence
  s.resetFrontSideSolarReflectanceatNormalIncidence
  s.resetBackSideSolarReflectanceatNormalIncidence
  s.resetVisibleTransmittanceatNormalIncidence
  s.resetFrontSideVisibleReflectanceatNormalIncidence
  s.resetBackSideVisibleReflectanceatNormalIncidence

  s.setInfraredTransmittance(0.0)
  s.setFrontSideInfraredHemisphericalEmissivity(0.44)
  s.setBackSideInfraredHemisphericalEmissivity(0.84)
  s.setConductivity(0.6)
  s.setDirtCorrectionFactorforSolarandVisibleTransmittance(1.0)
  s.setSolarDiffusing(false)

  data_set = OpenStudio::Model::MaterialPropertyGlazingSpectralData.new(model)
  s.setWindowGlassSpectralDataSet(data_set)
  s.setOpticalDataType('Spectral')

  data_set.setName("WO18RT#{opticalDataTemperature}SP")

  rows.each do |row|
    data_set.addSpectralDataField(
      row['wavelength'],
      row['transmittance'],
      row['frontReflectance'],
      row['backReflectance']
    )
  end

  if i.even?
    raise 'Failed to add ThermochromicGroup' unless t.addThermochromicGroup(s, opticalDataTemperature)
  else
    group = OpenStudio::Model::ThermochromicGroup.new(s, opticalDataTemperature)
    raise 'Failed to add ThermochromicGroup object' unless t.addThermochromicGroup(group)
  end
end

groups_list = t.thermochromicGroups
raise "Expected #{groups.size} groups, found #{groups_list.size}" unless groups.size == groups_list.size
raise 'Expected first group index to be 0' unless t.thermochromicGroupIndex(groups_list.first).get == 0
raise 'Failed to remove first group' unless t.removeThermochromicGroup(0)
raise 'Unexpected number of groups after removal' unless t.numberofThermochromicGroups == groups_list.size - 1

t.removeAllThermochromicGroups
raise 'Groups not all removed' unless t.numberofThermochromicGroups == 0
raise 'Failed to add ThermochromicGroups' unless t.addThermochromicGroups(groups_list)
raise "Expected #{groups.size} groups after add, found #{t.numberofThermochromicGroups}" unless groups.size == t.numberofThermochromicGroups

add_out_vars = false
if add_out_vars
  freq = 'Timestep'

  # These variables are actually on the Glazed Surface that uses the Construction that references this ThermochromicGlazing
  var_names = [
    'Surface Window Thermochromic Layer Temperature',
    'Surface Window Thermochromic Layer Property Specification Temperature'
  ]

  t.outputVariableNames.each do |varname|
    outvar = OpenStudio::Model::OutputVariable.new(varname, model)
    outvar.setReportingFrequency(freq)
  end
end

# save the OpenStudio model (.osm)
model.save_openstudio_osm({ 'osm_save_directory' => Dir.pwd,
                            'osm_name' => 'in.osm' })
