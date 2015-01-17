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
import SocketServer
import BaseHTTPServer
import SimpleHTTPServer
import gzip
import raspy.common.MDP as MDP
from raspy.common.server import Server
from raspy.common.mdwrkapi import MajorDomoWorker

import logging

class CompressedFile(object):
    """A compressed log file
    """
    def __init__(self, logfile='log1.log', mode='a+', compresslevel=1):
        """Initialize the server
        """
        pass

    def open(self):
        """
        """
        pass

    def close(self):
        """
        """
        pass

    def log(self, level, message):
        """
        """
        pass

    def rotate(self):
        """
        """
        pass

    def readlines(self, start=0, end=-1, limit=20):
        """Return lines from a file

        """
        res = []
        return res

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    """The request handler
    """
    def handle(self):
        data = "Ok"
        cur_thread = threading.current_thread()
        response = "{}: {}".format(cur_thread.name, data)
        self.request.sendall(response)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """The simple HTTP server
    Be careful ... no security at all
    """
    pass


class Logger(Server):
    """
    The logger server

    Will log data, events, ... in files, rrd, ...
    It can be called via the worker  or it can log data in pthe publisher

    What to log :

     - numeric : data for a device. We must be abble to aggregate data from multiple devices ( ie a graph for inside/outqide temperature)
     - text events : door open, notification, server log, ...
     - images for webcam ??? large amount of data, not a good idea to tranport it using zmq. A ftp client which sync to a server.

    How to log :

     - RRDtool:

      - http://segfault.in/2010/03/python-rrdtool-tutorial/
      - we must use rrcached : https://github.com/pbanaszkiewicz/python-rrdtool/blob/master/rrdtool-1.4.7/etc/rrdcached-init

     - Compressed text files :
      - stream compression : http://pymotw.com/2/bz2/index.html#module-bz2
      - file rotation
      - http://pymotw.com/2/gzip/

    How to distribute graph, text logs

     - via a local directory. The http server will server them to the final client => raspyweb and the logger must be launch on the same server : NO
     - via sync : add a ftp server service (in python or a a package : vsftp with xinet or in standalone) : Use a lot of bandwith, How to transfer log : every minutes ??? : NO
     - add a simpleHttp server here which will serve file  to the proxy (apache ? so that it will cache them).

    """

    def __init__(self, hostname='localhost', service="logger", broker_ip='127.0.0.1', broker_port=5514):
        """Initialize the server
        """
        Server.__init__(self, hostname, service, broker_ip, broker_port)
        self.worker_logger_thread = threading.Thread(target=self.worker_logger)
        self.worker_logger_thread.daemon = True
        self._active_threads.append(self.worker_logger_thread)
        self.http_server = ThreadedTCPServer(('', broker_port+4), ThreadedTCPRequestHandler)
        self.http_thread = threading.Thread(target=self.http_server.serve_forever)
        self.http_thread.daemon = True
        self._active_threads.append(self.http_thread)

    def worker_logger(self):
        """Create a worker to handle logger requests
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

    def shutdown(self):
        """Shutdown executive.
        """
        self.http_server.shutdown()
        Server.shutdown(self)
        self.http_server = None

if __name__ == '__main__': # pragma: no cover
    mylogger = Logger()     # pragma: no cover
    mylogger.run()           # pragma: no cover

