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

    You should have received a copy of the GNU General Public License
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
from raspy.common.mdcliapi import MajorDomoClient
from raspy.common.server import Server
from raspy.common.kvsimple import KVMsg
from raspy.common.kvcliapi import KvPublisherClient, KvSubscriberClient
import threading
import logging
import zmq
from cStringIO import StringIO
from contextlib import contextmanager

from tests.common import TestRasPy, TestExecutive

class TestProtocol(TestRasPy):
    """
    Test ZMQ protocols : Majordomo, titanic and subtree publisher
    """
    service=""

    def test_001_start_wait_and_stop(self):
        self.broker = Server(hostname=self.hostname, broker_ip=self.broker_ip, broker_port=self.broker_port)
        self.broker_thread = threading.Thread(target=self.broker.run)
        self.broker_thread.daemon = True
        self.titanic = Titanic(hostname=self.hostname, broker_ip=self.broker_ip, broker_port=self.broker_port, data_dir='.raspy_test2')
        self.titanic_thread = threading.Thread(target=self.titanic.run)
        self.titanic_thread.daemon = True
        self.broker_thread.start()
        self.titanic_thread.start()
        time.sleep(self.sleep*3)
        self.titanic.shutdown()
        self.broker.shutdown()
        time.sleep(self.sleep)
        self.titanic.destroy()
        self.broker.destroy()
        time.sleep(self.sleep)

    def test_100_kv_msg(self):
        ctx = zmq.Context()
        output = ctx.socket(zmq.DEALER)
        output.bind("ipc://kvmsg_selftest.ipc")
        input = ctx.socket(zmq.DEALER)
        input.connect("ipc://kvmsg_selftest.ipc")
        kvmap = {}
        kvmsg = KVMsg(1)
        kvmsg.key = "key"
        kvmsg.body = "body"
        kvmsg.send(output)
        kvmsg.store(kvmap)
        kvmsg2 = KVMsg.recv(input)
        self.assertTrue(kvmsg2.key == "key")
        kvmsg2.store(kvmap)
        self.assertTrue(len(kvmap) == 1)
        self.assertTrue(kvmsg.dump() is not None)

class TestMajordomo(TestExecutive):
    service=''

    def test_100_mmi_discovery_all(self):
        request = [".*"]
        reply = self.mdclient.send("mmi.discovery", request)
        self.assertNotEqual(reply, None)
        self.assertTrue("titanic.request" in reply)
        self.assertTrue("titanic.reply" in reply)
        self.assertTrue("titanic.close" in reply)
        self.assertTrue("titanic.store" in reply)
        self.assertEqual(reply[-1], MDP.T_OK)

    def test_101_mmi_discovery_many(self):
        self.server_bad = Server(hostname=self.hostname, service="badservice", broker_ip=self.broker_ip, broker_port=self.broker_port)
        self.server_bad_thread = threading.Thread(target=self.server_bad.run)
        self.server_bad_thread.daemon = True
        self.server_bad_thread.start()
        time.sleep(self.sleep)
        #Check that the bad worker is active
        request = "%s.mmi" % MDP.routing_key(self.hostname, "badservice")
        reply = self.mdclient.send("mmi.service", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[0], MDP.T_OK)
        request = [".*titanic\..*"]
        reply = self.mdclient.send("mmi.discovery", request)
        self.assertNotEqual(reply, None)
        self.assertTrue("titanic.request" in reply)
        self.assertTrue("titanic.reply" in reply)
        self.assertTrue("titanic.close" in reply)
        self.assertTrue("titanic.store" in reply)
        self.assertFalse("%s.mmi" % MDP.routing_key(self.hostname, "badservice") in reply)
        self.assertEqual(reply[-1], MDP.T_OK)
        self.server_bad.shutdown()
        time.sleep(self.sleep/4.0)
        self.server_bad.destroy()
        self.server_bad = None

    def test_102_mmi_discovery_one(self):
        request = ["titanic\.request"]
        reply = self.mdclient.send("mmi.discovery", request)
        self.assertNotEqual(reply, None)
        self.assertTrue("titanic.request" in reply)
        self.assertFalse("titanic.reply" in reply)
        self.assertFalse("titanic.close" in reply)
        self.assertFalse("titanic.store" in reply)
        self.assertEqual(reply[-1], MDP.T_OK)

