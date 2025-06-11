# frozen_string_literal: true

require 'openstudio' unless defined?(OpenStudio)

require 'etc'
require 'fileutils'
require 'json'
require 'erb'
require 'timeout'
require 'open3'

# ENV['N'] has to be before require 'minitest/autorun' as it will read it
# Nowadays MT_CPU should be preferred instead of N, but old minitest versions
# (like 5.4.3 bundled with OpenStudio 2.9.1)
# do not read it, so we pass both...
# Environment variables
if ENV['N'].nil?
  # Number of parallel runs caps to nproc - 1
  # For 2.0.4 (at least), ruby on the docker is 2.0.0,
  # and Etc doesn't have nprocessors
  nproc = nil
  begin
    nproc = Etc.nprocessors
  rescue StandardError
    begin
      nproc = `nproc`
      nproc = nproc.to_i
    rescue StandardError
      # Just fall back to whatever
      nproc = 16
    end
  end
  ENV['N'] = [1, nproc - 1].max.to_s
  puts "Setting ENV['N'] = #{ENV['N']}"
end
ENV['MT_CPU'] = ENV.fetch('N', nil)

$SdkVersion = OpenStudio.openStudioVersion

if Gem::Version.new($SdkVersion) < Gem::Version.new('3.0.0')
  # There was no prelease tags or anything like that
  # LongVersion was in format "2.9.1.3472e8b799"
  $SdkLongVersion = OpenStudio.openStudioLongVersion
  $Build_Sha = $SdkLongVersion.split('.')[-1]
else
  # This uses SemVer 2.0 and has new methods for easy access to the components
  # Format is like "3.0.0-beta+6648e88805" (with a prerelease tag)
  # or "3.0.0+6648e88805"
  $SdkLongVersion = OpenStudio.openStudioLongVersion
  $Build_Sha = OpenStudio.openStudioVersionBuildSHA
  $SdkPrerelease = OpenStudio.openStudioVersionPrerelease

  # I actually want them named like '3.0.0-rc1_out' (including the prerelease)
  if !$SdkPrerelease.empty?
    $SdkVersion << "-#{$SdkPrerelease}"
  end

  # Avoid the minitest message
  # "DEPRECATED: use MT_CPU instead of N for parallel test runs"
  ENV['N'] = nil

end

require 'minitest/autorun'
begin
  require 'minitest/reporters'
  require 'minitest/reporters/default_reporter'
  reporter = Minitest::Reporters::DefaultReporter.new
  reporter.start # had to call start manually otherwise was failing when trying to report elapsed time when run in CLI
  Minitest::Reporters.use! reporter
rescue LoadError
  puts 'Minitest Reporters not installed'
end

# Backward compat
Minitest::Test = MiniTest::Unit::TestCase unless defined?(Minitest::Test)

# Variables to store the environment variables
$Custom_tag = ''
$Save_idf = false

# Don't rerun test if there is already an OSW that shows success if the test/
# directory
$DoNotReRunIfSuccess = false

if ENV['DONOTRERUNIFSUCCESS'].to_s.downcase == 'true'
  puts "DONOTRERUNIFSUCCESS: Tests that already passed in this version (#{$SdkVersion}) will NOT be rerun"
  $DoNotReRunIfSuccess = true
end

# Force bundle_install gems, should be On, unless you're doing it on purpose
$ForceBundleInstall = true
if ENV['DONOTFORCEBUNDLEINSTALL'].to_s.downcase == 'true'
  puts 'DONOTFORCEBUNDLEINSTALL: Will not force bundle_install'
  $ForceBundleInstall = false
end

if !ENV['CUSTOMTAG'].nil?
  $Custom_tag = ENV.fetch('CUSTOMTAG', nil)
  # Debug
  # puts "Setting custom tag to #{$Custom_tag}"
end

if !$Custom_tag.empty?
  if $Custom_tag.downcase == 'sha'
    $Custom_tag = $Build_Sha
  end
  $Custom_tag = "_#{$Custom_tag}"
  puts "CUSTOMTAG: Custom tag will be appended, files will be named like 'testname_#{$SdkVersion}_out#{$Custom_tag}.osw'\n"
end

# If an ENV variable was given with a value of "True" (case insensitive)
if ENV['SAVE_IDF'].to_s.downcase == 'true'
  $Save_idf = true
  puts 'SAVE_IDF: Will save the IDF files in the test/ directory'
end

$UseEplusSpaces = nil
case ENV['USE_EPLUS_SPACES'].to_s.downcase
when 'true'
  puts 'USE_EPLUS_SPACES=true: Will use the E+ Space Feature'
  $UseEplusSpaces = true
when 'false'
  puts 'USE_EPLUS_SPACES=false: Will force not using the E+ Space Feature'
  $UseEplusSpaces = false
end

def get_cli_subcommand_from_env(sdk_version_str, debug: false)
  cur_sdk_version = Gem::Version.new(sdk_version_str)
  if debug
    puts "sdk_version_str=#{sdk_version_str}, cur_sdk_version=#{cur_sdk_version}"
  end
  labs_default = cur_sdk_version >= Gem::Version.new('3.7.0-rc2')

  cli_sub = ENV.fetch('CLI_SUBCOMMAND', 'default').to_s.downcase
  if cli_sub == 'default'
    default_cli_impl = labs_default ? 'labs (C++)' : 'classic (Ruby)'
    puts "Using the default CLI Implementation: #{default_cli_impl}"
    return ''
  end

  cpp_cli_exists = cur_sdk_version >= Gem::Version.new('3.5.0')
  if !cpp_cli_exists
    puts "Version #{cur_sdk_version} does not have the C++ CLI, ignoring CLI_SUBCOMMAND"
    return ''
  end

  if !['classic', 'labs'].include?(cli_sub.downcase)
    raise 'ERROR: CLI_SUBCOMMAND must be one of [labs, classic]'
  end

  is_labs = (cli_sub == 'labs')

  if is_labs && labs_default
    puts 'The C++ CLI is already the default, resetting the subcommand to empty'
    return ''
  end

  if !is_labs && !labs_default
    puts 'The Ruby CLI is already the default, resetting the subcommand to empty'
    return ''
  end

  puts "Setting CLI Subcommand to '#{cli_sub}'"

  return cli_sub
end

$Cli_Subcommand = get_cli_subcommand_from_env($SdkVersion, debug: false)

# config stuff
$OpenstudioCli = OpenStudio.getOpenStudioCLI
$RootDir = File.absolute_path(File.dirname(__FILE__))
$OswFile = File.join($RootDir, 'test.osw')
$ModelDir = File.join($RootDir, 'model/simulationtests/')
$IntersectDir = File.join($RootDir, 'model/intersectiontests/')
$IntersectFile = File.join($RootDir, 'intersect.rb.erb')
$TestDir = File.join($RootDir, 'testruns')
$SddSimDir = File.join($RootDir, 'model/sddtests/')
# $TestDirSddFT = File.join($RootDir, 'testruns/SddForwardTranslator/')
# if !File.exist?($TestDirSddFT)
#   FileUtils.mkdir_p($TestDirSddFT)
# end
#
# Temporary place to store the OSMs generated by Reverse Translator before
# they get simulated through OpenStudio/EnergyPlus
$TestDirSddRT = File.join($RootDir, 'testruns/SddReverseTranslator/')
FileUtils.mkdir_p($TestDirSddRT)

puts "Running for OpenStudio #{$SdkLongVersion}"

# Acceptable deviation in EUI = 0.5%
$EuiPctThreshold = 0.5

# Where to cp the out.osw for regression
# Depends on whether you are in a docker env or not
proc_file = '/proc/1/cgroup'
is_docker = File.file?(proc_file) && !File.readlines(proc_file).grep(/docker/).empty?
if is_docker
  # Mounted directory is at /root/test
  $OutOSWDir = File.join(Dir.home, 'test')
