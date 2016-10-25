#!/usr/bin/env python
"""
Defines the setup script. This installs UCVM and downloads all the requested models. Models
can be added or deleted after the fact with the ucvm_model_manager utility. This auto-downloads new
models and can remove existing ones.

:copyright: Southern California Earthquake Center
:author:    David Gill <davidgil@usc.edu>
:created:   July 6, 2016
:modified:  July 21, 2016
"""

from setuptools import setup
from distutils.command.install import install
import urllib.request
import xml.dom.minidom
import os
from math import log
from subprocess import Popen, PIPE, CalledProcessError
import shutil
import sys

from collections import OrderedDict


UCVM_INFORMATION = {
    "short_name": "ucvm",
    "version": "16.12.0",
    "long_name": "Unified Community Velocity Model Framework",
    "author": "Southern California Earthquake Center",
    "email": "software@scec.org",
    "url": "http://www.scec.org/projects/ucvm"
}

_HYPOCENTER_BASE = "http://hypocenter.usc.edu/research/ucvm/" + UCVM_INFORMATION["version"]
_HYPOCENTER_MODEL_LIST = _HYPOCENTER_BASE + "/model_list.xml"

INSTALL_REQUIRES = ["h5py", "xmltodict", "humanize", "pyproj", "Cython", "psutil", "matplotlib"]


class OnlyGetScriptPath(install):
    def run(self):
        self.distribution.install_scripts = self.install_scripts


def get_setuptools_script_dir():
    dist = setup(cmdclass={'install': OnlyGetScriptPath})
    dist.dry_run = True  # not sure if necessary
    command = dist.get_command_obj('install')
    command.ensure_finalized()
    command.run()
    return dist.install_scripts


def execute(cmd):
    popen = Popen(cmd, stdout=PIPE, universal_newlines=True)
    stdout_lines = iter(popen.stdout.readline, "")
    for stdout_line in stdout_lines:
        yield stdout_line

    popen.stdout.close()
    return_code = popen.wait()
    if return_code != 0:
        raise CalledProcessError(return_code, cmd)


def sizeof_fmt(num):
    """
    Taken from http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable \
               -version-of-file-size
    :param num: The number to make human readable.
    :return: The number.
    """
    unit_list = [
        ('bytes', 0),
        ('kB', 0),
        ('MB', 1),
        ('GB', 2),
        ('TB', 2),
        ('PB', 2)
    ]

    if num > 1:
        exponent = min(int(log(num, 1024)), len(unit_list) - 1)
        quotient = float(num) / 1024**exponent
        unit, num_decimals = unit_list[exponent]
        format_string = '{:.%sf} {}' % num_decimals
        return format_string.format(quotient, unit)
    if num == 0:
        return '0 bytes'
    if num == 1:
        return '1 byte'


def get_list_of_installable_internet_models() -> dict:
    model_list_xml = xml.dom.minidom.parseString(
        urllib.request.urlopen(_HYPOCENTER_MODEL_LIST).read()
    )

    installable_models = {
        "velocity": [],
        "elevation": [],
        "vs30": [],
        "modifier": []
    }

    all_models = model_list_xml.getElementsByTagName("model")

    for model_item in all_models:
        inner_item = {
            "id": str(model_item.getElementsByTagName("file")[0].firstChild.data).split(".")[0],
            "description": "\n".join([x.strip() for x in str(
                model_item.getElementsByTagName("description")[1].firstChild.data
            ).split("\n")]),
            "name": str(model_item.getElementsByTagName("name")[0].firstChild.data),
            "coverage": str(model_item.getElementsByTagName("coverage")[0].
                            getElementsByTagName("description")[0].firstChild.data),
            "type": str(model_item.getElementsByTagName("type")[0].firstChild.data)
        }

        installable_models[inner_item["type"]].append(inner_item)

    return installable_models

download_everything = False
if "--everything" in sys.argv:
    download_everything = True
    sys.argv.remove("--everything")

models_to_download = [
    ("onedimensional", "1D"),
    ("usgs-noaa", "USGS/NOAA Digital Elevation Model"),
    ("wills-wald-2006", "Wills-Wald Vs30"),
    ("vs30-calc", "Calculated Vs30 from the model (top 30 meters slowness)")
]

print(
    "\n"
    "Thank you for downloading and installing UCVM " + UCVM_INFORMATION["version"] + "!\n"
    "\n"
    "UCVM software framework is a collection of software tools designed to provide a standard\n"
    "interface to multiple, alternative 3D velocity models.\n"
    "\n"
    "UCVM requires the 1D velocity model, USGS/NOAA digital elevation model, and the Wills-Wald\n"
    "Vs30 model to operate. Additional velocity, elevation, and Vs30 models are available for\n"
    "download. These models cover various regions within the world, although most are located\n"
    "within California.\n"
)

if shutil.which("mpicc") is not None:
    print("Setup has detected that you have MPI installed on your computer. UCVM will be\n"
          "installed with MPI support.\n")
    INSTALL_REQUIRES += ["mpi4py", "psutil"]

print("Specify which of the following models you wish to download and install with UCVM:\n")

model_list_u = get_list_of_installable_internet_models()
model_list = OrderedDict()
model_list["velocity"] = model_list_u["velocity"]
model_list["elevation"] = model_list_u["elevation"]
model_list["vs30"] = model_list_u["vs30"]
model_list["modifier"] = model_list_u["modifier"]

