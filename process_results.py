"""
Command Line Utility (CLI) to parse and analyze the regression tests results.

Use it like so:
  python process_results.py command [options]

Usage:
  process_results.py heatmap [--tagged | --all]
                             [-r <r_t> | --row_threshold=<r_t>]
                             [-d <d_t> | --display_threshold=<d_t>]
                             [--max_eplus_versions=<n_versions>]
                             [--indiv_axes]
                             [--figname_with_thresholds]
                             [--figname_with_thresholds]
                             [--granular [--indiv_axes]]
                             [--quiet] [--ci]
  process_results.py upload
  process_results.py test-stability run -n <test_filter>
                                        [-N <n>]
                                        [--start_at=<i>]
                                        [--os_cli=<path>]
                                        [--eplus_exe=<path>]
                                        [--save_idf]
                                        [--platform_name=<str>]
  process_results.py test-stability clean [--contains=<str> | --pattern=<pat>]
  process_results.py test-status [--tagged | --all] [--entire_table] [--quiet]
                                 [--max_eplus_versions=<n_versions>] [--ci]
  process_results.py -h | --help

Options:

 heatmap:
 --------

  if --tagged or --all isn't passed, it will only pull out.osws that aren't
    tagged

  Both of these options make sense only after running test-stability
  --tagged  Only analyze custom tagged files
  --all     Analyze both tagged and non-tagged osws

  --quiet   Accepts the default mapping to E+ version in case OS version isn't
            in the compatbility matrix

  -r <r_t>, --row_threshold=<r_t>      Row Threshold [default: 0.01]
        Only display tests where there is at least one cell (=one OpenStudio
        Version) that has a change greater than this.
        This value is a percentage, eg: 0.005 means at least 0.5% change

  -d <d_t>, --display_threshold=<d_t>  Display threshold [default: 0.001]
        Apply the colorscale to the cells that are above this threshold,
        otherwise they get greyed out.

  --max_eplus_versions=<n_versions>  Limit column output to the N
        most recent E+ versions

  -g, --granular    Defaults row and display thresholds, see examples section

  -i, --indiv_axes  Save individual axes [default: False]
                    If a big figure is generated, save it several smaller
                    chunks, useful when used in conjuction with --granular

  -f, --figname_with_thresholds
        Append row and display thresholds to the heatmap figure name

  --ci  Creates annotations for github actions

 test-stability:
 ---------------

 * run

 Required:
  -n <test_filter>, --test_filter=<test_filter>
        Test filter to pass to model_tests.rb

 Optional:
  -N <n>, --run_n_times=<n>
        Number of times you run these tests [default: 5]

  -S <i>, --start_at=<i>  Start numbering runs at i [default: 1]

  --os_cli<path>         Path to OS_CLI (or 'ruby'), [default: openstudio']

  --eplus_exe=<path>     Same as ENERGYPLUS_EXE_PATH (typically not needed)

  --save_idf             If supplied, will save the idf files next to the OSWs

  --platform_name=<str>  Override the default `platform.system()` (eg: 'Linux')


 * clean:
  clean             Delete all custom tagged out.osw
  --contains=<str>  Only delete custom tagged files that contain this string
                    eg: 'Ubuntu'
  --pattern=<pat>   Only delete custom tagged files that contain the <pattern>
                    Pattern must be a python regex pattern
                    eg: '2.4.\d+_out_.+\.osw'

 * analyze: use `process_results.py heatmap --tagged` or `--all`

 test-status
 ------------
 This will create an HTML of the test status, by default only for failing tests
 and non tagged files.

  See --tagged, --all, --ci, --max_eplus_versions in the heatmap section above

  --entire_table  Output also tests that have no missing/fail tests
                  (makes a much bigger table)

 other:
 ------
  -h, --help         Show this screen.

Examples:
  process_results.py heatmap
        Parse results and generate a heatmap with default values
        of --row_threshold=0.01 and --display_threshold=0.005

  process_results.py heatmap --granular
        Heatmap with values of --row_threshold=0.0005
        and --display_threshold=0.0001

  process_results.py heatmap -g -i -f
        Granular heatmap, save individual axes, and figure name with thresholds

  process_results.py heatmap --row_threshold=0.01 --display_threshold=0.001
  process_results.py heatmap -r 0.01 -d 0.001
        Parse results and generate a heatmap with custom thresholds

  process_results.py upload
        Upload to the google spreadsheet.
        THIS SHOULD ONLY BE DONE ONCE THE OFFICIAL RELEASE IS OUT AND AFTER
        RUNNING ALL TESTS WITH THIS NEW VERSION.

  process_results.py test-stability run -n "fourpipebeam" -N 5 --os_cli=ruby
    Will run `model_tests.rb -n /fourpipebeam/` 5 times with the CLI as 'ruby'

  python process_results.py test-stability run -n "baseline_sys01_osm" --os_cli="C:/openstudio-2.5.0/bin/openstudio"
    Example of specifying a custom os_cli on Windows (forward slashes)

Help:
  For help using this tool, please open an issue on the Github repository:
  https://github.com/NREL/OpenStudio-resources
"""

