#!/usr/bin/python
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

    You should have received a copy of the NU General Public License
    along with raspyfish.  If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'

import sys, os
sys.path.insert(0, os.path.abspath('../'))
import time
import unittest
from pprint import pprint

from raspy.common.devices import *
import raspy.common.devices as devices
from raspy.common.devices.device import DReg
from common import TestDevice, BaseDevice
import json as mjson

class BaseMedia(object):
    pass

class TestCamera(TestDevice, BaseDevice, BaseMedia):
    key="media"
    oid = "camera"

    def test_200_device_register(self):
        device_name = 'test_%s_device' % self.oid
        conf = mjson.dumps(\
            { 'oid' : '%s.%s' % (self.key, self.oid), \
              'name' : device_name, \
            })
        device = DReg.new(json=conf)
        self.assertIsInstance(device, devices.media.MediaCamera)


class TestTV(TestDevice, BaseDevice, BaseMedia):
    key="media"
    oid = "tv"
    def test_200_device_register(self):
        device_name = 'test_%s_device' % self.oid
        conf = mjson.dumps(\
            { 'oid' : '%s.%s' % (self.key, self.oid), \
              'name' : device_name, \
            })
        device = DReg.new(json=conf)
        self.assertIsInstance(device, devices.media.MediaTV)

if __name__ == '__main__':
    sys.argv.append('-v')
    unittest.main()
