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

import threading
import traceback
import os
import raspy.common.MDP as MDP
from raspy.common.server import Server
from raspy.common.mdwrkapi import MajorDomoWorker
#from raspy.common.zhelpers import dump

import logging

class Fake(Server):
    """A fake server to test RasPy

        - we must developp "real" fake device : ie a temperature sensors must not send random values
        - a cyclic sensor : parameters : cycle length, min, max and unit. Will do cycle from min temp to max temp (at cycle/2) and fall back tp min temp at end of if
        - a linear sensor
        -
    """

    def __init__(self, hostname='localhost', service="fake", broker_ip='127.0.0.1', broker_port=5514):
        """Initialize the server
        """
        Server.__init__(self, hostname, service, broker_ip, broker_port)
        self.worker_devices_thread = threading.Thread(target=self.worker_devices)
        self.worker_devices_thread.daemon = True
        self._active_threads.append(self.worker_devices_thread)

    def worker_devices(self):
        """Create a worker to handle devices requests

        """
        worker = MajorDomoWorker("tcp://%s:%s" % (self.broker_ip, self.broker_port), \
                "%s.devices" % MDP.routing_key(self.hostname, self.service))
        self._active_workers.append(worker)
        reply = None
        logging.debug("Start worker for service %s", "%s.devices"%MDP.routing_key(self.hostname, self.service))
        while not self._stopevent.isSet():
            request = worker.recv(reply)
            if not request:
                break      # Interrupted, exit
            reply = [MDP.T_ERROR]
            try:
                action = request.pop(0)
                logging.debug("worker_devices received action %s", action)
                reply = [action] + [MDP.T_ERROR]
                if action == "list_keys":
                    try:
                        reply = [MDP.T_OK]
                        logging.debug("worker_devices send [%s]", action)
                    except OSError as exc:
                        logging.exception("OSError Exception in worker_devices for action %s", action)
                        reply = [MDP.T_ERROR]
                else:
                    reply = [action] + [MDP.T_NOTIMPLEMENTED]
                    logging.debug("worker_devices send [%s][%s]", action, MDP.T_NOTIMPLEMENTED)
            except IndexError:
                logging.exception("Exception in worker_devices")
                reply = [MDP.T_ERROR]

if __name__ == '__main__': # pragma: no cover
    myfake = Fake()     # pragma: no cover
    myfake.run()           # pragma: no cover

