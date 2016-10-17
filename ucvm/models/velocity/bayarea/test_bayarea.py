"""
Defines the tests for the USGS Bay Area model within UCVM.

:copyright: Southern California Earthquake Center
:author:    David Gill <davidgil@usc.edu>
:created:   October 4, 2016
:modified:  October 4, 2016
"""
import unittest

from ucvm.src.shared.properties import SeismicData, Point
from ucvm.src.shared.constants import UCVM_ELEVATION


class BayAreaVelocityModelTest(unittest.TestCase):

    def setUp(self):
        self.data = {
            "none": [],
            "one": [
                SeismicData(Point(-118, 34, 0))
            ],
            "elevation": [
                SeismicData(Point(-118, 34, 276.99, UCVM_ELEVATION))
            ]
        }