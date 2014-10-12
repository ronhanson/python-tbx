#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Bytes Utils
:author: Ronan Delacroix

Following generic byte functions are based on work at previous work.
Should be redone with Python 3 byte type...
"""

import calendar
import datetime
import socket
import time
import logging
import re
import struct
from datetime import timedelta
import six
import uuid
import binascii
from . import network


def bytes_to_int(byte_array, bigendian=True):

    if six.PY3:
        order = 'little'
        if bigendian:
            order = 'big'
        return int.from_bytes(byte_array, byteorder=order)
    else:
        raise Exception("TODO PYTHON 2")


def bytes_to_uuid(byte_array):
    return uuid.UUID(bytes=bytes(byte_array))


def uuid_to_bytes(id):
    return uuid.UUID(id).bytes


def bytes_to_uuid_list(byte_array):
    result = []
    for i in range(0, len(byte_array)//16):
        result.append(uuid.UUID(bytes=bytes(byte_array[i*16:i*16+16])))
    return result


def bytes_to_text(byte_array, encoding='UTF-8'):
    return bytes(byte_array).decode(encoding)


def bytes_to_hex(byte_array):
    return binascii.hexlify(byte_array).decode('ascii')


def int_to_bytes(val, size=4, signed=False, bigendian=True):
    if size == 1:
        code = 'B'
    elif size == 2:
        code = 'H'
    elif size == 4:
        code = 'I'
    elif size == 8:
        code = 'Q'
    else:
        raise Exception("int_to_bytes : size parameter value should be 1, 2, 4, or 8")

    if bigendian:
        code = '>'+code
    else:
        code = '<'+code

    if signed or val < 0:
        code = code.lower()

    return struct.pack(code, val)


def ip_to_bytes(ip_str, bigendian=True):
    """
    Converts an IP given as a string to a byte sequence
    """
    if bigendian:
        code = '>L'
    else:
        code = '<L'
    return bytes(struct.unpack(code, socket.inet_aton(ip_str))[0])


def ip_to_little_endian_word(ip_str, bigendian=False):
    """
    Converts an IP given as a string to a byte sequence
    """
    if bigendian:
        code = '>L'
    else:
        code = '<L'
    return bytes(struct.unpack(code, socket.inet_aton(ip_str))[0])


def int_to_time(totalseconds):
    """
    Given a number of seconds,  this method returns a string
    that breaks it down into hours/minutes seconds in the format
    of hh:mm:ss

    Returns - string hh:mm:ss

    Test a seconds value:
        >>> int_to_time(5782)
        '01:36:22'
    """
    try:
        totalseconds = int(totalseconds)
    except (ValueError,TypeError):
        totalseconds = 0
    totalminuts, seconds = divmod(totalseconds, 60)
    hours, minutes = divmod(totalminuts, 60)
    return "%s:%s:%s" % (str(hours).zfill(2), str(minutes).zfill(2), str(seconds).zfill(2))

def date_string_to_utc(local_datetime_string):
    """
    Attempts to convert a  local date time string string into a UTC Timestamp
    (the number of seconds since 1/1/1970)

        - local_datetime_string      a string containing a date/time in one of the
                                     following two formats:
                                                            yyyy-mm-dd hh:mm:ss
                                                            yyyy-mm-dd hh:mm

    Test a date string:
        >>> date_string_to_utc('2009-10-22 22:31:15')
        1256247075
        >>> date_string_to_utc('1976-04-03 11:23')
        197374980
    """
    local_datetime_string = str(local_datetime_string)
    time_offset = 0 # daylight savings offset
    if time.daylight and  time.localtime().tm_isdst:
        time_offset = timedelta(seconds=time.altzone)  # daylight savings offset
    else:
        time_offset = timedelta(seconds=time.timezone)
    try:
        datetime_object = datetime.datetime.strptime('%s UTC' % local_datetime_string, '%Y-%m-%d %H:%M:%S %Z')
    except:
        try:
            datetime_object = datetime.datetime.strptime('%s UTC' % local_datetime_string, '%Y-%m-%d %H:%M %Z')
        except:
            #invalid date time string
            logging.error('date_string_to_utc(): invalid format for datetime string: %s' % local_datetime_string)
            return 0
    # adjust for local time/DST
    datetime_object += time_offset
    tuple = datetime_object.timetuple()
    return calendar.timegm(tuple)


def get_time_from_string(timestring):
    """
    Get a time from a formatted date/time string

    Test date/time string:
        >>> get_time_from_string('2009-10-22 22:31:15')
        1256250675
        >>> get_time_from_string('1976-04-03')
        197337600
    """
    # using calendar.timegm because mktime returns localtime, not UTC
    if re.match('^\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}$', timestring):
        return calendar.timegm(time.strptime(timestring, '%Y-%m-%d %H:%M:%S'))
    elif re.match('^\d{4}-\d{1,2}-\d{1,2}?$', timestring):
        return calendar.timegm(time.strptime(timestring + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
    else:
        return 0



def convert_bytearray(func):
    """
    Decorator to convert the first parameter to a bytearray
    """
    def wrapped(ber, *args, **kwargs):
        return func(bytearray(ber), *args, **kwargs)
    return wrapped

def return_bytearray(func):
    """
    Decorator to convert a function's returned value to a bytearray
    """
    def wrapped(*args, **kwargs):
        return bytearray(func(*args, **kwargs))
    return wrapped


@convert_bytearray
def decode_ber(ber):
    """
    Decodes an array of bytes to an integer value

    If the first byte in the BER length field does not have the high bit set (0x80),
    then that single byte represents an integer between 0 and 127 and indicates
    the number of Value bytes that immediately follows. If the high bit is set,
    then the lower seven bits indicate how many bytes follow that make up a length field
    """
    length = ber[0]
    bytes_read = 1
    if length > 127:
        bytes_read += length & 127 # Strip off the high bit
        length = 0
        for i in range(1, bytes_read):
            length += ber[i] << (8 * (bytes_read - i - 1))
    return length, bytes_read


def ber_from_socket(s):
    """
    Decodes an array of bytes to an integer value

    If the first byte in the BER length field does not have the high bit set (0x80),
    then that single byte represents an integer between 0 and 127 and indicates
    the number of Value bytes that immediately follows. If the high bit is set,
    then the lower seven bits indicate how many bytes follow that make up a length field
    """
    if isinstance(s, network.SocketClient):
        recv = s.receive
    else:
        recv = s.recv
    data = recv(1)

    length = data[0]
    bytes_read = 1
    if length > 127:
        bytes_read += length & 127 # Strip off the high bit
        data += recv(bytes_read - 1)
        length = 0
        for i in range(1, bytes_read):
            length += data[i] << (8 * (bytes_read - i - 1))
    return length, bytes_read, data


@return_bytearray
def encode_ber(value, ber_length=0):
    """
    Encodes an integer to BER
    The length of the encoded BER value (in bytes) can be optionally specified
    """
    if not ber_length:
        if value < 127:
            return [value]
        elif value < 256:
            ber_length = 2
        elif value < 256 * 256:
            ber_length = 3
        elif value < 256 * 256 * 256:
            ber_length = 4
        else:
            ber_length = 5 # 32 bit unsigned int is the max for this function
    # Add the BER byte length
    ber = [127 + ber_length]
    for i in range(1, ber_length):
        ber.append( (value >> (8 * (ber_length - i - 1))) & 255 )
    return ber