class TestTitanic(TestExecutive):
    service="titanic"

    def test_100_mmi_titanic_request(self):
        request = ["titanic.request"]
        reply = self.mdclient.send("mmi.service", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_OK)

    def test_101_mmi_titanic_reply(self):
        request = ["titanic.reply"]
        reply = self.mdclient.send("mmi.service", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_OK)

    def test_102_mmi_titanic_close(self):
        request = ["titanic.close"]
        reply = self.mdclient.send("mmi.service", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_OK)

    def test_200_mmi_titanic_store(self):
        request = ["titanic.store"]
        reply = self.mdclient.send("mmi.service", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_OK)

    def test_201_titanic_store_bad(self):
        request = ["get"] + ["badservice"] + ["badsection"] + ["badkey"]
        reply = self.mdclient.send("titanic.store", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_NOTFOUND)
        request = ["delete"] + ["badservice"] + ["badsection"] + ["badkey"]
        reply = self.mdclient.send("titanic.store", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_ERROR)
        request = ["delete"] + ["badservice"] + ["badsection"]
        reply = self.mdclient.send("titanic.store", request)
        self.assertNotEqual(reply, None)
        #self.assertEqual(reply[-1], MDP.T_ERROR)
        request = ["delete"] + ["badservice"]
        reply = self.mdclient.send("titanic.store", request)
        self.assertNotEqual(reply, None)
        #self.assertEqual(reply[-1], MDP.T_ERROR)

    def test_202_titanic_store(self):
        request = ["set"] + ["testservice"] + ["testsection"] + ["testkey"] + ['testvalue']
        reply = self.mdclient.send("titanic.store", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_OK)
        request = ["get"] + ["testservice"] + ["testsection"] + ["testkey"]
        reply = self.mdclient.send("titanic.store", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_OK)
        self.assertEqual(reply[-2], 'testvalue')
        request = ["delete"] + ["testservice"] + ["testsection"] + ["testkey"]
        reply = self.mdclient.send("titanic.store", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_OK)
        request = ["get"] + ["testservice"] + ["testsection"] + ["testkey"]
        reply = self.mdclient.send("titanic.store", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_NOTFOUND)
        request = ["delete"] + ["testservice"] + ["testsection"]
        reply = self.mdclient.send("titanic.store", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_OK)
        request = ["delete"] + ["testservice"]
        reply = self.mdclient.send("titanic.store", request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_OK)

    def test_300_titanic_request(self):
        self.wipTest()
        service = "%s.request" % self.service
        request = []
        reply = self.mdclient.send(service, request)
        self.assertNotEqual(reply, None)
        self.assertEqual(reply[-1], MDP.T_OK)

class TestKV(TestExecutive):
    subtree='/test/'

    def startClient(self, subtree):
        self.publisher = KvPublisherClient(hostname=self.hostname, broker_ip=self.broker_ip, broker_port=self.broker_port)
        self.subscriber = KvSubscriberClient(hostname=self.hostname, subtree=self.subtree, broker_ip=self.broker_ip, broker_port=self.broker_port)
        self.subscriber_thread = threading.Thread(target=self.subscriber.run)
        self.subscriber_thread.daemon = True
        self.subscriber_thread.start()

    def stopClient(self):
        self.subscriber.shutdown()
        time.sleep(self.sleep/4.0)
        self.publisher.destroy()
        self.subscriber.destroy()
        self.publisher = None
        self.subscriber = None

    def test_100_kv_send(self):
        self.startClient(self.subtree)
        self.publisher.send(self.subtree, "key1", "value1")
        time.sleep(self.sleep)
        self.assertTrue("%skey1"%self.subtree in self.subscriber.kvmap)
        self.publisher.send("/testbad/", "key1", "value1")
        time.sleep(self.sleep)
        self.assertFalse("/testbad/key1" in self.subscriber.kvmap)
        self.stopClient()

    def test_101_kv_snapshot(self):
        self.startClient(self.subtree)
        self.publisher.send(self.subtree, "key1", "value1")
        time.sleep(self.sleep)
        self.assertTrue("%skey1"%self.subtree in self.subscriber.kvmap)
        self.stopClient()
        self.startClient(self.subtree)
        time.sleep(self.sleep)
        self.assertTrue("%skey1"%self.subtree in self.subscriber.kvmap)
        self.stopClient()

if __name__ == '__main__':
    sys.argv.append('-v')
    unittest.main()
