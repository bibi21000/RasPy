# -*- coding: utf-8 -*-

"""Majordomo Protocol Client API, Python version.

Implements the MDP/Worker spec at http:#rfc.zeromq.org/spec:7.

Author: Min RK <benjaminrk@gmail.com>
Based on Java example by Arkadiusz Orzechowski
"""

import zmq

from raspy.common.zhelpers import zpipe
import raspy.common.MDP as MDP

class MajorDomoClient(object):
    """Majordomo Protocol Client API, Python version.

      Implements the MDP/Worker spec at http:#rfc.zeromq.org/spec:7.
    """
    broker = None
    ctx = None
    client = None
    poller = None
    timeout = 2500
    retries = 3
    verbose = False

    def __init__(self, broker):
        self.broker = broker
        self.ctx = zmq.Context()
        self.poller = zmq.Poller()
        self.reconnect_to_broker()

    def reconnect_to_broker(self):
        """Connect or reconnect to broker"""
        if self.client:
            self.poller.unregister(self.client)
            self.client.close()
        self.client = self.ctx.socket(zmq.REQ)
        self.client.linger = 0
        self.client.connect(self.broker)
        self.poller.register(self.client, zmq.POLLIN)
        MDP.logger.info("CLIENT - Connecting to broker at %s...", self.broker)

    def send(self, service, request):
        """Send request to broker and get reply by hook or crook.

        Takes ownership of request message and destroys it when sent.
        Returns the reply message or None if there was no reply.
        """
        if not isinstance(request, list):
            request = [request]
        request = [MDP.C_CLIENT, service] + request
        MDP.logger.debug("Send request to '%s' service: ", service)
        reply = None
        retries = self.retries
        while retries > 0:
            self.client.send_multipart(request)
            try:
                items = self.poller.poll(self.timeout)
            except KeyboardInterrupt: # pragma: no cover
                break                 # pragma: no cover
            if items:
                msg = self.client.recv_multipart()
                MDP.logger.debug("CLIENT - Received reply: %s", msg)
                # Don't try to handle errors, just assert noisily
                assert len(msg) >= 3
                header = msg.pop(0)
                assert MDP.C_CLIENT == header
                reply_service = msg.pop(0)
                assert service == reply_service
                reply = msg
                break
            else:
                if retries:
                    MDP.logger.warn("CLIENT - No reply, reconnecting...")
                    self.reconnect_to_broker()
                else:
                    MDP.logger.warn("CLIENT - Permanent error, abandoning")
                    break
                retries -= 1
        return reply

    def destroy(self):
        """ Destroy object
        """
        self.ctx.destroy(0)
