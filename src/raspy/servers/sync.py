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
import json
import logging

class Sync(Server):
    """The Sync server

    Sync data from a or many folders (which we can configure via zmq) to a remote server.

    Used by logger, camera, ...

    Sync can be sheduled ( ie every day, ...) or laucnh on demand via worker
    We can sync a file or a directory

    """

    def __init__(self, hostname='localhost', service="sync", broker_ip='127.0.0.1', broker_port=5514):
        """Initialize the server
        """
        Server.__init__(self, hostname, service, broker_ip, broker_port)
        self.worker_sync_thread = threading.Thread(target=self.worker_sync)
        self.worker_sync_thread.daemon = True
        self._active_threads.append(self.worker_sync_thread)
        self.publisher = None

    def worker_sync(self):
        """Create a worker to handle sync requests
        """
        worker = MajorDomoWorker("tcp://%s:%s" % (self.broker_ip, self.broker_port), \
                "%s" % MDP.routing_key(self.hostname, self.service))
        self._active_workers.append(worker)
        reply = None
        logging.debug("Start worker for service %s", "%s" % MDP.routing_key(self.hostname, self.service))
        while not self._stopevent.isSet():
            # Send reply if it's not null
            # And then get next request from broker
            request = worker.recv(reply)
            if not request:
                break      # Interrupted, exit
            logging.debug("Receive job for service %s : %s", "%s" % MDP.routing_key(self.hostname, self.service), \
                            request)
            try:
                reply = [MDP.T_OK]
            except OSError as exc:
                reply = [MDP.T_ERROR]

    def run(self):
        """Sync data in a separate thread
        """
        self._start_active_threads()
        while not self._stopevent.isSet():
            #start sync here
            self._stopevent.wait(self.speed/3.0)

if __name__ == '__main__': # pragma: no cover
    mysync = Sync()        # pragma: no cover
    mysync.run()           # pragma: no cover
