#!/usr/bin/python
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

    You should have received a copy of the NU General Public License
    along with RasPy. If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'

import sys
import time
import unittest
from pprint import pprint

from raspy.common.devices import *
import raspy.common.devices as devices
from raspy.common.devices.device import DReg

from common import TestDevice, BaseDevice
import json as mjson

class BaseSensor(object):

    def test_100_device_register(self):
        device_name = 'test_%s_device' % self.oid
        conf = mjson.dumps(\
            { 'oid' : '%s.%s' % (self.key, self.oid), \
              'name' : device_name, \
              'unit' : 'some_unit', \
            })
        device = DReg.new(json=conf)
        self.assertEqual(device.config['unit'], 'some_unit')

class TestWind(TestDevice, BaseDevice, BaseSensor):
    oid = "wind"
    key="sensor"

    def test_200_device_register(self):
        device_name = 'test_%s_device' % self.oid
        conf = mjson.dumps(\
            { 'oid' : '%s.%s' % (self.key, self.oid), \
              'name' : device_name, \
            })
        device = DReg.new(json=conf)
        self.assertIsInstance(device, devices.sensor.SensorWind)

class TestTemperature(TestDevice, BaseDevice, BaseSensor):
    oid = "temperature"
    key="sensor"

    def test_200_device_register(self):
        device_name = 'test_%s_device' % self.oid
        conf = mjson.dumps(\
            { 'oid' : '%s.%s' % (self.key, self.oid), \
              'name' : device_name, \
            })
        device = DReg.new(json=conf)
        self.assertIsInstance(device, devices.sensor.SensorTemperature)

if __name__ == '__main__':
    sys.argv.append('-v')
    unittest.main()
