# -*- coding: utf-8 -*-

"""

kvsimple - simple key-value message class for example applications

Author: Min RK <benjaminrk@gmail.com>

From : http://zguide.zeromq.org/py:kvsimple
"""

import random
import time
import threading
import raspy.common.MDP as MDP
import zmq
from raspy.common.kvsimple import KVMsg

SUBTREE = "/client/"

class KvPublisherClient(object):
    """KeyValue Protocol Client API, Python version.

      Implements the client defined at http://zguide.zeromq.org/page:all#Working-with-Subtrees

      From https://raw.githubusercontent.com/imatix/zguide/master/examples/Python/clonecli4.py
    """

    def __init__(self, hostname='localhost', broker_ip='127.0.0.1', broker_port=5514):
        """Insitalize the client
        """
        self.ctx = zmq.Context()
        self.poller = zmq.Poller()
        self.publisher = self.ctx.socket(zmq.PUSH)
        self.publisher.linger = 0
        self.publisher.connect("tcp://%s:%s" % (broker_ip, broker_port+3))
        self.kvmap = {}
        self.sequence = 0

    def send(self, subtree='subtree', key='key', body='body'):
        """Send the update
        """
        if subtree[0] != "/":
            subtree = "/" + subtree
        if subtree[len(subtree)-1] != "/":
            subtree = subtree + "/"
        kvmsg = KVMsg(0)
        kvmsg.key = subtree + "%s" % key
        kvmsg.body = "%s" % body
        MDP.logger.debug("PROXY - Client publish update under %s for %s : %s", subtree, kvmsg.key, kvmsg.body)
        kvmsg.send(self.publisher)
        kvmsg.store(self.kvmap)

    def destroy(self):
        """ Destroy object
        """
        self.ctx.destroy(0)

class KvSubscriberClient(object):
    """KeyValue Protocol Client API, Python version.

      Implements the client defined at http://zguide.zeromq.org/page:all#Working-with-Subtrees
      From https://raw.githubusercontent.com/imatix/zguide/master/examples/Python/clonecli4.py

    """

    def __init__(self, hostname='localhost', subtree="subtree", broker_ip='127.0.0.1', broker_port=5514, speed=1.0):
        """Insitalize the client
        """
        self.ctx = zmq.Context()
        self.snapshot = self.ctx.socket(zmq.DEALER)
        self.snapshot.linger = 0
        self.snapshot.connect("tcp://%s:%s" % (broker_ip, broker_port+1))
        self.subscriber = self.ctx.socket(zmq.SUB)
        self.subscriber.linger = 0
        self.subtree = subtree
        self.subscriber.setsockopt(zmq.SUBSCRIBE, self.subtree)
        self.subscriber.connect("tcp://%s:%s" % (broker_ip, broker_port+2))
        self.kvmap = {}
        self.speed = speed
        self._stopevent = threading.Event()
        self.snapshot.send_multipart(["ICANHAZ?", self.subtree])
        while not self._stopevent.isSet():
            kvmsg = KVMsg.recv(self.snapshot)
            if kvmsg.key == "KTHXBAI":
                self.sequence = kvmsg.sequence
                MDP.logger.debug("PROXY - Client received snaphot for subtree %s with sequence %s", self.subtree, self.sequence)
                break          # Done
            kvmsg.store(self.kvmap)

    def run(self):
        """Run the poller
        """
        self.poller = zmq.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)
        while not self._stopevent.isSet():
            try:
                items = dict(self.poller.poll(self.speed*1000.0))
            except zmq.ZMQError as exc:
                if not self._stopevent.isSet():
                    raise exc
                else:
                    items = {}
            MDP.logger.debug("PROXY - Subscriber received items %s" % items)
            MDP.logger.debug("PROXY - kvmap %s" % self.kvmap)
            if self.subscriber in items:
                #MDP.logger.debug("PROXY - Subscriber received data")
                kvmsg = KVMsg.recv(self.subscriber)
                if kvmsg.sequence > self.sequence:
                    self.sequence = kvmsg.sequence
                    kvmsg.store(self.kvmap)
                    action = "update" if kvmsg.body else "delete"
                    MDP.logger.debug("PROXY - Client received action %s with sequence %s", action, self.sequence)

    def destroy(self):
        """ Destroy object
        """
        self.ctx.destroy(0)

    def shutdown(self):
        """Shutdown the broker.
        """
        self._stopevent.set()
