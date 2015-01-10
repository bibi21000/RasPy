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
import multiprocessing
import time
import threading
import logging

class Executive(object):
    """The Executive mother class for all workers

    todo :
     - bug : can't stop when jobs in queues

    """
    #HB_INTERVAL = 1000  # in milliseconds
    #__metaclass__ = AutoSlots

    def __init__(self, hostname='localhost', service="executive", broker_ip='127.0.0.1', broker_port=5514):
        """Initialize the executive.
        """
        self.service = service
        self.hostname = hostname
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self._stopevent = threading.Event()
        self.debug_level = 0
        self.update_in_progress = False
        self._active_workers = []
        self._active_threads = []
        self.speed = 1.0

    def shutdown(self):
        """Shutdown executive.
        """
        self._stopevent.set()
        while len(self._active_workers) > 0:
            wrk = self._active_workers.pop(0)
            wrk.shutdown()

    def _start_active_threads(self):
        """Wait for threads and destroy contexts.
        """
        for thr in self._active_threads:
            thr.start()

    def destroy(self):
        """Wait for threads and destroy contexts.
        """
        while len(self._active_threads) > 0:
            thr = self._active_threads.pop(0)
            #thr.join()
        #self.ctx.destroy(0)

    def run(self):
        """Run the executive
        """
        self._start_active_threads()
        while not self._stopevent.isSet():
            self._stopevent.wait(self.speed/3.0)

    def get_instance_id(self):
        """
        Return the instance of the exective

        ... todo : must be multihost and multithread.
        """
        return "%s.%s" % (self.hostname, self.service)

class ExecutiveProcess(multiprocessing.Process):
    """Process executing tasks from a given tasks queue"""
    def __init__(self, executive, executive_name):
        multiprocessing.Process.__init__(self)
        self.daemon = True
        self.executive = executive
        self.executive_name = executive_name

    def run(self):
        """
        """
        self.executive.run()
        #print "Ok0"
        #while self._stop==False:
        #    pass
        #print "Ok3"
        #self.worker=None;
        #print "Ok4"

    def shutdown(self):
        """
        Method to deactivate the client connection completely.

        Will delete the stream and the underlying socket.

        .. warning:: The instance MUST not be used after :func:`shutdown` has been called.

        :rtype: None
        """
        #print "Ok1"
        #self._stop=True
        #print "Ok2"
        self.executive.shutdown()
