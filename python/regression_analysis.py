#!/usr/bin/env python3

"""Support functions to cleanup and analyze the collections of out.osw
produced when running the regression tests.
If run from the command line rather than imported, will do the parsing and
upload results to the google spreasheet

    use help(function) to load the docstring for this function.

"""

# Python 2.x / 3.x compatibility
from __future__ import division, print_function

import glob as gb
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
import tqdm
from df2gspread import df2gspread as d2g
from IPython.display import display
from ipywidgets import HTML
from xmldiff import formatting, main

if sys.version_info < (3, 0):
    input = raw_input


__author__ = "Julien Marrec"
__license__ = "Standard OpenStudio License"
__maintainer__ = "Julien Marrec"
__email__ = "julien@effibem.com"
__status__ = "Production"

# Directory of this file
this_dir = os.path.dirname(os.path.abspath(__file__))
# Root of project (OpenStudio-resources)
ROOT_DIR = os.path.abspath(os.path.join(os.path.join(this_dir, "..")))

# Folder in which the out.osw are stored
TEST_DIR = os.path.join(ROOT_DIR, "test")

# STABILITY_DIR
STABILITY_DIR = os.path.join(ROOT_DIR, "Test-Stability")

# Google Spreadsheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1gL8KSwRPtMPYj-" "QrTwlCwHJvNRP7llQyEinfM1-1Usg/edit?usp=sharing"

# Used to pretty the fuel by end use dataframe
PRETTY_NAMES = {
    "cooling": "Cooling",
    "exterior_equipment": "Exterior Equipment",
    "exterior_lighting": "Exterior Lighting",
    "fans": "Fans",
    "generators": "Generators",
    "heat_recovery": "Heat Recovery",
    "heat_rejection": "Heat Rejection",
    "heating": "Heating",
    "humidification": "Humidification",
    "interior_equipment": "Interior Equipment",
    "interior_lighting": "Interior Lighting",
    "pumps": "Pumps",
    "refrigeration": "Refrigeration",
    "water_systems": "Water Systems",
    "electricity": "Electricity",
    "natural_gas": "Natural Gas",
}


# Avoid having a prompt for new version
OS_EPLUS_DICT = {"2.4.4": "8.9.0"}

# From https://semver.org/
SEMVER_REGEX = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def isnotebook():
    """
    Helper function: is this running in a jupyter notebook?
    """
    try:
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False  # Probably standard Python interpreter


def cleanup_bloated_osws():
    """
    The fuel cell tests produce out.osw files that are about 800 MB
    because E+ throws a warning in the Regula Falsi routine (an E+ bug)
    which results in about 7.5 Million times the same warning

    So if the result.osw is bigger than 100 KB, we remove the eplusout_err
    key and save in place.

    Note: this is now handled in model_tests.rb directly so you shouldn't
    really need to use this function
    """
    for out_osw_path in gb.glob(os.path.join(TEST_DIR, "*.osw")):
        # If bigger than 100 KB
        if os.path.getsize(out_osw_path) > 100000:
            with open(out_osw_path, "r") as jsonfile:
                json_text = jsonfile.read()
            data = json.loads(json_text)

            # Pop the eplusout_err messages
            data.pop("eplusout_err")
            print("Poping eplusout_err for {}".format(out_osw_path))

            try:
                with open(out_osw_path, "w") as jsonoutfile:
                    jsonoutfile.write(json.dumps(data))
            except IOError:
                print("cannot write to {}".format(out_osw_path))


def get_all_openstudio_docker_versions(latest=None):
    """
    Use the v2 Registry API to query all available docker hub tags
    https://hub.docker.com/r/nrel/openstudio/tags/

    Args:
    -----
    * latest (str, or default None): version string equivalent to 'latest'
        docker hub tag.
        If not None (eg: "2.4.0"), will replace the 'latest' tag with this str.
        Pass None to just ignore the 'latest' tag.

        The dockerhub repo has been inconsistent sometimes, but normally
        it should specifically tag the versions, eg if the last build is
        2.4.1 it should be tagged 2.4.1 AND latest

    Returns:
    --------
    * all_tags (list of str): list of all available versions (tags)

    Needs:
    -------
    requests, json
    """

    i = 1
    status_code = 200
    url = "https://registry.hub.docker.com/v2/" "repositories/nrel/openstudio/tags?page=1"

    all_tags = []
    while (status_code == 200) and (url is not None):
        response = requests.get(url)
        status_code = response.status_code
        i += 1
        if status_code == 200:
            data = json.loads(response.text)
            # Get next page
            url = data["next"]
            all_tags += [x["name"] for x in data["results"]]

    if latest is None:
        all_tags = [x for x in all_tags if x != "latest"]
    else:
        all_tags = [latest if x == "latest" else x for x in all_tags]

    return all_tags


def parse_compatibility_matrix(force_latest=False):
    """
    Parses the compatability matrix into a pandas dataframe. Matrix is here:
    https://github.com/NREL/OpenStudio/wiki/OpenStudio-Version-Compatibility-Matrix

    Also queries the docker hub API see (`get_all_openstudio_docker_versions`)
    to check if there is an available docker tag too.

    Args:
    ------
    * force_latest (bool): whether to replace the docker tag 'latest' with
    the latest available version. See get_all_openstudio_docker_versions
    for more info. In general False should be used

    Returns:
    ---------
    * compat_matrix (pd.DataFrame): a pandas dataframe of all versions.
        You can turn it into a valid json with:
        json.loads(compat_matrix.to_json(orient='records'))
    """

    compat_matrix_url = "https://github.com/NREL/OpenStudio/wiki/" "OpenStudio-SDK-Version-Compatibility-Matrix"
    compat_matrix = pd.read_html(compat_matrix_url, index_col=0)[0]
    compat_matrix.index = [x.replace("v", "").replace("*", "") for x in compat_matrix.index]
    compat_matrix.drop("Gemfile", axis=1, inplace=True)
    compat_matrix.index.name = "OpenStudio"
    compat_matrix.reset_index(inplace=True)
    compat_matrix["Released"] = pd.to_datetime(compat_matrix["Released"])

    if force_latest:
        latest = compat_matrix.set_index("OpenStudio")["Released"].idxmax()
    else:
        latest = None

    all_tags = get_all_openstudio_docker_versions(latest=latest)

    compat_matrix["Has_Docker"] = False
    compat_matrix.loc[compat_matrix["OpenStudio"].isin(all_tags), "Has_Docker"] = True

    return compat_matrix


def find_osm_test_versions(base_dir="model/simulationtests/"):
    """
    Globs the model/simulationtests/*.osm (or base_dir/*.osm)
    and parse the Version String
    Constructs a dataframe

    Args:
    ------
    None

    Returns:
    ---------
    model_test_cases (pd.DataFrame): index is testcase (eg 'air_chillers')
    columns are ['path', 'OSM Version', 'Major', 'Minor', 'Patch']
    """

    # Reconstruct by parsing file itself
    v_regex = re.compile(r"\s+(\d+\.\d+\.\d+);\s+!-? Version Identifier")

    model_version_lists = []
    osms = gb.glob(os.path.join(ROOT_DIR, base_dir, "*.osm"))
    for osm in osms:
        found = False
        test = os.path.splitext(os.path.split(osm)[1])[0]
        with open(osm, "r") as f:
            lines = f.read().splitlines()
        for i, line in enumerate(lines):
            if "OS:Version" in line:
                m = v_regex.search(lines[i + 2])
                if m:
                    found = True
                    model_version_lists.append([test, osm, m.groups()[0]])
                else:
                    print("Error for line: {}".format(lines[i + 2]))
        if not found:
            print("Problem for {}".format(osm))

    model_test_cases = pd.DataFrame(model_version_lists, columns=["testcase", "path", "OSM version"])
    model_test_cases.set_index("testcase", inplace=True)
    model_test_cases.sort_index(inplace=True)
    model_test_cases[["Major", "Minor", "Patch"]] = model_test_cases["OSM version"].str.split(".", expand=True)
    return model_test_cases


