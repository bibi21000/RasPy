#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

kvsimple - simple key-value message class for example applications

Author: Min RK <benjaminrk@gmail.com>

From : http://zguide.zeromq.org/py:kvsimple
"""

import struct # for packing integers
import sys

import zmq

class KVMsg(object):
    """
    Message is formatted on wire as 3 frames:
        - frame 0: key (0MQ string)
        - frame 1: sequence (8 bytes, network order)
        - frame 2: body (blob)
    """
    key = None # key (string)
    sequence = 0 # int
    body = None # blob

    def __init__(self, sequence, key=None, body=None):
        """Initialize the Key/value Message
        """
        assert isinstance(sequence, int)
        self.sequence = sequence
        self.key = key
        self.body = body

    def store(self, dikt):
        """Store me in a dict if I have anything to store"""
        # this seems weird to check, but it's what the C example does
        if self.key is not None and self.body is not None:
            dikt[self.key] = self

    def send(self, socket):
        """Send key-value message to socket; any empty frames are sent as such."""
        key = '' if self.key is None else self.key
        seq_s = struct.pack('!l', self.sequence)
        body = '' if self.body is None else self.body
        socket.send_multipart([key, seq_s, body])

    @classmethod
    def recv(cls, socket):
        """Reads key-value message from socket, returns new kvmsg instance."""
        key, seq_s, body = socket.recv_multipart()
        key = key if key else None
        seq = struct.unpack('!l', seq_s)[0]
        body = body if body else None
        return cls(seq, key=key, body=body)

    def dump(self):
        """Dump me to a string"
        """
        if self.body is None:
            size = 0
            data = 'NULL'
        else:
            size = len(self.body)
            data = repr(self.body)
        return "[seq:{seq}][key:{key}][size:{size}] {data}".format(
            seq=self.sequence,
            key=self.key,
            size=size,
            data=data,
        )
