# -*- coding: utf-8 -*-

"""Majordomo Protocol Worker API, Python version

Implements the MDP/Worker spec at http:#rfc.zeromq.org/spec:7.

Author: Min RK <benjaminrk@gmail.com>
Based on Java example by Arkadiusz Orzechowski
"""

import time
import zmq
import threading
from raspy.common.zhelpers import zpipe
import raspy.common.MDP as MDP

class MajorDomoWorker(object):
    """Majordomo Protocol Worker API, Python version

    Implements the MDP/Worker spec at http:#rfc.zeromq.org/spec:7.
    """

    HEARTBEAT_LIVENESS = 5 # 3-5 is reasonable
    broker = None
    ctx = None
    service = None

    worker = None # Socket to broker
    heartbeat_at = 0 # When to send HEARTBEAT (relative to time.time(), so in seconds)
    liveness = 0 # How many attempts left
    heartbeat = 3500 # Heartbeat delay, msecs
    reconnect = 3500 # Reconnect delay, msecs

    # Internal state
    expect_reply = False # False only at start

    timeout = 2500 # poller timeout
    verbose = False # Print activity to stdout

    # Return address, if any
    reply_to = None

    status = True
    """The status of the worker. Should be update by callback in the future
    """

    def __init__(self, broker, service):
        self.broker = broker
        self.service = service
        self.ctx = zmq.Context()
        self.poller = zmq.Poller()
        self.reconnect_to_broker()
        self._stopevent = threading.Event()

    def reconnect_to_broker(self):
        """Connect or reconnect to broker"""
        if self.worker:
            self.poller.unregister(self.worker)
            self.worker.close()
        self.worker = self.ctx.socket(zmq.DEALER)
        self.worker.linger = 0
        self.worker.connect(self.broker)
        self.poller.register(self.worker, zmq.POLLIN)
        MDP.logger.info("WORKER - Connecting to broker at %s...", self.broker)
        # Register service with broker
        self.send_to_broker(MDP.W_READY, self.service, [])
        # If liveness hits zero, queue is considered disconnected
        self.liveness = self.HEARTBEAT_LIVENESS
        self.heartbeat_at = time.time() + 1e-3 * self.heartbeat

    def send_to_broker(self, command, option=None, msg=None):
        """Send message to broker.

     . If no msg is provided, creates one internally
        """
        if msg is None:
            msg = []
        elif not isinstance(msg, list):
            msg = [msg]
        if option:
            msg = [option] + msg
        msg = ['', MDP.W_WORKER, command] + msg
        MDP.logger.debug("WORKER - Sending %s to broker", msg)
        self.worker.send_multipart(msg)

    def recv(self, reply=None):
        """Send reply, if any, to broker and wait for next request."""
        # Format and send the reply if we were provided one
        assert reply is not None or not self.expect_reply
        if reply is not None:
            assert self.reply_to is not None
            reply = [self.reply_to, ''] + reply
            self.send_to_broker(MDP.W_REPLY, msg=reply)
        self.expect_reply = True
        while not self._stopevent.isSet():
            # Poll socket for a reply, with timeout
            try:
                items = self.poller.poll(self.timeout)
            except KeyboardInterrupt: # pragma: no cover
                break                 # pragma: no cover
            if items:
                msg = self.worker.recv_multipart()
                MDP.logger.debug("WORKER - Received message %s from broker: ", msg)
                self.liveness = self.HEARTBEAT_LIVENESS
                # Don't try to handle errors, just assert noisily
                assert len(msg) >= 3
                empty = msg.pop(0)
                assert empty == ''
                header = msg.pop(0)
                assert header == MDP.W_WORKER
                command = msg.pop(0)
                if command == MDP.W_REQUEST:
                    # We should pop and save as many addresses as there are
                    # up to a null part, but for now, just save one...
                    self.reply_to = msg.pop(0)
                    # pop empty
                    assert msg.pop(0) == ''
                    return msg # We have a request to process
                elif command == MDP.W_HEARTBEAT:
                    # Do nothing for heartbeats
                    pass
                elif command == MDP.W_DISCONNECT:
                    self.reconnect_to_broker()
                else:
                    MDP.logger.error("WORKER - Invalid input message: %s", msg)
            else:
                self.liveness -= 1
                if self.liveness == 0:
                    MDP.logger.warn("WORKER - Disconnected from broker - retrying...")
                    try:
                        time.sleep(1e-3*self.reconnect)
                    except KeyboardInterrupt:
                        break
                    self.reconnect_to_broker()
            # Send HEARTBEAT if it's time
            if time.time() > self.heartbeat_at:
                self.send_to_broker(MDP.W_HEARTBEAT)
                self.heartbeat_at = time.time() + 1e-3*self.heartbeat
        MDP.logger.warn("WORKER - Interrupt received, killing worker...")
        return None

    def destroy(self):
        """ Destroy object
        """
        # context.destroy depends on pyzmq >= 2.1.10
        self.ctx.destroy(0)

    def shutdown(self):
        """Shutdown executive.
        """
        self._stopevent.set()
