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

import cPickle as pickle
import threading
from uuid import uuid4
import traceback
import os
from ConfigParser import SafeConfigParser
import ConfigParser
import zmq
import raspy.common.MDP as MDP
from raspy.common.executive import Executive
from raspy.common.mdwrkapi import MajorDomoWorker
from raspy.common.mdcliapi import MajorDomoClient
from raspy.common.zhelpers import zpipe

class Titanic(Executive):
    """The Titanic helper

    Also integrates a store for keys/values

    From http://zguide.zeromq.org/py:all#Disconnected-Reliability-Titanic-Pattern
         http://zguide.zeromq.org/py:all#Service-Oriented-Reliable-Queuing-Majordomo-Pattern
         https://github.com/imatix/zguide/tree/master/examples/Python
    """

    def __init__(self, hostname='localhost', service="titanic", broker_ip='127.0.0.1', broker_port=5514, \
            data_dir='/tmp/raspy'):
        """Initialize the Titanic helper
        """
        MDP.logger.debug("TITANIC - Starting ...")
        Executive.__init__(self, hostname, service, broker_ip, broker_port)
        self.data_dir = data_dir
        self.store_dir = os.path.join(self.data_dir, "store")
        self.queue_dir = os.path.join(self.data_dir, "queue")
        if not os.path.isdir(self.store_dir):
            os.makedirs(self.store_dir)
        self.ctx = zmq.Context()
        if not os.path.isdir(self.queue_dir):
            os.makedirs(self.queue_dir)
        self.ctx = zmq.Context()
        # Create MDP client session with short timeout
        MDP.logger.debug("TITANIC - Connect client to tcp://%s:%s", self.broker_ip, self.broker_port)
        self.client = MajorDomoClient("tcp://%s:%s" % (self.broker_ip, self.broker_port))
        self.client.timeout = 1000 # 1 sec
        self.client.retries = 1 # only 1 retry
        self.request_pipe, self.peer = zpipe(self.ctx)
        self.poller = zmq.Poller()
        self.poller.register(self.request_pipe, zmq.POLLIN)
        self.request_thread = threading.Thread(target=self.titanic_request, args=(self.peer,))
        self._active_threads.append(self.request_thread)
        self.request_thread.daemon = True
        self.reply_thread = threading.Thread(target=self.titanic_reply)
        self._active_threads.append(self.reply_thread)
        self.reply_thread.daemon = True
        self.close_thread = threading.Thread(target=self.titanic_close)
        self._active_threads.append(self.close_thread)
        self.close_thread.daemon = True
        self.store_thread = threading.Thread(target=self.titanic_store)
        self._active_threads.append(self.store_thread)
        self.store_thread.daemon = True
        MDP.logger.info("TITANIC - Started")

    def run(self):
        """Run the hub
        """
        self.request_thread.start()
        self.reply_thread.start()
        self.close_thread.start()
        self.store_thread.start()
        while not self._stopevent.isSet():
            # We'll dispatch once per second, if there's no activity
            try:
                items = self.poller.poll(self.speed*1000.0)
            except KeyboardInterrupt:
                break          # Interrupted
            except zmq.ZMQError as exc:
                if not self._stopevent.isSet():
                    raise exc
                else:
                    items = None
            if items:
                # Append UUID to queue, prefixed with '-' for pending
                uuid = self.request_pipe.recv()
                try:
                    with open(os.path.join(self.queue_dir, 'queue'), 'a') as f:
                        f.write("-%s\n" % uuid)
                except (IOError) as e:
                    MDP.logger.error("TITANIC - Can't create file %s", os.path.join(self.queue_dir, 'queue'))
            # Brute-force dispatcher
            try:
                with open(os.path.join(self.queue_dir, 'queue'), 'r+b') as f:
                    for entry in f.readlines():
                        # UUID is prefixed with '-' if still waiting
                        if entry[0] == '-':
                            uuid = entry[1:].rstrip() # rstrip '\n' etc.
                            MDP.logger.debug("TITANIC - Processing request %s", uuid)
                            if self.service_success(self.client, uuid):
                                # mark queue entry as processed
                                here = f.tell()
                                f.seek(-1*len(entry), os.SEEK_CUR)
                                f.write('+')
                                f.seek(here, os.SEEK_SET)
            except (IOError) as e:
                MDP.logger.debug("TITANIC - Can't open file %s ... Create it", os.path.join(self.queue_dir, 'queue'))
                try:
                    with open(os.path.join(self.queue_dir, 'queue'), 'a') as f:
                        f.write("")
                except (IOError) as e:
                    MDP.logger.error("TITANIC - Can't create file %s", os.path.join(self.queue_dir, 'queue'))

    #def destroy(self):
    #    """Wait for threads and destroy contexts.
    #    """
    #    self.request_thread.join()
    #    self.reply_thread.join()
    #    self.close_thread.join()
    #    self.store_thread.join()
    #    self.ctx.destroy(0)

    def request_filename(self, uuid):
        """Returns freshly allocated request filename for given UUID"""
        return os.path.join(self.queue_dir, "%s.req" % uuid)

    def reply_filename(self, uuid):
        """Returns freshly allocated reply filename for given UUID"""
        return os.path.join(self.queue_dir, "%s.rep" % uuid)

    def store_filename(self, service):
        """Returns store filename for given service"""
        return os.path.join(self.store_dir, "%s.sto" % service)

    def titanic_request(self, pipe):
        """Create a worker to handle titanic.request

        titanic.request: store a request message, and return a UUID for the request.
        """
        MDP.logger.info("TITANIC - Connect titanic_request worker to tcp://%s:%s", self.broker_ip, self.broker_port)
        worker = MajorDomoWorker("tcp://%s:%s" % (self.broker_ip, self.broker_port), "titanic.request")
        self._active_workers.append(worker)
        reply = None
        while not self._stopevent.isSet():
            # Send reply if it's not null
            # And then get next request from broker
            request = worker.recv(reply)
            if not request:
                break      # Interrupted, exit
            # Generate UUID and save message to disk
            uuid = uuid4().hex
            filename = self.request_filename(uuid)
            with open(filename, 'w') as f:
                pickle.dump(request, f)
            # Send UUID through to message queue
            pipe.send(uuid)
            # Now send UUID back to client
            # Done by the worker.recv() at the top of the loop
            reply = ["200", uuid]

    def titanic_reply(self):
        """Create a worker to handle titanic.service

        titanic.reply: fetch a reply, if available, for a given request UUID.
        """
        MDP.logger.info("TITANIC - Connect titanic_reply worker to tcp://%s:%s", self.broker_ip, self.broker_port)
        worker = MajorDomoWorker("tcp://%s:%s" % (self.broker_ip, self.broker_port), "titanic.reply")
        self._active_workers.append(worker)
        reply = None
        while not self._stopevent.isSet():
            request = worker.recv(reply)
            if not request:
                break      # Interrupted, exit
            uuid = request.pop(0)
            req_filename = self.request_filename(uuid)
            rep_filename = self.reply_filename(uuid)
            if os.path.exists(rep_filename):
                with open(rep_filename, 'r') as f:
                    reply = pickle.load(f)
                reply = [MDP.T_OK] + reply
            else:
                if os.path.exists(req_filename):
                    reply = [MDP.T_PENDING] # pending
                else:
                    reply = [MDP.T_UNKNOWN] # unknown

    def titanic_close(self):
        """Create a worker to handle titanic.close

        titanic.close: confirm that a reply has been stored and processed.
        """
        MDP.logger.info("TITANIC - Connect titanic_close worker to tcp://%s:%s", self.broker_ip, self.broker_port)
        worker = MajorDomoWorker("tcp://%s:%s" % (self.broker_ip, self.broker_port), "titanic.close")
        self._active_workers.append(worker)
        reply = None
        while not self._stopevent.isSet():
            request = worker.recv(reply)
            if not request:
                break      # Interrupted, exit
            uuid = request.pop(0)
            req_filename = self.request_filename(uuid)
            rep_filename = self.reply_filename(uuid)
            # should these be protected?  Does zfile_delete ignore files
            # that have already been removed?  That's what we are doing here.
            if os.path.exists(req_filename):
                os.remove(req_filename)
            if os.path.exists(rep_filename):
                os.remove(rep_filename)
            reply = [MDP.T_OK]

    def service_success(self, client, uuid):
        """Attempt to process a single request, return True if successful"""
        # Load request message, service will be first frame
        filename = self.request_filename(uuid)
        # If the client already closed request, treat as successful
        if not os.path.exists(filename):
            return True
        with open(filename, 'r') as f:
            request = pickle.load(f)
        service = request.pop(0)
        # Use MMI protocol to check if service is available
        mmi_request = [service]
        mmi_reply = client.send("mmi.service", mmi_request)
        service_ok = mmi_reply and mmi_reply[0] == MDP.T_OK
        if service_ok:
            reply = client.send(service, request)
            if reply:
                filename = self.reply_filename(uuid)
                with open(filename, "w") as f:
                    pickle.dump(reply, f)
                return True
        return False

    def titanic_store(self):
        """Create a worker to handle store services
        """
        MDP.logger.info("TITANIC - Connect titanic.store worker to tcp://%s:%s", self.broker_ip, self.broker_port)
        worker = MajorDomoWorker("tcp://%s:%s" % (self.broker_ip, self.broker_port), "titanic.store")
        self._active_workers.append(worker)
        reply = None
        while not self._stopevent.isSet():
            request = worker.recv(reply)
            if not request:
                break      # Interrupted, exit
            reply = [MDP.T_ERROR]
            try:
                action = request.pop(0)
                service = request.pop(0)
                reply = [service] + [MDP.T_ERROR]
                if action == "set":
                    try:
                        parser = SafeConfigParser()
                        parser.read(self.store_filename(service))
                        section = request.pop(0)
                        key = request.pop(0)
                        value = request.pop(0)
                        reply = [service] + [section] + [key] + [MDP.T_ERROR]
                        if not parser.has_section(section):
                            parser.add_section(section)
                        parser.set(section, key, value)
                        with open(self.store_filename(service), 'wb') as configfile:
                            parser.write(configfile)
                        reply = [service] + [section] + [key] + [MDP.T_OK]
                    except IOError:
                        reply = [service] + [MDP.T_ERROR]
                elif action == "get":
                    parser = SafeConfigParser()
                    parser.read(self.store_filename(service))
                    section = request.pop(0)
                    key = request.pop(0)
                    reply = [service] + [section] + [key] + [MDP.T_ERROR]
                    if parser.has_option(section, key) == True:
                        value = "%s" % parser.get(section, key)
                        MDP.logger.debug("TITANIC - Store retrieve value for %s.%s.%s : %s", service, section, key, value)
                        reply = [service] + [section] + [key] + [value] + [MDP.T_OK]
                    else:
                        MDP.logger.debug("TITANIC - Store can't retrieve value for %s.%s.%s", service, section, key)
                        reply = [service] + [section] + [key] + [MDP.T_NOTFOUND]
                elif action == "delete":
                    section = None
                    key = None
                    if len(request) > 0:
                        section = request.pop(0)
                    if len(request) > 0:
                        key = request.pop(0)
                    reply = [service] + [section] + [key] + [MDP.T_ERROR]
                    if key is not None:
                        try:
                            parser = SafeConfigParser()
                            parser.read(self.store_filename(service))
                            parser.remove_option(section, key)
                            with open(self.store_filename(service), 'wb') as configfile:
                                parser.write(configfile)
                            reply = [service] + [section] + [key] + [MDP.T_OK]
                        except (IOError, ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                            reply = [service] + [section] + [MDP.T_ERROR]
                    elif section is not None:
                        try:
                            parser = SafeConfigParser()
                            parser.read(self.store_filename(service))
                            parser.remove_section(section)
                            with open(self.store_filename(service), 'wb') as configfile:
                                parser.write(configfile)
                            reply = [service] + [section] + [MDP.T_OK]
                        except (ConfigParser.NoSectionError, IOError):
                            reply = [service] + [section] + [MDP.T_ERROR]
                    else:
                        try:
                            if os.path.isfile(self.store_filename(service)):
                                os.unlink(self.store_filename(service))
                            reply = [service] + [MDP.T_OK]
                        except OSError:
                            reply = [service] + [MDP.T_ERROR]
                else:
                    reply = [MDP.T_NOTIMPLEMENTED]
            except IndexError:
                MDP.logger.exception("TITANIC - Exception in store")
                reply = [MDP.T_ERROR]

if __name__ == '__main__': # pragma: no cover
    mytitanic = Titanic()  # pragma: no cover
    mytitanic.run()        # pragma: no cover
