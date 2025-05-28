import argparse
from python import performance


def setup_argparse():
    parser = argparse.ArgumentParser()

    # Force either urls or filenames to be present (but not both)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--urls",
                       dest="urls",
                       nargs='+',
                       help="List of OpenStudio SDK tar.gz urls",
                       action='store')

    group.add_argument("-f", "--filenames",
                       dest="filenames",
                       nargs='+',
                       help="List of OpenStudio SDK tar.gz filenames",
                       action='store')

    parser.add_argument('--number-runs', '-n',
                        dest="number_runs",
                        type=int,
                        default=50,
                        help=("The number of workflow runs to run on each "
                              "openstudio binary. Default 50 runs"),
                        action='store')
    parser.add_argument('--verbose', '-v',
                        default=False,
                        help="Enable verbose output",
                        action='store_true')

    parser.add_argument('--test-files', '-t',
                        nargs='+',
                        help=("List of test files to run. "
                              "Default ['baseline_sys01.rb']"),
                        default=['baseline_sys01.rb'],
                        action='store')

    # Parse the args
    args = parser.parse_args()

    is_url = False
    if args.urls:
        is_url = True
        paths = args.urls
    else:
        paths = args.filenames

    return paths, is_url, args.test_files, args.number_runs, args.verbose


if __name__ == '__main__':

    path_or_urls, is_url, test_files, number_runs, verbose = setup_argparse()

    perf_tester = performance.PerformanceTester(
        path_or_urls=path_or_urls, is_url=is_url,
        test_files=test_files, number_runs=number_runs,
        verbose=verbose, force_redownload_extract=False)

    perf_tester.logger.info(
        f'{path_or_urls=}, {is_url=}, {number_runs=}, {verbose=}\n'
        f'{test_files=}')


    # Download (if need be), extract, locate openstudio.exe, and check version
    perf_tester.prepare_installers()

    print('Running Performance Tests')

    df_all = perf_tester.run_performance_tests()
    perf_tester.make_html_report()

    q_low = df_all.quantile(0.02)
    q_hi = df_all.quantile(0.98)

    df_filtered = df_all[(df_all < q_hi) & (df_all > q_low)]

    print(df_filtered)
