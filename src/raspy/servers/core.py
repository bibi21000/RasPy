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

class Scenario(threading.Thread):
    """A scenario
    """
    conf = {}
    """The configuration of the scenario
    """
    entries = {}
    """The entries we must look at for an event driven scenario
    """
    running = False
    """Is the scenario running
    """
    code = None
    """The code we must exec
    """

    def __init__(self, name='scenar1', publisher=None):
        """Initialize the scenario
        """
        threading.Thread.__init__(self)
        logging.debug("Starting scenario %s", name)
        conf = {
            #Is this scenario active (must be start at startup, run from events, ...)
            'active' : False,
            #Start the scenario in background at startup
            'startup' : False
        }
        self.publisher = publisher
        self._stopevent = threading.Event()
        logging.info("Scenario %s is active", name)

    def run(self):
        """Run the scenario
        """
        self.running = True
        while not self._stopevent.isSet():
            pass
        self.running = False

    def shutdown(self):
        """Shutdown the scenario
        """
        self._stopevent.set()

    def fire(self):
        """Check if the scenario must be fired using entries and that is not already running. If so, call sself.run()

        :returns: True if the thread must be launch (self.run()), False otherwise
        :rtype: boolean
        """
        return False

    def load(self, store):
        """Load the scenario from titanic store

        :param store: the store to get info from
        :type: titani_store
        :returns: True if the scenario was loaded from store
        :rtype: boolean
        """
        return False

    def store(self, store):
        """Store the scenario to titanic store
        """
        return False

class ScenarioManager(object):
    """The manager of scenarios

    http://etutorials.org/Programming/Python+tutorial/Part+III+Python+Library+and+Extension+Modules/Chapter+13.+Controlling+Execution/13.1+Dynamic+Execution+and+the+exec+Statement/
    http://lucumr.pocoo.org/2011/2/1/exec-in-python/
    http://late.am/post/2012/04/30/the-exec-statement-and-a-python-mystery
    """

    scenarios = {}
    """The scenarios
    """

    def __init__(self, publisher=None):
        """Initialize the scenario Manager
        """
        self.publisher = publisher

    def load(self, store):
        """Load the scenarios from titanic store

        store keys :

            - scenario.main.conf : a json dict for configuration of scenario
            - scenario.main.keys : a json list of the scenario's names
            - scenario.key1.conf : a json dict for configuration of scenario key1
            - scenario.key1.entries : a json dict of entries of scenario key1
            - scenario.key1.code : a json string of code of scenario key1

        """
        return False

    def store(self, store):
        """Store the scenarios to titanic store
        """
        return False

    def shutdown(self):
        """Shutdown the scenario manager
        """
        pass

    def add(self, name='scenar1', entries={}, code=None, conf={}):
        """Add a scenario
        """
        pass

    def update(self, name='scenar1', entries={}, code=None, conf={}):
        """Update a scenario
        """
        pass

    def delete(self, name='scenar1'):
        """Delete a scenario
        """
        pass

    def list(self):
        """Return all scenarios with conf, entries, ... as json dict
        """
        pass

    def list_keys(self):
        """Return all scenarios key (=name) ... as json list
        """
        pass

class Cron(object):
    """A cron job
    """
    aps_job = None

class CronManager(object):
    """The manager of cron job
    """
    jobs = {}