def parse_model_tests_rb():
    """
    This functions looks for `def test_xxx_(rb|osm|osw)` in model_tests.rb and
    returns the name of the actual file called on the following line

    eg:
    model_tests.rb
    ```
    def test_intersect_test3_osm
      result = intersect_test('test3.osm')
    end

    ```
    Will append a tuple of ('test3', 'osm')

    Returns:
    --------
    tests (list of tuples): a list of all tests (filename, ext)

    """

    with open(os.path.join(ROOT_DIR, "model_tests.rb"), "r") as f:
        lines = f.read().splitlines()

    test_pat = re.compile(r"^\s*def test_(.+)_(rb|osm|osw)\s*$")
    # The intersect tests are special, so we only parse autosizing and sim
    res_pat = re.compile(r"^\s*result\s*=\s*(?:autosizing|sim)_test" r"\('(.*)\.(rb|osm|osw)',*.*\)\s*")

    # minitests = []
    tests = []
    # minitests_names = {}
    for i, line in enumerate(lines):
        m = test_pat.match(line)
        if m:
            # minitests.append((m.groups()[0], m.groups()[1]))
            m2 = res_pat.match(lines[i + 1])
            if m2:
                tests.append((m2.groups()[0], m2.groups()[1]))
                # minitests_names[(m2.groups()[0],
                # m2.groups()[1])] = (m.groups()[0], m.groups()[1])
            else:
                if "intersect_test" in lines[i + 1]:
                    # Expected behavior
                    pass
                elif "bundle_install" in lines[i + 1]:
                    # Expected behavior
                    pass
                else:
                    print("Expected result = xxxx on line {}, got: " "{}".format(i + 1, lines[i + 1]))
    return tests


def find_info_osws(compat_matrix=None, test_dir=None, testtype="model", quiet=False):
    """
    Looks for files in the test/ folder, and parses version and type (rb, osm)
    Constructs a dataframe that has E+/OS versions in column (by looking E+
    version in compat_matrix)

    IMPORTANT: this WILL NOT parse the custom-tagged out.osws
    (see `find_info_osws_with_tags`)

    Note: despite its name, it can also parse XMLs (and not OSWs)
    from SddForwardTranslatorTests by passing testtype='sddft'

    Args:
    ------
    * compat_matrix (pd.DataFrame or None)
        if None, calls parse_compatibility_matrix. Otherwise you can supply it
    * test_dir (str path or None): if None uses the global TEST_DIR constant
    * testtype (str): Defaults to 'model'. Must be in the list
                  `['model', 'sddft', 'sddrt', 'sql', 'utilities']`

    Returns:
    ---------
    * df_files (pd.DataFrame): A multi indexed dataframe in rows and columns
        Levels are as follows:
        index: ['Test', 'Type'], eg ('absorption_chiller', 'rb')
        columns: ['E+', 'OS'], the versions eg ('8.6.0', '2.4.0')

        values are the path of the corresponding out.osw,
        eg: 'absorption_chillers.rb_2.0.4_out.osw'

    """

    valid_testtypes = ["model", "sddft", "sddrt", "sql", "utilities"]
    if testtype not in valid_testtypes:
        warnings.warn(
            "Unknown 'testtype', defaulting to 'model'. " "Valid values are {}".format(valid_testtypes), UserWarning
        )
        testtype = "model"

    if test_dir is None:
        test_dir = TEST_DIR

    if compat_matrix is None:
        compat_matrix = parse_compatibility_matrix()

    if testtype == "sddft":
        ext = "xml"
        # This excludes the custom tagged files
        files = gb.glob(os.path.join(test_dir, "*out.xml"))
    elif testtype == "sql":
        ext = "sqltest"
        files = gb.glob(os.path.join(test_dir, "*out.sqltest"))
    elif testtype == "utilities":
        ext = "status"
        files = gb.glob(os.path.join(test_dir, "*out.status"))

    else:
        files = gb.glob(os.path.join(test_dir, "*out.osw"))
        ext = "osw"
        re_xml = re.compile(r"xml_\d+\.\d+\.\d+_out+")
        if testtype == "sddrt":
            # Only keep XML
            files = [f for f in files if re_xml.search(f)]

        else:
            # Exclude xml (SDDReverseTranslator) tests
            files = [f for f in files if not re_xml.search(f)]

    # With this pattern, we exclude the custom-tagged out.osw files
    filepattern = r"(?P<Test>.*?)\.(?P<Type>osm|rb|py|osw|xml|sql)_" r"(?P<version>\d+\.\d+\.\d+.*?)_out\.{}".format(
        ext
    )

    index = ["Test", "Type", "version"]
    if testtype == "utilities":
        filepattern = r"(?P<Test>.*?)_(?P<version>\d+\.\d+\.\d+.*?)_" r"(?P<Platform>.*?)_out.status"
        index = ["Test", "Platform", "version"]

    df_files = pd.DataFrame(files, columns=["path"])

    version = df_files["path"].apply(lambda p: os.path.relpath(p, test_dir)).str.extract(pat=filepattern, expand=True)
    df_files = pd.concat([df_files, version], axis=1)
    df_files = df_files.set_index(index)["path"].unstack(["version"]).sort_index(axis=1)

    version_dict = compat_matrix.set_index("OpenStudio")["E+"].to_dict()

    # Handle the case where you're working on a develop branch that is ahead
    # of the compatibility matrix
    all_versions = df_files.columns.unique()
    unknown_versions = set(all_versions) - set(version_dict.keys())

    latest_eplus = compat_matrix.iloc[0]["E+"]

    if unknown_versions:
        msg = (
            "OpenStudio Version {} is not in the compatibility matrix\n"
            "Please input the corresponding E+ version (default='{}'):\n"
        )
        for v in unknown_versions:
            # Skip the ones we hard mapped
            if v in OS_EPLUS_DICT.keys():
                is_correct = True
                eplus = OS_EPLUS_DICT[v]
            else:
                is_correct = False

            if quiet:
                eplus = latest_eplus
            else:
                while not is_correct:
                    # Ask user. If blank, then default to latest eplus known
                    eplus = input(msg.format(v, latest_eplus))
                    if not eplus:
                        eplus = latest_eplus

                    # Sanitize: it should be in the form "X.Y.Z"
                    if len(eplus.split(".")) == 3:
                        try:
                            [float(x) for x in eplus.split(".")]
                            is_correct = True
                        except ValueError:
                            pass
            print("Mapping OS '{}' to '{}'".format(v, eplus))
            # Add to the version_dict
            version_dict[v] = eplus

    # Prepend a column level for E+ version
    df_files.columns = pd.MultiIndex.from_tuples([(version_dict[x], x) for x in df_files.columns], names=["E+", "OS"])

    return df_files


