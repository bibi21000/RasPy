#!/usr/bin/python
# -*- coding: utf-8 -*-

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
__copyright__ = "Copyright © 2013-2014 Sébastien GALLET aka bibi21000"
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'

"""
Majordomo Protocol broker and key/value proxy.

Credits :
    A minimal implementation of http:#rfc.zeromq.org/spec:7 and spec:8
    Author: Min RK <benjaminrk@gmail.com>
    Based on Java example by Arkadiusz Orzechowski

"""

import logging
import time
from binascii import hexlify
import re
import threading
import zmq

import raspy.common.MDP as MDP
from raspy.common.executive import Executive
from raspy.common.kvsimple import KVMsg

# simple struct for routing information for a key-value snapshot
class Route:
    def __init__(self, socket, identity, subtree):
        self.socket = socket        # ROUTER socket to send to
        self.identity = identity    # Identity of peer who requested state
        self.subtree = subtree      # Client subtree specification

class Service(object):
    """a single Service"""
    name = None # Service name
    requests = None # List of client requests
    waiting = None # List of waiting workers

    def __init__(self, name):
        self.name = name
        self.requests = []
        self.waiting = []

class Worker(object):
    """a Worker, idle or active"""
    identity = None # hex Identity of worker
    address = None # Address to route to
    service = None # Owning service, if known
    expiry = None # expires at this point, unless heartbeat

    def __init__(self, identity, address, lifetime):
        self.identity = identity
        self.address = address
        self.expiry = time.time() + 1e-3*lifetime

class Proxy(threading.Thread):
    """The publisher

    Tree :
        - /event/
        - /scenario/
        - /device/

    from : http://zguide.zeromq.org/page:all#Working-with-Subtrees
    """

    def __init__(self, hostname='localhost', service="broker", broker_ip='*', broker_port=5514, speed=1.0):
        """Initialize the proxy
        """
        threading.Thread.__init__(self)
        MDP.logger.debug("PROXY - Starting ...")
        self.ctx = zmq.Context()
        self.snapshot = self.ctx.socket(zmq.ROUTER)
        self.snapshot.bind("tcp://%s:%s" % (broker_ip, broker_port+1))
        self.publisher = self.ctx.socket(zmq.PUB)
        self.publisher.bind("tcp://%s:%s" % (broker_ip, broker_port+2))
        self.collector = self.ctx.socket(zmq.PULL)
        self.collector.bind("tcp://%s:%s" % (broker_ip, broker_port+3))
        self.sequence = 0
        self.kvmap = {}
        self.poller = zmq.Poller()
        self.poller.register(self.collector, zmq.POLLIN)
        self.poller.register(self.snapshot, zmq.POLLIN)
        self._stopevent = threading.Event()
        self.speed = speed
        MDP.logger.info("PROXY - Snapshot server is active at tcp://%s:%s", broker_ip, broker_port+1)
        MDP.logger.info("PROXY - Publisher server is active at tcp://%s:%s", broker_ip, broker_port+2)
        MDP.logger.info("PROXY - Collector server is active at tcp://%s:%s", broker_ip, broker_port+3)

    def run(self):
        """Run the proxy
        """
        while not self._stopevent.isSet():
            try:
                items = dict(self.poller.poll(self.speed*1000.0))
            except KeyboardInterrupt: # pragma: no cover
                break                 # pragma: no cover
            except zmq.ZMQError as exc:
                if not self._stopevent.isSet():
                    raise exc
                else:
                    items = []
            # Apply state update sent from client
            if self.collector in items:
                kvmsg = KVMsg.recv(self.collector)
                self.sequence += 1
                kvmsg.sequence = self.sequence
                kvmsg.send(self.publisher)
                kvmsg.store(self.kvmap)
                MDP.logger.debug("PROXY - Server publishing update for sequence %5d", self.sequence)
            # Execute state snapshot request
            if self.snapshot in items:
                msg = self.snapshot.recv_multipart()
                identity, request, subtree = msg
                if request == "ICANHAZ?":
                    pass
                else:
                    MDP.logger.error("PROXY - Server recevie bad request. Aborting.")
                    break
                # Send state snapshot to client
                route = Route(self.snapshot, identity, subtree)
                # For each entry in kvmap, send kvmsg to client
                for k, v in self.kvmap.items():
                    self.send_single(k, v, route)
                # Now send END message with sequence number
                MDP.logger.debug("PROXY - Sending state shapshot %5d", self.sequence)
                self.snapshot.send(identity, zmq.SNDMORE)
                kvmsg = KVMsg(self.sequence)
                kvmsg.key = "KTHXBAI"
                kvmsg.body = subtree
                kvmsg.send(self.snapshot)
        #Destroy context
        self.ctx.destroy(0)

    def send_single(self, key, kvmsg, route):
        """Send one state snapshot key-value pair to a socket"""
        # check front of key against subscription subtree:
        if kvmsg.key.startswith(route.subtree):
            # Send identity of recipient first
            route.socket.send(route.identity, zmq.SNDMORE)
            kvmsg.send(route.socket)

    def shutdown(self):
        """Shutdown the proxy.
        """
        self._stopevent.set()

