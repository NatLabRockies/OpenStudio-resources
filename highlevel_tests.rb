# frozen_string_literal: true

require 'openstudio' unless defined?(OpenStudio)

require 'pathname'

# The config and helpers are inside this file
require_relative 'test_helpers'

# Some High level tests, that should help us in maintaining the repo/test suite
# in an orderly fashion. These tests should ALWAYS pass, and other tests should
# probably not be run until these do.
class HighLevelTests < Minitest::Test
  parallelize_me!

  puts 'Running HighLevelTests'

  # Ensures that all OSM files are included in an actual model_test
  def test_osms_are_defined_sim_tests
    all_model_paths = Dir.glob(File.join($ModelDir, '*.osm'))
    all_model_filenames = all_model_paths.map { |p| File.basename(p) }

    content = File.read('model_tests.rb')
    sim_test_re = Regexp.new('def test_.*\n(?:\s*#)*\s+result = sim_test\(\'(?<filename>.*\.osm)\'\)\n(?:\s*#)*\s+end')
    osms_in_sim_test = content.scan(sim_test_re).map(&:first)
    missing_osms = all_model_filenames - osms_in_sim_test

    # These are the OSMS we expect NOT to find in a sim_test
    expected_sim_missing = [
      # Unusual structure
      'space_level_dsoa.osm'
    ]
    missing_osms -= expected_sim_missing

    assert missing_osms.empty?, "Error in model_tests.rb: The following OSMs are not in any sim_tests:\n  * #{missing_osms.join("\n  * ")}"
  end

  # Ensures that all Ruby files are included in an actual model_test
  def test_rbs_are_defined_sim_tests
    all_ruby_paths = Dir.glob(File.join($ModelDir, '*.rb'))
    all_ruby_filenames = all_ruby_paths.map { |p| File.basename(p) }

    content = File.read('model_tests.rb')
    sim_test_re = Regexp.new('def test_.*\n(?:\s*#)*\s+result = sim_test\(\'(?<filename>.*\.rb)\'\)\n(?:\s*#)*\s+end')
    rbs_in_sim_test = content.scan(sim_test_re).map(&:first)
    missing_rbs = all_ruby_filenames - rbs_in_sim_test

    # These are the ruby tests we expect NOT to find in a sim_test
    expected_sim_missing = [
      # This is autosizing_test
      'autosize_hvac.rb',
      # This one has an unusual structure, and I don't feel like playing with the
      # regex above any more
      'outputcontrol_files.rb',
      'space_level_dsoa.rb'
    ]

    missing_rbs -= expected_sim_missing

    assert missing_rbs.empty?, "Error in model_tests.rb: The following Ruby tests are not in any sim_tests:\n  * #{missing_rbs.join("\n  * ")}"
  end

  # Ensures that all Python files are included in an actual model_test
  def test_pys_are_defined_sim_tests
    all_python_paths = Dir.glob(File.join($ModelDir, '*.py'))
    all_python_filenames = all_python_paths.map { |p| File.basename(p) }
    all_python_filenames -= ['python_plugin_program.py']

    content = File.read('model_tests.rb')
    sim_test_re = Regexp.new('def test_.*\n(?:\s*#)*\s+result = sim_test\(\'(?<filename>.*\.py)\'\)\n(?:\s*#)*\s+end')
    pys_in_sim_test = content.scan(sim_test_re).map(&:first)
    missing_pys = all_python_filenames - pys_in_sim_test

    expected_sim_missing = [
      'outputcontrol_files.py',
      'space_level_dsoa.py'
    ]
    missing_pys -= expected_sim_missing

    assert missing_pys.empty?, "Error in model_tests.rb: The following Python tests are not in any sim_tests:\n  * #{missing_pys.join("\n  * ")}"
  end

  def test_all_ruby_have_matching_python_tests
    model_dir = Pathname.new($ModelDir)

    expected_missing = [
      'autosize_hvac.py'
    ]

    model_dir.glob('*.rb').each do |ruby_file|
      python_file = ruby_file.sub_ext('.py')
      next if expected_missing.include?(python_file.basename.to_s)

      assert_path_exists(python_file)
    end
  end

  # Ensures that all Ruby tests have a matching OSM tests in model_tests,
  # unless explicitly expected
  def test_rbs_have_matching_osm_tests
    # List of tests that don't have a matching OSM test for a valid reason
    # No "Warn" will be issued for these
    # input the ruby file name, eg `xxxx.rb` NOT `test_xxx_rb`
    noMatchingOSMTests = ['ExampleModel.rb',
                          'autosize_hvac.rb',
                          # TODO: Not enabled
                          'afn_single_zone_ac.rb']

    content = File.read('model_tests.rb')
    sim_test_commented_out_re = /TODO[ :\w]+(\d+\.\d+\.\d+).*?#\s*result = sim_test\('([\w\.]+)'\)/m
    # eg: [["3.1.0", "coil_cooling_dx.osm"], ["3.1.0", "swimmingpool_indoor.osm"]]
    matches = content.scan(sim_test_commented_out_re)
    files_with_todo = matches.map { |m| m[1] }

    base_dir = $ModelDir
    all_ruby_paths = Dir.glob(File.join(base_dir, '*.rb'))
    all_ruby_filenames = all_ruby_paths.map { |p| File.basename(p) }

    all_ruby_filenames.each do |filename|
      if !noMatchingOSMTests.include?(filename)
        # Check if there is a matching OSM file
        osm_name = filename.sub('.rb', '.osm')
        matching_osm = File.join(base_dir, osm_name)

        # If you want to be stricter than warn, uncomment this
        # assert File.exists?(matching_osm), "There is no matching OSM test for #{filename}"

        if File.exist?(matching_osm)
          v = OpenStudio::IdfFile.loadVersionOnly(matching_osm)
          # Seems like something we should definitely fix anyways, so throwing
          if !v
            raise "Cannot find versionString in #{matching_osm}"
          end

          # If there is a version, check that it's not newer than current bindings
          model_version = v.get.str

          if Gem::Version.new(model_version) > Gem::Version.new($SdkVersion)
            # Skip instead of fail
            skip "Matching OSM Model version is newer than the SDK version used (#{model_version} versus #{$SdkVersion})"
          end
        else
          # If there isn't a match, let's just if there's a TODO in
          # model_tests.rb
          if !files_with_todo.include?(osm_name)
            msg = "There is no matching OSM test for #{filename}. If you recently added the test please add this in model_tests.rb\n"
            msg += "```\n"
            msg += "  # TODO: To be added in the next official release after: #{OpenStudio.openStudioVersion}\n"
            msg += "  def test_#{osm_name.sub('.osm', '_osm')}\n"
            msg += "    result = sim_test('#{osm_name}')\n"
            msg += "  end\n"
            msg += '```'
            raise msg
          end
        end
      end
    end
  end

  # Ensures that any pending OSMs are added once the official version is out
  def test_ensure_pending_osms_are_added
    # Don't deal with pre-release
    if !OpenStudio.openStudioVersionPrerelease.empty?
      skip 'Current version is a prerelease'
    end

    content = File.read('model_tests.rb')
    sim_test_commented_out_re = /TODO[ :\w]+(\d+\.\d+\.\d+).*?#\s*result = sim_test\('([\w\.]+)'\)/m
    # eg: [["3.1.0", "coil_cooling_dx.osm"], ["3.1.0", "swimmingpool_indoor.osm"]]
    matches = content.scan(sim_test_commented_out_re)
    matches.each do |v, t|
      if Gem::Version.new($SdkVersion) > Gem::Version.new(v)
        raise "#{t} was expected to be added after #{v}, we're already at #{$SdkVersion}"
      end
    end
  end

  # Ensures that all OSM files are included in an actual
  # SDD ForwardTranslator test
  def test_osms_are_defined_sdd_ft_tests
    all_model_paths = Dir.glob(File.join($ModelDir, '*.osm'))
    all_model_filenames = all_model_paths.map { |p| File.basename(p) }

    content = File.read('SDD_tests.rb')

    sdd_ft_test_re = Regexp.new('def test_FT_.*\n(?:\s*#)*\s+sdd_ft_test\(\'(?<filename>.*\.osm)\'\)\n(?:\s*#)*\s+end')
    osms_in_sdd_test = content.scan(sdd_ft_test_re).map(&:first)
    missing_osms = all_model_filenames - osms_in_sdd_test

    # These are the OSMS we expect NOT to find in a sdd_ft_test
    expected_sdd_missing = ['schedule_file.osm']
    missing_osms -= expected_sdd_missing

    assert missing_osms.empty?, "Error in SDD_tests.rb: The following OSMs are not in any sdd_ft_tests:\n  * #{missing_osms.join("\n  * ")}"
  end

  # Ensures that all SDD XML files are included in an actual
  # SDD ReverseTranslator test
  def test_simsddxmls_are_defined_sdd_rt_tests
    all_sddsimxml_paths = Dir.glob(File.join($SddSimDir, '*.xml'))
    all_sdd_simxml_filenames = all_sddsimxml_paths.map { |p| File.basename(p) }

    content = File.read('SDD_tests.rb')

    sdd_rt_test_re = Regexp.new('def test_RT_.*\n(?:\s*#)*\s+sdd_rt_test\(\'(?<filename>.*\.xml)\'\)\n(?:\s*#)*\s+end')
    xmls_in_sdd_test = content.scan(sdd_rt_test_re).map(&:first)
    missing_xmls = all_sdd_simxml_filenames - xmls_in_sdd_test

    # These are the XMLs we expect NOT to find in a sdd_rt_test
    expected_sdd_missing = []
    missing_xmls -= expected_sdd_missing

    assert missing_xmls.empty?, "Error in SDD_tests.rb: The following XMLs are not in any sdd_rt_tests:\n  * #{missing_xmls.join("\n  * ")}"
  end
end
