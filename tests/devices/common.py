# -*- coding: utf-8 -*-

"""Unittests for the Onewire Server.
"""


__license__ = """
    This file is part of raspyfish.

    raspyfish is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    raspyfish is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with raspyfish.  If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'

import sys, os
import time
import unittest
import logging

from raspy.common.devices import *
import raspy.common.devices as devices
from raspy.common.devices.device import DReg


import json as mjson

class TestRasPy(unittest.TestCase):
    """Grand mother
    """
    loglevel = logging.DEBUG

    @classmethod
    def setUpClass(self):
        logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=self.loglevel)
        self.skip = True
        if 'NOSESKIP' in os.environ:
            print os.environ['NOSESKIP']
            self.skip = eval(os.environ['NOSESKIP'])

    def skipTest(self, message):
        """Skip a test
        """
        if self.skip == True:
            raise SkipTest("%s" % (message))

    def wipTest(self):
        """Work In Progress test
        """
        raise SkipTest("Work in progress")

class TestDevice(TestRasPy):
    key="base"

class BaseDevice(object):

    def test_000_device_register(self):
        device_name = 'test_%s_device' % self.oid
        conf = mjson.dumps(\
            { 'oid' : '%s.%s' % (self.key, self.oid), \
              'name' : device_name, \
            })
        device = DReg.new(json=conf)
        self.assertEqual(device.name, device_name)
        template = device.template
        self.assertNotEqual(template, None)
        self.assertTrue('config' in template)
        json = device.json
        self.assertNotEqual(json, None)
        self.assertTrue('oid' in json)
        self.assertTrue('name' in json)

    def test_001_device_register_bad(self):
        device_name = 'test_%s_device' % self.oid
        conf = mjson.dumps(\
            { 'oid' : '%s.%s' % (self.key, self.oid), \
            })
        self.assertRaises(KeyError, DReg.new,json=conf)
        conf = mjson.dumps(\
            { 'name' : device_name, \
            })
        self.assertRaises(KeyError, DReg.new,json=conf)

if __name__ == '__main__':
    sys.argv.append('-v')
    unittest.main()
