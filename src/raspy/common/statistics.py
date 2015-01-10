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

import raspy.common.MDP as MDP
from raspy.common.executive import Executive
from raspy.common.mdwrkapi import MajorDomoWorker
import logging

class Statistics(object):
    """The statistics manager
    """

    def __init__(self):
        """Initialize the worker
        """
        self.worker_statistics_thread = threading.Thread(target=self.worker_statistics)
        self.worker_statistics_thread.daemon = True
        self._active_threads.append(self.worker_statistics_thread)
        self._statistics = {}

    def worker_statistics(self):
        """Send statistics via mmi
        """
        worker = MajorDomoWorker("tcp://%s:%s" % (self.broker_ip, self.broker_port), "%s.statistics" % MDP.routing_key(self.hostname, self.service))
        self._active_workers.append(worker)
        reply = None
        logging.debug("Start worker for service %s", "%s.statistics"%MDP.routing_key(self.hostname, self.service))
        while not self._stopevent.isSet():
            request = worker.recv(reply)
            if not request:
                break      # Interrupted, exit
            reply = [MDP.T_ERROR]
            try:
                action = request.pop(0)
                logging.debug("worker_statistics received action %s", action)
                reply = [MDP.T_ERROR]
                if "all" == action:
                    reply = [MDP.T_OK]
                elif "list_keys" == action:
                    reply = [json.dumps(self._statistics.keys())] + [MDP.T_OK]
                else:
                    reply = [MDP.T_NOTIMPLEMENTED]
                    logging.debug("worker_statistics send [%s][%s]", action, MDP.T_NOTIMPLEMENTED)
            except IndexError:
                logging.exception("Exception in worker_statistics")
                reply = [MDP.T_ERROR]

    def add_statistic(self):
        """Add a new statistic to the manager
        """
        pass

    def remove_statistic(self, oid):
        """Remove a statistic from the manager
        """
        if oid in self._statistics:
            del self._statistics[oid]

    def update_statistic(self, oid="", ):
        """Add a new statistic to the manager
        """
        pass

class SNMP(object):
    '''Abstract statistic item
    '''
    def __init__(self, oid="module.snmp.key", doc="A statistic integer value", initial=0):
        """Init the object
        """
        self.value = initial
        self.oid = oid
        self.doc = doc

    def set(self, value):
        """ Set a value to the snmp object
        """
        self.value += value

    def __str__(self):
        """Return a string representation of the value
        """
        return repr(self.value)

class SNMPCounter(SNMP):
    '''Long (32bits) with overflow
    '''
    def __init__(self, oid="module.snmp.key", doc="A statistic counter value with overflow", initial=0, overflow=4294967296):
        """
        """
        SNMP.__init__(self, oid=oid, doc=doc, initial=initial)
        self.overflow = overflow

    def set(self, value=1):
        """Add value (default=1) to current value. Also manage overflow.
        """
        self.value += value
        if self.value > self.overflow :
            self.value -= self.overflow

class SNMPFloat(SNMP):
    '''Float counter
    '''
    def __init__(self, oid="module.snmp.key", doc="A statistic float value", initial=0.0):
        """Init the object
        """
        SNMP.__init__(self, oid=oid, doc=doc, initial=initial)

class SNMPString(SNMP):
    '''Float counter
    '''
    def __init__(self, oid="module.snmp.key", doc="A statistic string value", initial=""):
        """Init the object
        """
        SNMP.__init__(self, oid=oid, doc=doc, initial=initial)
