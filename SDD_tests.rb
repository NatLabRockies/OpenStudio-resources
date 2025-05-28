# frozen_string_literal: true

require 'openstudio' unless defined?(OpenStudio)
# TODO: not in openstudio gems...
# require 'equivalent-xml'

# The config and helpers are inside this file
require_relative 'test_helpers'

###############################################################################
#                     For comparison, pass ENV variables                      #
###############################################################################

$IsCompareOK = true
if ENV['OLD_VERSION'].nil?
  $IsCompareOK = false
else
  $Old_Version = ENV['OLD_VERSION']
end
if ENV['NEW_VERSION'].nil?
  $IsCompareOK = false
else
  $New_Version = ENV['NEW_VERSION']
end

$all_model_paths = Dir.glob(File.join($ModelDir, '*.osm'))
$all_sddsimxml_paths = Dir.glob(File.join($SddSimDir, '*.xml'))

def apply_known_ft_changes(doc_new)
  # Previously, CoilHtg was incorrectly mapped to CoilClg
  doc_new.xpath('//CoilHtg').each do |node|
    node.name = 'CoilClg'
  end

  return doc_new
end

# Disable the logger (Switch to enable otherwise)
OpenStudio::Logger.instance.standardOutLogger.disable
# If enabled, set the LogLevel (Error, Warn, Info, Debug, Trace)
OpenStudio::Logger.instance.standardOutLogger.setLogLevel(OpenStudio::Error)

# This is the sanitzed filename, with ' - ap.xml'
$Disabled_RT_Tests = [
  # These make both 2.7.1 and 2.7.2 hard crash
  # 'OffSml_MiniSplit',

]

# Runs a single SddReverseTranslator path given the name of a SDD SIM XML file
# It will raise if the path (or the model) isn't valid
#
# @param sddsimxml_path [String] The name of the XML, eg: 'blabla.xml'
# It will go look in SddSimDir for this will
# @return None. Will assert that the model can be RT'ed, and save it in
# $TestDirSddRT for comparison
def sdd_ft_test(osm_path)
  full_path = File.join($ModelDir, osm_path)

  filename = File.basename(osm_path) # .gsub('.osm', '')

  # Load Model
  translator = OpenStudio::OSVersion::VersionTranslator.new
  _m = translator.loadModel(OpenStudio::Path.new(full_path))
  assert _m.is_initialized, "Could not Load #{osm_path}"
  m = _m.get

  # We save in the test/ folder like the OSW for sim_tests
  sdd_out = File.join($TestDirSddFT, "#{filename}_#{$SdkVersion}_out#{$Custom_tag}.xml")
  ft = OpenStudio::SDD::SddForwardTranslator.new
  test = ft.modelToSDD(m, sdd_out)
  assert test, "Failed SDD FT for #{filename}"
end

# Runs a single SddReverseTranslator path given the name of a SDD SIM XML file
# It will raise if the path (or the model) isn't valid
#
# @param sddsimxml_path [String] The name of the XML, eg: 'blabla.xml'
# It will go look in SddSimDir for this will
# @return None. Will assert that the model can be RT'ed, and save it in
# $TestDirSddRT for comparison
def sdd_rt_test(sddsimxml_path)
  full_path = File.join($SddSimDir, sddsimxml_path)

  filename = escapeName(sddsimxml_path.gsub(' - ap.xml', '.xml'))

  # puts "\nRunning for #{filename}"
  # puts "Loading #{full_path}"

  if $Disabled_RT_Tests.include?(filename)
    skip "Test is disabled for #{filename}"
  end
  rt = OpenStudio::SDD::SddReverseTranslator.new
  _m = rt.loadModel(full_path)
  # Test that RT Worked
  assert _m.is_initialized, "Failed SDD RT for #{filename}"

  # Need to add the DDY
  m = add_design_days(_m.get)

  # If so, then save resulting OSM for diffing
  m_out = File.join($TestDirSddRT, filename)
  # puts "Saving at #{m_out}"

  m.save(m_out, true)

  # Now do the sim_test portion!
  sim_test(filename, { base_dir: $TestDirSddRT })
  # m_out = File.join($TestDirSddRT, "#{filename}_#{$SdkVersion}_out#{$Custom_tag}.osm")
end

