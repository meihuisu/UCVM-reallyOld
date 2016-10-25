import os
import unittest
import xmltodict
import numpy as np

from ucvm.src.shared.properties import SeismicData, VelocityProperties, Point
from ucvm.src.shared.constants import UCVM_MODELS_DIRECTORY
from ucvm.src.framework.ucvm import UCVM


def assert_velocity_properties(test_case: unittest.TestCase, data: SeismicData,
                               velocity_prop: VelocityProperties) -> None:
    test_case.assertIsNotNone(data)
    test_case.assertIsNotNone(data.velocity_properties)
    test_case.assertIsNotNone(velocity_prop)

    for prop in dir(data.velocity_properties):
        if "_" in prop[0:1] or prop == "count" or prop == "index":
            continue

        if getattr(data.velocity_properties, prop) is None:
            test_case.assertIsNone(getattr(velocity_prop, prop))
        else:
            try:
                float(getattr(data.velocity_properties, prop))
                test_case.assertAlmostEqual(getattr(data.velocity_properties, prop),
                                            getattr(velocity_prop, prop), 3)
            except ValueError:
                test_case.assertEqual(getattr(data.velocity_properties, prop),
                                      getattr(velocity_prop, prop))


def run_acceptance_test(test_case: unittest.TestCase, model_id: str) -> bool:
    """
    Runs the acceptance test for the given model id.
    :param test_case: The unittest case.
    :param model_id: The model ID to run the test for.
    :return: True if successful, false or exception if not.
    """
    npy_test_file = os.path.join(UCVM_MODELS_DIRECTORY, model_id, "test_" + model_id + ".npy")
    ucvm_model_file = os.path.join(UCVM_MODELS_DIRECTORY, model_id, "ucvm_model.xml")
    model_type = ""

    spacing = 0.05
    depth = 5000
    bottom_corner = {
        "e": 0,
        "n": 0
    }

    if not os.path.exists(npy_test_file) or not os.path.exists(ucvm_model_file):
        return False

    with open(ucvm_model_file, "r") as fd:
        ucvm_model = xmltodict.parse(fd.read())
        bottom_corner["e"] = \
            float(ucvm_model["root"]["information"]["coverage"]["bottom-left"]["e"])
        bottom_corner["n"] = \
            float(ucvm_model["root"]["information"]["coverage"]["bottom-left"]["n"])
        model_type = ucvm_model["root"]["information"]["type"]

    arr = np.load(npy_test_file)
    nums = {
        "x": len(arr),
        "y": len(arr[0]),
        "z": len(arr[0][0])
    }

    sd_array = [SeismicData() for _ in range(nums["x"] * nums["y"] * nums["z"])]
    counter = 0

    for x in range(nums["x"]):
        for y in range(nums["y"]):
            for z in range(nums["z"]):
                sd_array[counter].original_point = Point(bottom_corner["e"] + spacing * x,
                                                         bottom_corner["n"] + spacing * y,
                                                         0 + depth * z)
                counter += 1

    UCVM.query(sd_array, model_id, [model_type])

    counter = 0
    for x in range(nums["x"]):
        for y in range(nums["y"]):
            for z in range(nums["z"]):
                if arr[x][y][z][0] <= 0 and sd_array[counter].velocity_properties.vp is None or \
                   arr[x][y][z][1] <= 0 and sd_array[counter].velocity_properties.vs is None or \
                   arr[x][y][z][2] <= 0 and sd_array[counter].velocity_properties.density is None:
                    counter += 1
                    continue
                test_case.assertAlmostEqual(sd_array[counter].velocity_properties.vp,
                                            arr[x][y][z][0], 0)
                test_case.assertAlmostEqual(sd_array[counter].velocity_properties.vs,
                                            arr[x][y][z][1], 0)
                test_case.assertAlmostEqual(sd_array[counter].velocity_properties.density,
                                            arr[x][y][z][2], 0)
                counter += 1

    return True