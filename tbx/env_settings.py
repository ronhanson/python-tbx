#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Environment-Based Settings
:author: Ronan Delacroix

# WARNING : THIS MODULE IS ACTUALLY DEPRECATED AND ABANDONNED...

"""
import os
import sys
from . import code as code
from configobj import ConfigObj, ConfigObjError, flatten_errors
from validate import Validator

script_folder = os.path.abspath(os.path.dirname(sys.modules.get('__main__', sys.modules[__name__]).__file__))

environment = "development" #by default
try:
    with open(os.path.join(script_folder, 'environment.txt'), 'r') as f:
        environment = f.readline().strip()
except (ConfigObjError, IOError) as e:
    pass
    #print('Could not read environment from "environment.txt": %s' % e)
    #exit(1)

config_path = os.path.join(script_folder, "settings_%s.ini" % environment)

conf = {}
try:
    conf = ConfigObj(
        config_path,
        file_error=True,
        unrepr=True,
        raise_errors=False,
        list_values=True,
        configspec=os.path.join(script_folder, 'settings.spec')
    )
    validator = Validator()
    results = conf.validate(validator, preserve_errors=True)
    if not results:
        for (section_list, key, _) in flatten_errors(conf, results):
            if key is not None:
                print("The '%s' key in the section '%s' failed validation" % (key, ', '.join(section_list)))
            else:
                print("The following section was missing: %s " % ', '.join(section_list))

except (ConfigObjError, IOError) as e:
    pass
    #print('Environment invalid. Could not read config from "%s": %s, %s' % (config_path, e, e.__dict__))

config = code.AttributeDict(conf)
if config.DEBUG:
    print("Working Folder : " + script_folder)

this_module = sys.modules[__name__]
for k, v in config.iteritems():
    if isinstance(v, dict):
        v = code.AttributeDict(v)
    setattr(this_module, k, v)
