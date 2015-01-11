#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup file of RasPyWeb
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

from os import name as os_name
#from distutils.core import setup
from setuptools import setup, find_packages
from distutils.extension import Extension
#from Cython.Distutils import build_ext
from platform import system as platform_system
import glob
import os
import sys

DEBIAN_PACKAGE = False
filtered_args = []

for arg in sys.argv:
    if arg == "--debian-package":
        DEBIAN_PACKAGE = True
    else:
        filtered_args.append(arg)
sys.argv = filtered_args

def _getDirs(base):
    return [x for x in glob.iglob(os.path.join( base, '*')) if os.path.isdir(x) ]

def data_files_config(target, source, pattern):
    ret = list()
    tup = list()
    tup.append(target)
    tup.append(glob.glob(os.path.join(source,pattern)))
    #print tup
    ret.append(tup)
    dirs = _getDirs(source)
    if len(dirs):
        for d in dirs:
            #print os.path.abspath(d)
            rd = d.replace(source+os.sep, "", 1)
            #print target,rd
            #print os.path.join(target,rd)
            ret.extend(data_files_config(os.path.join(target,rd), \
                os.path.join(source,rd), pattern))
    return ret

setup(
    name = 'raspyweb',
    author='Sébastien GALLET aka bibi2100 <bibi21000@gmail.com>',
    author_email='bibi21000@gmail.com',
    url='http://bibi21000.gallet.info/',
    version = '0.0.1',
    data_files =[],
    packages = find_packages('src-http', exclude=["scripts"]),
    package_dir = { '': 'src-http' },
    install_requires=[
                     'raspy >= 0.0.1',
                     'lockfile >= 0.10',
                     'docutils >= 0.11',
                     'pyzmq == 14.4.1',
                     'Flask == 0.10.1',
                     'Flask-Testing == 0.4.2',
                     'Flask-WTF == 0.9.5',
                     'Babel >= 1.0',
                     'Flask-Babel == 0.9',
                     'Jinja2 >= 2.5.5',
                     'nose-html == 1.1',
                     'nose-progressive == 1.5.1',
                     'nose >= 1.3.1',
                     'coverage >= 3.7.1',
                     'python-daemon >= 2.0.0',
                    ]
)
