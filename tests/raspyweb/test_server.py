#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Unittests for the Onewire Server.

See http://werkzeug.pocoo.org/docs/0.9/test/
See http://werkzeug.pocoo.org/docs/0.9/wrappers/

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

    You should have received a copy of the NU General Public License
    along with RasPy. If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'

import sys
import time
import logging

from tests.raspyweb.common import FlaskTestCase

from raspyweb.app import app

class FlaskServerTest(FlaskTestCase):

    def test_000_server_start(self):
        rv = self.app.get('/')
        self.assertTrue('RasPyWeb' in rv.data)

    def test_001_server_is_running(self):
        #self.wipTest()
        rv = self.app.get('/')
        self.assertEqual(rv.status,'200 OK')

if __name__ == '__main__':
    sys.argv.append('-v')
    unittest.main()
