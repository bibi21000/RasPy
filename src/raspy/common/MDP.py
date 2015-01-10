# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger("MDP")

"""Majordomo Protocol definitions"""
#  This is the version of MDP/Client we implement
C_CLIENT = "MDPC01"

#  This is the version of MDP/Worker we implement
W_WORKER = "MDPW01"

#  MDP/Server commands, as strings
W_READY = "\001"
W_REQUEST = "\002"
W_REPLY = "\003"
W_HEARTBEAT = "\004"
W_DISCONNECT = "\005"

commands = [None, "READY", "REQUEST", "REPLY", "HEARTBEAT", "DISCONNECT"]

T_OK = '200'
T_PENDING = '300'
T_UNKNOWN = '400'
T_NOTFOUND = '404'
T_ERROR = '500'
T_NOTIMPLEMENTED = '501'

def routing_key(hostname, service):
    return "%s.%s"%(hostname, service)

class GenericError(Exception):
    """Generic exception
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.__repr(value)
    def __repr__(self):
        return "Generic Error :" + repr(self.value)

class ClientError(GenericError):
    """Client side exception
    """
    def __repr__(self):
        return "Client Error :" + repr(self.value)

class ServerError(GenericError):
    """Server side exception
    """
    def __repr__(self):
        return "Server Error :" + repr(self.value)
