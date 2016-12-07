"""
Defines the tests for the trilinear operator within UCVM.

Copyright:
    Southern California Earthquake Center

Developer:
    David Gill <davidgil@usc.edu>
"""
# UCVM Imports
from ucvm.src.framework.ucvm import UCVM
from ucvm.src.shared.properties import SeismicData, Point
from ucvm.src.shared.test import UCVMTestCase


class TrilinearOperatorTest(UCVMTestCase):
    """
    Defines the test cases for the trilinear interpolation operator.
    """
    description = "Trilinear Interpolation"

    def test_trilinear_query(self):
        """
        Tests that the Trilinear interpolation works.

        Returns:
            None
        """
        self._test_start("test trilinear works with one corner different")

        sd_array = [SeismicData(Point(-118, 34, 0))]

        UCVM.query(sd_array, "1d.trilinear")

        self._test_end()
