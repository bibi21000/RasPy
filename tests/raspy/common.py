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

import sys, os
import time
import unittest
import threading
import logging
import json as mjson
import shutil
from nose.plugins.skip import SkipTest

import raspy.common.MDP as MDP
from raspy.servers.broker import Broker
from raspy.servers.titanic import Titanic
from raspy.common.server import Server
from raspy.common.mdcliapi import MajorDomoClient
from raspy.common.devices import *
import raspy.common.devices as devices
from raspy.common.devices.device import DReg, BaseDevice

from tests.common import SLEEP
from tests.common import TestRasPy

class TestRasPyIP(TestRasPy):
    """
    Parent test class for network tests
    """
    broker_ip = "127.0.0.1"
    broker_port = 5514
    hostname = "localhost"
    service = "worker"
    sleep = SLEEP

class TestExecutive(TestRasPyIP):
    """
    Parent test class for workers
    """
    broker = None
    titanic = None

    def setUp(self):
        self.broker = Broker(hostname=self.hostname, broker_ip=self.broker_ip, broker_port=self.broker_port)
        self.broker_thread = threading.Thread(target=self.broker.run)
        self.broker_thread.daemon = True
        self.titanic = Titanic(hostname=self.hostname, broker_ip=self.broker_ip, broker_port=self.broker_port, data_dir='.raspy_test')
        self.titanic_thread = threading.Thread(target=self.titanic.run)
        self.titanic_thread.daemon = True
        self.broker_thread.start()
        self.titanic_thread.start()
        time.sleep(self.sleep/4.0)
        self.mdclient = MajorDomoClient("tcp://%s:%s"%(self.broker_ip,self.broker_port))

    def tearDown(self):
        if self.titanic:
            self.titanic.shutdown()
        if self.broker:
            self.broker.shutdown()
        time.sleep(self.sleep/4.0)
        if self.mdclient:
            self.mdclient.destroy()
            self.mdclient = None
        if self.titanic:
            self.titanic.destroy()
            self.titanic = None
        if self.broker:
            self.broker.destroy()
            self.broker = None
        try:
            shutil.rmtree('.raspy_test')
        except:
            pass

class TestServer(TestExecutive):
    """
    Parent test class for servers
    """
    def startServer(self):
        self.server = Server(hostname=self.hostname, service=self.service, broker_ip=self.broker_ip, broker_port=self.broker_port)
        self.server_thread = threading.Thread(target=self.server.run)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stopServer(self):
        self.server.shutdown()
        time.sleep(self.sleep/4.0)
        self.server.destroy()
        self.server = None

class ServerBase():
    """
    Common tests class for servers
    """
    def test_000_service_mmi_statistics(self):
        self.startServer()
        request = "%s.mmi"%MDP.routing_key(self.hostname, self.service)
        reply = self.mdclient.send("mmi.service", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[0], MDP.T_OK)
        request = "%s.statistics"%MDP.routing_key(self.hostname, self.service)
        reply = self.mdclient.send("mmi.service", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[0], MDP.T_OK)
        self.stopServer()

    def test_010_mmi_status(self):
        self.startServer()
        request = "status"
        reply = self.mdclient.send("%s.mmi"%MDP.routing_key(self.hostname, self.service), request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[0], MDP.T_OK)
        self.server._active_workers[0].status = False
        reply = self.mdclient.send("%s.mmi"%MDP.routing_key(self.hostname, self.service), request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[0], MDP.T_ERROR)
        self.stopServer()

    def test_049_mmi_not_implemented_action(self):
        self.startServer()
        request = "notimplemmmmment"
        reply = self.mdclient.send("%s.mmi"%MDP.routing_key(self.hostname, self.service), request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_NOTIMPLEMENTED)
        self.stopServer()

    def test_050_statistics_all(self):
        self.startServer()
        request = "all"
        reply = self.mdclient.send("%s.statistics"%MDP.routing_key(self.hostname, self.service), request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[0], MDP.T_OK)
        self.stopServer()

    def test_051_statistics_not_implemented_action(self):
        self.startServer()
        request = "notimplemmmmment"
        reply = self.mdclient.send("%s.statistics"%MDP.routing_key(self.hostname, self.service), request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_NOTIMPLEMENTED)
        self.stopServer()

class TestDevice(TestRasPy):
    key="base"

class DeviceBase(object):

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

    def test_010_cmd_commands(self):
        device_name = 'test_%s_device' % self.oid
        device = BaseDevice()
        cmds = device.cmd_commands().split('|')
        self.assertTrue('config' in cmds)
        self.assertTrue('poll' in cmds)
        self.assertTrue('reset' in cmds)

    def test_020_cmd_config(self):
        device_name = 'test_%s_device' % self.oid
        device = BaseDevice()
        self.assertNotEqual(device, None)
        conf = device.cmd_config()
        self.assertTrue('name' in conf)
        self.assertTrue(device.cmd_config(value={'name':device_name}))
        conf = device.cmd_config()
        self.assertTrue('name' in conf)
        self.assertEqual(conf['name'], device_name)

    def test_021_cmd_bad_config(self):
        device_name = 'test_%s_device' % self.oid
        device = BaseDevice()
        self.assertNotEqual(device, None)
        self.assertTrue(device.cmd_config(value={}) is None)

    def test_030_cmd_poll(self):
        device_name = 'test_%s_device' % self.oid
        device = BaseDevice()
        self.assertNotEqual(device, None)
        device.poll = -1
        res = device.cmd_poll()
        self.assertEqual(res, -1)
        res = device.cmd_poll(5)
        self.assertTrue(res is None)
        self.assertEqual(device.poll, -1)
        device.poll = 0
        res = device.cmd_poll(5)
        self.assertEqual(res, True)
        res = device.cmd_poll()
        self.assertEqual(res, 5)

    def test_040_cmd_log(self):
        device_name = 'test_%s_device' % self.oid
        device = BaseDevice()
        self.assertNotEqual(device, None)
        device.log = False
        res = device.cmd_log()
        self.assertEqual(res, False)
        self.assertTrue(device.cmd_log(True))
        res = device.cmd_log()
        self.assertEqual(res, True)
