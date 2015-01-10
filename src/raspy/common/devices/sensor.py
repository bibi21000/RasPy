# -*- coding: utf-8 -*-

"""Sensors devices
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

import sys, os
import time
from raspy.common.devices.device import BaseDevice, DReg
import logging
import json as mjson

class SensorDevice(BaseDevice):
    """The sensor device object
    """

    oid = "sensor"
    """The Object Identifier
    It should be given by the core team as it can break other devices.
    Need to define a naming convention : sensor, sensor.temperature, media.camera, ...
    """

    def __init__(self, **kwargs):
        """Initialize the Device
        """
        BaseDevice.__init__(self, **kwargs)
        self.templates[self.oid] = self._base_template

    def check(self, json=None):
        """Check that the JSON is a valid device
        """
        return True

class SensorWind(SensorDevice):
    """The wind sensor device object
    """

    oid = "sensor.wind"
    """The Object Identifier
    It should be given by the core team as it can break other devices.
    Need to define a naming convention : sensor, sensor.temperature, media.camera, ...
    """

    def __init__(self, **kwargs):
        """Initialize the Device
        """
        SensorDevice.__init__(self, **kwargs)
        self.templates[self.oid] = self._base_template

    def new(self, **kwargs):
        """Create a new device and return it
        """
        return SensorWind(**kwargs)

class SensorTemperature(SensorDevice):
    """The temperature sensor device object
    """

    oid = "sensor.temperature"
    """The Object Identifier
    It should be given by the core team as it can break other devices.
    Need to define a naming convention : sensor, sensor.temperature, media.camera, ...
    """

    def __init__(self, **kwargs):
        """Initialize the Device
        """
        SensorDevice.__init__(self, **kwargs)
        self.templates[self.oid] = self._base_template

    def new(self, **kwargs):
        """Create a new device and return it
        """
        return SensorTemperature(**kwargs)

Temperature = SensorTemperature()
DReg.register(Temperature)
Wind = SensorWind()
DReg.register(Wind)
