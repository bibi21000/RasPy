# -*- coding: utf-8 -*-

"""Devices.

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
import json as mjson
import logging

class BaseDevice(object):
    """The base device object

    What is a device :

        - a temperature sensor
        - a wind sensor
        - a camera
        - the clock RTC
        - a dimmer
        - a TV
        - ...

    What can we do with a device :

        - get value of a sensor
        - dim a dimmer
        - take a photo with camera
        - ...

    We shoud do auto-mapping :

        - python object <-> json
        - python object <-> html

    We whould manage complex devices, ie a TV : it groups a channel selector (+, -, and direct access to a channel), a volume selector, ...
    In an ideal world we should not be obliged to create each sub-devices.

    Naming convention of devices on the network : (MDP.routing_key(hostname, service)).{device_name}[.subdevice]
    """

    oid = "base"
    """The Object Identifier
    It should be given by the core team as it can break other devices.
    Need to define a naming convention : sensor, sensor.temperature, media.camera, ...
    """
    _base_template = { 'config' : {}, 'methods' : {} }

    templates = {}
    """The templates dictionnary
    Every device must add an entry for its config
    Will be used to check the device
    """

    def __init__(self, json=None):
        """Initialize the BaseDevice
        """
        self.templates[self.oid] = self._base_template
        if json is not None:
            self.config = mjson.loads(json)
            self._name = self.config['name']
        else:
            self.config = None
            self._name = None

    def new(self, json=None):
        """Create a new device and return it
        """
        return None

    def check(self, json=None):
        """Check that the JSON is a valid device
        """
        return True

    @property
    def json(self):
        """Check that the JSON is a valid device
        """
        return mjson.dumps(self.config)

    @property
    def name(self):
        """The name of the device
        Must be unique for the instance server.
        """
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self.config['name'] = self._name

    def fullname(self, prefix):
        """The fullname of the device
        """
        return "%s.%s" % (prefix, self._name)

    @property
    def template(self):
        """The template of the device
        """
        template = None
        for tmpl in sorted(self.templates, key=str.lower):
            if template is None:
                template = self._base_template
            for item in self._base_template:
                template[item].update(self.templates[tmpl][item])
        return template

class DeviceRegister(object):
    """The device register

    All devices must register to this register (in main module)
    """
    def __init__(self):
        """Initialize the Device Register
        """
        self._register = {}
        """The register"""

    def check(self, json=None):
        """Check that the JSON is a valid device
        """
        return True

    def register(self, device_type):
        """Register a device_type under key
        """
        assert device_type is not None
        assert device_type.oid not in self._register
        logging.debug("DReg - Registering oid %s" % device_type.oid)
        self._register[device_type.oid] = device_type.new

    def new(self, **kwargs):
        """Create a new device and return it
        """
        conf = mjson.loads(kwargs['json'])
        oid = conf['oid']
        print oid
        print self._register
        assert oid in self._register
        logging.debug("DReg - Create new device for oid %s" % oid)
        #That works ... but I don't know why !!!
        device = self._register[oid](**kwargs)
        return device

DReg = DeviceRegister()
