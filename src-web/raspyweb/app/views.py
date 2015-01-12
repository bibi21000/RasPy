#!/usr/bin/python
# -*- coding: utf-8 -*-

"""The main views

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

import os,sys
from flask import Flask, render_template, request

@app.route('/')
def home_req():
    res = mdp_request(socket, 'mmi.directory', [], 2.0)
    dirs = res[1].split('|')
    links = []
    for diir in dirs :
        service, numb = diir.split('=')
        links.append(service)
    links.sort()
    return render_template('home.html', links=links, res=res)

@app.route('/replies/<path:path>')
def requests(path):
    ""
    ""
    path = path.encode('ascii', 'ignore')
    subpath = ""
    if path.find('/') != -1 :
        path,subpath = path.split("/")
    if subpath == "" :
        res = mdp_request(socket, b'%s' % path, [b'mmi.directory'], 2.0)
        print res
        if res != None and res[len(res)-1] == '200' :
            print "yeah"
            services = res[2].split('|')
            services.sort()
            topics = res[3].split('|')
            topics.sort()
            mmis = res[4].split('|')
            mmis.sort()
        else :
            services = []
            topics = []
            mmis = []
        return render_template('service.html', services=services, topics=topics, mmis=mmis, res=res, path=path)
    else :
        rtype = request.args.get('type')
        rtype = rtype.encode('ascii', 'ignore')
        res = mdp_request(socket, b'%s' % path, [b'mmi.helper.%s' % rtype, subpath], 2.0)
        print res
        if res != None and res[len(res)-1] == '200' :
            print "yeah"
            services = res[2].split('|')
            services.sort()
            topics = res[3].split('|')
            topics.sort()
            mmis = res[4].split('|')
            mmis.sort()
        else :
            services = []
            topics = []
            mmis = []
        return render_template('reply.html', services=services, topics=topics, mmis=mmis, res=res, path=path)

