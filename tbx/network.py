#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Network Utils
:author: Ronan Delacroix
"""

import socket
import logging


PACKET_SIZE = 4096


def get_local_ip_address(target):
    """
    Get the local ip address to access one specific target.
    """
    ip_adr = ''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((target, 8000))
        ip_adr = s.getsockname()[0]
        s.close()
    except:
        pass

    return ip_adr


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
        except socket.error as ex:
            logging.error('Exception while connecting socket on %s:%s - Error %s' % (self.host, self.port, ex))
            raise
        except Exception as ex:
            logging.exception('Exception while connecting socket on %s:%s - Error %s' % (self.host, self.port, ex))
            raise

    def send_by_packet(self, data):
        """
        Send data by packet on socket
        """
        total_sent = 0
        while total_sent < PACKET_SIZE:
            sent = self.sock.send(data[total_sent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            total_sent += sent
        return total_sent

    def sendall(self, data):
        """
        Send all data on socket
        """
        sent = self.sock.sendall(data)
        return sent

    def send(self, data):
        """
        Send data on socket
        """
        return self.sendall(data)

    def receive(self, siz):
        """
        Receive a known length of bytes from a socket
        """
        result = bytearray()
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
        self.sock = None

