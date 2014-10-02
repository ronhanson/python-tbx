#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Network Utils
:author: Ronan Delacroix
"""

import socket


MSGLEN = 1024


def get_local_ip_address(target):
    """
    Get the local ip address to access one specific target.
    """
    ipaddr = ''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((target, 8000))
        ipaddr = s.getsockname()[0]
        s.close()
    except:
        pass

    return ipaddr


class SocketClient:
    """
    SocketClient class.
    """

    def __init__(self, host, port, timeout=30, sock=None):
        """
        Creates the socket object, but still does not connect it.
        """
        self.host = host
        self.port = int(port)
        if sock is None:
            self.sock = socket.socket() #socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
        else:
            self.sock = sock

    def connect(self):
        """
        Connect socket to server
        """
        try:
            self.sock.connect((self.host, self.port))
            return self.sock
        except socket.error, ex:
            raise Exception('Unable to connect socket on %s:%s - Error %s' % (self.host, self.port, ex))
        except Exception, ex:
            raise Exception('Unable to connect socket on %s:%s - Error %s' % (self.host, self.port, ex))

#    def send(self, data):
#        totalsent = 0
#        while totalsent < MSGLEN:
#            sent = self.sock.send(data[totalsent:])
#            if sent == 0:
#                raise RuntimeError("socket connection broken")
#            totalsent = totalsent + sent
#        return totalsent

    def send(self, data):
        """
        Send data on socket
        """
        sent = self.sock.sendall(data)
        return sent

    def receive(self, siz):
        """
        Receive a known length of bytes from a socket
        """
        result = ''
        data = 'x'
        while len(data) > 0:
            data = self.sock.recv(siz - len(result))
            result += data
            if len(result) == siz:
                return result
            if len(result) > siz:
                raise Exception('Received more bytes than expected')
        raise Exception('Error receiving data. %d bytes received'%len(result))

    def close(self):
        self.sock.close()
        self.sock=None

