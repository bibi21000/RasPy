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

CommandTypes = ['List', 'Bool', "Byte", "Int", "Real", "Str", "Sch", "Dict"]

class Command(object):
    """A command for a device. Use the same "spirit" as ZWave command classes
    """
    readonly = False
    """Is this command readonly ie a sensor
    """
    writeonly = False
    """Is this command writeonly ie a change dimmer command
    """
    type = CommandTypes[0]
    """The type of the value
    Will be used to represent the value ie in a form, in a graph, ...
    """
    value = None
    """The value
    """
    info = "info"
    """Some information about the command
    Will be used to represent the value ie in a form, in a graph, ...
    """
    callback = None
    """The callback method associated with this command
    """

    _fields = ['info', 'readonly', 'writeonly', 'type', 'value']
    """What to jsonify
    """
    def __init__(self, **kwargs):
        """Initialize the Command
        """
        if 'json ' in kwargs:
            self.from_json(kwargs['json'])
        for field in self._fields:
            if field in kwargs:
                setattr(self, field, kwargs[field])
        if 'callback ' in kwargs:
            self.callback = kwargs["callback"]

#    def __init__(self, readonly=False, writeonly=False, callback=None):
#        """Initialize the Command
#        """
#        if json is not None:
#            self.from_json(json)

    def from_json(self, json=None):
        """Create the command from JSON
        """
        if json is not None:
            config = mjson.loads(json)
            for field in self._fields:
                if field in config:
                    setattr(self, field, config[field])
            return True
        return False

    def to_json(self):
        """Copy command to JSON
        """
        config = {}
        for field in self._fields:
            config[field] = getattr(self, field)
        return mjson.dumps(config)

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

    What can we do with a device : a command (same "spirit" as zwave's command classes

        - configure it
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
    Naming convention for devices / subdevices : categorie.device-subdevice (ie media.tv-volume, ... )

    """

    oid = "base"
    """The Object Identifier
    It should be given by the core team as it can break other devices.
    Need to define a naming convention : sensor, sensor.temperature, media.camera, ...
    """
    _base_template = { 'config' : {}, 'commands' : {} }

    templates = {}
    """The templates dictionnary
    Every device must add an entry for its config
    Will be used to check the device
    """

    config = {'name' : None}
    """The device's configuration
    """

    subdevices = None
    """The subdevices of this device
    """

    commands = {}
    """The commands available on the device
    """

    poll = -1
    """The poll value of this device : -1 not pollable, 0 : not poll and other = poll delay in seconds
    """

    log = False
    """Should we log this value (in the RasPy Logger)
    """

    def __init__(self, json=None):
        """Initialize the BaseDevice
        """
        self.templates[self.oid] = self._base_template
        if json is not None:
            self.config = mjson.loads(json)
            self._name = self.config['name']
        else:
            config = {'name' : None}
            self._name = None
        self.commands['commands'] = Command(readonly=True, writeonly=False, type='List', info="All commands available on this device", callback=self.cmd_commands)
        self.commands['config'] = Command(readonly=False, writeonly=False, type='Dict', info="Configure device", callback=self.cmd_config)
        self.commands['poll'] = Command(readonly=False, writeonly=False, type='Int', info="Define polling for this device", callback=self.cmd_poll)
        self.commands['log'] = Command(readonly=False, writeonly=False, type='Bool', info="Define logging for this device", callback=self.cmd_log)
        self.commands['reset'] = Command(readonly=False, writeonly=True, type='Bool', info="Rsett the device to factory settings", callback=self.cmd_reset)

    def cmd_commands(self, value=None):
        """Command fof retrieving all commands supported by this device

        :parameter value: the value. If value is None this command send the current config. Otherwise it will set it to calue
        """
        res = None
        for key in self.commands.iterkeys():
            if res == None:
                res = key
            else:
                res = res + '|' + key
        return res

    def cmd_config(self, value=None):
        """Command for configuring device
        Must be overloaded and called by the subclass

        :parameter value: the value. If value is None this command send the current config. Otherwise it will set it to calue
        """
        if value is None:
            return self.config
        try:
            self.name = value['name']
            return True
        except KeyError:
            return None
        return None

    def cmd_log(self, value=None):
        """Command for configuring logging of the device
        """
        if value is None:
            return self.log
        self.log = value
        return True

    def cmd_poll(self, value=None):
        """Command for configuring polling of the device
        """
        if value is None:
            return self.poll
        if self.poll != -1 and value != -1:
            self.poll = value
            return True
        return None

    def do_poll(self):
        """Grab the value and return it
        """
        return None

    def cmd_reset(self, value=None):
        """Command for resetting device
        Must be overloaded (and called) by the subclass
        """
        if value == True :
            self.poll = -1
            return True
        return None

    def exec_cmd(self, oid, command, value=None):
        """Execute a command

        :parameter device: the oid device
        :parameter command: the cid device
        :parameter value: the value
        :returns: a value if the command succeed. None if it fails
        """
        if command in self.commands :
            return self.commands[command](value)
        subdev = device.split(oid, "-", 1)
        if len(subdev) > 0 :
            if self.subdevices is not None and subdev in self.subdevices:
                if command in self.subdevices[subdev].commands and self.subdevices[subdev].commands[command] is not None:
                    return self.subdevices[subdev].commands[command](value)
        return None

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
        assert oid in self._register
        logging.debug("DReg - Create new device for oid %s" % oid)
        #That works ... but I don't know why !!!
        device = self._register[oid](**kwargs)
        return device

DReg = DeviceRegister()