def find_info_osws_with_tags(compat_matrix=None, test_dir=None, tags_only=True, testtype="model", quiet=False):
    """
    Looks for files in the test/ folder, and parses version
    and type (rb, osm, or osw)

    Constructs a dataframe that has E+/OS versions in column (by looking E+
    version in compat_matrix)

    IMPORTANT: this WILL parse the custom-tagged out.osws
    (see `find_info_osws`)

    Args:
    ------
    * compat_matrix (pd.DataFrame or None)
        if None, calls parse_compatibility_matrix. Otherwise you can supply it

    * test_dir (str path or None): if None uses the global TEST_DIR constant

    * tags_only (bool): if True, only greps custom tagged files, if False will
        grep tagged and regular files

    * testtype (str): either 'model' (default) or 'sddft' or 'sddrt'

    Returns:
    ---------
    * df_files (pd.DataFrame): A multi indexed dataframe in rows and columns
        Levels are as follows:
        index: ['Test', 'Type'], eg ('absorption_chiller', 'rb')
        columns: ['E+', 'OS'], the versions eg ('8.6.0', '2.4.0')

        values are the path of the corresponding out.osw,
        eg: 'absorption_chillers.rb_2.0.4_out.osw'

    """

    valid_testtypes = ["model", "sddft", "sddrt"]
    if testtype not in valid_testtypes:
        warnings.warn(
            "Unknown 'testtype', defaulting to 'model'. " "Valid values are {}".format(valid_testtypes), UserWarning
        )
        testtype = "model"

    if test_dir is None:
        test_dir = TEST_DIR

    if compat_matrix is None:
        compat_matrix = parse_compatibility_matrix()

    if testtype == "sddft":
        ext = "xml"
        if tags_only:
            files = gb.glob(os.path.join(test_dir, "*out_*.xml"))
        else:
            files = gb.glob(os.path.join(test_dir, "*out*.xml"))
    else:
        if tags_only:
            files = gb.glob(os.path.join(test_dir, "*out_*.osw"))
        else:
            files = gb.glob(os.path.join(test_dir, "*out*.osw"))

        ext = "osw"
        re_xml = re.compile(r"xml_\d+\.\d+\.\d+_out+")
        if testtype == "sddrt":
            # Only keep XML
            files = [f for f in files if re_xml.search(f)]

        else:
            # Exclude xml (SDDReverseTranslator) tests
            files = [f for f in files if not re_xml.search(f)]

    if tags_only:
        filepattern = (
            r"(?P<Test>.*?)\.(?P<Type>osm|rb|py|osw|xml|sql)_"
            r"(?P<version>\d+\.\d+\.\d+.*?)_out"
            r"_(?P<Tag>.*?)\.{}".format(ext)
        )
    else:
        filepattern = (
            r"(?P<Test>.*?)\.(?P<Type>osm|rb|py|osw|xml|sql)_"
            r"(?P<version>\d+\.\d+\.\d+.*?)_out"
            r"_?(?P<Tag>.*?)?\.{}".format(ext)
        )

    if not files:
        raise RuntimeError("Couldn't find any files matching the pattern")

    df_files = pd.DataFrame(files, columns=["path"])

    version = df_files["path"].apply(lambda p: os.path.relpath(p, test_dir)).str.extract(pat=filepattern, expand=True)
    df_files = pd.concat([df_files, version], axis=1)
    df_files = (
        df_files.set_index(["Test", "Type", "Tag", "version"])["path"].unstack(["version", "Tag"]).sort_index(axis=1)
    )

    version_dict = compat_matrix.set_index("OpenStudio")["E+"].to_dict()

    # Handle the case where you're working on a develop branch that is ahead
    # of the compatibility matrix
    all_versions = df_files.columns.get_level_values(0).unique()
    unknown_versions = set(all_versions) - set(version_dict.keys())

    latest_eplus = compat_matrix.iloc[0]["E+"]

    if unknown_versions:
        msg = (
            "OpenStudio Version {} is not in the compatibility matrix\n"
            "Please input the corresponding E+ version (default='{}'):\n"
        )
        for v in unknown_versions:
            # Skip the ones we hard mapped
            if v in OS_EPLUS_DICT.keys():
                is_correct = True
                eplus = OS_EPLUS_DICT[v]
            else:
                is_correct = False

            if quiet:
                eplus = latest_eplus
            else:
                while not is_correct:
                    # Ask user. If blank, then default to latest eplus known
                    eplus = input(msg.format(v, latest_eplus))
                    if not eplus:
                        eplus = latest_eplus

                    # Sanitize: it should be in the form "X.Y.Z"
                    if len(eplus.split(".")) == 3:
                        try:
                            [float(x) for x in eplus.split(".")]
                            is_correct = True
                        except ValueError:
                            pass
            print("Mapping OS '{}' to '{}'".format(v, eplus))
            # Add to the version_dict
            version_dict[v] = eplus

    # Prepend a column level for E+ version
    df_files.columns = pd.MultiIndex.from_tuples(
        [(version_dict[x[0]], x[0], x[1]) for x in df_files.columns], names=["E+", "OS", "Tag"]
    )
    return df_files


###############################################################################
#                P A R S I N G    F U N C T I O N S
###############################################################################

# These functions are designed to be used via `df_files.applymap`


def load_osw(out_osw_path):
    """
    Loads the JSON into a dict

    Args:
    -----
    * out_osw_path (str, path): path to the out.osw

    Returns:
    --------
    * data (dict): the parsed data
    """
    # Check is 'NaN', 'NaT' or 'None'
    if pd.isna(out_osw_path):
        return None

    with open(out_osw_path, "r") as jsonfile:
        json_text = jsonfile.read()
    data = json.loads(json_text)
    return data


def _parse_success(data, extra_check=True, verbose=False):
    """
    2.0.4 has a bug, it reports "Fail" when really it worked
    so if extra_check is True (for 2.0.4 only),
    if status='Fail', we check whether we can find 'EnergyPlus Completed
    Sucessfully' in the eplusout_err, in which case we return success

    Args:
    ------
    * data (dict): the dictionary corresponding to the out.osw JSON file
    * extra_check (bool): whether to ignore the completed_status when Fail
        and check the eplusout_err, pass True only for 2.0.4

    Returns:
    --------
    * status (str): 'Fail' or 'Success'
    """
    status = data["completed_status"]

    # OS 2.0.4 has a bug, it reports "Fail" when really it worked
    if status == "Fail" and extra_check:
        if "eplusout_err" in data.keys():
            # if "EnergyPlus Completed Successfully" in data['eplusout_err']:
            # This is now a list:
            if any("EnergyPlus Completed Successfully" in x for x in data["eplusout_err"]):
                if verbose:
                    print("OSW status is 'Fail' but E+ completed successfully")
                status = "Success"
    return status


def parse_success(out_osw_path):
    """
    Loads out.osw (load_osw) and checks the success
    Calls `load_osw` and `_parse_success`

    Args:
    -----
    * out_osw_path (str, path): path to the out.osw

    Returns:
    --------
    * status (str): 'Fail' or 'Success', or '' (empty) if there isn't even an
    OSW, which could happen in particular for OSMs that have a version older
    than the OpenStudio version used to run the tests

    """
    if out_osw_path is None:
        return ""

    data = load_osw(out_osw_path)
    if data is None:
        return ""

    extra_check = False
    if "2.0.4" in out_osw_path:
        extra_check = True

    status = _parse_success(data, extra_check=extra_check, verbose=False)
    # print("{} - {}".format(out_osw_path, status))
    return status


def _get_os_results(data, out_osw_path):
    """
    Helper function that finds the openstudio_result data in the dict

    Args:
    -----
    * data (dict): the dictionary corresponding to the out.osw JSON file
    * out_osw_path (str, path): path to the out.osw

    """
    if "2.0.4" in out_osw_path:
        os_results = [x for x in data["steps"] if x["measure_dir_name"] == "openstudio_results"]
    else:
        # This works from 2.0.5 onward...
        os_results = [x for x in data["steps"] if x["result"]["measure_name"] == "openstudio_results"]

    if len(os_results) == 0:
        print("There are no OpenStudio results for {}".format(out_osw_path))
        return None
    elif len(os_results) != 1:
        print("Warning: there are more than one openstudio_results measure " "for {}".format(out_osw_path))
    os_result = os_results[0]["result"]
    return os_result


def parse_total_site_energy(out_osw_path):
    """
    Finds the 'total_site_energy' (kBTU) in an out_osw_path

    Args:
    -----
    * out_osw_path (str, path): path to the out.osw

    Returns:
    * site_kbtu (float): the 'total_site_energy' from the openstudio_results
        measure. Returns np.nan is status is not Success or path is empty
    """

    data = load_osw(out_osw_path)
    if data is None:
        return np.nan
    extra_check = False
    if "2.0.4" in out_osw_path:
        extra_check = True

    status = _parse_success(data, extra_check=extra_check)
    if status != "Success":
        return np.nan

    os_result = _get_os_results(data, out_osw_path)
    if os_result is None:
        return np.nan

    site_kbtu = [x for x in os_result["step_values"] if x["name"] == "total_site_energy"][0]["value"]
    return site_kbtu


