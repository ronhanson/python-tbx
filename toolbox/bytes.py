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
from struct import pack, unpack
from datetime import timedelta
from array import array


def int_2_ber(siz):
    byte_length = word_2_byte_array(siz + 4)
    return array('B', (0x83, byte_length[1], byte_length[2], byte_length[3]))


def ber_2_int(ber):
    return byte_array_2_word('\x00' + ber[1:])


def pack_word(word):
    return pack('>I', word)


def byte_array_2_word(byte_array):
    """
    Converts a 4 byte array (either as a string or an array) to a 32-bit unsigned int; assumes big-endian form

    Test with misc. string byte arrays:
        >>> byte_array_2_word('\\x00\\x00\\x00\\x01')
        1
        >>> byte_array_2_word('\\x00\\x00\\x01\\x01')
        257
        >>> byte_array_2_word('\\x00\\x01\\x01\\x01')
        65793

    Test with misc. array byte arrays:
        >>> byte_array_2_word(array('B', (0, 0, 0, 1)))
        1
        >>> byte_array_2_word(array('B', (0, 0, 1, 1)))
        257
        >>> byte_array_2_word(array('B', (0, 1, 1, 1)))
        65793

    Test incorrect type error:
        >>> byte_array_2_word(123)
        Traceback (most recent call last):
        ...
        TypeError
    """
    if isinstance(byte_array, str):
        return unpack('>I', pack('>BBBB', ord(byte_array[0]), ord(byte_array[1]), ord(byte_array[2]), ord(byte_array[3])))[0]
    elif hasattr(byte_array, "__getitem__"): #isinstance(byte_array, (array, list, tuple)):
        return unpack('>I', pack('>BBBB', byte_array[0], byte_array[1], byte_array[2], byte_array[3]))[0]
    else:
        raise TypeError


def byte_array_2_little_endian_word(byte_array):
    if isinstance(byte_array, str):
        return unpack('<I', pack('<BBBB', ord(byte_array[0]), ord(byte_array[1]), ord(byte_array[2]), ord(byte_array[3])))[0]
    elif hasattr(byte_array, "__getitem__"): #isinstance(byte_array, (array, list, tuple)):
        return unpack('<I', pack('<BBBB', byte_array[0], byte_array[1], byte_array[2], byte_array[3]))[0]
    else:
        raise TypeError


def byte_array_2_short(byte_array):
    if isinstance(byte_array, str):
        return unpack('>h', pack('>BB', ord(byte_array[0]), ord(byte_array[1])))[0]
    elif hasattr(byte_array, "__getitem__"): #isinstance(byte_array, (array, list, tuple)):
        return unpack('>h', pack('>BB', byte_array[0], byte_array[1]))[0]
    else:
        raise TypeError


def byte_array_2_long(byte_array):
    if isinstance(byte_array, str):
        return unpack('>Q', pack('>BBBBBBBB', ord(byte_array[0]), ord(byte_array[1]),
            ord(byte_array[2]), ord(byte_array[3]) , ord(byte_array[4]),
            ord(byte_array[5]), ord(byte_array[6]), ord(byte_array[7])))[0]
    elif hasattr(byte_array, "__getitem__"):
        return unpack('>Q', pack('>BBBBBBBB', byte_array[0], byte_array[1], byte_array[2],
            byte_array[3], byte_array[4], byte_array[5], byte_array[6], byte_array[7]))[0]
    else:
        raise TypeError


def byte_array_2_little_endian_long(byte_array):
    if isinstance(byte_array, str):
        return unpack('<Q', pack('<BBBBBBBB', ord(byte_array[0]), ord(byte_array[1]),
            ord(byte_array[2]), ord(byte_array[3]) , ord(byte_array[4]), ord(byte_array[5]),
            ord(byte_array[6]), ord(byte_array[7])))[0]
    elif hasattr(byte_array, "__getitem__"):
        return unpack('<Q', pack('<BBBBBBBB', byte_array[0], byte_array[1], byte_array[2],
            byte_array[3], byte_array[4], byte_array[5], byte_array[6], byte_array[7]))[0]
    else:
        raise TypeError


def word_2_byte_array(word):
    """
    Converts a 32-bit int to a byte array in big-endian form

    Test misc. 32-bit ints:
        >>> word_2_byte_array(1)
        (0, 0, 0, 1)
        >>> word_2_byte_array(257)
        (0, 0, 1, 1)
        >>> word_2_byte_array(65793)
        (0, 1, 1, 1)
    """
    return unpack('>BBBB', pack('>I', word))

def long_2_byte_array(longLong):
    """
    Converts a 64-bit long to a byte array in big-endian form
    """
    return unpack('>BBBBBBBB', pack('>Q', longLong))

def long_2_byte_array_little_endian(longLong):
    """
    Converts a 64-bit long to a byte array in big-endian form
    """
    return unpack('<BBBBBBBB', pack('<Q', longLong))

def short_2_byte_array(short):
    return unpack('>BB', pack('>H', short))

def uuid_bytes_2_canonical(some_bytes):
    """
    Creates a canonical representation of a byte-represented UUID

    Test a canonical UUID:
        >>> uuid_bytes_2_canonical('\\xf8\\x1dO\\xae}\\xec\\x11\\xd0\\xa7e\\x00\\xa0\\xc9\\x1ek\\xf6')
        'f81d4fae-7dec-11d0-a765-00a0c91e6bf6'
    """
    uuid = ''
    for byte in some_bytes[:4]:
        h = hex(ord(byte))[2:]
        if len(h) == 1:
            uuid += '0' + h
        else:
            uuid += h
    uuid += '-'
    for byte in some_bytes[4:6]:
        h = hex(ord(byte))[2:]
        if len(h) == 1:
            uuid += '0' + h
        else:
            uuid += h
    uuid += '-'
    for byte in some_bytes[6:8]:
        h = hex(ord(byte))[2:]
        if len(h) == 1:
            uuid += '0' + h
        else:
            uuid += h
    uuid += '-'
    for byte in some_bytes[8:10]:
        h = hex(ord(byte))[2:]
        if len(h) == 1:
            uuid += '0' + h
        else:
            uuid += h
    uuid += '-'
    for byte in some_bytes[10:16]:
        h = hex(ord(byte))[2:]
        if len(h) == 1:
            uuid += '0' + h
        else:
            uuid += h
    return uuid


def uuid_canonical_2_bytes(uuid_str):
    """
    Converts a UUID from its canonical form to an array of 16 bytes

    Test a canonical to bytes (return in string form to compare to uuid_bytes_2_canonical test):
        >>> uuid_canonical_2_bytes('f81d4fae-7dec-11d0-a765-00a0c91e6bf6').tostring()
        '\\xf8\\x1dO\\xae}\\xec\\x11\\xd0\\xa7e\\x00\\xa0\\xc9\\x1ek\\xf6'
    """
    if uuid_str == None:
        uuid_str = '00000000000000000000000000000000'
    else:
        uuid_str = uuid_str.replace('-', '')    # Strip all '-'s from the string
    some_bytes = array('B')
    for i in xrange(0, len(uuid_str), 2):
        some_bytes.append(int(uuid_str[i:i + 2], 16))
    return some_bytes

def ip_to_little_endian_word(ip_str):
    """
    Converts a dotted quad notation IP address into
    a word in little endian format

    Returns - word

    Test an IP address:
        >>> ip_to_little_endian_word('192.168.10.50')
        839559360
    """
    return unpack('<L', socket.inet_aton(ip_str))[0]

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
