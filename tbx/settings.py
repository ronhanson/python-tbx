#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Settings Utils
:author: Ronan Delacroix
"""
import os
import platform
from . import code
from configobj import ConfigObj, ConfigObjError, flatten_errors
from validate import Validator


def from_file(name="config", application_name=None, path_template=None):

    if not path_template:
        system_config_path = "/etc/"
        if platform.system() == "Windows":
            system_config_path = "C:/python_app_settings/"
        path_template = system_config_path + "<app_name>"

    script_folder, app_name = code.get_app_name()
    if not application_name:
        application_name = app_name

    path = path_template.replace('<app_name>', application_name).replace('<name>', name)

    config_path = os.path.join(script_folder, name + '.ini')
    if not os.path.isfile(config_path):
        config_path = os.path.join(path, name + '.ini')
    if not os.path.isfile(config_path):
        print("Settings file %s could not be loaded. Exiting." % config_path)
        exit(1)

    spec_path = os.path.join(script_folder, name + '.spec')
    if not os.path.isfile(spec_path):
        spec_path = os.path.join(path, name + '.spec')
    if not os.path.isfile(spec_path):
        spec_path = None

    conf = {}
    try:
        conf = ConfigObj(
            config_path,
            file_error=True,
            unrepr=True,
            raise_errors=False,
            list_values=True,
            configspec=spec_path
        )
        validator = Validator()
        results = conf.validate(validator, preserve_errors=True)
        if not results:
            #weird return value : True if validated, a dict of errors if not. So can't do a simple "if results:".
            for (section_list, key, _) in flatten_errors(conf, results):
                if key is not None:
                    print('The "%s" key in the section "%s" failed validation' % (key, ', '.join(section_list)))
                else:
                    print('The following section was missing:%s ' % ', '.join(section_list))
            exit(1)

    except (ConfigObjError, IOError) as e:
        print('Could not read config from "%s": %s, %s' % (config_path, e, e.__dict__))
        exit(1)

    config = code.AttributeDict(conf)

    return config