for key, models in model_list.items():
    # If all the models are already set to be downloaded by default, remove them.
    if len([x for x in models if (x["id"], x["name"]) not in models_to_download]) == 0:
        continue

    # Print the header.
    print(str(key).capitalize() + " Models:\n")
    for item in models:

        # If this model is already set to be downloaded, skip it.
        if (item["id"], item["name"]) in models_to_download:
            continue

        # Ask the user if they would like to download it
        print("Name:   " + item["name"])
        print("Covers: " + item["coverage"])
        print(item["description"])
        if download_everything:
            models_to_download.append((item["id"], item["name"]))
        else:
            if str(input("Would you like to install " +
                         item["name"] + "?\nType yes or y to install, no or n to pass: ")).\
                       strip().lower()[:1] == "y":
                models_to_download.append((item["id"], item["name"]))
        print("")
    print("")

total_model_size = 0

print("You have selected to install the following models: ")
for item in models_to_download:
    model_file = urllib.request.urlopen(_HYPOCENTER_BASE + "/models/" + item[0] + ".ucv")
    model_size = int(model_file.headers["Content-Length"])
    total_model_size += model_size
    print("   - " + (item[1][:42] + "..." if len(item[1]) > 45 else item[1]).ljust(55) +
          (" (" + item[0] + ")").ljust(20) + sizeof_fmt(model_size).rjust(10))

print("\nYour total download size will be: " + sizeof_fmt(total_model_size))

if not download_everything:
    if str(input("Would you like to install UCVM with these models? "
                 "Type yes or y to start the installation: ")).strip().lower()[:1] != "y":
        print("Aborting installation...")
        exit(1)

print("\nInstalling UCVM...")

setup(name=UCVM_INFORMATION["short_name"],
      version=UCVM_INFORMATION["version"],
      description=UCVM_INFORMATION["long_name"],
      author=UCVM_INFORMATION["author"],
      author_email=UCVM_INFORMATION["email"],
      url=UCVM_INFORMATION["url"],
      packages=["ucvm", "ucvm.src", "ucvm.src.framework", "ucvm.src.model",
                "ucvm.src.model.velocity", "ucvm.src.model.elevation", "ucvm.src.model.vs30",
                "ucvm.src.model.fault", "ucvm.src.model.modifier", "ucvm.src.shared",
                "ucvm.src.visualization", "ucvm.models", "ucvm.src.visualization.internal_basemap",
                "ucvm.tests", "ucvm.tests.data", "ucvm.tests.scratch", "ucvm.libraries"],
      package_dir={'ucvm': 'ucvm',
                   'ucvm.src': 'ucvm/src',
                   'ucvm.src.framework': 'ucvm/src/framework',
                   'ucvm.src.model': 'ucvm/src/model',
                   'ucvm.src.model.velocity': 'ucvm/src/model/velocity',
                   'ucvm.src.model.elevation': 'ucvm/src/model/elevation',
                   'ucvm.src.model.vs30': 'ucvm/src/model/vs30',
                   'ucvm.src.model.fault': 'ucvm/src/model/fault',
                   'ucvm.src.model.modifier': 'ucvm/src/model/modifier',
                   'ucvm.src.shared': 'ucvm/src/shared',
                   'ucvm.src.visualization': 'ucvm/src/visualization',
                   'ucvm.models': 'ucvm/models',
                   'ucvm.src.visualization.internal_basemap':
                       'ucvm/src/visualization/internal_basemap',
                   'ucvm.tests': 'ucvm/tests',
                   'ucvm.tests.data': 'ucvm/tests/data',
                   'ucvm.tests.scratch': 'ucvm/tests/scratch',
                   'ucvm.libraries': 'ucvm/libraries'},
      package_data={'ucvm.models': ['ucvm/models/installed.xml'],
                    'ucvm.libraries': ['ucvm/libraries/installed.xml'],
                    'ucvm.tests.data': ['ucvm/tests/data/simple_mesh_ijk12_rotated.xml',
                                        'ucvm/tests/data/simple_mesh_ijk12_unrotated.xml',
                                        'ucvm/tests/data/simple_utm_mesh_ijk12_rotated.xml']},
      data_files=[("ucvm/models", ["ucvm/models/installed.xml"]),
                  ("ucvm/libraries", ["ucvm/libraries/installed.xml"]),
                  ('ucvm/tests/data', ['ucvm/tests/data/simple_utm_mesh_ijk12_rotated.xml',
                                       'ucvm/tests/data/simple_mesh_ijk12_unrotated.xml',
                                       'ucvm/tests/data/simple_mesh_ijk12_rotated.xml'])],
      install_requires=INSTALL_REQUIRES,
      scripts=['ucvm/bin/ucvm_query', 'ucvm/bin/ucvm_model_manager', 'ucvm/bin/ucvm_mesh_create',
               'ucvm/bin/ucvm_model_manager', 'ucvm/bin/ucvm_plot_cross_section',
               'ucvm/bin/ucvm_plot_depth_profile', 'ucvm/bin/ucvm_plot_horizontal_slice',
               'ucvm/bin/ucvm_run_tests', 'ucvm/bin/ucvm_help'],
      zip_safe=False
      )

_LOCAL_SCRIPT_PATH = get_setuptools_script_dir()
print("")

# Now that UCVM is installed, we can go through the requested models and install them.
for model in models_to_download:
    for line in execute([os.path.join(_LOCAL_SCRIPT_PATH, "ucvm_model_manager"), "-a", model[0]]):
        print(line, end="")
    print("")

# Run the tests.
for line in execute([os.path.join(_LOCAL_SCRIPT_PATH, "ucvm_run_tests"), "-t"]):
    print(line, end="")

print("Thank you for installing UCVM. The installation is now complete. To learn more about")
print("UCVM, please run the command ucvm_help.")
