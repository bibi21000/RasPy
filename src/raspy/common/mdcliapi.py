# -*- coding: utf-8 -*-

"""Majordomo Protocol Client API, Python version.

Implements the MDP/Worker spec at http:#rfc.zeromq.org/spec:7.

Author: Min RK <benjaminrk@gmail.com>
Based on Java example by Arkadiusz Orzechowski
"""

import zmq

from raspy.common.executive import Executive
from raspy.common.zhelpers import zpipe
import raspy.common.MDP as MDP
import threading
import time
import logging

class MajorDomoClient(object):
    """Majordomo Protocol Client API, Python version.

      Credits : https://github.com/imatix/zguide/blob/master/examples/Python/mdcliapi.py
    """
    broker = None
    ctx = None
    client = None
    poller = None
    timeout = 500
    retries = 5
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
                if retries > 0:
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

class TitanicClient(object):
    """The titanic client

    Credits: https://github.com/imatix/zguide/blob/master/examples/Python/ticlient.py

    """

    def __init__(self, broker_ip='localhost', broker_port=5514, poll=1500, ttl=900):
        """Initialize the client
        """
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self._stopevent = threading.Event()
        self.client = MajorDomoClient("tcp://%s:%s" % (broker_ip, broker_port))
        self.poll = poll
        self.ttl = ttl
        self.requests = {}

    def shutdown(self):
        """Shutdown executive.
        """
        self._stopevent.set()

    def send(self, service, request):
        """Send a Majordomo request directly to worker
        """
        return self.client.send(service, request)

    def request(self, hostname="localhost", service="worker", data=["mmi.echo"], callback=None, args=(), kwargs={}):
        """Request a job for a worker to titanic
        """
        req = [MDP.routing_key(hostname, service)] + data
        reply = self.client.send("titanic.request", req)
        uuid = None
        if reply:
            status = reply.pop(0)
            if status == MDP.T_OK:
                uuid = reply.pop(0)
                self.requests[uuid] = { \
                        'callback' : callback, \
                        'args' : args, \
                        'kwargs' : kwargs, \
                        'status' : MDP.T_PENDING, \
                        'data' : None, \
                        'req_date' : time.time(), \
                        }
                logging.debug("CLIENT - Request UUID %s", uuid)
            elif status == MDP.T_UNKNOWN:
                logging.error("CLIENT - MDP.ClientError in titanic.request : routing_key=%s data=%s", req, data)
                raise MDP.ClientError("titanic.request : routing_key=%s data=%s" % (req, data))
            elif status == MDP.T_ERROR:
                logging.error("CLIENT - MDP.ServerError in titanic.request : routing_key=%s data=%s", req, data)
                raise MDP.ServerError("titanic.request : routing_key=%s data=%s" % (req, data))
        return uuid

    def status(self, uuid):
        """Retrieve the status of a work from titanic
        """
        if uuid:
            if uuid in self.requests:
                status = self.requests[uuid]['status']
                if status != MDP.T_PENDING:
                    #The tasks is finished or is in error. Remove it from pending requests
                    del self.requests[uuid]
                return [status]
        return [MDP.T_UNKNOWN]

    def run(self):
        """Run the client in a loop
        """
        while not self._stopevent.isSet():
            start_at = time.clock()
            uuids = [uid for uid in self.requests.keys() if self.requests[uid]['status'] == MDP.T_PENDING]
            for uuid in uuids:
                logging.debug("CLIENT - titanic.reply for uuid %s", uuid)
                reply = self.client.send("titanic.reply", [uuid])
                if reply:
                    status = reply.pop(0)
                    self.requests[uuid]['status'] = status
                    if status == MDP.T_OK:
                        self.requests[uuid]['data'] = reply
                        if self.requests[uuid]['callback']:
                            self.requests[uuid]['callback'](reply, self.requests[uuid]['args'], self.requests[uuid]['kwargs'])
                            del self.requests[uuid]
                        logging.debug("CLIENT - Titanic received: %s", reply)
                        reply = self.client.send("titanic.close", [uuid])
                        if reply:
                            status = reply.pop(0)
                            if status == MDP.T_UNKNOWN:
                                logging.error("CLIENT - MDP.ClientError in titanic.close : uuid=%s", uuid)
                                raise MDP.ClientError("titanic.close : uuid=%s" % (uuid))
                            elif status == MDP.T_ERROR:
                                logging.error("CLIENT - MDP.ServerError in titanic.close : uuid=%s", uuid)
                                raise MDP.ServerError("titanic.close : uuid=%s" % (uuid))
                    elif status == MDP.T_UNKNOWN:
                        logging.error("CLIENT - MDP.ClientError in titanic.reply : uuid=%s", uuid)
                        raise MDP.ClientError("titanic.reply : uuid=%s" %(uuid))
                    elif status == MDP.T_ERROR:
                        logging.error("CLIENT - MDP.ServerError in titanic.reply : uuid=%s", uuid)
                        raise MDP.ServerError("titanic.reply : uuid=%s" %(uuid))
            now = time.time()
            uuids_to_del = [uid for uid in self.requests.keys() if (self.requests[uid]['status'] == MDP.T_UNKNOWN or \
                                                                     self.requests[uid]['status'] == MDP.T_ERROR or \
                                                                     self.requests[uid]['status'] == MDP.T_ERROR) and \
                                                                     (now-self.requests[uid]['req_date']) > self.ttl]
            for uuid in uuids_to_del:
                logging.info("CLIENT - Titanic remove uuid %s because of ttl", uuid)
                del self.requests[uuid]
            sleep_time = self.poll - (time.clock() - start_at)
            if sleep_time > 0:
                self._stopevent.wait(sleep_time/500.0)
            else:
                logging.warning("CLIENT - Not enough time to sleep with current poll : %s ", sleep_time)
