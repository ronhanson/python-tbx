#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
File Utils
:author: Ronan Delacroix
"""

import os
import sys
from . import sequential

ZIP_EXTENSIONS = ['bz2', 'gz', 'xz', 'bz2', 'rar', 'gz', 'tar', 'tbz2', 'tgz', 'zip', 'Z', '7z', 'xz', 'ace']


def full_file_list(scan_path):
    """
    Returns a list of all files in a folder and its subfolders (only files).
    """
    file_list = []
    path = os.path.abspath(scan_path)
    for root, dirs, files in os.walk(path):
        if len(files) != 0 and not '.svn' in root and not '.git' in root:
            for f in files:
                file_list.append(os.path.join(root, f))
    return file_list


def list_files(scan_path, contains=None):
    """
    Returns a list of all files in a folder, without subfolders (only files).
    """
    file_list = []
    path = os.path.abspath(scan_path)
    for f in sorted(os.listdir(path)):
        if contains and f.find(contains) < 0:
            continue
        filepath = os.path.join(path, f)
        if os.path.isfile(filepath):
            file_list.append(filepath)
    return file_list


def full_file_list_with_sequence(scan_path):
    """
    Returns a list of all files in a folder and its subfolders (only files).
    """
    
    file_list = []
    path = os.path.abspath(scan_path)
    
    for root, dirs, files in os.walk(path):
        if len(files) != 0 and not '.svn' in root and not '.git' in root:
            try:
                sc = sequential.SequentialFolder(str(root))
                if sc.sequence:
                    file_list.append(sc)
                    continue
            except Exception as e:
                pass
                
            for f in files:
                file_list.append(os.path.join(root, f))
    return file_list


def readlinkabs(l):
    """
    Return an absolute path for the destination 
    of a symlink
    """
    assert (os.path.islink(l))
    p = os.readlink(l)
    if os.path.isabs(p):
        return os.path.abspath(p)
    return os.path.abspath(os.path.join(os.path.dirname(l), p))


def unzip(filepath, output_path):
    """
    Unzip an archive file
    """
    filename = os.path.split(filepath)[1]
    (name, extension) = os.path.splitext(filename)
    extension = extension[1:].lower()
    extension2 = os.path.splitext(name)[1][1:].lower()

    if extension not in ZIP_EXTENSIONS:
        raise Exception("Impossible to extract archive file %s" % filepath)

    extract_command = "unzip"
    output_args = "-d"
    if extension == 'bz2' and extension2 == 'tar':
        extract_command = "tar -xjf"
        output_args = "-C"
    elif extension == 'gz' and extension2 == 'tar':
        extract_command = "tar -xzf"
        output_args = "-C"
    elif extension == 'xz' and extension2 == 'tar':
        extract_command = "tar -xJf"
        output_args = "-C"
    elif extension == 'bz2':
        extract_command = "bunzip2 -dc "
        output_args = ">"
        output_path = os.path.join(output_path, name)
    elif extension == 'rar':
        extract_command = "unrar x"
        output_args = ""
    elif extension == 'gz':
        extract_command = "gunzip"
        output_args = ""
    elif extension == 'tar':
        extract_command = "tar -xf"
        output_args = "-C"
    elif extension == 'tbz2':
        extract_command = "tar -xjf"
        output_args = "-C"
    elif extension == 'tgz':
        extract_command = "tar -xzf"
        output_args = "-C"
    elif extension == 'zip':
        extract_command = "unzip"
        output_args = "-d"
    elif extension == 'Z':
        extract_command = "uncompress"
        output_args = ""
    elif extension == '7z':
        extract_command = "7z x"
        output_args = ""
    elif extension == 'xz':
        extract_command = "unxz"
        output_args = ""
    elif extension == 'ace':
        extract_command = "unace"
        output_args = ""
    elif extension == 'iso':
        extract_command = "7z x"
        output_args = ""
    elif extension == 'arj':
        extract_command = "7z x"
        output_args = ""

    command = """%(extract_command)s "%(filepath)s" %(output_args)s "%(output_folder)s" """
    params = {
        'extract_command': extract_command,
        'filepath': filepath,
        'output_folder': output_path,
        'output_args': output_args,
    }
    result = os.system(command % params)
    return result