def parse_end_use(out_osw_path, throw_if_path_none=True):
    """
    Finds the fuel by end use in an out_osw_path

    Args:
    -----
    * out_osw_path (str, path): path to the out.osw

    Returns:
    * cleaned_end_use (pd.DataFrame): Fuel by End Use data
        index = 'End Use
        columns = ['Fuel', 'units']
    """

    data = load_osw(out_osw_path)
    if data is None:
        if throw_if_path_none:
            raise ("No path")
        else:
            return np.nan
    status = _parse_success(data)
    if status != "Success":
        raise ("Simulation failed for #{out_osw_path}")

    os_result = _get_os_results(data, out_osw_path)
    if os_result is None:
        return np.nan

    df = pd.DataFrame.from_records([x for x in os_result["step_values"] if "units" in x.keys()])

    end_use = df[df.name.str.contains("end_use")].copy()

    end_use[["Fuel", "End Use"]] = (
        end_use["name"].replace(PRETTY_NAMES, regex=True).str.replace("end_use_", "").str.split("_", expand=True)
    )

    filt1 = end_use["End Use"].isnull()
    end_use.loc[filt1, "End Use"] = end_use.loc[filt1, "Fuel"]
    end_use.loc[filt1, "Fuel"] = "Total"

    cleaned_end_use = end_use.set_index(["Fuel", "End Use", "units"])["value"].unstack([1]).T.replace(0, np.nan)

    return cleaned_end_use


def success_sheet(df_files, model_test_cases=None, add_missing=True):
    """
    High-level method to construct a dataframe of Success

    Args:
    -----
    * df_files (pd.DataFrame): from `find_info_osws()`
    * model_test_cases (pd.DataFrame): if not calls, `find_osm_test_versions()`

    """
    success = df_files.map(parse_success)
    if model_test_cases is None:
        model_test_cases = find_osm_test_versions()

    # Put N/A where OSM is newer than than the OS version
    for index, row in success.iterrows():
        if index[1] == "osm":
            test = index[0]
            version_osm = tuple(model_test_cases.loc[test, "OSM version"].split("."))
            filt1 = row.index.map(lambda x: tuple(x[1].split(".")) < version_osm)
            filt2 = row == ""
            row[filt1 & filt2] = "N/A"

    # Push OSM N/A to ruby N/A
    if "osm" in success.index.get_level_values("Type"):
        success = success.unstack("Test").T
        success.loc[(success["osm"] == "N/A") & (success["rb"] == ""), "rb"] = "N/A"
        success.loc[(success["osm"] == "N/A") & (success["py"] == ""), "py"] = "N/A"
        success = success.unstack("Test").swaplevel(axis=1).T
        # This messed up the order, 22.1.0 is now before 8.6.0
        success = success.loc[:, df_files.columns]

    # Put N/A for python tests before 3.7.0
    success.loc[
        success.index.get_level_values("Type") == "py",
        success.columns.get_level_values("OS").map(lambda x: tuple(map(int, x.split("-")[0].split("."))) < (3, 7, 0)),
    ] = "N/A"

    # Create n_fail and order by that
    n_fail = (success == "Fail").sum(axis=1)
    n_missing = (success == "").sum(axis=1)
    n_fail_miss = n_fail + n_missing

    success["n_fail"] = n_fail

    if add_missing:
        success["n_missing"] = n_missing
        success["n_fail+missing"] = n_fail_miss
        # Order by n_fail, then by n_fail+missing
        order_n_fail = success.groupby(level="Test").sum().sort_values(by=["n_fail", "n_fail+missing"], ascending=False)
    else:
        order_n_fail = success.groupby(level="Test")["n_fail"].sum().sort_values(ascending=False)

    success = success.reindex(index=order_n_fail.index, level=0)

    return success


def success_sheet_utilities(df_files):
    """
    High-level method to construct a dataframe of Success for utilities tests

    Args:
    -----
    * df_files (pd.DataFrame): from `find_info_osws()`
    """

    def parse_status_success(out_status_path):
        if out_status_path is None:
            return ""
        data = load_osw(out_status_path)
        if data is None:
            return ""
        return data["Status"]

    success = df_files.applymap(parse_status_success)

    # Create n_fail and order by that
    n_fail = (success == "Fail").sum(axis=1)
    success["n_fail"] = n_fail

    # Order by n_fail, then by n_fail+missing
    order_n_fail = success.groupby(level="Test").sum().sort_values(by="n_fail", ascending=False)

    success = success.reindex(index=order_n_fail.index, level=0)
    return success


def encoding_sheet_utilities(df_files):
    """
    High-level method to construct a dataframe of encoding for the
    'path_special_chars_pwd' test case

    Args:
    -----
    * df_files (pd.DataFrame): from `find_info_osws()`
    """

    def parse_status_encoding(out_status_path):
        if out_status_path is None:
            return ""
        data = load_osw(out_status_path)
        if data is None:
            return ""
        if "Dir.pwd_Encoding" not in data:
            print("Error: {}, {}".format(out_status_path, data))
            return None
        return data["Dir.pwd_Encoding"]

    return df_files.loc["path_special_chars_pwd"].applymap(parse_status_encoding)


def success_sheet_sql(df_files):
    """
    High-level method to construct a dataframe of Success for sql tests

    Args:
    -----
    * df_files (pd.DataFrame): from `find_info_osws()`
    """

    def parse_sql_success(out_sql_path):
        if out_sql_path is None:
            return ""
        with open(out_sql_path, "r") as f:
            status = f.read().strip()
        return status

    success = df_files.applymap(parse_sql_success)

    # Create n_fail and order by that
    n_fail = (success == "Fail").sum(axis=1)
    success["n_fail"] = n_fail

    # Order by n_fail, then by n_fail+missing
    order_n_fail = success.groupby(level="Test").sum().sort_values(by="n_fail", ascending=False)

    success = success.reindex(index=order_n_fail.index, level=0)
    return success


def test_implemented_sheet(df_files, success=None, model_test_cases=None, only_for_mising_osm=False):
    """
    High-level method to construct a dataframe of test implemented or not
    as well as OSM version (+ Major, Minor, Patc)

    Args:
    -----
    * df_files (pd.DataFrame): from `find_info_osws()`
    * success (pd.DataFrame): if None, calls `success_sheet`
    * model_test_cases (pd.DataFrame): if None, calls `find_osm_test_versions`
    * only_for_mising_osm (bool): include "First Ruby Version Worked"
    for only the tests with missing OSMs or all
    """

    if model_test_cases is None:
        model_test_cases = find_osm_test_versions()
    if success is None:
        success = success_sheet(df_files)

    test_impl = pd.DataFrame(df_files.index.tolist(), columns=["Test", "Type"])
    test_impl["Has_Test"] = True
    test_impl = test_impl.pivot(index="Test", columns="Type", values="Has_Test").fillna(False)

    # Filter out OSW:
    test_impl = test_impl[[x for x in test_impl.columns if x != "osw"]]
    test_impl = test_impl.join(model_test_cases[["OSM version", "Major", "Minor", "Patch"]]).fillna("")

    if only_for_mising_osm:
        missing_osms = test_impl[~test_impl["osm"] & test_impl["rb"]].index.tolist()
        temp = (
            success.swaplevel(1, 0, axis=0)
            .loc["rb"]
            .loc[missing_osms, [x for x in success.columns if x[0] != "n_fail"]]
        )
    else:
        temp = success.swaplevel(1, 0, axis=0).loc["rb"].loc[:, [x for x in success.columns if x[0] != "n_fail"]]

    first_success = temp.apply(lambda row: (row == "Success").idxmax()[1], axis=1)
    first_success.name = "First Version Ruby Worked"

    test_impl = test_impl.join(first_success).fillna("")

    return test_impl


