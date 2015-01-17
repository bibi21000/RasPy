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

import raspy.common.MDP as MDP
from raspy.servers.broker import Broker
from raspy.servers.titanic import Titanic
from raspy.servers.onewire import OneWire
from raspy.common.mdcliapi import MajorDomoClient
import threading
import logging

from tests.raspy.common import TestServer, ServerBase

class TestOneWire(TestServer, ServerBase):
    service="onewire"

    def startServer(self):
        self.server = OneWire(hostname=self.hostname, broker_ip=self.broker_ip, broker_port=self.broker_port)
        self.server_thread = threading.Thread(target=self.server.run)
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(self.sleep/3.0)

    def test_100_service_devices(self):
        self.startServer()
        request = "%s.devices"%MDP.routing_key(self.hostname, self.service)
        reply = self.mdclient.send("mmi.service", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[0], MDP.T_OK)
        self.stopServer()

    def test_101_devices_list(self):
        self.skipTest("Only on Rapsberry Pi")
        self.startServer()
        request = "list_keys"
        reply = self.mdclient.send("%s.devices"%MDP.routing_key(self.hostname, self.service), request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_OK)
        self.stopServer()

    def test_102_devices_list_bad(self):
        self.server = OneWire(hostname=self.hostname, service="onewire2", broker_ip=self.broker_ip, broker_port=self.broker_port, devices_dir='/tmp/badir')
        self.server_thread = threading.Thread(target=self.server.run)
        self.server_thread.daemon = True
        self.server_thread.start()
        request = "list_keys"
        reply = self.mdclient.send("%s.devices"%MDP.routing_key(self.hostname, "onewire2"), request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_ERROR)
        self.server.shutdown()
        time.sleep(self.sleep/3.0)
        self.server.destroy()
        time.sleep(self.sleep)

    def test_103_devices_not_implemented_action(self):
        self.startServer()
        request = "notimplemmmmment"
        reply = self.mdclient.send("%s.devices"%MDP.routing_key(self.hostname, self.service), request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_NOTIMPLEMENTED)
        self.stopServer()

if __name__ == '__main__':
    sys.argv.append('-v')
    unittest.main()
