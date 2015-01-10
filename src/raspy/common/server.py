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
import threading
import logging
import raspy.common.MDP as MDP
from raspy.common.executive import Executive
from raspy.common.mdwrkapi import MajorDomoWorker
from raspy.common.statistics import Statistics
from raspy.common.zhelpers import dump

class Server(Executive, Statistics):
    """The generic worker

    From http://zguide.zeromq.org/py:all#header-48

    """

    def __init__(self, hostname='localhost', service="worker", broker_ip='127.0.0.1', broker_port=5514):
        """Initialize the worker
        """
        Executive.__init__(self, hostname, service, broker_ip, broker_port)
        self.worker_mmi_thread = threading.Thread(target=self.worker_mmi)
        self.worker_mmi_thread.daemon = True
        self._active_threads.append(self.worker_mmi_thread)
        Statistics.__init__(self)

    def worker_mmi(self):
        """Retrieve mmi informations of the worker
        """
        worker = MajorDomoWorker("tcp://%s:%s" % (self.broker_ip, self.broker_port), "%s.mmi" % MDP.routing_key(self.hostname, self.service))
        self._active_workers.append(worker)
        reply = None
        logging.debug("Start worker for service %s", "%s.mmi"%MDP.routing_key(self.hostname, self.service))
        while not self._stopevent.isSet():
            request = worker.recv(reply)
            if not request:
                break      # Interrupted, exit
            reply = [MDP.T_ERROR]
            try:
                action = request.pop(0)
                logging.debug("worker_mmi received action %s", action)
                reply = [MDP.T_ERROR]
                if action == "status":
                    status = True
                    for wrk in self._active_workers:
                        if wrk.status == False:
                            status = False
                    if status == True:
                        reply = [MDP.T_OK]
                    else:
                        reply = [MDP.T_ERROR]
                else:
                    reply = [MDP.T_NOTIMPLEMENTED]
                    logging.debug("worker_mmi send [%s][%s]", action, MDP.T_NOTIMPLEMENTED)
            except IndexError:
                logging.exception("Exception in worker_mmi")
                reply = [MDP.T_ERROR]

if __name__ == '__main__': # pragma: no cover
    myserver = Server()    # pragma: no cover
    myserver.run()         # pragma: no cover

