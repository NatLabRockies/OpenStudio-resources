import base64
import logging
import os
import re
import requests
import subprocess
import shlex
import shutil
import tarfile

import pandas as pd
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

from datetime import datetime
from distutils.dir_util import copy_tree
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote

from ipywidgets import HTML
from IPython.display import display

from tqdm.auto import tqdm, trange

ROOT_DIR = Path(__file__).parent.parent
PERF_DIR = ROOT_DIR / "perf_test"

mpl.rcParams['figure.figsize'] = (16, 9)
pd.options.display.max_rows = 200

RE_TIME = re.compile(r'(\w+): ([\d\.]+) seconds')


class PerformanceTester():

    def __init__(self, path_or_urls: list[str], is_url: bool,
                 test_files: list[Path],
                 number_runs: int = 50,  verbose: bool = False,
                 force_redownload_extract: bool = False,
                 base_dir_path: Path = PERF_DIR):

        self.path_or_urls = path_or_urls
        self.is_url = is_url
        self.test_files = test_files
        self.number_runs = number_runs
        self.verbose = verbose
        self.force_redownload_extract = force_redownload_extract
        self.base_dir_path = base_dir_path
        # Setup base path and create if need be
        if not os.path.exists(self.base_dir_path):
            os.makedirs(self.base_dir_path)
            print(f"Output in {self.base_dir_path}")

        loglevel = logging.WARNING
        if self.verbose:
            loglevel = logging.DEBUG

        self.setup_logger(level=loglevel)

    def set_console_log_level(self, level: int):
        self.console_log_level = level
        self._stream_handler.setLevel(level)

    def setup_logger(self, level: int):

        self.console_log_level = level
        self.file_log_level = logging.DEBUG

        # Create a formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s |  %(levelname)s: %(message)s')

        # Get a logger
        self.logger = logging.getLogger("performance_baseline")
        # Set it's level to the lowest possible (for file)
        self.logger.setLevel(logging.DEBUG)

        # Create a console handler
        self._stream_handler = logging.StreamHandler()
        self._stream_handler.setFormatter(formatter)
        self.set_console_log_level(level=level)

        # Create a log handler, in DEBUG mode
        logfname = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
        self.logFilePath = self.base_dir_path / f'{logfname}.log'
        print(f"File logging set to output to {self.logFilePath}")
        self._file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.logFilePath, when='midnight', backupCount=30)
        self._file_handler.setFormatter(formatter)
        self._file_handler.setLevel(logging.DEBUG)

        self.logger.addHandler(self._file_handler)
        self.logger.addHandler(self._stream_handler)

    def download_sdk(self, url: str, dest_tar_gz_filepath: Path):
        """
        Downloads the openstudio sdk to a specified path
        """
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '}
        self.logger.debug(f"Downloading {url}")

        response = requests.get(url, stream=True, headers=headers)
        with tqdm.wrapattr(
            open(dest_tar_gz_filepath, "wb"), "write", miniters=1,
            desc=f"Downloading {dest_tar_gz_filepath.name}",
            total=int(response.headers.get('content-length', 0))
        ) as fout:
            for chunk in response.iter_content(chunk_size=4096):
                fout.write(chunk)

        response.raise_for_status()

    def extract_sdk(self, tar_gz_file: Path):
        """
        Extract the openstudio.tar.gz sdk to same path
        """
        if not tar_gz_file.exists():
            raise OSError("tar.gz file '{tar_gz_file}' does not exists!")
        self.logger.debug(f"Extracting {tar_gz_file} to {self.base_dir_path}")
        tar_file = tarfile.open(tar_gz_file)
        tar_file.extractall(self.base_dir_path)
        tar_file.close()

    def _prepare_installer(self, path_or_url: str):
        """
        Downloads and extracts if url, otherwise just extracts

        Returns the path to the openstudio CLI
        """
        # Replace url safe chars with the real thing
        base_filename = unquote(os.path.basename(path_or_url))
        dest_tar_gz_filepath = self.base_dir_path / base_filename

        base_extract_path = dest_tar_gz_filepath
        while base_extract_path.suffix in {'.tar', '.gz', '.zip'}:
            base_extract_path = base_extract_path.with_suffix('')

        if self.force_redownload_extract:
            if base_extract_path.exists():
                logging.warning(
                    'Force removing extracted directory at: '
                    f'{base_extract_path}')
                shutil.rmtree(base_extract_path)
            if self.is_url:
                if dest_tar_gz_filepath.exists():
                    logging.info(f'Removing tar.gz at: {dest_tar_gz_filepath}')
                    shutil.rmtree(base_extract_path)

        if self.is_url:
            if not dest_tar_gz_filepath.exists():
                self.download_sdk(path_or_url,
                                  dest_tar_gz_filepath=dest_tar_gz_filepath)
            else:
                self.logger.info(f'{dest_tar_gz_filepath} already exists')

        if not base_extract_path.exists():
            self.extract_sdk(tar_gz_file=dest_tar_gz_filepath)
        else:
            self.logger.info(f'{base_extract_path} already exists')

        # Ubuntu has extract paths in the tar.gz. Check for that and append.
        if base_filename.lower().find("ubuntu") >= 0:

            openstudio_version = base_filename.split('+')[0]
            openstudio_bin_path = (
                base_extract_path / "usr/local/" /
                openstudio_version.lower() / "bin/openstudio")

        else:
            openstudio_bin_path = base_extract_path / "bin/openstudio"

        return openstudio_bin_path

    def _check_version(self, openstudio_exe: Path):
        if not openstudio_exe.exists:
            raise OSError("{openstudio_exe=} does not exist")
        return subprocess.check_output([openstudio_exe,
                                        '--version']).strip().decode()

    def prepare_installers(self):
        self.openstudio_bins = {}

        for path in self.path_or_urls:
            openstudio_exe = self._prepare_installer(path)
            version = self._check_version(openstudio_exe=openstudio_exe)
            self.openstudio_bins[openstudio_exe] = version

    def _prepare_ruby_bench_file(self, test_file_abs_path: str) -> Path:
        """
        Open a ruby simulationtests file, insert the timing code, and save it
        under base_path_dir / bench_files, returning that path
        """
        with open(test_file_abs_path, 'r') as f:
            lines = f.read().splitlines()

        bench_lines = []
        for line in lines:
            if 'BaselineModel.new' in line:
                bench_lines.append(
                    '# Start benchmarking of model_articulation')
                bench_lines.append("t = Time.now")
            if 'model.save_openstudio_osm' in line:
                bench_lines.append(
                    'puts "model_articulation: #{Time.now - t} seconds"')
            bench_lines.append(line)

        bench_lines += ('''
puts "model_save: #{Time.now - t} seconds"
t = Time.now

ft = OpenStudio::EnergyPlus::ForwardTranslator.new
w = ft.translateModel(model)

puts "ForwardTranslator: #{Time.now - t} seconds"'''.splitlines())

        out_file_dir = self.base_dir_path / 'bench_files'
        if not out_file_dir.exists():
            os.makedirs(out_file_dir)

        out_file_path = out_file_dir / test_file_abs_path.name
        with open(out_file_path, 'w') as f:
            f.write("\n".join(bench_lines) + '\n')

        self.logger.debug(f'Bench file saved to {out_file_path}')

        return out_file_path


    def _run_ruby_file(self, ruby_file: Path,
                       os_cli_path: Path) -> dict:
        """
        Runs the simulation with NEW_EPLUS_EXE and calls parse_sql
        """
        p = (ROOT_DIR / 'model' / 'simulationtests' / ruby_file).absolute()
        if not p.exists():
            raise ValueError(f"Test file at '{p}' does not exist")

        bench_p = self._prepare_ruby_bench_file(p)
        run_dir = bench_p.parent / "run" / ruby_file
        if not run_dir.exists():
            os.makedirs(run_dir)

        cmd = f"{os_cli_path} {bench_p}"
        self.logger.debug(f'{cmd}')
        res = subprocess.run(shlex.split(cmd), cwd=run_dir, capture_output=True)
        timings = {'file': ruby_file, 'cli_path': os_cli_path}
        if res.returncode != 0:
            print(f"Simulation failed for {cmd}")
            print(res.stdout.decode())
            print(res.stderr.decode())
            print("\n\n")
            # TODO: raise? in which case use check_output rather than run
        else:
            out = res.stdout.decode()
            for line in out.splitlines():
                if (m := RE_TIME.match(line)):
                    timing, val = m.groups()
                    timings[timing] = float(val)

        return timings

    def _copy_lib_dir(self):
        lib_dir = (ROOT_DIR / 'model' / 'simulationtests' / 'lib').absolute()
        target_dir = self.base_dir_path / 'bench_files' / 'lib'
        copy_tree(src=str(lib_dir), dst=str(target_dir))

    def _cleanup_perf_test_folder(self):
        p = self.base_dir_path / 'bench_files'
        if p.exists():
            shutil.rmtree(p)

    def _run_ruby_file_n_times(self, ruby_file: Path,
                               os_cli_path: Path,
                               number_runs: int) -> list[dict]:
        all_results = []
        for i in trange(number_runs, desc='Run'):
            timings = self._run_ruby_file(
                ruby_file=ruby_file,
                os_cli_path=os_cli_path
            )
            timings['i'] = i
            all_results.append(timings)

        return all_results

    def _run_ruby_file_n_times_with_all_installers(
        self, ruby_file: Path, number_runs: int
    ) -> list[dict]:
        all_results = []
        for os_cli_path in tqdm(self.openstudio_bins, desc='Installer'):
            cli_results = self._run_ruby_file_n_times(
                ruby_file=ruby_file, os_cli_path=os_cli_path,
                number_runs=number_runs)
            all_results += cli_results

        return all_results

    def run_performance_tests(self):
        self._cleanup_perf_test_folder()
        # Copy the 'lib' dir over
        self._copy_lib_dir()

        all_results = []
        for ruby_file in tqdm(self.test_files, desc='Test File'):
            all_results += self._run_ruby_file_n_times_with_all_installers(
                ruby_file=ruby_file, number_runs=self.number_runs)

        # Cache for debugging for now
        self._raw_results = all_results

        df_all = pd.DataFrame(all_results)

        # Replace full CLI path with version
        df_all['cli'] = df_all['cli_path'].map(self.openstudio_bins)
        df_all.columns.name = 'timing_type'
        df_all.drop(columns='cli_path', inplace=True)
        df_all.set_index(['cli', 'file', 'i'], inplace=True)

        self.results = df_all

        return self.results

    def plot_total_time_boxplot_by_file_and_cli(self):
        grouped = self.results.sum(axis=1).unstack('cli').groupby(level='file')
        ncols = 1
        nrows = int(np.ceil(grouped.ngroups/ncols))

        fig, axes = plt.subplots(nrows=nrows, ncols=ncols,
                                 figsize=(16, 9), sharey=False)

        fig.suptitle('Total elapsed time, by CLI and Test file', fontsize=16)

        for (key, ax) in zip(grouped.groups.keys(), axes.flatten()):
            grouped.get_group(key).loc[key].boxplot(ax=ax)
            ax.set_title(key)

        fig.savefig(self.base_dir_path / 'total_time_by_file_and_cli.png')
        self._total_time_boxplot = fig

    def plot_grouped_boxplot(self):

        toplot = self.results.stack()
        toplot.name = 'timing'
        toplot = toplot.reset_index()

        g = sns.catplot(
            x="file", y="timing", hue="cli", row="timing_type",
            data=toplot, kind="box", height=4, aspect=2,
            sharex=True, sharey=False,
        )
        g.fig.savefig(self.base_dir_path / 'catplot.png')
        self._grouped_boxplot = g.fig

    def get_tables(self):
        df_means = self.results.groupby('cli').mean().T
        df_export = (self.results.unstack(['cli', 'file'])
                     .reorder_levels(['file', 'timing_type', 'cli'], axis=1)
                     .sort_index(axis=1))
        df_means.to_csv(self.base_dir_path / "perf_means.csv")
        df_export.to_csv(self.base_dir_path / "perf_all.csv")
        self.df_means = df_means
        self.df_export = df_export

    def _fig_to_html(self, fig):
        tmpfile = BytesIO()
        fig.savefig(tmpfile, format='png')
        encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
        return f'<img class="img-fluid" src=\'data:image/png;base64,{encoded}\'>'

    def make_html_report(self):
        self.plot_total_time_boxplot_by_file_and_cli()
        self.plot_grouped_boxplot()
        self.get_tables()
        # TODO: create an HTML file, should use Jinja with a template...
        html = '''<!doctype html>
<html lang="en">
  <head>

    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">

    <title>Test_output</title>
  </head>

  <body>
'''

        html += "    <h1>Performance Results</h1>\n\n\n"

        html += "    <h2>Mean Times</h2>\n\n"
        html += '    <div class="container-fluid">\n      '
        html += self.df_means.to_html(classes=['table', 'table-striped', 'table-bordered'])
        html += "    </div>\n\n\n"

        html += "    <h2>Grouped Boxplot Plot</h2>\n\n"
        html += self._fig_to_html(self._grouped_boxplot)
        html += "\n\n\n"

        html += "    <h2>Box Plot of Total Time, file v CLI</h2>\n\n"
        html += self._fig_to_html(self._total_time_boxplot)
        html += "\n\n\n"

        html += "    <h2>All Timings</h2>\n\n"
        html += self.df_export.to_html(classes=['table', 'table-striped', 'table-bordered'])
        html += "\n\n\n"

        html += """
      </body>
    </html>
        """
        with open(self.base_dir_path / 'results.html', 'w') as f:
            f.write(html)
