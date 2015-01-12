# -*- coding: utf-8 -*-

"""RasPyWeb app module.
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

import os
import sys

from flask import Flask, render_template
from flask_fanstatic import Fanstatic
#from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('raspyweb.config.DevelopmentConfig')
fanstatic = Fanstatic(app)

@app.route('/')
def home_req():
    #res = mdp_request(socket, 'mmi.directory', [], 2.0)
    #dirs = res[1].split('|')
    res = '200'
    dirs = []
    links = []
    #for diir in dirs :
    #    service, numb = diir.split('=')
    #    links.append(service)
    #links.sort()
    return render_template('home.html', links=links, res=res)

#import raspyweb.app.views

#db = SQLAlchemy(app)

########################
# Configure Secret Key #
########################
def install_secret_key(app, filename='secret_key'):
    """Configure the SECRET_KEY from a file
    in the instance directory.

    If the file does not exist, print instructions
    to create it from a shell with a random key,
    then exit.
    """
    filename = os.path.join(app.instance_path, filename)

    try:
        app.config['SECRET_KEY'] = open(filename, 'rb').read()
    except IOError:
        print('Error: No secret key. Create it with:')
        full_path = os.path.dirname(filename)
        if not os.path.isdir(full_path):
            print('mkdir -p {filename}'.format(filename=full_path))
        print('head -c 24 /dev/urandom > {filename}'.format(filename=filename))
        sys.exit(1)

if not app.config['DEBUG']:
    install_secret_key(app)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

#from app.users.views import mod as usersModule
#app.register_blueprint(usersModule)

# Later on you'll import the other blueprints the same way:
#from app.comments.views import mod as commentsModule
#from app.posts.views import mod as postsModule
#app.register_blueprint(commentsModule)
#app.register_blueprint(postsModule)

#try:
#    __import__('pkg_resources').declare_namespace(__name__)
#except:
#    # bootstrapping
#    pass
#
#from flask import Flask
#import zmq
#
#app = Flask(__name__)
#context = zmq.Context()
#endpoint_cmd = "tcp://*:14015"
#socket = context.socket(zmq.REQ)
#socket.setsockopt(zmq.LINGER, 0)
#socket.connect(endpoint_cmd)
#
#import views