else
  # Directly in here
  $OutOSWDir = File.join($RootDir, 'test')

  # if the user didn't supply env CUSTOMTAG=whatever,
  # we ask him to optionally supply a tag
  #      n
  #      n  if ENV["CUSTOMTAG"].nil?
  #      n    # Ask user if he wants to append a custom tag to the result out.osw
  #      n    # We don't do it in docker so it can just run without user input
  #      n    prompt = ("If you want to append a custom tag to the result out.osw(s) (eg: 'Windows_run3')\n"\
  #      n              "enter it now, or type 'SHA' to append the build sha (#{$Build_Sha}),\n"\
  #      n              "or leave empty if not desired\n> ")
  #      n    ENV["CUSTOMTAG"] = [(print prompt), STDIN.gets.chomp][1]
  #      n  end

end

# Output the SDDFT'ed XMLs in the same folder as model/rb out.OSW
$TestDirSddFT = $OutOSWDir

$:.unshift($ModelDir)
ENV['RUBYLIB'] = $ModelDir
ENV['RUBYPATH'] = $ModelDir

# Determines the test plaftorm that is being used
# It will try to use the 'os' gem, and if not available falls back on RbConfig
#
# @param None
# @return [String] Plaftorm name, one of ['Windows', 'Darwin', 'Linux']
def check_test_platform
  platform = 'Unknown'

  begin
    require 'os'

    if OS.mac?
      platform = 'Darwin'
    elsif OS.linux?
      platform = 'Linux'
    elsif OS.windows?
      platform = 'Windows'
    else
      puts 'Unknown Plaftorm?!'
    end
  rescue LoadError
    require 'rbconfig'

    host_os = RbConfig::CONFIG['host_os']
    case host_os
    when /mswin|msys|mingw|cygwin|bccwin|wince|emc/
      platform = 'Windows'
    when /darwin|mac os/
      platform = 'Darwin'
    when /linux|solaris|bsd/
      platform = 'Linux'
    else
      puts "Unknown Plaftorm?! #{host_os.inspect}"
    end
  end
  return platform
end

$Platform = check_test_platform

# Sanitizes a filename replaces any of '-+= ' with '_'
#
# @param filename [String] The filename to sanitize
# @return [String] Sanitized filename
def escapeName(filename)
  return filename.gsub('-', '_')
                 .gsub('+', '_')
                 .gsub(' ', '_')
                 .gsub('=', '_')
end

# This globs all OSW tests to find all known versions to date
# and finds the previous one before the current SdkVersion uses to run the
# script. If SdkVersion isn't know, returns the last known one. If the
# SdkVersion is the oldest known to date, returns nil. If the SdkVersion is
# already know, returns the one just before.
#
# @return previousVersion [String] the string of the previous version if found,
# nil otherwise
def find_previous_version
  thisVersion = Gem::Version.new($SdkVersion)

  # We parse the test/ folder for all osm tests
  out_files = Dir.glob(File.join($OutOSWDir, '*'))
  re_version = Regexp.new('.*\.osm_(\d+\.\d+\.\d+)_out\.osw')
  version_strings = out_files.select { |f| f.match(re_version) }.map { |f| f.scan(re_version).first.last }.uniq
  # We sort them by the actual version
  versions = version_strings.map { |v| Gem::Version.new(v) }.sort

  if versions.include?(thisVersion)
    thisIndex = versions.index(thisVersion)
    if thisIndex > 0
      previousVersion = versions[thisIndex - 1]
      return previousVersion
    else
      puts "Cannot find a previous version for #{$SdkVersion} as it's the oldest known"
      return nil
    end
  else
    lastVersion = versions.last
    return lastVersion if thisVersion > lastVersion

    puts "Cannot find a previous version for #{$SdkVersion} as it's older than the oldest known"
    return nil
  end
end

$SdkPreviousVersion = find_previous_version
puts "Running for OpenStudio #{$SdkLongVersion} (Previous=#{$SdkPreviousVersion})"

# Add Chicago Design days to an OpenStudio Model
# Used to add DDays to a SddReverseTranslated (from XML) OSM
#
# @param path [OpenStudio::Model::Model] the model to add the ddy to
# @return model [OpenStudio::Model::Model].
def add_design_days(model)
  ddy_path = OpenStudio::Path.new(File.join($RootDir, 'weatherdata/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.ddy'))

  ddy_idf = OpenStudio::IdfFile.load(ddy_path, 'EnergyPlus'.to_IddFileType).get
  ddy_workspace = OpenStudio::Workspace.new(ddy_idf)
  reverse_translator = OpenStudio::EnergyPlus::ReverseTranslator.new
  ddy_model = reverse_translator.translateWorkspace(ddy_workspace)

  # Try to limit to the two main design days
  ddy_objects = ddy_model.getDesignDays.select { |d| d.name.get.include?('.4% Condns DB') || d.name.get.include?('99.6% Condns DB') }
  # Otherwise, get all .4% and 99.6%
  if ddy_objects.size < 2
    ddy_objects = ddy_model.getDesignDays.select { |d| d.name.get.include?('.4%') || d.name.get.include?('99.6%') }
  end
  # add the objects in the ddy file to the model
  model.addObjects(ddy_objects)

  # Do a couple more things
  sc = model.getSimulationControl
  sc.setRunSimulationforSizingPeriods(false)
  sc.setRunSimulationforWeatherFileRunPeriods(true)

  timestep = model.getTimestep
  timestep.setNumberOfTimestepsPerHour(4)

  return model
end

# bundle install a gemfile identified by directory name inside of 'gemfiles'
# returns full directory name gemfile_dir
# gemfile at gemfile_dir + 'Gemfile', bundle at gemfile_dir + 'gems'
def bundle_install(gemfile_dirname, force_install)
  gemfile_dir = File.join($RootDir, 'gemfiles', gemfile_dirname)
  raise "Gemfile dir '#{gemfile_dir}' does not exist" if !File.exist?(gemfile_dir)

  if force_install
    ['Gemfile.lock', 'gems', 'bundle'].each do |x|
      target = File.join(gemfile_dir, x)
      FileUtils.rm_rf(target) if target
    end
  end

  run_command('bundle install --path ./gems', gemfile_dir, 3600)

  run_command('bundle lock --add_platform ruby', gemfile_dir, 3600)

  return gemfile_dir
end

# run a command in directory dir, throws exception on timeout or exit status != 0, always returns to initial directory
def run_command(command, dir, timeout)
  result = nil
  Open3.popen3(command, chdir: dir) do |i, o, e, w|
    out = ''
    begin
      Timeout.timeout(timeout) do
        # process output of the process. it will produce EOF when done.
        out += o.readpartial(100) until o.eof?
        out += e.readpartial(100) until e.eof?
      end
      # Debug
      # puts "\n\n#{command} in dir=#{dir}, pwd=#{Dir.pwd}"
      # puts out
      # puts "\n\n"
      result = w.value.exitstatus
      # If you can find an out.osw, don't throw. It means E+ fataled out
      # https://github.com/NREL/OpenStudio/pull/4370 changed return code to 1
      # puts "result=#{result}"
      if result != 0 && !File.exist?(File.join(dir, 'out.osw'))
        raise "Exit code #{result}:\n#{out}"
      end
    rescue Timeout::Error
      # Process.kill does not work on Windows
      # https://blog.simplificator.com/2016/01/18/how-to-kill-processes-on-windows-using-ruby/
      if Gem.win_platform?
        system("taskkill /f /pid #{w.pid}")
      else
        Process.kill('KILL', w.pid)
      end
      raise "Timeout #{timeout}:\n#{out}"
    end
  end
end

