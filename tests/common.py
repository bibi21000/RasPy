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
from pprint import pprint

import raspy.common.MDP as MDP
from raspy.servers.broker import Broker
from raspy.servers.titanic import Titanic
from raspy.common.server import Server
from raspy.common.mdcliapi import MajorDomoClient
import threading
import logging

from cStringIO import StringIO
from contextlib import contextmanager

from nose.plugins.skip import SkipTest

@contextmanager
def capture(command, *args, **kwargs):
  out, sys.stdout = sys.stdout, StringIO()
  command(*args, **kwargs)
  sys.stdout.seek(0)
  yield sys.stdout.read()
  sys.stdout = out

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

    def wipTest(self):
        """Work In Progress test
        """
        raise SkipTest("Work in progress")


class TestRasPy(TestRasPy):
    """
    Parent test class for RasPy
    """
    broker_ip = "127.0.0.1"
    broker_port = 5514
    hostname = "localhost"
    service = "worker"
    logstdout = False
    #Update this value on a slow computer (ie Raspberry Pi)
    sleep = .25

    @classmethod
    def setUpClass(self):
        logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=self.loglevel)
        self.skip = True
        if 'NOSESKIP' in os.environ:
            self.skip = eval(os.environ['NOSESKIP'])
        if not self.logstdout:
            self.output = StringIO()
            self.saved_stdout = sys.stdout
            sys.stdout = self.output

    @classmethod
    def tearDownClass(self):
        if not self.logstdout:
            self.output.close()
            sys.stdout = self.saved_stdout

class TestExecutive(TestRasPy):
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
        if not self.logstdout:
            self.output.close()
            sys.stdout = self.saved_stdout
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
    def test_000_service_mmi(self):
        self.startServer()
        request = "%s.mmi"%MDP.routing_key(self.hostname, self.service)
        reply = self.mdclient.send("mmi.service", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[0], MDP.T_OK)
        self.stopServer()

    def test_001_service_statistics(self):
        self.startServer()
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

if __name__ == '__main__':
    sys.argv.append('-v')
    unittest.main()
