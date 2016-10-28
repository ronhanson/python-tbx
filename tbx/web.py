#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Text Utils
:author: Ronan Delacroix
"""
import re
import requests
import os
import os.path


def download(url, folder, force_filename=None, verify=False):
    folder = os.path.abspath(folder)

    if url.startswith('//'):
        url = 'http:'+url
    if force_filename:
        file_name = force_filename
    else:
        file_name = url.split('/')[-1]
        file_name = file_name.split('?')[0]
        file_name = file_name.split('#')[0]

    r = requests.get(url, verify=verify)

    d = r.headers.get('content-disposition', '')
    request_fname = re.findall("filename=(.+)", d)
    if request_fname and not force_filename:
        file_name = request_fname

    path = os.path.abspath(os.path.join(folder, file_name))
    if folder not in path:
        raise Exception("Problem with filepath being not contained in targeted folder (security issue) - %s / %s" %
                        (folder, path))

    with open(path, "wb") as img_file:
        img_file.write(r.content)

    return path