# Finds the 'total_site_energy' (kBTU) in an out_osw_path that has the
# OpenStudio results measure in the workflow
#
# @param out_osw_path [String]: Any path to a valid OSW file
# @return site_kbtu [Float]: the 'total_site_energy' from the openstudio_results
# measure. Returns nil if cannot find file or cannot find the entry in question
def parse_total_site_energy(out_osw_path)
  if !File.exist?(out_osw_path)
    puts "Cannot find file #{out_osw_path}"
    return nil
  end

  result_osw = nil
  File.open(out_osw_path, 'r') do |f|
    result_osw = JSON.parse(f.read, symbolize_names: true)
  end

  if result_osw[:completed_status] == 'Fail'
    # puts "#{out_osw_path} is a failed workflow"
    return nil
  end

  if !result_osw.key?(:steps)
    # puts "#{out_osw_path} doesn't have :steps"
    return nil
  end

  if result_osw[:steps].empty?
    # puts "#{out_osw_path} has empty :steps"
    return nil
  end

  if !result_osw[:steps][0].key?(:result)
    # puts "#{out_osw_path} has steps without :result"
    return nil
  end

  if out_osw_path.include?('2.0.4')
    os_results = result_osw[:steps].select { |s| s[:measure_dir_name] == 'openstudio_results' }
  else
    # This works from 2.0.5 onward...
    os_results = result_osw[:steps].select { |s| s[:result][:measure_name] == 'openstudio_results' }
  end

  if os_results.empty?
    puts "There are no OpenStudio results for #{out_osw_path}"
    return nil

  elsif os_results.size != 1
    puts('Warning: there are more than one openstudio_results measure ' \
         "for #{out_osw_path}")
  end

  os_result = os_results[0][:result]

  site_kbtu = os_result[:step_values].select { |s| s[:name] == 'total_site_energy' }[0][:value]
  return site_kbtu
end