class SddForwardTranslatorTests < Minitest::Test
  parallelize_me!

  # TODO: re-enable
  # To be called manually after both the old and new have run
  # TODO: Should also probably make it a method that would be called at the end
  # of each sdd_ft_test (similar to what I've done for sim_tests)
  #   def test_FT_compare
  #
  #     if not $IsCompareOK
  #       skip "You must pass the environment variables " +
  #            "OLD_VERSION & NEW_VERSION in order to run " +
  #            "the SddForwardTranslator_compare test.\n" +
  #            "eg: `OLD_VERSION=2.7.1 NEW_VERSION=2.7.2 ruby SDD_tests.rb -n /compare/`"
  #     end
  #
  #     puts "Running XML Diffs for #{$Old_Version} > #{$New_Version}"
  #
  #     all_old_sdds = Dir.glob(File.join($TestDirSddFT, "*#{$Old_Version}_out.xml"))
  #     puts "Discovered #{all_old_sdds.size} SDD XMLs to compare"
  #     all_old_sdds.each do |sdd_ori|
  #       sdd_new = sdd_ori.sub($Old_Version, $New_Version)
  #       assert File.exist?(sdd_new)
  #       doc_ori = File.open(sdd_ori) {|f| Nokogiri::XML(f) };
  #       doc_new = File.open(sdd_new) {|f| Nokogiri::XML(f) };
  #
  #       # Known-changes to XML structure itself
  #       doc_new = apply_known_ft_changes(doc_new)
  #
  #       # Local only ignores
  #       opts = { :element_order => false, :normalize_whitespace => true }
  #       if sdd_ori.include?('scheduled_infiltration.osm_2.7.1_out.xml')
  #         # BlgAz is "0" in ori, '-0' in new
  #         opts[:ignore_content] = ["Proj > Bldg > BldgAz"]
  #       end
  #
  #       # Assert XMLs are the same
  #       assert EquivalentXml.equivalent?(doc_ori, doc_new, opts), "Failed: #{sdd_ori}"
  #
  #     end
  #   end

  #  Note: JM 2019-01-18
  #  Not used because you can't parallelize this
  #

  # Dynamically create the SddForwardTranslator tests
  # by discovering all OSMs in model/simulationtests
  # $all_model_paths.each do |model_path|
  #  filename = escapeName(File.basename(model_path).gsub('.osm', ''))
  #  define_method("test_FT_#{filename}") do
  #    sdd_ft_test(File.basename(model_path))
  #  end
  # end

  ###############################################################################
  #                           Hardcoded SDD FT Tests                            #
  ###############################################################################

  def test_FT_absorption_chillers
    sdd_ft_test('absorption_chillers.osm')
  end

  def test_FT_additional_props
    sdd_ft_test('additional_props.osm')
  end

  def test_FT_adiabatic_construction_set
    sdd_ft_test('adiabatic_construction_set.osm')
  end

  # TODO: not enabled in model_tests.rb yet
  # def test_FT_afn_single_zone_ac
  #   sdd_ft_test('afn_single_zone_ac.osm')
  # end

  def test_FT_afn_single_zone_nv
    sdd_ft_test('afn_single_zone_nv.osm')
  end

  def test_FT_air_chillers
    sdd_ft_test('air_chillers.osm')
  end

  def test_FT_air_terminals
    sdd_ft_test('air_terminals.osm')
  end

  def test_FT_airloop_and_zonehvac
    sdd_ft_test('airloop_and_zonehvac.osm')
  end

  def test_FT_airloop_avms
    sdd_ft_test('airloop_avms.osm')
  end

  def test_FT_airterminal_cooledbeam
    sdd_ft_test('airterminal_cooledbeam.osm')
  end

  def test_FT_airterminal_fourpipebeam
    sdd_ft_test('airterminal_fourpipebeam.osm')
  end

  def test_FT_airterminal_inletsidemixer
    sdd_ft_test('airterminal_inletsidemixer.osm')
  end

  def test_FT_asymmetric_interior_constructions
    sdd_ft_test('asymmetric_interior_constructions.osm')
  end

  def test_FT_availability_managers
    sdd_ft_test('availability_managers.osm')
  end

  def test_FT_baseline_sys01
    sdd_ft_test('baseline_sys01.osm')
  end

  def test_FT_baseline_sys02
    sdd_ft_test('baseline_sys02.osm')
  end

  def test_FT_baseline_sys03
    sdd_ft_test('baseline_sys03.osm')
  end

  def test_FT_baseline_sys04
    sdd_ft_test('baseline_sys04.osm')
  end

  def test_FT_baseline_sys05
    sdd_ft_test('baseline_sys05.osm')
  end

  def test_FT_baseline_sys06
    sdd_ft_test('baseline_sys06.osm')
  end

  def test_FT_baseline_sys07
    sdd_ft_test('baseline_sys07.osm')
  end

  def test_FT_baseline_sys08
    sdd_ft_test('baseline_sys08.osm')
  end

  def test_FT_baseline_sys09
    sdd_ft_test('baseline_sys09.osm')
  end

  def test_FT_baseline_sys10
    sdd_ft_test('baseline_sys10.osm')
  end

  def test_FT_centralheatpumpsystem
    sdd_ft_test('centralheatpumpsystem.osm')
  end

  def test_FT_chiller_electric_ashrae205
    sdd_ft_test('chiller_electric_ashrae205.osm')
  end

  def test_FT_chiller_reformulated
    sdd_ft_test('chiller_reformulated.osm')
  end

  def test_FT_chillers_tertiary
    sdd_ft_test('chillers_tertiary.osm')
  end

  def test_FT_coil_cooling_dx
    sdd_ft_test('coil_cooling_dx.osm')
  end

  def test_FT_coil_cooling_dx_airloop
    sdd_ft_test('coil_cooling_dx_airloop.osm')
  end

  def test_FT_coil_cooling_dx_singlespeed_thermalstorage
    sdd_ft_test('coil_cooling_dx_singlespeed_thermalstorage.osm')
  end

  def test_FT_coilsystem_dxhx
    sdd_ft_test('coilsystem_dxhx.osm')
  end

  def test_FT_coilsystem_dxhx_desiccant_balancedflow
    sdd_ft_test('coilsystem_dxhx_desiccant_balancedflow.osm')
  end

  def test_FT_coilsystem_integrated_heatpump
    sdd_ft_test('coilsystem_integrated_heatpump.osm')
  end

  def test_FT_coilsystem_waterhx
    sdd_ft_test('coilsystem_waterhx.osm')
  end

  def test_FT_coil_waterheating_desuperheater
    sdd_ft_test('coil_waterheating_desuperheater.osm')
  end

  def test_FT_coil_waterheating_desuperheater_2
    sdd_ft_test('coil_waterheating_desuperheater_2.osm')
  end

  def test_FT_coil_userdefined
    sdd_ft_test('coil_userdefined.osm')
  end

  def test_FT_cooling_coils
    sdd_ft_test('cooling_coils.osm')
  end

  def test_FT_coolingtowers
    sdd_ft_test('coolingtowers.osm')
  end

  def test_FT_daylighting_no_shades
    sdd_ft_test('daylighting_no_shades.osm')
  end

  def test_FT_daylighting_shades
    sdd_ft_test('daylighting_shades.osm')
  end

  def test_FT_design_day
    sdd_ft_test('design_day.osm')
  end

  def test_FT_dist_ht_cl
    sdd_ft_test('dist_ht_cl.osm')
  end

  def test_FT_doas
    sdd_ft_test('doas.osm')
  end

  def test_FT_doas_coil_cooling_dx_two_speed
    sdd_ft_test('doas_coil_cooling_dx_two_speed.osm')
  end

  def test_FT_doas_heatexchanger_airtoair_sensibleandlatent
    sdd_ft_test('doas_heatexchanger_airtoair_sensibleandlatent.osm')
  end

  def test_FT_daylighting_devices
    sdd_ft_test('daylighting_devices.osm')
  end

  def test_FT_dsn_oa_w_ideal_loads
    sdd_ft_test('dsn_oa_w_ideal_loads.osm')
  end

  def test_FT_dual_duct
    sdd_ft_test('dual_duct.osm')
  end

  def test_FT_ducts_and_pipes
    sdd_ft_test('ducts_and_pipes.osm')
  end

  def test_FT_elcd_no_generators
    sdd_ft_test('elcd_no_generators.osm')
  end

  def test_FT_electric_equipment_ITE
    sdd_ft_test('electric_equipment_ITE.osm')
  end

  def test_FT_ems
    sdd_ft_test('ems.osm')
  end

  def test_FT_ems_1floor_SpaceType_1space
    sdd_ft_test('ems_1floor_SpaceType_1space.osm')
  end

  def test_FT_ems_scott
    sdd_ft_test('ems_scott.osm')
  end

  def test_FT_environmental_factors
    sdd_ft_test('environmental_factors.osm')
  end

  def test_FT_epw_design_conditions
    sdd_ft_test('epw_design_conditions.osm')
  end

  def test_FT_evaporative_cooling
    sdd_ft_test('evaporative_cooling.osm')
  end

  def test_FT_exterior_equipment
    sdd_ft_test('exterior_equipment.osm')
  end

  def test_FT_fan_componentmodel
    sdd_ft_test('fan_componentmodel.osm')
  end

  def test_FT_fan_on_off
    sdd_ft_test('fan_on_off.osm')
  end

  def test_FT_fan_systemmodel
    sdd_ft_test('fan_systemmodel.osm')
  end

  def test_FT_fluid_coolers
    sdd_ft_test('fluid_coolers.osm')
  end

  def test_FT_foundation_kiva
    sdd_ft_test('foundation_kiva.osm')
  end

  def test_FT_foundation_kiva_customblocks
    sdd_ft_test('foundation_kiva_customblocks.osm')
  end

  def test_FT_fuelcell
    sdd_ft_test('fuelcell.osm')
  end

  def test_FT_generator_microturbine
    sdd_ft_test('generator_microturbine.osm')
  end

  def test_FT_generator_windturbine
    sdd_ft_test('generator_windturbine.osm')
  end

  def test_FT_ghx_horizontal_trench_kusuda
    sdd_ft_test('ghx_horizontal_trench_kusuda.osm')
  end

  def test_FT_ghx_horizontal_trench_xing
    sdd_ft_test('ghx_horizontal_trench_xing.osm')
  end

  def test_FT_ghx_vertical_kusuda
    sdd_ft_test('ghx_vertical_kusuda.osm')
  end

  def test_FT_ghx_vertical_xing
    sdd_ft_test('ghx_vertical_xing.osm')
  end

  def test_FT_headered_pumps
    sdd_ft_test('headered_pumps.osm')
  end

  def test_FT_heatexchanger_airtoair_sensibleandlatent
    sdd_ft_test('heatexchanger_airtoair_sensibleandlatent.osm')
  end

  def test_FT_heatexchanger_desiccant_balancedflow
    sdd_ft_test('heatexchanger_desiccant_balancedflow.osm')
  end

  def test_FT_heatpump_airtowater_fuelfired
    sdd_ft_test('heatpump_airtowater_fuelfired.osm')
  end

  def test_FT_heatpump_hot_water
    sdd_ft_test('heatpump_hot_water.osm')
  end

  def test_FT_heatpump_plantloop_eir
    sdd_ft_test('heatpump_plantloop_eir.osm')
  end

  def test_FT_heatpump_plantloop_eir_heatrecovery
    sdd_ft_test('heatpump_plantloop_eir_heatrecovery.osm')
  end

  def test_FT_heatpump_varspeed
    sdd_ft_test('heatpump_varspeed.osm')
  end

  def test_FT_heatrecovery_chiller
    sdd_ft_test('heatrecovery_chiller.osm')
  end

  def test_FT_hightemprad
    sdd_ft_test('hightemprad.osm')
  end

  def test_FT_hot_water
    sdd_ft_test('hot_water.osm')
  end

  def test_FT_humidity_control
    sdd_ft_test('humidity_control.osm')
  end

  def test_FT_humidity_control_2
    sdd_ft_test('humidity_control_2.osm')
  end

  def test_FT_ideal_loads_w_plenums
    sdd_ft_test('ideal_loads_w_plenums.osm')
  end

  def test_FT_ideal_plant
    sdd_ft_test('ideal_plant.osm')
  end

  def test_FT_infiltration
    sdd_ft_test('infiltration.osm')
  end

  def test_FT_interior_partitions
    sdd_ft_test('interior_partitions.osm')
  end

  def test_FT_lifecyclecostparameters
    sdd_ft_test('lifecyclecostparameters.osm')
  end

  def test_FT_lowtemprad_constflow
    sdd_ft_test('lowtemprad_constflow.osm')
  end

  def test_FT_lowtemprad_electric
    sdd_ft_test('lowtemprad_electric.osm')
  end

  def test_FT_lowtemprad_varflow
    sdd_ft_test('lowtemprad_varflow.osm')
  end

  def test_FT_meters
    sdd_ft_test('meters.osm')
  end

  def test_FT_moisture_settings
    sdd_ft_test('moisture_settings.osm')
  end

  def test_FT_multi_stage
    sdd_ft_test('multi_stage.osm')
  end

  def test_FT_multi_stage_electric
    sdd_ft_test('multi_stage_electric.osm')
  end

  def test_FT_multiple_airloops
    sdd_ft_test('multiple_airloops.osm')
  end

  def test_FT_multiple_loops_w_plenums
    sdd_ft_test('multiple_loops_w_plenums.osm')
  end

  def test_FT_performanceprecisiontradeoffs
    sdd_ft_test('performanceprecisiontradeoffs.osm')
  end

  def test_FT_phase_change
    sdd_ft_test('phase_change.osm')
  end

  def test_FT_photovoltaics_sandia
    sdd_ft_test('photovoltaics_sandia.osm')
  end

  def test_FT_outputcontrol_files
    sdd_ft_test('outputcontrol_files.osm')
  end

  def test_FT_outputcontrol_timestamp
    sdd_ft_test('outputcontrol_timestamp.osm')
  end

  def test_FT_output_objects
    sdd_ft_test('output_objects.osm')
  end

  def test_FT_output_objects_2
    sdd_ft_test('output_objects_2.osm')
  end

  def test_FT_photovoltaics
    sdd_ft_test('photovoltaics.osm')
  end

  def test_FT_plant_op_deltatemp_schemes
    sdd_ft_test('plant_op_deltatemp_schemes.osm')
  end

  def test_FT_plant_op_schemes
    sdd_ft_test('plant_op_schemes.osm')
  end

  def test_FT_plant_op_temp_schemes
    sdd_ft_test('plant_op_temp_schemes.osm')
  end

  def test_FT_plantloop_avms
    sdd_ft_test('plantloop_avms.osm')
  end

  def test_FT_plantloop_avms_temp
    sdd_ft_test('plantloop_avms_temp.osm')
  end

  def test_FT_plenums
    sdd_ft_test('plenums.osm')
  end

  def test_FT_ptac_othercoils
    sdd_ft_test('ptac_othercoils.osm')
  end

  def test_FT_pthp_othercoils
    sdd_ft_test('pthp_othercoils.osm')
  end

  def test_FT_pv_and_storage_demandleveling
    sdd_ft_test('pv_and_storage_demandleveling.osm')
  end

  def test_FT_pv_and_storage_facilityexcess
    sdd_ft_test('pv_and_storage_facilityexcess.osm')
  end

  def test_FT_pvwatts
    sdd_ft_test('pvwatts.osm')
  end

  def test_FT_python_plugin
    sdd_ft_test('python_plugin.osm')
  end

  def test_FT_refrigeration_system
    sdd_ft_test('refrigeration_system.osm')
  end

  def test_FT_refrigeration_system_2
    sdd_ft_test('refrigeration_system_2.osm')
  end

  def test_FT_roof_vegetation
    sdd_ft_test('roof_vegetation.osm')
  end

  def test_FT_schedule_file
    sdd_ft_test('schedule_file.osm')
  end

  def test_FT_schedule_fixed_interval
    sdd_ft_test('schedule_fixed_interval.osm')
  end

  def test_FT_schedule_fixed_interval_schedulefile
    sdd_ft_test('schedule_fixed_interval_schedulefile.osm')
  end

  def test_FT_schedule_ruleset_2012_LeapYear
    sdd_ft_test('schedule_ruleset_2012_LeapYear.osm')
  end

  def test_FT_schedule_ruleset_2012_NonLeapYear
    sdd_ft_test('schedule_ruleset_2012_NonLeapYear.osm')
  end

  def test_FT_schedule_ruleset_2013
    sdd_ft_test('schedule_ruleset_2013.osm')
  end

  def test_FT_scheduled_infiltration
    sdd_ft_test('scheduled_infiltration.osm')
  end

  def test_FT_setpoint_managers
    sdd_ft_test('setpoint_managers.osm')
  end

  def test_FT_setpoint_manager_systemnodereset
    sdd_ft_test('setpoint_manager_systemnodereset.osm')
  end

  def test_FT_shadingcontrol_singlezone
    sdd_ft_test('shadingcontrol_singlezone.osm')
  end

  def test_FT_shadowcalculation
    sdd_ft_test('shadowcalculation.osm')
  end

  def test_FT_sizing_zone_dszad
    sdd_ft_test('sizing_zone_dszad.osm')
  end

  def test_FT_solar_collector_flat_plate_photovoltaicthermal
    sdd_ft_test('solar_collector_flat_plate_photovoltaicthermal.osm')
  end

  def test_FT_solar_collector_flat_plate_photovoltaicthermal_bipvt
    sdd_ft_test('solar_collector_flat_plate_photovoltaicthermal_bipvt.osm')
  end

  def test_FT_solar_collector_flat_plate_water
    sdd_ft_test('solar_collector_flat_plate_water.osm')
  end

  def test_FT_solar_collector_integralcollectorstorage
    sdd_ft_test('solar_collector_integralcollectorstorage.osm')
  end

  def test_FT_space_level_dsoa
    sdd_ft_test('space_level_dsoa.osm')
  end

  def test_FT_space_load_instances
    sdd_ft_test('space_load_instances.osm')
  end

  def test_FT_storage_liion_battery
    sdd_ft_test('storage_liion_battery.osm')
  end

  def test_FT_surface_properties
    sdd_ft_test('surface_properties.osm')
  end

  def test_FT_surface_properties_lwr
    sdd_ft_test('surface_properties_lwr.osm')
  end

  def test_FT_surface_properties_ground_and_solarmult
    sdd_ft_test('surface_properties_ground_and_solarmult.osm')
  end

  def test_FT_surfacecontrol_moveableinsulation
    sdd_ft_test('surfacecontrol_moveableinsulation.osm')
  end

  def test_FT_swimmingpool_indoor
    sdd_ft_test('swimmingpool_indoor.osm')
  end

  def test_FT_tablelookup
    sdd_ft_test('tablelookup.osm')
  end

  def test_FT_tablemultivariablelookup
    sdd_ft_test('tablemultivariablelookup.osm')
  end

  def test_FT_thermal_storage
    sdd_ft_test('thermal_storage.osm')
  end

  def test_FT_transformer
    sdd_ft_test('transformer.osm')
  end

  def test_FT_unitary_vav_bypass_coiltypes
    sdd_ft_test('unitary_vav_bypass_coiltypes.osm')
  end

  def test_FT_unitary_system
    sdd_ft_test('unitary_system.osm')
  end

  def test_FT_unitary_system_performance_multispeed
    sdd_ft_test('unitary_system_performance_multispeed.osm')
  end

  def test_FT_unitary_systems_airloop_and_zonehvac
    sdd_ft_test('unitary_systems_airloop_and_zonehvac.osm')
  end

  def test_FT_unitary_test
    sdd_ft_test('unitary_test.osm')
  end

  def test_FT_unitary_vav_bypass
    sdd_ft_test('unitary_vav_bypass.osm')
  end

  def test_FT_unitary_vav_bypass_plenum
    sdd_ft_test('unitary_vav_bypass_plenum.osm')
  end

  def test_FT_utility_bill01
    sdd_ft_test('utility_bill01.osm')
  end

  def test_FT_utility_bill02
    sdd_ft_test('utility_bill02.osm')
  end

  def test_FT_vrf
    sdd_ft_test('vrf.osm')
  end

  def test_FT_vrf_airloophvac
    sdd_ft_test('vrf_airloophvac.osm')
  end

  def test_FT_vrf_fluid_temperature_control
    sdd_ft_test('vrf_fluid_temperature_control.osm')
  end

  def test_FT_vrf_fluid_temperature_control_hr
    sdd_ft_test('vrf_fluid_temperature_control_hr.osm')
  end

  def test_FT_vrf_watercooled
    sdd_ft_test('vrf_watercooled.osm')
  end

  def test_FT_water_economizer
    sdd_ft_test('water_economizer.osm')
  end

  def test_FT_water_heaters
    sdd_ft_test('water_heaters.osm')
  end

  def test_FT_window_property_frame_and_divider
    sdd_ft_test('window_property_frame_and_divider.osm')
  end

  def test_FT_zone_air_movement
    sdd_ft_test('zone_air_movement.osm')
  end

  def test_FT_zone_control_contaminant_controller
    sdd_ft_test('zone_control_contaminant_controller.osm')
  end

  def test_FT_zone_fan_exhaust
    sdd_ft_test('zone_fan_exhaust.osm')
  end

  def test_FT_zone_hvac
    sdd_ft_test('zone_hvac.osm')
  end

  def test_FT_zone_hvac2
    sdd_ft_test('zone_hvac2.osm')
  end

  def test_FT_zone_hvac_cooling_panel
    sdd_ft_test('zone_hvac_cooling_panel.osm')
  end

  def test_FT_zone_hvac_equipment_list
    sdd_ft_test('zone_hvac_equipment_list.osm')
  end

  def test_FT_zone_mixing
    sdd_ft_test('zone_mixing.osm')
  end

  def test_FT_zone_property_user_view_factors_by_surface_name
    sdd_ft_test('zone_property_user_view_factors_by_surface_name.osm')
  end

  def test_FT_zoneventilation_windandstackopenarea
    sdd_ft_test('zoneventilation_windandstackopenarea.osm')
  end