def update_and_upload():
    """
    High level function to generate all needed dataframes and upload them
    to the google spreadsheet

    Args:
    ------
    None

    Returns:
    --------
    site_kbtu (pd.DataFrame): the dataframe with all parsed total_site_energy
    for use in post processing

    """
    spreadsheet = "/EffiBEM&NREL-Regression-Test_Status"

    compat_matrix = parse_compatibility_matrix()
    df_files = find_info_osws(compat_matrix=compat_matrix, test_dir="./test/")

    model_test_cases = find_osm_test_versions()

    # Test Status
    success = success_sheet(df_files=df_files, model_test_cases=model_test_cases)
    wks_name = "Test_Status"
    msg = "Uploading to '{}'".format(wks_name)
    if sys.version_info >= (3, 3):
        print(msg, end="", flush=True)
    else:
        print(msg, end="")

    d2g.upload(
        success.T.reset_index().T.reset_index(), gfile=spreadsheet, wks_name=wks_name, row_names=False, col_names=False
    )
    print("... Done")

    # Missing / Implemented test
    test_impl = test_implemented_sheet(df_files=df_files, success=success, only_for_mising_osm=False)

    wks_name = "Tests_Implemented"
    msg = "Uploading to '{}'".format(wks_name)
    if sys.version_info >= (3, 3):
        print(msg, end="", flush=True)
    else:
        print(msg, end="")

    d2g.upload(test_impl, gfile=spreadsheet, wks_name=wks_name, row_names=True, col_names=True)
    print("... Done")

    # Site kbtu
    site_kbtu = df_files.applymap(parse_total_site_energy)
    wks_name = "SiteKBTU"
    msg = "Uploading to '{}'".format(wks_name)
    if sys.version_info >= (3, 3):
        print(msg, end="", flush=True)
    else:
        print(msg, end="")

    d2g.upload(
        site_kbtu.T.reset_index().T.reset_index().fillna(""),
        gfile=spreadsheet,
        wks_name=wks_name,
        # Skip first row
        start_cell="A1",
        row_names=False,
        col_names=False,
    )
    print("... Done")

    # Rolling percent difference of total kBTU from one version to the next
    wks_name = "SiteKBTU_Percent_Change"
    msg = "Uploading to '{}'".format(wks_name)
    if sys.version_info >= (3, 3):
        print(msg, end="", flush=True)
    else:
        print(msg, end="")

    d2g.upload(
        (site_kbtu.pct_change(axis=1).T.reset_index().T.reset_index().fillna("")),
        gfile=spreadsheet,
        wks_name=wks_name,
        row_names=False,
        col_names=False,
    )
    print("... Done")

    return site_kbtu


def full_extent(ax, pad=0.0):
    """Get the full extent of an axes, including axes labels, tick labels, and
    titles."""
    # For text objects, we need to draw the figure first, otherwise the extents
    # are undefined.
    ax.figure.canvas.draw()
    items = ax.get_xticklabels() + ax.get_yticklabels()
    # items += [ax, ax.title, ax.xaxis.label, ax.yaxis.label]
    items += [ax, ax.title]
    bbox = mpl.transforms.Bbox.union([item.get_window_extent() for item in items])

    return bbox.expanded(1.0 + pad, 1.0 + pad)


def heatmap_sitekbtu_pct_change_on_ax(toplot, ax, display_threshold, repeat_x_on_top=False):
    """
    Plots the heatmap on a given axis
    Typically this is a helper called from `heatmap_sitekbtu_pct_change`
    so see this function too.

    The principle is to plot 3 seaborn heatmap atop each other so we can give
    different colors based on the amount of variation experienced based on the
    display_threshold:
        * if above: plot with colorscale
        * if below but non zero: plot in grey italic
        * if zero: plot in green
        (if missing: white)

    Args:
    -----
    * toplot (pd.DataFrame): the data to be plotted as a heatmap. Typically
    this is a subset of site_kbtu_change

    * ax (AxesSubplot): the matplotlib ax on which to plot

    * display_threshold (float): apply the colorscale to the cells that are
    above this threshold, otherwise they get greyed out

    * repeat_x_on_top (bool): the OS/Version labels on the xaxis will be at the
    bottom anyways, but if this is True, it is repeated above the plot too.

    """

    # Same as: fmt = lambda x,pos: '{:.1%}'.format(x)
    def fmt(x, pos):
        return "{:.1%}".format(x)

    # Prepare two custom cmaps with one single color
    grey_cmap = mpl.colors.ListedColormap("#f7f7f7")
    green_cmap = mpl.colors.ListedColormap("#f0f7d9")

    # Plot with colors, for those that are above the display_threshold
    # Note: cells not shown where mask is True
    sns.heatmap(
        toplot.abs(),
        mask=toplot.abs() <= display_threshold,
        ax=ax,
        cmap="YlOrRd",  # cmap='Reds', 'RdYlGn_r'
        vmin=0,
        vmax=0.5,
        cbar_kws={"format": mpl.ticker.FuncFormatter(fmt)},
        annot=toplot,
        fmt=".2%",
        linewidths=0.5,
    )

    # Plot a second heatmap on top, for those are below the display threshold,
    # but not zero: these you print the value

    # Plot a second heatmap on top, only for those that are below
    sns.heatmap(
        toplot,
        mask=((toplot.abs() > display_threshold) | (toplot.abs() == 0)),
        cbar=False,
        annot=True,
        fmt=".3%",
        annot_kws={"style": "italic"},
        ax=ax,
        cmap=grey_cmap,
    )

    # Plot a third heatmap on top, only for those that are zero,
    # no annot just green
    sns.heatmap(
        toplot,
        mask=(toplot.abs() != 0),
        cbar=False,  # linewidths=.5, linecolor='#cecccc',
        annot=False,
        ax=ax,
        cmap=green_cmap,
    )

    # If the format is more high than wide (based on 16/9), display xticks on
    # top too.
    if repeat_x_on_top:
        ax.xaxis.set_tick_params(labeltop="on")


def dataframe_row_chunks(df, n):
    """Yield successive n-sized chunks (rows) from a dataframe."""
    for i in range(0, len(df), n):
        yield df.iloc[i : i + n]