# Checks that % diff of EUI didn't vary too much compared to previous version
#
# @param cp_out_osw [String]: path to the test/*.osw to be compared
# Will look for the previous one in there based on $SdkPreviousVersion
# Will remove custom tags to find previous version, so that it uses the
# previous **official** run
def compare_osw_eui_with_previous_version(cp_out_osw, eui_pct_threshold: $EuiPctThreshold)
  # We can't just replace the versions, in case there's a custom tag
  # which is almost guaranteed to not exist in the previous version
  # So instead, we try to compare to the last **official** run
  filename = File.basename(cp_out_osw).scan(/(.*)_#{$SdkVersion}/).first.first
  previous_out_osw = File.join(File.dirname(cp_out_osw),
                               "#{filename}_#{$SdkPreviousVersion}_out.osw")

  old_eui = parse_total_site_energy(previous_out_osw)
  new_eui = parse_total_site_energy(cp_out_osw)

  if old_eui.nil? || new_eui.nil?
    if old_eui.nil?
      skip "Cannot compare EUIs because couldn't find old EUI"
    end
    if new_eui.nil?
      skip "Cannot compare EUIs because couldn't find new EUI"
    end
    return
  end

  pct_diff = 100 * (new_eui - old_eui) / old_eui.to_f

  assert (pct_diff < eui_pct_threshold), "#{pct_diff.round(3)}% difference in EUI is too large for #{cp_out_osw} " \
                                         "between #{$SdkPreviousVersion} and #{$SdkVersion}"
end

# Helper function to post-process the out.osw and save it in test/ with
# the right naming pattern
# It also asserts whether the run was successful, and compares EUI with
# previous version by calling compare_osw_eui_with_previous_version
#
# Cleaning includes removing timestamp and deleting :eplusout_err key if
# bigger than 100 KiB
# @param out_osw [String]: full path to the out_osw
# @param cp_out_osw [String]: path to where the sanitized OSW should be output
# @param compare_eui [Boolean, default true]: switch to false to skip the call
#   to compare_osw_eui_with_previous_version
#
# @return result_osw [Hash]: the sanitized result_osw should you need to do
# more stuff with it
def postprocess_out_osw_and_copy(out_osw, cp_out_osw, compare_eui = true)
  raise "Cannot find file #{out_osw}" if !File.exist?(out_osw)

  result_osw = nil
  File.open(out_osw, 'r') do |f|
    result_osw = JSON.parse(f.read, symbolize_names: true)
  end

  if !result_osw.nil?
    # FileUtils.cp(out_osw, cp_out_osw)

    # Instead of just copying, we clean up the osw then export that to a file
    # Remove timestamps and hash
    if result_osw.keys.include?(:eplusout_err)
      result_osw[:eplusout_err].gsub!(/YMD=.*?,/, '')
      result_osw[:eplusout_err].gsub!(/Elapsed Time=.*?\n/, '')
      # Replace eplusout_err by a list of lines instead of a big string
      # Will make git diffing easier
      result_osw[:eplusout_err] = result_osw[:eplusout_err].split("\n")
    end

    result_osw.delete(:completed_at)
    result_osw.delete(:hash)
    result_osw.delete(:started_at)
    result_osw.delete(:updated_at)

    # steps.size == 1 Should always be true,
    # unless this is one of the model_articulation ones...
    raise 'postprocess_out_osw_and_copy: there should always be one openstudio_results measure!' unless
      (result_osw[:steps].size >= 1) && (result_osw[:steps].select { |s| s[:measure_dir_name] == 'openstudio_results' }.size == 1)

    # If something went wrong, there wouldn't be results
    result_osw[:steps].each_with_index do |hs, is|
      if result_osw[:steps][is].keys.include?(:result)
        result_osw[:steps][is][:result].delete(:completed_at)
        result_osw[:steps][is][:result].delete(:started_at)
        result_osw[:steps][is][:result].delete(:step_files)

        # Round all numbers to 2 digits to avoid excessive diffs
        # result_osw[:steps][0][:result][:step_values].each_with_index do |h, i|
        result_osw[:steps][is][:result][:step_values].each_with_index do |h, i|
          if h[:value].is_a? Float
            result_osw[:steps][is][:result][:step_values][i][:value] = h[:value].round(2)
          end
        end
      end
    end

    # The fuel cell tests produce out.osw files that are about 800 MB in old
    # versions of E+, because E+ throws a warning in the Regula Falsi routine (an E+ bug)
    # which results in about 7.5 Million times the same warning
    # So if the file size is bigger than 100 KiB, we throw out the eplusout_err
    if File.size(out_osw) > 100000
      result_osw.delete(:eplusout_err)
    end

    File.write(cp_out_osw, JSON.pretty_generate(result_osw))

  end

  # standard checks
  assert_equal('Success', result_osw[:completed_status])

  # Assert that EUI didn't change too much
  if compare_eui
    compare_osw_eui_with_previous_version(cp_out_osw)
  end

  return result_osw
end

# run a simulation test
# @param filename [String]: the filename to run, will be located and copied
# @param options [Hash]: can specify the following values:
#   * :outdir [String]: another level
#   * :base_dir [String]: where to look for filename to copy it (OSM) or run it
#   (RB), defaults to $ModelDir
def sim_test(filename, options = {})
  dir = File.join($TestDir, filename)
  if options[:outdir]
    dir = File.join($TestDir, options[:outdir])
    # For model_articulation1_bundle* we pass filename =
    # model_articulation1.osw yet we need the cp_out_osw to match
    # Cp to the OutOSW directory
    cp_out_osw = File.join($OutOSWDir, "#{options[:outdir]}_#{$SdkVersion}_out#{$Custom_tag}.osw")
  else
    # Cp to the OutOSW directory
    cp_out_osw = File.join($OutOSWDir, "#{filename}_#{$SdkVersion}_out#{$Custom_tag}.osw")
  end
  # rubocop:disable Style/RedundantCondition
  if options[:base_dir]
    base_dir = options[:base_dir]
    # puts "Setting base_dir to #{base_dir}"
  else
    base_dir = $ModelDir
  end
  # rubocop:enable Style/RedundantCondition

  if options[:compare_eui].nil?
    compare_eui = true
  else
    compare_eui = options[:compare_eui]
  end

  # puts "Running sim_test(#{filename})"

  in_osw = File.join(dir, 'in.osw')
  out_osw = File.join(dir, 'out.osw')
  in_osm = File.join(dir, 'in.osm')

  # If $DoNotReRunIfSuccess is true, we check if the out_osw already exists
  # and whether it was successful already
  if $DoNotReRunIfSuccess && File.exist?(cp_out_osw)
    cp_result_osw = nil
    File.open(cp_out_osw, 'r') do |f|
      cp_result_osw = JSON.parse(f.read, symbolize_names: true)
    end
    if !cp_result_osw.nil? && (cp_result_osw[:completed_status] == 'Success')
      skip 'Already ran with success'
    end
  end

  # todo, modify different weather file in osw

  # todo, add other measures to the workflow

  # Start by deleting the testruns/test_xxx directory and recreating it
  FileUtils.rm_rf(dir)
  FileUtils.mkdir_p(dir)

  ext = File.extname(filename)
  case ext
  when '.osm', '.xml'

    if ext == '.xml'
      new_filename = filename.sub('.xml', '.osm')
      FileUtils.mv(File.join(base_dir, filename),
                   File.join(base_dir, new_filename))
      filename = new_filename
      # puts "Filename is now #{filename}"
    end

    # Copy the generic OSW needed for sim
    FileUtils.cp($OswFile, in_osw)

    # Check that version of OSM is inferior or equal to the current
    # openstudio sdk used (only for docker...)
    ori_file_path = File.join(base_dir, filename)
    v = OpenStudio::IdfFile.loadVersionOnly(ori_file_path)
    if !v
      raise "Cannot find versionString in #{filename}"
    end

    model_version = v.get.str

    if Gem::Version.new(model_version) > Gem::Version.new($SdkVersion)
      # Skip instead of fail
      skip "Model version is newer than the SDK version used (#{model_version} versus #{$SdkVersion})"
    end

    # Copy OSM to testruns dir
    FileUtils.cp(ori_file_path, in_osm)

    # Specific case for schedule_file_osm
    case filename
    when 'schedule_file.osm'
      # We need to manually copy the supporting schedule into
      # the testruns folder for the simulation to be able to find it
      sch_ori_path = File.join(File.dirname(__FILE__),
                               'model/simulationtests/lib/schedulefile.csv')
      sch_ori_path = File.realpath(sch_ori_path)

      if Gem::Version.new($SdkVersion) == Gem::Version.new('2.7.0')
        # in 2.7.0, it needs to be at the same level as the OSM
        sch_target_path = File.join(dir, File.basename(sch_ori_path))
      else
        # Going forward, it's inside the files/ subdirectory
        # Have to make the directory first
        files_dir = File.join(dir, 'files/')
        FileUtils.mkdir_p(files_dir)
        sch_target_path = File.join(files_dir, File.basename(sch_ori_path))
      end

      FileUtils.cp(sch_ori_path, sch_target_path)
    when 'chiller_electric_ashrae205.osm'
      # We need to manually copy the supporting schedule into
      # the testruns folder for the simulation to be able to find it
      cbor_ori_path = File.join(File.dirname(__FILE__),
                                'model/simulationtests/CoolSys1-Chiller-Detailed.RS0001.a205.cbor')
      cbor_ori_path = File.realpath(cbor_ori_path)

      # Have to make the directory first
      files_dir = File.join(dir, 'files/')
      FileUtils.mkdir_p(files_dir)
      cbor_target_path = File.join(files_dir, File.basename(cbor_ori_path))

      FileUtils.cp(cbor_ori_path, cbor_target_path)
    when 'python_plugin.osm', 'python_plugin_search_paths.osm'
      # We need to manually copy the supporting schedule into
      # the testruns folder for the simulation to be able to find it
      program_file_name = "#{File.basename(filename, File.extname(filename))}_program.py"
      plugin_ori_path = File.join(File.dirname(__FILE__),
                                  'model/simulationtests', program_file_name)
      plugin_ori_path = File.realpath(plugin_ori_path)

      # Have to make the directory first
      files_dir = File.join(dir, 'files/')
      FileUtils.mkdir_p(files_dir)
      python_target_path = File.join(files_dir, File.basename(plugin_ori_path))

      FileUtils.cp(plugin_ori_path, python_target_path)
    end

  when '.rb', '.py'

    # Copy the generic OSW file, needed to add design days in particular when
    # running the measure to generate the OSM, and then of course for the sim
    FileUtils.cp($OswFile, in_osw)

    # Needed for python to be able to load lib/baseline_model.py
    python_opts = ''
    if ext == '.py'
      if $Cli_Subcommand == 'classic'
        skip('Python tests not available with classic')
      end
      python_opts = "--python_path \"#{base_dir}\""
    end

    # command to generate the initial osm
    command = "\"#{$OpenstudioCli}\" #{$Cli_Subcommand} #{python_opts} \"#{File.join(base_dir, filename)}\""
    run_command(command, dir, 3600)

    # tests used to write out.osm
    out_osm = File.join(dir, 'out.osm')
    if File.exist?(out_osm)
      raise "You cannot use out.osm as an osm_name, use in.osm! Occurred in #{filename}"
    end

  when '.osw'

    # make an empty osm
    model = OpenStudio::Model::Model.new
    model.save(in_osm, true)

    # Copy the specific osw
    FileUtils.cp(File.join(base_dir, filename), in_osw)

  end

  raise "Cannot find file #{in_osm}" if !File.exist?(in_osm)
  raise "Cannot find file #{in_osw}" if !File.exist?(in_osw)

  # extra options passed to cli
  extra_options = ''
  extra_options += '--verbose ' if options[:verbose]
  extra_options += "--include #{options[:include]} " if options[:include]
  extra_options += "--gem_path #{options[:gem_path]} " if options[:gem_path]
  extra_options += "--gem_home #{options[:gem_home]} " if options[:gem_home]
  extra_options += "--bundle #{options[:bundle]} " if options[:bundle]
  extra_options += "--bundle_path #{options[:bundle_path]} " if options[:bundle_path]

  extra_run_options = ''
  extra_run_options += '--debug ' if options[:debug]
  if !$UseEplusSpaces.nil?
    if $UseEplusSpaces
      extra_run_options += '--space-translation '
    else
      extra_run_options += '--no-space-translation '
    end
  end

  # command to run the in_osw
  command = "\"#{$OpenstudioCli}\" #{$Cli_Subcommand} #{extra_options} run #{extra_run_options} -w \"#{in_osw}\""
  if options[:debug]
    puts 'COMMAND:'
    puts command
  end
  run_command(command, dir, 3600)

  if $Save_idf
    in_idf = File.join(File.dirname(out_osw), 'run/in.idf')
    if File.exist?(in_idf)
      cp_in_idf = File.join($OutOSWDir, "#{filename}_#{$SdkVersion}_out#{$Custom_tag}.idf")
      FileUtils.cp(in_idf, cp_in_idf)
    end
  end

  # Post-process the out_osw
  result_osw = postprocess_out_osw_and_copy(out_osw, cp_out_osw, compare_eui)

  # return result_osw for further checks
  return result_osw
end

def intersect_test(filename)
  dir = File.join($TestDir, 'intersections', filename)
  src_osm = File.join($IntersectDir, filename)
  in_osm = File.join(dir, 'in.osm')
  out_osm = File.join(dir, 'out.osm')
  rb_file = File.join(dir, 'intersect.rb')

  FileUtils.rm_rf(dir)
  FileUtils.mkdir_p(dir)

  erb_in = ''
  File.open($IntersectFile, 'r') do |file|
    erb_in = file.read
  end

  # configure template with variable values
  renderer = ERB.new(erb_in)
  erb_out = renderer.result(binding)

  File.open(rb_file, 'w') do |file|
    file.puts erb_out
  end

  command = "\"#{$OpenstudioCli}\" #{$Cli_Subcommand} intersect.rb"
  run_command(command, dir, 360)
end

# test the autosizing methods
def autosizing_test(filename, weather_file = nil, model_measures = [], energyplus_measures = [], reporting_measures = []) # rubocop:disable Metrics/CyclomaticComplexity, Metrics/PerceivedComplexity, Metrics/ParameterLists
  dir = File.join($TestDir, filename)
  in_osw = File.join(dir, 'in.osw')
  out_osw = File.join(dir, 'out.osw')
  cp_out_osw = File.join($OutOSWDir, "#{filename}_#{$SdkVersion}_out#{$Custom_tag}.osw")
  in_osm = File.join(dir, 'in.osm')
  sql_path = File.join(dir, 'run', 'eplusout.sql')

  $OPENSTUDIO_LOG = OpenStudio::StringStreamLogSink.new
  $OPENSTUDIO_LOG.setLogLevel(OpenStudio::Debug)

  # Run the workflow
  # Switch this to to false if you're just modifying the code below
  # (= the checks) after a successful first run as you don't have to wait
  # for the simulation itself to rerun
  run_sim = true
  if run_sim
    FileUtils.rm_rf(dir)
    FileUtils.mkdir_p(dir)
    FileUtils.cp($OswFile, in_osw)

    ext = File.extname(filename)
    case ext
    when '.osm'
      FileUtils.cp(File.join($ModelDir, filename), in_osm)
    when '.rb'
      command = "\"#{$OpenstudioCli}\" #{$Cli_Subcommand} \"#{File.join($ModelDir, filename)}\""
      run_command(command, dir, 3600)

      # tests used to write out.osm
      out_osm = File.join(dir, 'out.osm')
      if File.exist?(out_osm)
        # puts "moving #{out_osm} to #{in_osm}"
        FileUtils.mv(out_osm, in_osm)
      end

      raise "Cannot find file #{in_osm}" if !File.exist?(in_osm)
    end

    command = "\"#{$OpenstudioCli}\" #{$Cli_Subcommand} run -w \"#{in_osw}\""
    # command = "\"#{$OpenstudioCli}\" #{$Cli_Subcommand} run --debug -w \"#{in_osw}\""

    run_command(command, dir, 3600)
  end

  # DLM: this line fails on a clean repo if run_sim is false, why would you want run_sim to be false?
  # JM: because this is useful if you're just modifying the code below
  # (= the checks) after a successful first run as you don't have to wait
  # minutes for the simulation itself to rerun
  # fail "Cannot find file #{out_osw}" if !File.exist?(out_osw)

  # false to skip the call to compare_osw_eui_with_previous_version
  # this is an ever changing test, so EUI comparison is boggus
  result_osw = postprocess_out_osw_and_copy(out_osw, cp_out_osw, false)

  # Load the model
  versionTranslator = OpenStudio::OSVersion::VersionTranslator.new
  model = versionTranslator.loadModel(in_osm)
  if model.empty?
    assert(model.is_initialized, "Could not load the resulting model, #{in_osm}")
  end
  model = model.get

  # Load and attach the sql file to the model
  sql_path = OpenStudio::Path.new(sql_path)
  if OpenStudio.exists(sql_path)
    sql = OpenStudio::SqlFile.new(sql_path)
    # Check to make sure the sql file is readable,
    # which won't be true if EnergyPlus crashed during simulation.
    unless sql.connectionOpen
      OpenStudio.logFree(OpenStudio::Error, 'openstudio.model.Model', "The run failed, cannot create model.  Look at the eplusout.err file in #{File.dirname(sql_path.to_s)} to see the cause.")
      return false
    end
    # Attach the sql file from the run to the model
    model.setSqlFile(sql)
  else
    OpenStudio.logFree(OpenStudio::Error, 'openstudio.model.Model', "Results for the run couldn't be found here: #{sql_path}.")
    return false
  end

  # Assert that the sizing run succeeded
  assert_equal('Success', result_osw[:completed_status])

  # Skip testing all methods for some objects
  # Skip testing some methods for other objects
  obj_types_to_skip = {
    'OS:WaterHeater:Mixed' => 'all', # WH sizing object not wrapped
    'OS:WaterHeater:Stratified' => 'all', # WH sizing object not wrapped
    'OS:WaterHeater:HeatPump' => 'all', # WH sizing object not wrapped
    'OS:WaterHeater:HeatPump:PumpedCondenser' => 'all', # WH sizing object not wrapped
    # CoilHeatingSteam, Pump:VariableSpeed:Condensate, Pipe:Adiabatic:Steam is not wrapped, cannot use steam in OS
    'OS:Boiler:Steam' => 'all',
    'OS:DistrictHeating:Steam' => 'all',

    'OS:Coil:Cooling:DX:SingleSpeed:ThermalStorage' => [
      'autosizedFluidStorageVolume' # Only autosized if storage type is Water, but we use 'Ice' which has autosizedIceStorageCapacity
    ],

    'OS:ChillerHeaterPerformance:Electric:EIR' => 'all', # TODO: Not in test model (central HP system)
    'OS:SolarCollector:FlatPlate:PhotovoltaicThermal' => 'all', # TODO: Not in test model

    'OS:Chiller:Absorption' => [
      'autosizedDesignGeneratorFluidFlowRate' # Generator loop not supported by OS
    ],
    'OS:Chiller:Absorption:Indirect' => [
      'autosizedDesignGeneratorFluidFlowRate' # Generator loop not supported by OS
    ],
    'OS:AirConditioner:VariableRefrigerantFlow' => [
      'autosizedResistiveDefrostHeaterCapacity', # OS is missing newly added E+ units in 3.6.0: TODO remove in 3.6.1 https://github.com/NREL/EnergyPlus/pull/9898
      'autosizedWaterCondenserVolumeFlowRate' # Water-cooled VRF not supported by OS (It is nowadays, but can't do both evaporatively cooled and water cooled)
    ],
    'OS:CoolingTower:TwoSpeed' => [
      'autosizedLowSpeedNominalCapacity', # Method only works on cooling towers sized a certain way, which test model isn't using
      'autosizedFreeConvectionNominalCapacity' # Method only works on cooling towers sized a certain way, which test model isn't using
    ],
    'OS:ZoneHVAC:LowTemperatureRadiant:VariableFlow' => [
      'autosizedHeatingDesignCapacity', # No OS methods for this field
      'autosizedCoolingDesignCapacity' # No OS methods for this field
    ],
    'OS:AirConditioner:VariableRefrigerantFlow:FluidTemperatureControl' => [
      'autosizedResistiveDefrostHeaterCapacity', # Missing units in 23.1.0-IOFreeze. TODO: hopefully remove in 23.1.0 official
      'autosizedRatedEvaporativeCapacity' # As of 23.1.0, this is never autosized nor reported
    ],
    'OS:AirConditioner:VariableRefrigerantFlow:FluidTemperatureControl:HR' => [
      'autosizedResistiveDefrostHeaterCapacity', # Missing units in 23.1.0-IOFreeze. TODO: hopefully remove in 23.1.0 official
      'autosizedRatedEvaporativeCapacity' # As of 23.1.0, this is never autosized nor reported
    ],
    'OS:HeatPump:AirToWater:FuelFired:Cooling' => [
      'autosizedDesignTemperatureLift' # E+ is missing it
    ],
    'OS:HeatPump:AirToWater:FuelFired:Heating' => [
      'autosizedDesignTemperatureLift' # E+ is missing it
    ]
  }

  # Aliases for some OS onjects
  os_type_aliases = {
    'OS:Coil:Cooling:LowTemperatureRadiant:VariableFlow' => 'OS:Coil:Cooling:LowTempRadiant:VarFlow',
    'OS:Coil:Heating:LowTemperatureRadiant:VariableFlow' => 'OS:Coil:Heating:LowTempRadiant:VarFlow',
    'OS:ZoneHVAC:LowTemperatureRadiant:VariableFlow' => 'OS:ZoneHVAC:LowTempRadiant:VarFlow',
    'OS:ZoneHVAC:LowTemperatureRadiant:ConstantFlow' => 'OS:ZoneHVAC:LowTempRadiant:ConstFlow',
    'OS:Coil:Cooling:LowTemperatureRadiant:ConstantFlow' => 'OS:Coil:Cooling:LowTempRadiant:ConstFlow',
    'OS:Coil:Heating:LowTemperatureRadiant:ConstantFlow' => 'OS:Coil:Heating:LowTempRadiant:ConstFlow'
  }

  # List of objects and fields where the autosized output does
  # not exist in the E+ output, even under a different name.
  # These are things the E+ team should fix.
  missing_getters = {
    'OS:Coil:Heating:Water:Baseboard:Radiant' => [
      'autosizedHeatingDesignCapacity'
    ],
    'OS:AirLoopHVAC:Unitary:HeatPump:AirToAir' => [
      'autosizedSupplyAirFlowRateWhenNoCoolingorHeatingisNeeded'
    ],
    'OS:Coil:Heating:Water:Baseboard' => [
      'autosizedHeatingDesignCapacity'
    ],
    'OS:EvaporativeFluidCooler:TwoSpeed' => [
      'autosizedLowSpeedUserSpecifiedDesignCapacity',
      'autosizedLowSpeedStandardDesignCapacity'
    ],
    'OS:ZoneHVAC:IdealLoadsAirSystem' => [
      'autosizedMaximumSensibleHeatingCapacity',
      'autosizedMaximumTotalCoolingCapacity'
    ],
    'OS:ZoneHVAC:FourPipeFanCoil' => [
      'autosizedMinimumSupplyAirTemperatureinCoolingMode',
      'autosizedMaximumSupplyAirTemperatureinHeatingMode'
    ],
    'OS:ZoneHVAC:UnitHeater' => [
      'autosizedMaximumHotWaterFlowRate'
    ],
    'OS:FluidCooler:TwoSpeed' => [
      'autosizedLowSpeedStandardDesignCapacity',
      'autosizedLowSpeedUserSpecifiedDesignCapacity'
    ],
    'OS:ZoneHVAC:Baseboard:RadiantConvective:Water' => [
      'autosizedHeatingDesignCapacity' # OS method for child coil, but E+ is missing output
    ],
    'OS:ZoneHVAC:Baseboard:Convective:Water' => [
      'autosizedHeatingDesignCapacity' # OS method for child coil, but E+ is missing output
    ],
    'OS:ThermalStorage:ChilledWater:Stratified' => [
      'autosizedUseSideInletHeight',
      'autosizedSourceSideOutletHeight'
    ],
    'OS:Fan:ComponentModel' => [
      'autosizedMinimumFlowRate' # Not in E+ SQL
    ]
  }

  # List of objects and methods where the getter name does not
  # match the IDD field name because of IDD shift, capitalization, etc.
  getter_aliases = {
    'OS:AirTerminal:SingleDuct:VAV:Reheat' => {
      'autosizedMaximumHotWaterorSteamFlowRate' => 'autosizedMaximumHotWaterOrSteamFlowRate', # Capitalization of 'Or'
      'autosizedMaximumFlowperZoneFloorAreaDuringReheat' => 'autosizedMaximumFlowPerZoneFloorAreaDuringReheat' # Capitalization of 'Per'
    },
    'OS:HeatPump:WaterToWater:EquationFit:Heating' => {
      'autosizedReferenceHeatingCapacity' => 'autosizedRatedHeatingCapacity',
      'autosizedReferenceHeatingPowerConsumption' => 'autosizedRatedHeatingPowerConsumption'
    },
    'OS:HeatPump:WaterToWater:EquationFit:Cooling' => {
      'autosizedReferenceCoolingCapacity' => 'autosizedRatedCoolingCapacity',
      'autosizedReferenceCoolingPowerConsumption' => 'autosizedRatedCoolingPowerConsumption'
    }
  }

  extra_methods = {
    'OS:AirLoopHVAC' => [
      'autosizedSumMinimumHeatingAirFlowRates',
      'autosizedSumAirTerminalMaxAirFlowRate'
    ],
    'OS:Coil:Cooling:Water' => [
      'autosizedDesignCoilLoad'
    ],
    'OS:ThermalZone' => [
      # 'autosizedMaximumOutdoorAirFlowRate',
      'autosizedMinimumOutdoorAirFlowRate',
      'autosizedCoolingDesignAirFlowRate',
      'autosizedHeatingDesignAirFlowRate',
      'autosizedCoolingDesignLoad',
      'autosizedDesignAirFlowRate',
      'autosizedHeatingDesignLoad'
    ]
  }

  # Search the IDD associated with this model
  # and assert that there is at least one of every object
  # that has autosized fields in the test model.
  obj_counts = {}
  not_wrapped = []
  missing_autosizedFoo = []
  failed_autosizedFoo = []
  succeeded_autosizedFoo = []
  model.iddFile.objects.each do |idd_obj_type|
    autosizable_field_names = []
    idd_obj_type.nonextensibleFields.each do |idd_field|
      if idd_field.properties.autosizable
        autosizable_field_names << idd_field.name
      end
    end

    # Get the OS type
    os_type = idd_obj_type.type.valueDescription

    # Check if this object type has a different name in OS
    os_type = os_type_aliases[os_type] if os_type_aliases[os_type]

    has_extra_methods = extra_methods.include?(os_type)

    # Convert to IDD type
    type = os_type.gsub('OS:', '').gsub(':', '')

    # Skip objects with no autosizable fields
    next if autosizable_field_names.empty? && !has_extra_methods

    # Skip certain object types entirely
    methods_to_skip = obj_types_to_skip[os_type]
    next if methods_to_skip == 'all'

    methods_to_skip = [] if methods_to_skip.nil?

    # Convert the type name into a getter for objects from model
    method_name = "get#{type}s"

    # Skip objects that are in the IDD but not wrapped
    unless model.respond_to? method_name
      not_wrapped << type
      next
    end

    # Get the total number count of the objects
    # Add the objects to a hash by object type
    objs = model.public_send(method_name)
    obj_counts[type] = objs.size
    next if objs.empty?

    # Get the first instance of this object type in the model
    obj = objs.min

    # Special cases
    case type
    when 'SizingSystem' # Need to check an AirLoop with an OA system
      objs.sort.each do |o|
        obj = o if o.airLoopHVAC.name.get == 'Air Loop'
      end
    when 'SizingZone' # Need to check a zone sized w/ DOAS
      objs.sort.each do |o|
        obj = o if o.thermalZone.name.get == 'Story 5 North Perimeter Thermal Zone'
      end
    when 'ThermalZone' # Get one that has an entry in the ZoneSizes
      objs.sort.each do |o|
        obj = o if o.nameString == 'Story 5 North Perimeter Thermal Zone'
      end
    when 'AirLoopHVACUnitarySystem' # Need to check a unitary where no load flow is autosized
      objs.sort.each do |o|
        obj = o if o.name.get == 'Air Loop HVAC Unitary System 3'
      end
    when 'CoilCoolingWater' # Need to check a coil that is on an AirLoopHVAC directly or `autosizedDesignCoilLoad` won't work
      objs.sort.each do |o|
        obj = o if o.airLoopHVAC.is_initialized
      end
    end

    # Test all autosizedFoo methods on this instance
    autosizable_field_names.each do |auto_field|
      # Make the getter name from the IDD field
      getter_name = "autosized#{auto_field.gsub(/\W/, '').strip}"

      if ['HeatPumpPlantLoopEIRHeating', 'HeatPumpPlantLoopEIRCooling'].include?(type)
        if getter_name == 'autosizedHeatRecoveryReferenceFlowRate'
          obj = objs.sort.select { |o| o.heatRecoveryLoop.is_initialized }.first
        else
          obj = objs.sort.reject { |o| o.heatRecoveryLoop.is_initialized }.first
        end
      end

      # Replace the getter name with known alias, if one exists
      obj_aliases = getter_aliases[os_type]
      if obj_aliases && !obj_aliases[getter_name].nil?
        getter_name = obj_aliases[getter_name]
      end

      # Don't test this getter if it is designated to be skipped
      next if methods_to_skip.include?(getter_name)

      # Don't test this getter if it is known to be missing from E+ output
      obj_missing_getters = missing_getters[os_type]
      next if obj_missing_getters&.include?(getter_name)

      # Check if the autosizedFoo method has been implemented for this object
      unless obj.respond_to? getter_name
        missing_autosizedFoo << "'#{getter_name}' not a valid method for object of type #{type}"
        next
      end

      # Try the method on the object to ensure that the SQL query in C++ is correct
      val = obj.public_send(getter_name)
      if val.is_initialized
        succeeded_autosizedFoo << "'#{getter_name}' succeeded for '#{obj.name}' of type '#{type}'"
      else
        # require 'pry-byebug'; binding.pry
        failed_autosizedFoo << "'#{getter_name}' failed for '#{obj.name}' of type '#{type}'"
      end
    end

    if has_extra_methods
      extra_methods[os_type].each do |getter_name|
        # Check if the autosizedFoo method has been implemented for this object
        unless obj.respond_to? getter_name
          missing_autosizedFoo << "Extra getter '#{getter_name}' not a valid method for object of type '#{type}'"
          next
        end

        # Try the method on the object to ensure that the SQL query in C++ is correct
        val = obj.public_send(getter_name)
        if val.is_initialized
          succeeded_autosizedFoo << "Extra getter '#{getter_name}' succeeded for '#{obj.name}' of type '#{type}'"
        else
          # require 'pry-byebug'; binding.pry
          failed_autosizedFoo << "Extra getter '#{getter_name}' failed for '#{obj.name}' of type '#{type}'"
        end
      end
    end
  end
  puts "\n*** Autosizable Objects not Wrapped by OpenStudio ***"
  not_wrapped.each { |f| puts f }

  puts "\n*** Failures ***"
  failed_autosizedFoo.each { |f| puts f }

  puts "\n*** Methods that aren't implemented in C++ (but should be) ***"
  missing_autosizedFoo.each { |f| puts f }

  puts "\n*** Missing Objects ***"
  missing_objs = []
  obj_counts.each do |type, count|
    if count.zero?
      missing_objs << type
      puts "#{type} is missing from test model"
    end
  end

  # Assert that no autosizable objects are missing from the test model
  # so that if someone wraps a new object and doesn't add it to this file, the test will fail.
  assert_equal(0, missing_objs.size, "There are #{missing_objs.size} autosizable objects missing from the test model:\n#{missing_objs.join("\n")}.")

  # Assert that every autosizable field for every object has a corresponding method implemented
  assert_equal(0, missing_autosizedFoo.size, "#{missing_autosizedFoo.size} autosizedFoo methods not implemented in C++:\n#{missing_autosizedFoo.join("\n")}.")

  # Assert that every autosizable field's getter returns a value
  assert_equal(0, failed_autosizedFoo.size, "#{failed_autosizedFoo.size} autosizedFoo methods failed to return a value:\n#{failed_autosizedFoo.join("\n")}.")

  # Add a few more object types to skip testing for based on test file object inputs
  obj_types_to_skip['OS:EvaporativeFluidCooler:TwoSpeed'] = [
    'autosizedDesignWaterFlowRate' # Value only present for some fluid cooler sizing input methods in test file
  ]
  obj_types_to_skip['OS:Sizing:System'] = [
    'autosizedDesignOutdoorAirFlowRate' # Not all AirLoopHVACs in model have OA system, needed for this output to exist
  ]
  obj_types_to_skip['OS:AirLoopHVAC:UnitarySystem'] = [
    'autosizedNoLoadSupplyAirFlowRate' # Not all Unitarys in test model have this field autosized
  ]

  # Count the number of autosized fields in the model
  autosized_fields = lambda { |t_model, t_obj_types_to_skip, t_missing_getters|
    # Convert to IDF
    idf = OpenStudio::EnergyPlus::ForwardTranslator.new.translateModel(t_model).toIdfFile

    # Ensure that all fields are set to "Autosize" or "Autocalculate"
    fields_autosized = []
    autosize_aliases = ['autosize', 'autocalculate']
    idf.objects.sort.each do |obj|
      os_type = "OS:#{obj.iddObject.type.valueDescription}"

      # Skip certain object types entirely
      methods_to_skip = t_obj_types_to_skip[os_type]
      next if methods_to_skip == 'all'

      methods_to_skip = [] if methods_to_skip.nil?

      # Get the list of getters to skip because missing from E+
      fields_to_skip = t_missing_getters[os_type]
      fields_to_skip = [] if fields_to_skip.nil?

      for field_num in 0..obj.numFields
        field_name = obj.fieldComment(field_num, true).to_s.gsub('!-', '').gsub(/{.*}/, '').gsub(' ', '').strip
        getter_name = "autosized#{field_name}"
        # Don't check fields whose getters aren't being tested
        next if methods_to_skip.include?(getter_name)
        # Don't check fields whose getters aren't working because of E+ defficiencies
        next if fields_to_skip.include?(getter_name)

        # Check the value of the field
        val = obj.getString(field_num).to_s.downcase
        if autosize_aliases.include?(val)
          fields_still_autosized << "field #{field_name} in #{obj.iddObject.type.valueDescription}"
        end
      end

      return fields_autosized
    end

    # return result_osw for further checks
    return result_osw
  }

  # Get the autosized fields before hard sizing
  autosized_fields_before_hard_size = autosized_fields.call(model, obj_types_to_skip, missing_getters)

  # Hard-size the entire model
  model.applySizingValues

  # Get the autosized fields after hard sizing
  autosized_fields_after_hard_size = autosized_fields.call(model, obj_types_to_skip, missing_getters)

  # Auto-size the entire model
  model.autosize

  # Get the autosized fields after hard sizing
  autosized_fields_after_auto_size = autosized_fields.call(model, obj_types_to_skip, missing_getters)

  puts "\n*** Fields that are still autosized after hard sizing (but should not be) ***"
  autosized_fields_after_hard_size.each { |f| puts f }

  # Assert that all fields were hard-sized appropriately
  assert_equal(0, autosized_fields_after_hard_size.size, "#{autosized_fields_after_hard_size.size} autosized fields should be hard-sized, but aren't:\n#{failed_autosizedFoo.join("\n")}.")

  # Assert that all fields were set back to autosized
  assert_equal(autosized_fields_before_hard_size.size, autosized_fields_after_auto_size.size, "The number of autosized fields before hard sizing and after autosizing don't match.")
end

# run a sql test
# @param options [Hash]: can specify the following values:
#   options = {
#         :start => '2013-01-01', # or nil
#         :end => '2013-12-31',   # or nil
#         :isLeapYear => false,   # or true
#         :type => 'Full',        # or 'Partial'
#       }
def sql_test(options = {})
  require 'date'

  # Get name of calling method and remove the 'test_' portion
  filename = caller[0][/`.*'/][1..-2].gsub('test_', '')

  # We start by outputing a simple "Fail" into the output file
  # If everything passes, and we hit no assert, then we overwrite with
  # "Success"
  test_result_file = File.join($OutOSWDir, "#{filename}.sql_#{$SdkVersion}_out#{$Custom_tag}.sqltest")

  File.write(test_result_file, 'Fail', mode: 'w')

  # Create a model
  m = OpenStudio::Model::Model.new
  # Add three output variables from EPW
  out_var = OpenStudio::Model::OutputVariable.new('Site Outdoor Air Drybulb Temperature', m)
  out_var.setReportingFrequency('RunPeriod')

  out_var = OpenStudio::Model::OutputVariable.new('Site Outdoor Air Drybulb Temperature', m)
  out_var.setReportingFrequency('Annual')

  out_var = OpenStudio::Model::OutputVariable.new('Site Outdoor Air Drybulb Temperature', m)
  out_var.setReportingFrequency('Daily')

  yd = m.getYearDescription
  # Historically, YearDescription had a default of 'UseWeatherFile' but that
  # option was not supported until 3.3.0. So it would instead default to
  # assumedBaseYear which is 2009, which starts on a Thursday.
  # Except that 3.3.0 does take it into account and Chicago EPW has a start day
  # of Sunday (and changes year to 2006). So to avoid problems, we force it to
  # Thursday explicitly
  yd.setDayofWeekforStartDay('Thursday')

  r = m.getRunPeriod

  # Deal with input
  if (options[:start] && !options[:end]) || (!options[:start] && options[:end])
    raise 'If you specify start date, you must specify end date and vice versa'
  end

  if options[:start]
    # Ruby dates
    dr_start = Date.iso8601(options[:start])
    dr_end = Date.iso8601(options[:end])
    start_day = dr_start.day
    start_month = dr_start.month
    start_year = dr_start.year
    end_day = dr_end.day
    end_month = dr_end.month
    end_year = dr_end.year

    # Day/Month goes into Runperiod
    r.setBeginDayOfMonth(start_day)
    r.setBeginMonth(start_month)
    r.setEndDayOfMonth(end_day)
    r.setEndMonth(end_month)

    # Year goes into YearDescription
    yd.setCalendarYear(start_year)
  else
    # Defaults to full year, with assumed base year (2009)
    start_year = yd.assumedYear
    end_year = start_year

    start_day = r.getBeginDayOfMonth
    start_month = r.getBeginMonth
    end_day = r.getEndDayOfMonth
    end_month = r.getEndMonth

    # Double check that we have the right defaults
    assert_equal(1, start_day)
    assert_equal(1, start_month)
    assert_equal(31, end_day)
    assert_equal(12, end_month)
    assert_equal(2009, start_year)

  end

  # OpenStudio dates
  d_start = OpenStudio::Date.new(OpenStudio::MonthOfYear.new(start_month),
                                 start_day, start_year)
  d_end = OpenStudio::Date.new(OpenStudio::MonthOfYear.new(end_month),
                               end_day, end_year)

  dir = File.join($TestDir, filename)
  osw = File.join(dir, 'in.osw')
  out_osw = File.join(dir, 'out.osw')
  in_osm = File.join(dir, 'in.osm')
  sql_path = File.join(dir, 'run', 'eplusout.sql')

  # Run the workflow
  # Switch this to to false if you're just modifying the code below
  # (= the checks) after a successful first run as you don't have to wait
  # for the simulation itself to rerun
  run_sim = true
  if run_sim
    FileUtils.rm_rf(dir)
    FileUtils.mkdir_p(dir)
    # FileUtils.cp($OswFile, osw)

    # NOTE: If you give E+ a weather file that doesn't have a leap day
    # It won't give you an output that has a leap day...
    # And it doesn't appear to let you know about it either
    if options[:isLeapYear]
      weather_file = 'USA_IL_Chicago-OHare.Intl.AP.725300_AMY_2012_LeapYear.epw'
    else
      # If we have a start date, assume an AMY
      if options[:start]
        weather_file = 'USA_IL_Chicago-OHare.Intl.AP.725300_AMY_2012_NonLeapYear.epw'
      else
        # Otherwise a TMY
        weather_file = 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
      end
    end

    osw_content = {
      'weather_file' => "../../weatherdata/#{weather_file}",
      'seed_file' => 'in.osm'
      # "steps" => [],
    }

    File.write(osw, JSON.pretty_generate(osw_content))

    # Save to above model into dir
    m.save(in_osm, true)

    # Run it
    command = "\"#{$OpenstudioCli}\" #{$Cli_Subcommand} run -w \"#{osw}\""
    # command = "\"#{$OpenstudioCli}\" #{$Cli_Subcommand} run --debug -w \"#{osw}\""

    run_command(command, dir, 3600)
  end

  # Typically we do this:
  # result_osw = postprocess_out_osw_and_copy(filename)
  # Here we actually don't care about the OSW at all,
  # just want to make sure that E+ completed successfully
  # (though I don't see a reason it wouldn't)
  raise "Cannot find file #{out_osw}" if !File.exist?(out_osw)

  result_osw = nil
  File.open(out_osw, 'r') do |f|
    result_osw = JSON.parse(f.read, symbolize_names: true)
  end

  assert_equal('Success', result_osw[:completed_status])

  # Load the model
  versionTranslator = OpenStudio::OSVersion::VersionTranslator.new

  model = versionTranslator.loadModel(in_osm)
  if model.empty?
    assert(model.is_initialized, "Could not load the resulting model, #{in_osm}")
  end
  model = model.get

  # Load and attach the sql file to the model
  sql_path = OpenStudio::Path.new(sql_path)
  if OpenStudio.exists(sql_path)
    sql = OpenStudio::SqlFile.new(sql_path)
    # Check to make sure the sql file is readable,
    # which won't be true if EnergyPlus crashed during simulation.
    unless sql.connectionOpen
      OpenStudio.logFree(OpenStudio::Error, 'openstudio.model.Model', "The run failed, cannot create model.  Look at the eplusout.err file in #{File.dirname(sql_path.to_s)} to see the cause.")
      return false
    end
    # Attach the sql file from the run to the model
    model.setSqlFile(sql)
  else
    OpenStudio.logFree(OpenStudio::Error, 'openstudio.model.Model', "Results for the run couldn't be found here: #{sql_path}.")
    return false
  end

  # Assert that the sizing run succeeded
  assert_equal('Success', result_osw[:completed_status])

  # Now do actual stuff!

  # Get the run period series
  ts = sql.timeSeries(sql.availableEnvPeriods[0], 'RunPeriod', 'Site Outdoor Air Drybulb Temperature', 'Environment')
  assert(ts.is_initialized, "Timeseries isn't initialized")
  run_periods = ts.get
  puts run_periods.values
  puts run_periods.dateTimes

  # Get the annual series
  ts = sql.timeSeries(sql.availableEnvPeriods[0], 'Annual', 'Site Outdoor Air Drybulb Temperature', 'Environment')

  # Check run period and annual series
  assert_equal(run_periods.dateTimes.length, 1)
  assert_equal(run_periods.values.length, 1)
  case options[:type]
  when 'Full'
    assert(ts.is_initialized, "Timeseries isn't initialized")
    annuals = ts.get
    assert_equal(annuals.dateTimes.length, 1)
    assert_equal(annuals.values.length, 1)
    assert_equal(run_periods.dateTimes[0], annuals.dateTimes[0])
    assert_equal(run_periods.values[0], annuals.values[0])
    assert(annuals.values[0] == run_periods.values[0])
  when 'Partial'
    assert(!ts.is_initialized, 'Timeseries is initialized')
  when 'Wrap-around'
    assert(ts.is_initialized, "Timeseries isn't initialized")
    annuals = ts.get
    assert_equal(run_periods.dateTimes.length, 1)
    assert_equal(run_periods.values.length, 1)
    assert_equal(annuals.dateTimes.length, 1)
    assert_equal(annuals.values.length, 1)
    assert(annuals.values[0] != run_periods.values[0])
  end

  # Get the daily series
  ts = sql.timeSeries(sql.availableEnvPeriods[0], 'Daily', 'Site Outdoor Air Drybulb Temperature', 'Environment')
  assert(ts.is_initialized, "Timeseries isn't initialized")
  ts = ts.get

  # End date minus start date, + 1 because we count the start AND the end day
  n_days = (d_end - d_start).totalDays + 1
  assert_equal(n_days, ts.values.size, 'Bad number of days!')

  # E+ reports with an end convention, meaning that for a daily timeseries
  # each entry is labeled as the next day
  # eg: if you start on 2009-01-01, eplus reports as 2009-01-02 00:00
  sql_start_dt = ts.firstReportDateTime
  sql_end_dt = ts.dateTimes[-1]

  # Easy check first, check that the year was correctly sent to E+
  assert_equal(start_year, sql_start_dt.date.year, "Start year doesn't match")

  # Remove 1 day so we can compare with the above
  sql_start_date = (sql_start_dt - OpenStudio::Time.new(1)).date
  sql_end_date = (sql_end_dt - OpenStudio::Time.new(1)).date

  assert_equal(d_start, sql_start_date, "Start date doesn't match")
  assert_equal(d_end, sql_end_date, "End date doesn't match")

  # If we got here, then all good
  File.write(test_result_file, 'Success', mode: 'w')
end