class Broker(Executive):
    """Majordomo Protocol broker and key/value proxy.

    **Discovery process**

    Here is the way for a client to discover all devices on network

    .. seqdiag::

        seqdiag mmi_discovery {
          client;broker;worker1;worker2;
          client  -> broker [label = "[mmi.discovery][.*\.devices\..*]"];
          client  <-- broker [label = "[service1][service2][...][200]"];
          client  -> worker1 [label = "[service1][list_keys]"];
          client  <-- worker1 [label = "[device1][device2][...][200]"];
          client  -> worker2 [label = "[service2][list_keys]"];
          client  <-- worker2 [label = "[device1][device2][...][200]"];
        }

    You can do the same for crons and scenarios
    """

    # We'd normally pull these from config data
    INTERNAL_SERVICE_PREFIX = "mmi."
    HEARTBEAT_LIVENESS = 5 # 3-5 is reasonable
    HEARTBEAT_INTERVAL = 3500 # msecs
    HEARTBEAT_EXPIRY = HEARTBEAT_INTERVAL * HEARTBEAT_LIVENESS

    ctx = None # Our context
    socket = None # Socket for clients & workers
    poller = None # our Poller

    heartbeat_at = None# When to send HEARTBEAT
    services = None # known services
    workers = None # known workers
    waiting = None # idle workers

    def __init__(self, hostname='localhost', service="broker", broker_ip='127.0.0.1', broker_port=15514):
        """Initialize the Broker
        """
        MDP.logger.debug("BROKER - Starting ...")
        Executive.__init__(self, hostname, service, broker_ip, broker_port)
        self.services = {}
        self.workers = {}
        self.waiting = []
        self.heartbeat_at = time.time() + 1e-3*self.HEARTBEAT_INTERVAL
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.ROUTER)
        self.socket.linger = 0
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.socket.bind("tcp://%s:%s" % (self.broker_ip, self.broker_port))
        self.proxy_thread = Proxy(hostname=hostname, service=service, broker_ip=broker_ip, broker_port=broker_port, speed=self.speed)
        self.proxy_thread.daemon = True
        MDP.logger.info("BROKER - MDP broker is active at tcp://%s:%s", self.broker_ip, self.broker_port)

    def run(self):
        """Main broker work happens here"""
        self.proxy_thread.start()
        while not self._stopevent.isSet():
            try:
                items = self.poller.poll(self.HEARTBEAT_INTERVAL)
            except KeyboardInterrupt: # pragma: no cover
                break                 # pragma: no cover
            except zmq.ZMQError as exc:
                if not self._stopevent.isSet():
                    raise exc
                else:
                    items = []
            if items:
                try:
                    msg = self.socket.recv_multipart()
                    MDP.logger.debug("BROKER - Received message: %s", msg)
                    sender = msg.pop(0)
                    empty = msg.pop(0)
                    assert empty == ''
                    header = msg.pop(0)
                    if MDP.C_CLIENT == header:
                        self.process_client(sender, msg)
                    elif MDP.W_WORKER == header:
                        self.process_worker(sender, msg)
                    else:
                        MDP.logger.error("BROKER - Invalid message: %s", msg)
                except zmq.ZMQError as exc:
                    if not self._stopevent.isSet():
                        raise exc
            self.purge_workers()
            self.send_heartbeats()

    def shutdown(self):
        """Shutdown the broker.
        """
        self._stopevent.set()
        self.proxy_thread.shutdown()
        self.proxy_thread.join()

    def destroy(self):
        """Disconnect all workers, destroy context."""
        self.proxy_thread = None
        for key in self.workers.keys():
            try:
                self.delete_worker(self.workers[key], True)
            except ValueError:
                pass
            except RuntimeError:
                pass
        self.ctx.destroy(0)

    def process_client(self, sender, msg):
        """Process a request coming from a client."""
        #Removed because of mmi.discovery message, ...
        assert len(msg) >= 2 # Service name + body
        #assert len(msg) >= 1 # Service name. Body can be null. But it fails ...
        service = msg.pop(0)
        # Set reply return address to client sender
        msg = [sender, ''] + msg
        if service.startswith(self.INTERNAL_SERVICE_PREFIX):
            self.service_internal(service, msg)
        else:
            self.dispatch(self.require_service(service), msg)

    def process_worker(self, sender, msg):
        """Process message sent to us by a worker."""
        assert len(msg) >= 1 # At least, command
        command = msg.pop(0)
        worker_ready = hexlify(sender) in self.workers
        worker = self.require_worker(sender)
        if MDP.W_READY == command:
            assert len(msg) >= 1 # At least, a service name
            service = msg.pop(0)
            # Not first command in session or Reserved service name
            if worker_ready or service.startswith(self.INTERNAL_SERVICE_PREFIX):
                self.delete_worker(worker, True)
            else:
                MDP.logger.debug("BROKER - Attach worker for service : %s", service)
                # Attach worker to service and mark as idle
                worker.service = self.require_service(service)
                self.worker_waiting(worker)
        elif MDP.W_REPLY == command:
            if worker_ready == True:
                # Remove & save client return envelope and insert the
                # protocol header and service name, then rewrap envelope.
                client = msg.pop(0)
                empty = msg.pop(0) # ?
                msg = [client, '', MDP.C_CLIENT, worker.service.name] + msg
                self.socket.send_multipart(msg)
                self.worker_waiting(worker)
            else:
                self.delete_worker(worker, True)
        elif MDP.W_HEARTBEAT == command:
            if worker_ready == True:
                worker.expiry = time.time() + 1e-3*self.HEARTBEAT_EXPIRY
            else:
                self.delete_worker(worker, True)
        elif MDP.W_DISCONNECT == command:
            self.delete_worker(worker, False)
        else:
            MDP.logger.error("BROKER - Invalid message: %s", msg)

    def delete_worker(self, worker, disconnect):
        """Deletes worker from all data structures, and deletes worker."""
        assert worker is not None
        if disconnect == True:
            self.send_to_worker(worker, MDP.W_DISCONNECT, None, None)
        if worker.service is not None:
            worker.service.waiting.remove(worker)
        self.workers.pop(worker.identity)

    def require_worker(self, address):
        """Finds the worker (creates if necessary)."""
        assert address is not None
        identity = hexlify(address)
        worker = self.workers.get(identity)
        if worker is None:
            worker = Worker(identity, address, self.HEARTBEAT_EXPIRY)
            self.workers[identity] = worker
            MDP.logger.info("BROKER - Registering new worker: %s", identity)
        return worker

    def require_service(self, name):
        """Locates the service (creates if necessary)."""
        assert name is not None
        service = self.services.get(name)
        if service is None:
            service = Service(name)
            self.services[name] = service
        return service

    def service_internal(self, service, msg):
        """Handle internal service according to 8/MMI specification"""
        returncode = "501"
        if "mmi.service" == service:
            name = msg[-1]
            returncode = "200" if name in self.services else "404"
        elif "mmi.discovery" == service:
            name = msg[-1]
            try:
                srvs = [k for k in self.services.keys() if len(k) > 0 and re.search(name, k)] + msg[-1:]
                msg = msg[:-1] + srvs
                MDP.logger.debug("BROKER - Discovery send : %s", srvs)
                returncode = "200"
            except re.error:
                pass
        msg[-1] = returncode
        # insert the protocol header and service name after the routing envelope ([client, ''])
        msg = msg[:2] + [MDP.C_CLIENT, service] + msg[2:]
        self.socket.send_multipart(msg)

    def send_heartbeats(self):
        """Send heartbeats to idle workers if it's time"""
        if time.time() > self.heartbeat_at:
            for worker in self.waiting:
                self.send_to_worker(worker, MDP.W_HEARTBEAT, None, None)
            self.heartbeat_at = time.time() + 1e-3*self.HEARTBEAT_INTERVAL

    def purge_workers(self):
        """Look for & kill expired workers.

        Workers are oldest to most recent, so we stop at the first alive worker.
        """
        while self.waiting:
            w = self.waiting[0]
            if w.expiry < time.time():
                MDP.logger.info("BROKER - Deleting expired worker: %s", w.identity)
                self.delete_worker(w, False)
                self.waiting.pop(0)
            else:
                break

    def worker_waiting(self, worker):
        """This worker is now waiting for work."""
        # Queue to broker and service waiting lists
        self.waiting.append(worker)
        worker.service.waiting.append(worker)
        worker.expiry = time.time() + 1e-3*self.HEARTBEAT_EXPIRY
        self.dispatch(worker.service, None)

    def dispatch(self, service, msg):
        """Dispatch requests to waiting workers as possible"""
        assert service is not None
        if msg is not None:# Queue message if any
            service.requests.append(msg)
        self.purge_workers()
        while service.waiting and service.requests:
            msg = service.requests.pop(0)
            worker = service.waiting.pop(0)
            self.waiting.remove(worker)
            self.send_to_worker(worker, MDP.W_REQUEST, None, msg)

    def send_to_worker(self, worker, command, option, msg=None):
        """Send message to worker.

     . If message is provided, sends that message.
        """
        if self._stopevent.isSet():
            return
        if msg is None:
            msg = []
        elif not isinstance(msg, list):
            msg = [msg]
        # Stack routing and protocol envelopes to start of message
        # and routing envelope
        if option is not None:
            msg = [option] + msg
        msg = [worker.address, '', MDP.W_WORKER, command] + msg
        MDP.logger.debug("BROKER - Sending %r to worker : %s", command, msg)
        self.socket.send_multipart(msg)

if __name__ == '__main__': # pragma: no cover
    mybroker = Broker()    # pragma: no cover
    mybroker.run()         # pragma: no cover