def heatmap_sitekbtu_pct_change(
    site_kbtu_change,
    row_threshold=0.005,
    display_threshold=0.001,
    show_plot=True,
    savefig=False,
    figname=None,
    figsize=None,
    save_indiv_figs_for_ax=False,
):
    """
    Plots a heatmap to show difference in site kbtu from one version to the
    next for each test. It has options to display more or less variations
    to emphasis meaningful differences.
    If the figure becomes too big, it is broken in chunks of maximum 40 rows
    so we can repeat the version labels every so often so its readable,
    but it saves a single figure

    Args
    -----
    * site_kbtu_change (pd.DataFrame): typically gotten from
    `df_files.applymap(regression_analysis.parse_total_site_energy)`
    then calling `site_kbtu.pct_change(axis=1)`

    * row_threshold (float): only display tests where there is at least one
    cell that has a change greater than this. This value is a percentage,
    eg: 0.005 means at least 0.5% change

    * display_threshold (float): apply the colorscale to the cells that are
    above this threshold, otherwise they get greyed out

    * savefig (boolean): whether to save the figure or not.
    * figname (str): if savefig is true, you can force a .png name
        if None, defaults to 'site_kbtu_pct_change.png'.
        You must pass the .png with it.

    * figsize (tuple, optional): the figure size, if None it is calculated

    * save_indiv_figs_for_ax (bool, optional): If a big figure is generated,
    save it in several chunks

    Returns:
    --------
    True if there are diffs above the threshold, False otherwise
    """

    g_toplot = site_kbtu_change[(site_kbtu_change.abs() > row_threshold).any(axis=1)]
    g_toplot.index = [".".join(x) for x in g_toplot.index]
    g_toplot.columns = ["\n".join(x) for x in g_toplot.columns]
    g_toplot.columns.names = ["E+\nOS"]

    max_abs_diff = site_kbtu_change.iloc[:, 1:].abs().max().max()

    if g_toplot.empty:

        if max_abs_diff != 0:

            if max_abs_diff > (0.0001 / 100.0):
                msg = (
                    "Warning: There are no percentages differences that are"
                    " above the threshold={:.4%} for any test/version,"
                    "but there are some non-zero values, absolute max diff "
                    "is {:.4%}".format(row_threshold, site_kbtu_change.abs().max().max())
                )
            else:
                msg = "OK: There are no meaningful differences (<0.0001%)" "Max diff is {}".format(max_abs_diff)
        else:
            msg = "OK: There are NO differences at all"

        print(msg)
        return False
    else:
        print("Max Absolute difference: {:.4%}".format(max_abs_diff))
        max_last_diff = site_kbtu_change.iloc[:, -1].abs().max()
        print("Max Absolute difference of last version: " "{:.4%}".format(max_last_diff))
    if figsize is None:
        w = 16
        h = max(w * g_toplot.shape[0] / (3 * g_toplot.shape[1]), 4.0)
    else:
        w = figsize[0]
        h = figsize[1]

    # Maximum rows on a single axis
    max_rows = 40
    # Break the global toplot dataframe into chunks of 40 rows max
    my_chunks = list(dataframe_row_chunks(g_toplot, max_rows))
    n_chunks = len(my_chunks)

    # If the figure is bigger than height=9in, we repeat the xaxis (E+/OS
    # versions) on top as well as the bottom
    if h > 9:
        repeat_x_on_top = True
    else:
        repeat_x_on_top = False

    # Create a figure with dimensions and an appropriate number of rows
    fig, axes = plt.subplots(figsize=(w, h), nrows=n_chunks)
    # If n_chunks is 1, we still make an array of a single axis so that
    # indexing will work in the for loop below
    if not isinstance(axes, np.ndarray):
        axes = np.array([axes])

    # Reserve 1.5 inches at bottom for explanation
    fig.subplots_adjust(bottom=1.5 / h)

    # Plot each single chunk as a heatmap
    for i, toplot in enumerate(my_chunks):
        ax = axes[i]
        heatmap_sitekbtu_pct_change_on_ax(
            toplot=toplot, ax=ax, display_threshold=display_threshold, repeat_x_on_top=repeat_x_on_top
        )

    # Figure Annotations: The title on the top axis, and the explanation
    # on the bottom axis
    title = "Percent difference total site kBTU from one version to the next"

    axes[0].annotate(
        title,
        xy=(0.5, 1.0),
        xycoords="axes fraction",
        ha="center",
        va="top",
        xytext=(0, 60),
        textcoords="offset points",
        weight="bold",
        fontsize=16,
    )

    ann = (
        "Rows (Tests) have been filtered and are only displayed if there "
        "is at least one cell with more than {:.2%} change.\n"
        "Colorscale applies to cells that are above a display threshold "
        "of {:.2%}.\n"
        "Cells in grey are below the display threshold. "
        "Cells in green are zero.\n"
        "White cells indicate a missing/failed test "
        "(except for 2.0.4, it's a rolling pct_change)"
        "".format(row_threshold, display_threshold)
    )

    # Some hardcoded options
    annotate_in_axes_coord = False
    style = "italic"
    style = None
    if annotate_in_axes_coord:
        axes[-1].annotate(
            ann,
            xy=(0.0, 0.0),
            xycoords="axes fraction",
            ha="left",
            va="top",
            xytext=(0, -80),
            textcoords="offset points",
            style=style,
        )
    else:
        axes[-1].annotate(ann, xy=(0.0, 0.0), xycoords="figure fraction", ha="left", va="bottom", style=style)
    if savefig:
        if not os.path.exists(STABILITY_DIR):
            os.makedirs(STABILITY_DIR)
        if figname is None:
            figname = os.path.join(STABILITY_DIR, "site_kbtu_pct_change.png")
        plt.savefig(figname, dpi=150, bbox_inches="tight")
        print("Saved to {}".format(os.path.abspath(figname)))
        if save_indiv_figs_for_ax:
            for i, ax in enumerate(axes):
                # Save just the portion _inside_ the second axis's boundaries
                extent = full_extent(ax).transformed(fig.dpi_scale_trans.inverted())
                # Alternatively,
                # extent = (ax.get_tightbbox(fig.canvas.renderer)
                #             .transformed(fig.dpi_scale_trans.inverted()))
                fname, fext = os.path.splitext(figname)

                filepath = os.path.join(STABILITY_DIR, "{}_ax{}.png".format(fname, i))
                fig.savefig(filepath, dpi=150, bbox_inches=extent.expanded(1.3, 1.15))

    if show_plot:
        # fig.tight_layout()
        plt.show()

    return True


###############################################################################
#             S T A B I L I T Y    T E S T I N G
###############################################################################


def delete_custom_tagged_osws(contains=None, regex_pattern=None):
    # Glob all
    custom_osws = gb.glob(os.path.join(TEST_DIR, "*out_*.osw"))

    # Check if need to only keep certain ones
    if contains:
        custom_osws = [x for x in custom_osws if contains in os.path.split(x)[1]]
    elif regex_pattern:
        re_pat = re.compile(r"{}".format(regex_pattern))
        custom_osws = [x for x in custom_osws if re_pat.search(os.path.split(x)[1])]

    if custom_osws:
        for x in custom_osws:
            print("Deleting: {}".format(os.path.split(x)[1]))
            os.remove(x)

        return True
    else:
        print("Did not find any custom tagged files matching")
        return False