from docopt import docopt

if __name__ == "__main__":

    """Main CLI entrypoint."""
    from python.regression_analysis import (
        cli_heatmap,
        cli_test_status_html,
        cli_upload,
        delete_custom_tagged_osws,
        test_stability,
    )

    options = docopt(__doc__)

    # Debug
    # print(options)
    # exit()

    if options["heatmap"]:
        max_eplus_versions = options["--max_eplus_versions"]
        if max_eplus_versions is not None:
            try:
                max_eplus_versions = int(max_eplus_versions)
            except ValueError:
                raise ValueError("max_eplus_versions must be an int")

        if options["--granular"]:
            options["--row_threshold"] = 0.0005
            options["--display_threshold"] = 0.0001
        else:
            try:

                r_t = float(options["--row_threshold"])
                options["--row_threshold"] = r_t

                d_t = float(options["--display_threshold"])
                options["--display_threshold"] = d_t
            except ValueError:
                raise ValueError("row_threshold and display_threshold must be numeric")

        cli_heatmap(
            tagged=options["--tagged"],
            all_osws=options["--all"],
            row_threshold=options["--row_threshold"],
            display_threshold=options["--display_threshold"],
            save_indiv_figs_for_ax=options["--indiv_axes"],
            figname_with_thresholds=options["--figname_with_thresholds"],
            quiet=options["--quiet"],
            max_eplus_versions=max_eplus_versions,
            ci_annotations=options["--ci"],
        )
    elif options["upload"]:
        cli_upload()

    elif options["test-stability"]:
        if options["clean"]:
            delete_custom_tagged_osws(contains=options["--contains"], regex_pattern=options["--pattern"])
        elif options["run"]:
            try:
                options["--run_n_times"] = int(options["--run_n_times"])
                options["--start_at"] = int(options["--start_at"])

            except ValueError:
                print("N (run_n_times) must be numeric")
                exit()
            test_stability(
                os_cli=options["--os_cli"],
                test_filter=options["--test_filter"],
                run_n_times=options["--run_n_times"],
                start_at=options["--start_at"],
                save_idf=options["--save_idf"],
                energyplus_exe_path=options["--eplus_exe"],
                platform_name=options["--platform_name"],
            )

        elif options["analyze"]:
            pass
    elif options["test-status"]:
        max_eplus_versions = options["--max_eplus_versions"]
        if max_eplus_versions is not None:
            try:
                max_eplus_versions = int(max_eplus_versions)
            except ValueError:
                raise ValueError("max_eplus_versions must be an int")
        return_code = cli_test_status_html(
            entire_table=options["--entire_table"],
            tagged=options["--tagged"],
            all_osws=options["--all"],
            quiet=options["--quiet"],
            max_eplus_versions=max_eplus_versions,
            ci_annotations=options["--ci"],
        )
        exit(return_code)