end

# the tests
class SddReverseTranslatorTests < Minitest::Test
  parallelize_me!
  # i_suck_and_my_tests_are_order_dependent! # To debug a crash

  #  Note: JM 2019-01-18
  #  Not used because you can't parallelize this
  #
  # Dynamically create the SddReverseTranslator tests
  # by discovering all SDD Sim XMLs in model/sddtests
  # $all_sddsimxml_paths.each do |sddsimxml_path|
  # filename = escapeName(File.basename(sddsimxml_path).gsub(' - ap.xml', ''))
  # define_method("test_RT_auto#{filename}") do
  # sdd_rt_test(File.basename(sddsimxml_path))
  # end
  # end

  ###############################################################################
  #                             Hardcoded RT tests                              #
  ###############################################################################

  def test_RT_010012_SchSml_CECStd
    sdd_rt_test('010012-SchSml-CECStd - ap.xml')
  end

  def test_RT_010112_SchSml_PSZ16
    sdd_rt_test('010112-SchSml-PSZ16 - ap.xml')
  end

  def test_RT_010212_SchSml_PVAVAirZnSys16
    sdd_rt_test('010212-SchSml-PVAVAirZnSys16 - ap.xml')
  end

  def test_RT_010312_SchSml_VAVFluidZnSys16
    sdd_rt_test('010312-SchSml-VAVFluidZnSys16 - ap.xml')
  end

  def test_RT_020006_OffSml_Run01
    sdd_rt_test('020006-OffSml-Run01 - ap.xml')
  end

  def test_RT_020006_OffSml_Run14
    sdd_rt_test('020006-OffSml-Run14 - ap.xml')
  end

  def test_RT_020006_OffSml_Run18
    sdd_rt_test('020006-OffSml-Run18 - ap.xml')
  end

  def test_RT_020006_OffSml_Run24
    sdd_rt_test('020006-OffSml-Run24 - ap.xml')
  end

  def test_RT_020006_OffSml_Run25
    sdd_rt_test('020006-OffSml-Run25 - ap.xml')
  end

  def test_RT_020006_OffSml_Run26
    sdd_rt_test('020006-OffSml-Run26 - ap.xml')
  end

  def test_RT_020006S_OffSml_Run01
    sdd_rt_test('020006S-OffSml-Run01 - ap.xml')
  end

  def test_RT_020006S_OffSml_Run14
    sdd_rt_test('020006S-OffSml-Run14 - ap.xml')
  end

  def test_RT_020006S_OffSml_Run18
    sdd_rt_test('020006S-OffSml-Run18 - ap.xml')
  end

  def test_RT_020012_OffSml_CECStd
    sdd_rt_test('020012-OffSml-CECStd - ap.xml')
  end

  def test_RT_020012S_OffSml_CECStd
    sdd_rt_test('020012S-OffSml-CECStd - ap.xml')
  end

  def test_RT_020015_OffSml_Run02
    sdd_rt_test('020015-OffSml-Run02 - ap.xml')
  end

  def test_RT_020015S_OffSml_Run02
    sdd_rt_test('020015S-OffSml-Run02 - ap.xml')
  end

  def test_RT_030006_OffMed_Run04
    sdd_rt_test('030006-OffMed-Run04 - ap.xml')
  end

  def test_RT_030006_OffMed_Run12
    sdd_rt_test('030006-OffMed-Run12 - ap.xml')
  end

  def test_RT_030006_OffMed_Run13
    sdd_rt_test('030006-OffMed-Run13 - ap.xml')
  end

  def test_RT_030006_OffMed_Run19
    sdd_rt_test('030006-OffMed-Run19 - ap.xml')
  end

  def test_RT_030006_OffMed_Run23
    sdd_rt_test('030006-OffMed-Run23 - ap.xml')
  end

  def test_RT_030006_OffMed_Run29
    sdd_rt_test('030006-OffMed-Run29 - ap.xml')
  end

  def test_RT_030006_OffMed_Run30
    sdd_rt_test('030006-OffMed-Run30 - ap.xml')
  end

  def test_RT_030006S_OffMed_Run04
    sdd_rt_test('030006S-OffMed-Run04 - ap.xml')
  end

  def test_RT_030006S_OffMed_Run12
    sdd_rt_test('030006S-OffMed-Run12 - ap.xml')
  end

  def test_RT_030006S_OffMed_Run13
    sdd_rt_test('030006S-OffMed-Run13 - ap.xml')
  end

  def test_RT_030012_OffMed_CECStd
    sdd_rt_test('030012-OffMed-CECStd - ap.xml')
  end

  def test_RT_030012S_OffMed_CECStd
    sdd_rt_test('030012S-OffMed-CECStd - ap.xml')
  end

  def test_RT_040006_OffLrg_Run05
    sdd_rt_test('040006-OffLrg-Run05 - ap.xml')
  end

  def test_RT_040006_OffLrg_Run06
    sdd_rt_test('040006-OffLrg-Run06 - ap.xml')
  end

  def test_RT_040006_OffLrg_Run11
    sdd_rt_test('040006-OffLrg-Run11 - ap.xml')
  end

  def test_RT_040006_OffLrg_Run20
    sdd_rt_test('040006-OffLrg-Run20 - ap.xml')
  end

  def test_RT_040012_OffLrg_CECStd
    sdd_rt_test('040012-OffLrg-CECStd - ap.xml')
  end

  def test_RT_040112_OffLrg_AbsorptionChiller16
    sdd_rt_test('040112-OffLrg-AbsorptionChiller16 - ap.xml')
  end

  def test_RT_040112_OffLrg_VAVPriSec16
    sdd_rt_test('040112-OffLrg-VAVPriSec16 - ap.xml')
  end

  def test_RT_040112_OffLrg_Waterside_Economizer16
    sdd_rt_test('040112-OffLrg-Waterside Economizer16 - ap.xml')
  end

  def test_RT_050006_RetlMed_Run16
    sdd_rt_test('050006-RetlMed-Run16 - ap.xml')
  end

  def test_RT_050006_RetlMed_Run27
    sdd_rt_test('050006-RetlMed-Run27 - ap.xml')
  end

  def test_RT_050006_RetlMed_Run28
    sdd_rt_test('050006-RetlMed-Run28 - ap.xml')
  end

  def test_RT_050012_RetlMed_CECStd
    sdd_rt_test('050012-RetlMed-CECStd - ap.xml')
  end

  def test_RT_050112_RetlMed_SZVAV16
    sdd_rt_test('050112-RetlMed-SZVAV16 - ap.xml')
  end

  def test_RT_050312_RetlMed_Alterations16
    sdd_rt_test('050312-RetlMed-Alterations16 - ap.xml')
  end

  def test_RT_060012_RstntSml_CECStd
    sdd_rt_test('060012-RstntSml-CECStd - ap.xml')
  end

  def test_RT_070012_HotSml_CECStd
    sdd_rt_test('070012-HotSml-CECStd - ap.xml')
  end

  def test_RT_070015_HotSml_Run03
    sdd_rt_test('070015-HotSml-Run03 - ap.xml')
  end

  def test_RT_070015_HotSml_Run22
    sdd_rt_test('070015-HotSml-Run22 - ap.xml')
  end

  def test_RT_080006_Whse_Run07
    sdd_rt_test('080006-Whse-Run07 - ap.xml')
  end

  def test_RT_080006_Whse_Run08
    sdd_rt_test('080006-Whse-Run08 - ap.xml')
  end

  def test_RT_080006_Whse_Run15
    sdd_rt_test('080006-Whse-Run15 - ap.xml')
  end

  def test_RT_080006_Whse_Run21
    sdd_rt_test('080006-Whse-Run21 - ap.xml')
  end

  def test_RT_080012_Whse_CECStd
    sdd_rt_test('080012-Whse-CECStd - ap.xml')
  end

  def test_RT_090012_RetlLrg_CECStd
    sdd_rt_test('090012-RetlLrg-CECStd - ap.xml')
  end

  def test_RT_OffLrg_PlenumsFPBsData16
    sdd_rt_test('OffLrg-PlenumsFPBsData16 - ap.xml')
  end

  def test_RT_OffLrg_PrkgExhaust16
    sdd_rt_test('OffLrg-PrkgExhaust16 - ap.xml')
  end

  def test_RT_OffLrg_PrkgLab16
    sdd_rt_test('OffLrg-PrkgLab16 - ap.xml')
  end

  def test_RT_OffLrg_PrkgLabKitchen16
    sdd_rt_test('OffLrg-PrkgLabKitchen16 - ap.xml')
  end

  def test_RT_OffLrg_ThermalEnergyStorage_ChillerPriority
    sdd_rt_test('OffLrg-ThermalEnergyStorage_ChillerPriority - ap.xml')
  end

  def test_RT_OffLrg_ThermalEnergyStorage_StoragePriority
    sdd_rt_test('OffLrg-ThermalEnergyStorage_StoragePriority - ap.xml')
  end

  def test_RT_OffMed_CoreAndShell
    sdd_rt_test('OffMed-CoreAndShell - ap.xml')
  end

  def test_RT_OffSml_ActiveBeams
    sdd_rt_test('OffSml-ActiveBeams - ap.xml')
  end

  def test_RT_OffSml_CombDHWSpcHt16
    sdd_rt_test('OffSml-CombDHWSpcHt16 - ap.xml')
  end

  def test_RT_OffSml_CommKit_SZVAV16
    sdd_rt_test('OffSml-CommKit_SZVAV16 - ap.xml')
  end

  def test_RT_OffSml_Data_SZVAV16
    sdd_rt_test('OffSml-Data_SZVAV16 - ap.xml')
  end

  def test_RT_OffSml_HtRcvry16
    sdd_rt_test('OffSml-HtRcvry16 - ap.xml')
  end

  def test_RT_OffSml_Lab_SZVAV16
    sdd_rt_test('OffSml-Lab_SZVAV16 - ap.xml')
  end

  def test_RT_OffSml_MiniSplit
    sdd_rt_test('OffSml-MiniSplit - ap.xml')
  end

  def test_RT_OffSml_Office_SZVAV16
    sdd_rt_test('OffSml-Office_SZVAV16 - ap.xml')
  end

  def test_RT_OffSml_PSZ_Evap16
    sdd_rt_test('OffSml-PSZ-Evap16 - ap.xml')
  end

  def test_RT_OffSml_PassiveBeams
    sdd_rt_test('OffSml-PassiveBeams - ap.xml')
  end

  def test_RT_OffSml_PassiveBeams_DOASCV_HtRcvry
    sdd_rt_test('OffSml-PassiveBeams-DOASCV+HtRcvry - ap.xml')
  end

  def test_RT_OffSml_PassiveBeams_DOASVAV
    sdd_rt_test('OffSml-PassiveBeams-DOASVAV - ap.xml')
  end

  def test_RT_OffSml_WSHP16
    sdd_rt_test('OffSml-WSHP16 - ap.xml')
  end

  def test_RT_RetlMed_PVAV_IndirDirEvap16
    sdd_rt_test('RetlMed-PVAV-IndirDirEvap16 - ap.xml')
  end

  def test_RT_RetlSml_DOAS_FPFC16
    sdd_rt_test('RetlSml-DOAS+FPFC16 - ap.xml')
  end

  def test_RT_RetlSml_DOAS_GravityFurnace
    sdd_rt_test('RetlSml-DOAS+GravityFurnace - ap.xml')
  end

  def test_RT_RetlSml_DOAS_GravityFurnace_HasNoClg_0
    sdd_rt_test('RetlSml-DOAS+GravityFurnace_HasNoClg=0 - ap.xml')
  end

  def test_RT_RetlSml_DOAS_GravityFurnace_HasNoClg_1
    sdd_rt_test('RetlSml-DOAS+GravityFurnace_HasNoClg=1 - ap.xml')
  end
end