def test_os_cli(os_cli=None):
    """
    Make sure the CLI is configured properly, and return a version information
    dictionary if worked
    False otherwise.
    """
    # Check correct CLI
    if os_cli is None:
        os_cli = "openstudio"

    cmd = "{} -e \"require 'openstudio'; " 'puts OpenStudio::openStudioLongVersion"'.format(os_cli)
    # Shlex does weird things with windows path and it's not necessary on
    # Windows, so might as well not do it.
    if sys.platform == "win32":
        c_args = cmd
    else:
        c_args = shlex.split(cmd)

    os_long_version = None
    # os_short_version = None
    try:
        process = subprocess.Popen(c_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lines = process.stdout.readlines()
        os_long_version = lines[0].rstrip().decode()
        # os_short_version = ".".join(os_long_version.split('.')[:-1])
        print("Selected OS_CLI has version '{}'".format(os_long_version))
        m = SEMVER_REGEX.match(os_long_version)
        if m:
            return m.groupdict()
        else:
            print("Couldn't parse the os_long_version, returning as is")
            return os_long_version
    except:
        print("Problem with the CLI, make sure it is configured properly")
        print("Command that was run to test it:\n{}".format(c_args))
        return False


def test_stability(
    os_cli=None,
    test_filter=None,
    run_n_times=5,
    start_at=1,
    save_idf=False,
    energyplus_exe_path=None,
    platform_name=None,
):
    """
    This function will run model_tests.rb several times and save the out.osw
    with a custom tag so they can be analyzed after. It is useful for testing
    the stability of a given test (or several)

    OSW files will be named like `testname_X.Y.Z_out_{platform}_run{n_i}.osw'

    Args:
    ------
    * os_cli (path): Path to the CLI to be used defaults to 'openstudio'
    You can use 'ruby' if the include paths are set correctly, or you could
    provide the full path to your openstudio CLI

    * test_filter (str): filter to pass to model_tests.rb.
        eg: 'fourpipebeam' will results in `model_tests.rb -n /fourpipebeam/`
        If omitted, runs all tests

    * run_n_times (int): number of times to run the tests
    * start_at (int): Override if you have already run N times before,
    and do not want to override.
        eg: n=2 and start_at=3 will results in '_run3' and 'run4'

    * save_idf (bool): Whether you want to also save the IDF next to out.osw
    Useful for checking IDF diffs for ruby tests that are unstable

    * energyplus_exe_path (str, path): sets the ENERGYPLUS_EXE_PATH variable
        Useful when the CLI doesn't find the E+ exe by himself.

    * platform_name (str): Will default to `platform.system()` (eg: Linux)
        You could pass stuff like 'Ubuntu'

    """
    if os_cli is None:
        os_cli = "openstudio"

    if not test_os_cli(os_cli):
        return False

    # Copy environment to add custom ENV variables
    # passing env VAR=VALUE openstudio Xxxxx doesn't work on Windows
    my_env = os.environ.copy()

    # Configure env-like variables
    if energyplus_exe_path is None:
        eplus_exe = ""
    else:
        eplus_exe = "ENERGYPLUS_EXE_PATH='{}'".format(energyplus_exe_path)
        my_env["ENERGYPLUS_EXE_PATH"] = energyplus_exe_path

    if save_idf:
        save_idf = "SAVE_IDF=True"
        my_env["SAVE_IDF"] = "True"
    else:
        save_idf = ""

    if test_filter is None:
        filt = ""
    else:
        if test_filter.count("/") >= 2:
            filt = "-n {}".format(test_filter)
        else:
            filt = "-n /{}/".format(test_filter)

    # Default platform
    if platform_name is None:
        platform_name = platform.system()

    example_tag = "{}_run{}".format(platform_name, start_at)
    print("Custom tags will be like this: first run = " "'{}'".format(example_tag))

    # Used for display only
    EXPLICIT_COMMAND = "env CUSTOMTAG={c} {s} {e} {cli} {m} {filt}"
    print(
        "\nExample Command:\n"
        "{}".format(
            EXPLICIT_COMMAND.format(
                c=example_tag,
                s=save_idf,
                e=eplus_exe,
                m=os.path.join(ROOT_DIR, "model_tests.rb"),
                cli=os_cli,
                filt=filt,
            )
        )
    )

    # Actual command, env variables are passed as such (env parameter)
    COMMAND = "{cli} {m} {filt}"
    m = os.path.join(ROOT_DIR, "model_tests.rb")

    if isnotebook():
        tdqm_bar = tqdm.tqdm_notebook
        desc = "<h3>Running {} Times</h3>".format(run_n_times)
        label = HTML(desc)
        display(label)
    else:
        tdqm_bar = tqdm.tqdm

    for i in tdqm_bar(range(start_at, run_n_times + start_at), total=run_n_times):
        print("\n\n" + "=" * 80)
        print(" " * 20 + "S T A R T I N G    O N    R U N   {}".format(i))
        print("=" * 80)
        custom_tag = "{}_run{}".format(platform_name, i)

        my_env["CUSTOMTAG"] = custom_tag

        explicit_command = EXPLICIT_COMMAND.format(c=custom_tag, s=save_idf, e=eplus_exe, m=m, cli=os_cli, filt=filt)
        print(explicit_command)

        # Actual command, the env variables are passed as such (env)
        full_command = COMMAND.format(m=m, cli=os_cli, filt=filt)

        # Shlex does weird things with windows path and it's not necessary on
        # Windows, so might as well not do it.
        if sys.platform == "win32":
            c_args = full_command
        else:
            c_args = shlex.split(full_command)

        process = subprocess.Popen(c_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=my_env)

        for line in iter(process.stdout.readline, b""):
            stripped_line = line.rstrip().decode()
            # Skip this output
            if any(c in stripped_line.lower() for c in ("started", "run options")):
                continue
            print(stripped_line)

        process.stdout.close()
        returncode = process.wait()
        # If something went wrong (very likely in the first run of the loop),
        # we raise and don't try further runs (they'll fail too)
        if returncode != 0:
            print(r"\n/!\ Something went wrong, process returned a " "returncode of {}".format(returncode))
            print("Command: {}".format(c_args))
            print(
                "Custom ENV variables: "
                "{}".format({k: my_env[k] for k in my_env if k in ["CUSTOMTAG", "SAVE_IDF", "ENERGYPLUS_EXE_PATH"]})
            )
            raise subprocess.CalledProcessError(returncode=1, cmd=c_args)

    return True


###############################################################################
#                             S D D    T E S T S                              #
###############################################################################


def success_sheet_sddft(df_files):
    success = df_files.applymap(lambda x: "Fail" if pd.isnull(x) else "Success")
    success["n_fail"] = (success == "Fail").sum(axis=1)
    success["n_passed"] = (success == "Success").sum(axis=1)
    return success


def diff_xmls(start_file, end_file):
    """
    Diffs two xml files, removing known changes for select version

    Args:
    -----
    * start_file (str): path to old XML
    * end_file (str): path to new XML

    Returns:
    --------
    * diff (list): list of changed, or None if no changes

    Needs:
    ------
    from xmldiff import main, formatting

    """
    fmt = formatting.DiffFormatter()

    # This python module seems to have problems sometimes...
    try:
        diff = main.diff_files(start_file, end_file, formatter=fmt)
    except:
        warnings.warn("Diff failed for start_file={}, " "end_file={}".format(start_file, end_file), UserWarning)
        return

    known_changes = []
    m = re.search(r"(?P<version>\d+\.\d+\.\d+)_out", end_file)
    if m:
        # Add known changes here.
        end_version = m.groupdict()["version"]
        if end_version == "2.7.2":
            # Between 2.7.1 and 2.7.2, a few things changed
            known_changes = [
                # CoilHtg used to incorrectly map as CoilClg
                re.compile(r"\[rename, \/.*CoilClg\[\d+\], CoilHtg]"),
                # BldgAz goes from "0" to "-0"
                re.compile(r"\[update, \/.*BldgAz\[\d+\]\/text\(\)\[\d+\]," r' "0"]'),
            ]

    diff = diff.splitlines()
    diff = [line for line in diff if not any(regex.match(line) for regex in known_changes)]
    if diff:
        return diff


def diff_all_xmls(df_files):
    """
    Computes all XMLs changed from one version to the next
    by calling `diff_xmls` for each test

    Args:
    -----
    * df_files (pd.DataFrame): a DataFrame that has

    """
    df_diff = pd.DataFrame(index=df_files.index, columns=df_files.columns)
    for i, (index, row) in enumerate(df_files.iterrows()):
        if index == ("scheduled_infiltration", "osm"):
            # This one's weird, it thinks the coordinates of the points moved
            # when in reality they didn't at all
            warnings.warn(
                "Skipping scheduled_infiltration.osm as it produces " "weird diffs that aren't true", UserWarning
            )
            continue
        for j, (colindex, end_file) in enumerate(row.iteritems()):
            if j == 0:
                continue
            start_file = df_files.iloc[i, j - 1]
            df_diff.iloc[i, j] = diff_xmls(start_file, end_file)
    df_diff.dropna(axis=0, how="all", inplace=True)
    return df_diff


###############################################################################
#                                S T Y L I N G                                #
###############################################################################


def background_colors(val):
    fmt = ""
    s = "background-color: {}"
    if val == "Fail":
        fmt = s.format("#F4C7C3")
    elif val == "N/A":
        fmt = s.format("#EDEDED") + "; color: #ADADAD;"
    elif val == "":
        fmt = s.format("#f2e2c1")
    return fmt


def hover(hover_color="#ffff99"):
    return dict(selector="tr:hover", props=[("background-color", "%s" % hover_color)])


def getStyles():
    styles = [
        hover(),
        dict(selector="tr:nth-child(2n+1)", props=[("background", "#f5f5f5")]),
        dict(selector="td", props=[("text-align", "center")]),
        dict(selector="caption", props=[("caption-side", "bottom"), ("color", "grey")]),
    ]
    return styles


###############################################################################
#             C O M M A N D    L I N E    F U N C T I O N S
###############################################################################


def make_ci_annotations(failures_index, title, message, log_level="error", pct_diffs=None):
    accepted_log_levels = ["error", "warning", "notice"]
    if log_level not in accepted_log_levels:
        raise ValueError(f"log_level must be one of {accepted_log_levels}, not {log_level}")
    for i, (test_name, test_type) in enumerate(failures_index):
        if test_name == "autosizing":
            test_name = "autosize_hvac"
        fname = f"{test_name}.{test_type}"
        test_file = os.path.join("model/simulationtests", fname)
        if os.path.exists(test_file):
            name = test_file
        else:
            # Annotate on model_tests.rb
            name = "model_tests.rb"

        line = 1
        endLine = 2
        thisTitle = f"{title}: {fname}"
        thisMessage = message
        if pct_diffs is not None:
            thisMessage += f": {pct_diffs[i]:.3%}"
        print(f"::{log_level} file={name},line={line},endLine={endLine}," f"title={thisTitle}::{thisMessage}")


def cli_test_status_html(
    entire_table=False, tagged=False, all_osws=False, quiet=False, max_eplus_versions=None, ci_annotations=False
):
    if tagged:
        # Tagged-only
        df_files = find_info_osws_with_tags(compat_matrix=None, tags_only=True, quiet=quiet)
    elif all_osws:
        # All osws
        df_files = find_info_osws_with_tags(compat_matrix=None, tags_only=False, quiet=quiet)
    else:
        df_files = find_info_osws()

    if max_eplus_versions is not None:
        df_files = df_files[df_files.columns.get_level_values(level="E+").unique()[-max_eplus_versions:]]

    styles = getStyles()

    # This shows all tests that are implemented but where we don't even have
    # a single out.osw in any OpenStudio that exists,
    # meaning the simulation didn't even start
    # (ruby measure failed, or OSM failed to load)
    if not tagged:
        all_tests = parse_model_tests_rb()
        totally_failing_tests = set(all_tests) - set(df_files.index.tolist())
        if totally_failing_tests:
            print("The following tests may have failed in all " "openstudio versions. Exclude them.")
            print(totally_failing_tests)

    success = success_sheet(df_files)
    caption = "Test Success - All found"

    # Filter all NA rows
    success = success.loc[success.any(axis=1)]

    return_code = 0

    if not entire_table:
        ruby_or_osm_fail = success.groupby(level="Test")["n_fail+missing"].sum().sort_values(ascending=False) > 0

        print("Filtering only tests where there is a missing or failed osm OR " "ruby test")
        # success = success[success['n_fail+missing'] > 0]
        success2 = success.loc[[x for x in success.index if x[0] in ruby_or_osm_fail.index[ruby_or_osm_fail]]]

        if success2.empty:
            print("\nOK: No Failing tests were found")
        else:
            success = success2
            caption = "Test Success - Failed only"

            failures_idx = success.index[(success.iloc[:, -4] != "Success") & (success.iloc[:, -5] == "Success")]
            if failures_idx.empty:
                print("\nInfo: you have failing tests, but no new failures")
            else:
                failures = [f"{x[0]}.{x[1]}" for x in failures_idx]
                print(f"\nWARNING: you have {len(failures)} NEW failing tests:" f"\n{failures}")
                return_code = 1
                if ci_annotations:
                    make_ci_annotations(
                        failures_index=failures_idx,
                        title="New failure",
                        message=("This file passed in the last version but " "is now failing"),
                        log_level="error",
                    )

    html = (
        success.style.set_table_attributes('style="border:1px solid black;' 'border-collapse:collapse;"')
        .set_properties(**{"border": "1px solid black", "border-collapse": "collapse", "border-spacing": "0px"})
        .applymap(background_colors)
        .set_table_styles(styles)
        .set_caption(caption)
    ).render()

    if not os.path.exists(STABILITY_DIR):
        os.makedirs(STABILITY_DIR)
    filepath = os.path.join(STABILITY_DIR, "Regression_Test_Status.html")
    with open(filepath, "w") as f:
        f.write(html)

    print("HTML file saved in {}".format(os.path.join(os.getcwd(), filepath)))
    if not quiet:
        if sys.platform.startswith("darwin"):
            subprocess.call(("open", filepath))
        elif os.name == "nt":
            os.startfile(filepath)
        elif os.name == "posix":
            subprocess.call(("xdg-open", filepath))

    return return_code


def cli_heatmap(
    tagged=False,
    all_osws=False,
    row_threshold=0.01,
    display_threshold=0.001,
    save_indiv_figs_for_ax=False,
    figname_with_thresholds=True,
    quiet=False,
    max_eplus_versions=None,
    ci_annotations=False,
):
    """
    Helper function called from the CLI to plot the heatmap
    """

    if tagged:
        # Tagged-only
        df_files = find_info_osws_with_tags(compat_matrix=None, tags_only=True, quiet=quiet)
    elif all_osws:
        # All osws
        df_files = find_info_osws_with_tags(compat_matrix=None, tags_only=False, quiet=quiet)
    else:
        df_files = find_info_osws()

    if max_eplus_versions is not None:
        df_files = df_files[df_files.columns.get_level_values(level="E+").unique()[-max_eplus_versions:]]

    site_kbtu = df_files.applymap(parse_total_site_energy)

    if figname_with_thresholds:
        figname = "site_kbtu_pct_change_row{}_display{}" ".png".format(row_threshold, display_threshold)
    else:
        figname = "site_kbtu_pct_change.png"

    if os._exists(figname):
        os.remove(figname)

    site_kbtu_change = site_kbtu.pct_change(axis=1)

    hasDiffs = heatmap_sitekbtu_pct_change(
        site_kbtu_change=site_kbtu_change,
        row_threshold=row_threshold,
        display_threshold=display_threshold,
        figname=figname,
        savefig=True,
        show_plot=False,
        save_indiv_figs_for_ax=True,
    )

    if hasDiffs:

        if ci_annotations:

            # Create annotations for diffs in the last version
            s_last_diff = site_kbtu_change.iloc[:, -1].sort_values()
            fail_mask = s_last_diff.abs() > row_threshold
            failures_idx = s_last_diff.index[fail_mask]
            if not failures_idx.empty:
                make_ci_annotations(
                    failures_index=failures_idx,
                    title="EUI deviation too large",
                    message=("This file exceeds the threshold of " f"{row_threshold:.2%}"),
                    log_level="error",
                    pct_diffs=s_last_diff[failures_idx],
                )
            else:
                hasDiffs = False

            warn_mask = s_last_diff.abs() > display_threshold
            warnings_idx = s_last_diff.index[warn_mask & ~fail_mask]
            make_ci_annotations(
                failures_index=warnings_idx,
                title="EUI deviation is concerning",
                message=("This file exceeds the display threshold of " f"{display_threshold:.2%}"),
                log_level="warning",
                pct_diffs=s_last_diff[warnings_idx],
            )

            if hasDiffs:
                exit(1)

        elif quiet:
            # Throw for stability error
            exit(1)
        else:
            if sys.platform.startswith("darwin"):
                subprocess.call(("open", figname))
            elif os.name == "nt":
                os.startfile(figname)
            elif os.name == "posix":
                subprocess.call(("xdg-open", figname))


def cli_upload():
    """
    Helper function called from the CLI to upload to google sheets
    """
    update_and_upload()
    print("All results uploaded to {}".format(SHEET_URL))


# If run from command line rather than imported
# This should really happen anymore unless for testing
# Preferred way is to either import or just the CLI
if __name__ == "__main__":

    site_kbtu = None

    question = "Do you want to parse the regression OSWs from '{}' and upload" " to Google Sheets?".format(TEST_DIR)

    reply = str(input(question + " [Y/n]: ")).lower().strip()
    if reply[:1] == "n":
        print("In this case, you can import this python file in an interactive" " environment to play with the results")
    else:
        site_kbtu = update_and_upload()
        print("All results uploaded to {}".format(SHEET_URL))

    question = "Do you want to plot the site kbtu percentage change?"

    reply = str(input(question + " [Y/n]: ")).lower().strip()
    if not reply[:1] == "n":
        question = "Input a row threshold, suggested values are " "0.01 (>1% change) or 0.005 (>0.5% change)\n"
        threshold = None
        while not threshold:
            try:
                threshold = float(input(question))
            except ValueError:
                print("Please input a float")

        # Plot the heatmap. On Ubuntu you will need to do:
        #    $ sudo apt-get install python-tk python3-tk tk-dev
        if site_kbtu is None:
            df_files = find_info_osws()
            site_kbtu = df_files.applymap(parse_total_site_energy)
        heatmap_sitekbtu_pct_change(
            site_kbtu_change=site_kbtu.pct_change(axis=1), row_threshold=threshold, savefig=True, show_plot=False
        )
        filepath = "site_kbtu_pct_change.png"
        if sys.platform.startswith("darwin"):
            subprocess.call(("open", filepath))
        elif os.name == "nt":
            os.startfile(filepath)
        elif os.name == "posix":
            subprocess.call(("xdg-open", filepath))
