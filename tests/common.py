# -*- coding: utf-8 -*-

"""Unittests for the Onewire Server.
"""


__license__ = """
    This file is part of RasPy.

    RasPy is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    RasPy is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with RasPy. If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'

# Update this value when running on raspberry
# 1.5 is a good choice
SLEEP = 0.50

import sys, os
import time
import unittest
import threading
import logging
import json as mjson

from nose.plugins.skip import SkipTest

class TestRasPy(unittest.TestCase):
    """Grand mother
    """
    loglevel = logging.DEBUG

    @classmethod
    def setUpClass(self):
        logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=self.loglevel)
        self.skip = True
        if 'NOSESKIP' in os.environ:
            self.skip = eval(os.environ['NOSESKIP'])

    def skipTest(self, message):
        """Skip a test
        """
        if self.skip == True:
            raise SkipTest("%s" % (message))

    def skipTravisTest(self, message):
        """Skip a test on travis
        """
        if 'TRAVIS_OS_NAME' in os.environ:
            raise SkipTest("%s" % ("Skip on travis : %s" % message))

    def wipTest(self):
        """Work In Progress test
        """
        raise SkipTest("Work in progress")

    def touchFile(self, path):
        with open(path, 'a'):
            os.utime(path, None)
