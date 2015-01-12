# -*- coding: utf-8 -*-

"""Unittests for the Onewire Server.

Credits : https://flask-testing.readthedocs.org/en/latest/
"""


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
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'

import sys, os
import time
import logging
import json as mjson

from flask import Flask

from raspyweb.app import app

from tests.common import SLEEP
from tests.common import TestRasPy

class FlaskTestCase(TestRasPy):

    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        pass
