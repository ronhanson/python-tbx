#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Bytes Utils
:author: Ronan Delacroix

Generic byte functions.
Should work in Python 3 and 2
"""
import socket
import struct
import six
import uuid
import binascii
from . import network


def bytes_to_int(byte_array, big_endian=True, signed=False):
    """
    Converts a byte array to an integer.
    """
    if six.PY3:
        order = 'little'
        if big_endian:
            order = 'big'
        return int.from_bytes(byte_array, byteorder=order, signed=signed)
    else:
        length = len(byte_array)
        if length == 1:
            code = 'B'
        elif length == 2:
            code = 'H'
        elif length == 4:
            code = 'L'
        elif length == 8:
            code = 'Q'
        else:
            raise Exception("bytes_to_int : length of byte_array should be 1, 2, 4, or 8")
        if big_endian:
            code = '>'+code
        else:
            code = '<'+code

        if signed:
            code = code.lower()
        return struct.unpack(code, byte_array)[0]


def bytes_to_uuid(byte_array):
    """
    Converts a byte array (should be 16 bytes length) to a uuid object.
    :param byte_array: the byte array to convert
    :return: uuid object
    """
    return uuid.UUID(bytes=bytes(byte_array))


def uuid_to_bytes(id):
    """
    Convert a uuid to a 16-byte string (containing the six integer fields in big-endian byte order)
    :param id: uuid string or object
    :return: a byte array
    """
    return uuid.UUID(id).bytes


def bytes_to_uuid_list(byte_array):
    """
    Converts a byte array to a list of uuids. Cuts the byte array by packets of 16 bytes and parse each as uuid.
    :param byte_array: a byte array of length n*16
    :return: a list of uuid objects
    """
    result = []
    for i in range(0, len(byte_array)//16):
        result.append(uuid.UUID(bytes=bytes(byte_array[i*16:i*16+16])))
    return result


def batch(byte_array, funcs):
    """
    Converts a batch to a list of values.
    :param byte_array: a byte array of length n*item_length + 8
    :return: a list of uuid objects
    """
    result = []
    length = bytes_to_int(byte_array[0:4])
    item_size = bytes_to_int(byte_array[4:8])
    for i in range(0, length):
        chunk = byte_array[8+i*item_size:8+(i+1)*item_size]
        for f in funcs:
            f(chunk)
    return result


def bytes_to_text(byte_array, encoding='UTF-8'):
    """
    Decode a byte array to a string following the given encoding.
    :param byte_array: Byte array to decode.
    :param encoding: String encoding (default UTF-8)
    :return: a decoded string
    """
    return bytes(byte_array).decode(encoding)


def text_to_bytes(text, encoding='UTF-8', size=None):
    """
    Encode some text or string to a byte array
    :param text: text to encode to bytes
    :param encoding: optional encoding of the passed string. default to utf-8.
    :param size: optional, if given the text will be padded with 0x00 to the right size
    :return: a bytes object
    """
    res = str(text).encode(encoding)
    if size:
        res = res.rjust(size, b'\x00')
    return res


def bytes_to_hex(byte_array):
    """
    Converts byte to hex string...
    :param byte_array: byte array to return as hex
    :return: an ascii string, hex representation of the byte array
    """
    return binascii.hexlify(bytes(byte_array)).decode('ascii')


def int_to_bytes(val, bit=32, signed=False, big_endian=True):
    """
    Converts an int to a byte array (bytes).
    :param val: value to encode
    :param bit: bit length of the integer to encode
    :param signed: encode as unsigned int if false
    :param big_endian: encode with big or little endian
    :return:
    """
    val = int(val) #ensure it is an int

    if six.PY3:
        order = 'little'
        if big_endian:
            order = 'big'
        return val.to_bytes(length=bit//8, byteorder=order, signed=signed)

    if bit == 8:
        code = 'B'
    elif bit == 16:
        code = 'H'
    elif bit == 32:
        code = 'I'
    elif bit == 64:
        code = 'Q'
    else:
        raise Exception("int_to_bytes : size parameter value should be 8, 16, 32, or 64")

    if big_endian:
        code = '>'+code
    else:
        code = '<'+code

    if signed or val < 0:
        code = code.lower()

    return struct.pack(code, val)


def ip_to_bytes(ip_str, big_endian=True):
    """
    Converts an IP given as a string to a byte sequence
    """
    if big_endian:
        code = '>L'
    else:
        code = '<L'
    return bytes(struct.unpack(code, socket.inet_aton(ip_str))[0])


def decode_ber(ber):
    """
    Decodes a ber length byte array into an integer
    return: (length, bytes_read) - a tuple of values
    """
    ber = bytearray(ber)
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
    Reads a ber length from a socket.
    Reads first byte to read the ber length first, then read the actual data.
    return: (length, bytes_read, data) - a tuple of values
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


def encode_ber(value, ber_length=0):
    """
    Encodes an integer to ber length
    You can set the ber_length manually.
    return: bitearray object
    """
    if not ber_length:
        if value < 127: # 1 byte case
            return bytearray([value])
        ber_length = 1
        while value >= pow(2, 8*ber_length):
            ber_length += 1
        ber_length += 1


    ber = bytearray(ber_length)
    ber[0] = 127 + ber_length #ber length byte
    for i in range(1, ber_length):
        ber[i] = (value >> (8 * (ber_length - 1 - i))) & 255
    return ber

