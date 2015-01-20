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

from flask import Blueprint, request, render_template, flash, g, session, redirect, url_for
import json as mjson
from raspyweb.app import app
from raspy.common.mdcliapi import TitanicClient

mod = Blueprint('ajax', __name__, url_prefix='/ajax')

@mod.route('/')
def home():
    data = {}
    return mjson.dumps(data)

@mod.route('/mmi/')
def mmi():
    data = {}
    data['iTotalRecords'] = 2
    data['sEcho'] = 1
    data['iTotalDisplayRecords'] = 2

    #aaData = []
    #users=models.Users.query.with_entities(
    #    models.Users.id, models.Users.username,
    #    models.Users.email).order_by(models.Users.username).all()
    #for user in users:
    #    aaData.append([user.id, user.username, user.email, 'Modify'])

    #data['aaData']=aaData
    return mjson.dumps(data)

@mod.route('/devices/')
def devices():
    data = {}
    data['iTotalRecords'] = 2
    data['sEcho'] = 1
    data['iTotalDisplayRecords'] = 2

    #aaData = []
    #users=models.Users.query.with_entities(
    #    models.Users.id, models.Users.username,
    #    models.Users.email).order_by(models.Users.username).all()
    #for user in users:
    #    aaData.append([user.id, user.username, user.email, 'Modify'])

    #data['aaData']=aaData
    return mjson.dumps(data)
