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
import os, sys
import time
from raspy.common.executive import ExecutiveProcess
from ConfigParser import SafeConfigParser

class Supervisor():
    """The worker supervisor

    Start executives in separate process see futures
    Each executive start multiples threads of workers

    todo :
     - bug : can't stop when jobs in queues

    """
    #HB_INTERVAL = 1000  # in milliseconds
    #__metaclass__ = AutoSlots

    def __init__(self, runner=None):
        """Initialize the Supervisor.

        context is the zmq context to create the socket from.
        service is a byte-string with the service name.

        """
        self.options = {}
        self.options['service'] = runner.options['service']
        self.options['conffile_path'] = runner.options['conffile_path']
        self.options['hostname'] = runner.options['hostname']
        self.options['url_autoconf'] = runner.options['url_autoconf']
        self.options_candidates = ['executives']
        self.options['executives'] = [runner.options['service']]
        self.reload_in_progress = False
        self.executives = []

    def reload(self):
        """Request the workers confguration against the configurator.

        Will unregister all workers, stop all timers and ignore all further
        messages.

        .. warning:: The instance MUST not be used after :func:`shutdown` has been called.

        :rtype: None
        """
        if self.reload_in_progress == True or self._stop == True:
            return
        #print "reload"
        self.reload_in_progress = True
        self.stop_executives()
        if os.path.isfile(self.options['conffile_path']):
            parser = SafeConfigParser()
            parser.read(self.options['conffile_path'])
            if parser.has_option('Service', 'url_autoconf'):
                self.options['url_autoconf'] = parser.get('Service', 'url_autoconf')
            for candidate in self.options_candidates:
                if parser.has_option(self.options['service'], candidate):
                    if candidate in ['executives']:
                        self.options[candidate] = parser.get(self.options['service'], candidate).split(',')
                    else:
                        self.options[candidate] = parser.get(self.options['service'], candidate)
            for executive in self.options['executives']:
                self.executives.append(ExecutiveProcess(self, executive_name))
        self.reload_in_progress = False
        return

    def stop_executives(self):
        """Shutdown executives.
        """
        for process in self.executives:
            process.shutdown()
        for process in self.executives:
            process.join()
        self.executives = []

    def shutdown(self):
        """Shutdown supervisor.

        Will unregister all workers, stop all timers and ignore all further
        messages.

        .. warning:: The instance MUST not be used after :func:`shutdown` has been called.

        :rtype: None
        """
        self.stop_executives()
        self._stop = True
        return

    def run(self):
        """Start the IOLoop instance
        """
        self.reload()
        while not self._stop:
            # pass
            time.sleep(.25)
            #print "loop"
        #print "run"
        #IOLoop.instance().start()
        return

    def get_instance_id(self):
        """
        Return the instance of the worker : must be multihost and multithread.
        """
        return "%s#%s" % (self.service, self.hostname)