class Core(Server):
    """The Core server

    - Cron
        - Generate events in the publisher

    - Scenario
        - a scenario can run in background at startup (ie thermostat) or fired by an event (ie cron, sun is down, temperature is under 0°C)
        - a scenario can be a loop so it must be launch in a separate thread : start filling, loop until water level is ok : need to call self._stopevent.isSet() in it so that the tread can shutdown.
        - look for updates in entries list (cron, sensors, variables in the publisher) : a list mapped in friendly user's names (using store)
        - it can publish some values with publisher
        - do some work using inline code python :
        - send commands to devices, cron jobs, start other scenario, update some variables in publisher
        - we can export/import scenarios : share with friends

    - NTP / Sytem Time / RTC Sync
        - sync from ntp to rtc
        - sync from trc to system : using sudo with no password
    """

    def __init__(self, hostname='localhost', service="core", broker_ip='127.0.0.1', broker_port=5514):
        """Initialize the server
        """
        Server.__init__(self, hostname, service, broker_ip, broker_port)
        self.worker_cron_thread = threading.Thread(target=self.worker_cron)
        self.worker_cron_thread.daemon = True
        self._active_threads.append(self.worker_cron_thread)
        self.worker_scenario_thread = threading.Thread(target=self.worker_scenario)
        self.worker_scenario_thread.daemon = True
        self._active_threads.append(self.worker_scenario_thread)
        self.worker_scenarios_thread = threading.Thread(target=self.worker_scenarios)
        self.worker_scenarios_thread.daemon = True
        self._active_threads.append(self.worker_scenarios_thread)
        self.publisher = None
        self.manager_scenario = ScenarioManager(publisher=self.publisher)

    def worker_cron(self):
        """Create a worker to handle cron requests
        """
        worker = MajorDomoWorker("tcp://%s:%s" % (self.broker_ip, self.broker_port), \
                "%s.cron" % MDP.routing_key(self.hostname, self.service))
        self._active_workers.append(worker)
        reply = None
        logging.debug("Start worker for service %s", "%s.cron" % MDP.routing_key(self.hostname, self.service))
        while not self._stopevent.isSet():
            # Send reply if it's not null
            # And then get next request from broker
            request = worker.recv(reply)
            if not request:
                break      # Interrupted, exit
            logging.debug("Receive job for service %s : %s", "%s.cron" % MDP.routing_key(self.hostname, self.service), \
                            request)
            try:
                reply = [MDP.T_OK]
            except OSError as exc:
                reply = [MDP.T_ERROR]

    def worker_scenario(self):
        """Create a worker to handle scenario's requests
        """
        worker = MajorDomoWorker("tcp://%s:%s" % (self.broker_ip, self.broker_port), \
                "%s.scenario" % MDP.routing_key(self.hostname, self.service))
        self._active_workers.append(worker)
        reply = None
        logging.debug("Start worker for service %s", "%s.scenario" % MDP.routing_key(self.hostname, self.service))
        while not self._stopevent.isSet():
            request = worker.recv(reply)
            if not request:
                break      # Interrupted, exit
            reply = [MDP.T_ERROR]
            try:
                action = request.pop(0)
                logging.debug("worker_scenario received action %s", action)
                reply = [MDP.T_ERROR]
                if action == "info":
                    logging.debug("worker_scenario send %s", json.dumps(self.manager_scenario.scenarios.keys()))
                    reply = [json.dumps(self.manager_scenario.scenarios.keys())] + [MDP.T_OK]
                else:
                    reply = [MDP.T_NOTIMPLEMENTED]
            except IndexError:
                logging.exception("Exception in worker_scenario")
                reply = [MDP.T_ERROR]

    def worker_scenarios(self):
        """Create a worker to handle scenarios requests (list_keys, ...)
        """
        worker = MajorDomoWorker("tcp://%s:%s" % (self.broker_ip, self.broker_port), \
                "%s.scenarios" % MDP.routing_key(self.hostname, self.service))
        self._active_workers.append(worker)
        reply = None
        logging.debug("Start worker for service %s", "%s.scenarios" % MDP.routing_key(self.hostname, self.service))
        while not self._stopevent.isSet():
            request = worker.recv(reply)
            if not request:
                break      # Interrupted, exit
            reply = [MDP.T_ERROR]
            try:
                action = request.pop(0)
                logging.debug("worker_scenario received action %s", action)
                reply = [MDP.T_ERROR]
                if action == "list_keys":
                    res = ""
                    for key in self.manager_scenario.scenarios.iterkeys():
                        if res == None:
                            res = key
                        else:
                            res = res + '|' + key
                    reply = [res] + [MDP.T_OK]
                else:
                    reply = [MDP.T_NOTIMPLEMENTED]
            except IndexError:
                logging.exception("Exception in worker_scenarios")
                reply = [MDP.T_ERROR]

if __name__ == '__main__': # pragma: no cover
    mycore = Core()        # pragma: no cover
    mycore.run()           # pragma: no cover
