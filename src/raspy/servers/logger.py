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

import logging

class Logger(Server):
    """
    The logger server

    Will log data, events, ... in files, rrd, ...

    It can be called via the worker  or it can log data in pthe publisher

    From : http://segfault.in/2010/03/python-rrdtool-tutorial/
    From :
    """

    def __init__(self, hostname='localhost', service="logger", broker_ip='127.0.0.1', broker_port=5514):
        """Initialize the server
        """
        Server.__init__(self, hostname, service, broker_ip, broker_port)


if __name__ == '__main__': # pragma: no cover
    mylogger = Logger()     # pragma: no cover
    mylogger.run()           # pragma: no cover

