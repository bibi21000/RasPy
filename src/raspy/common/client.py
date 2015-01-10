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

import traceback
import time

import raspy.common.MDP as MDP
from raspy.common.executive import Executive
from raspy.common.mdcliapi import MajorDomoClient

import logging

class Client(Executive):
    """The generic worker

    From http://zguide.zeromq.org/py:all#header-48

    """

    def __init__(self, hostname='localhost', service="worker", broker_ip='127.0.0.1', broker_port=5514, poll=1500, ttl=900):
        """Initialize the client
        """
        Executive.__init__(self, hostname, service, broker_ip, broker_port)
        self.client = MajorDomoClient("tcp://%s:%s" % (broker_ip, broker_port))
        self.poll = poll
        self.ttl = ttl
        self.requests = {}

    def request(self, service=None, data=["mmi.echo"], callback=None, args=(), kwargs={}):
        """Request a job to a worker
        """
        req = [MDP.routing_key(self.hostname, service)] + data if service else [MDP.routing_key(self.hostname, self.service)] + data
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
        """Request a job to a worker
        """
        if uuid:
            if uuid in self.requests:
                status = self.requests[uuid]['status']
                if status != MDP.T_PENDING:
                    #The tasks is finished or is in error. Remove it from pending requests
                    del self.requests[uuid]
                return status
        return MDP.T_UNKNOWN

    def run(self):
        """Run the client
        """
        while not self._stopevent.isSet():
            start_at = time.clock()
            uuids = [uid for uid in self.requests.keys() if self.requests[uid]['status'] == MDP.T_PENDING]
            for uuid in uuids:
                reply = self.client.send("titanic.reply", [uuid])
                if reply:
                    status = reply.pop(0)
                    self.requests[uuid]['status'] = status
                    if status == MDP.T_OK:
                        self.requests[uuid]['data'] = reply
                        if self.requests[uuid]['callback']:
                            self.requests[uuid]['callback'](reply, self.requests[uuid]['args'], self.requests[uuid]['kwargs'])
                            del self.requests[uuid]
                        logging.debug("CLIENT - Reply: %s", reply)
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
                logging.info("CLIENT - Remove uuid %s because of ttl", uuid)
                del self.requests[uuid]
            sleep_time = self.poll - (time.clock() - start_at)
            if sleep_time > 0:
                self._stopevent.wait(sleep_time/1000.0)
            else:
                logging.warning("CLIENT - Not enough time to sleep with current poll : %s ", sleep_time)
