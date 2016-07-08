#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Code Utils
:author: Ronan Delacroix
"""

import sys
import importlib
import os
import re
from operator import itemgetter

__singleton_instances = {}


def static_singleton(*args, **kwargs):
    """
    STATIC Singleton Design Pattern Decorator
    Class is initialized with arguments passed into the decorator.

    :Usage: 
     >>> @static_singleton('yop')
        class Bob(Person):
            def __init__(arg1):
                self.info = arg1
            def says(self):
                print self.info
        b1 = Bob #note that we call it by the name of the class, no instance created here, kind of static linking to an instance
        b2 = Bob #here b1 is the same object as b2
        Bob.says() # it will display 'yop'
    """
    
    def __static_singleton_wrapper(cls):        
        if cls not in __singleton_instances:
            __singleton_instances[cls] = cls(*args, **kwargs)

        return __singleton_instances[cls]

    return __static_singleton_wrapper


class AttributeDict(dict):
    #__getattr__ = dict.__getitem__
    #__setattr__ = dict.__setitem__  #Not using this method as setattr dont work at runtime...

    def __getitem__(self, attr):
        try:
            item = super(AttributeDict, self).__getitem__(attr)
        except KeyError:
            return AttributeDict()
        if isinstance(item, dict) and not isinstance(item, AttributeDict):
            new = AttributeDict(item)
            self.__setitem__(attr, new)
            return new
        return item

    def __getattr__(self, attr):
        if isinstance(self[attr], dict) and not isinstance(self[attr], AttributeDict):
            self[attr] = AttributeDict(self[attr])
            return self[attr]
        if isinstance(self[attr], list):
            res = []
            for f in self[attr]:
                if isinstance(f, dict) and not isinstance(f, AttributeDict):
                    res.append(AttributeDict(f))
                else:
                    res.append(f)
            return res
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


class ProcessException(Exception):
    """
       Process Exception class.
       Displays the PID of the process in its representation.
    """
    def __init__(self, message):
        super(ProcessException, self).__init__(message)

    def __str__(self):
        return self.__repr__()

    def __unicode__(self):
        return self.__repr__()

    def __repr__(self):
        return "%s - Process ID : %s" % (super(ProcessException, self).__str__(), os.getpid())


def get_method_documentation(method):
    """
    This function uses "inspect" to retrieve information about a method.

    Also, if you place comment on the method, method can be docummented with "reStructured Text".

    :param method:    method to describe

    :returns:
        {
            'name'          : <string> - name of the method,
            'friendly_name' : <string> - friendly name of the method,
            'parameters'    : {
                'required'     : [ 'param1', 'param2' ],
                'optionnal'    : {
                    'param3'       : 'default_value3',
                    'param4'       : 'default_value4',
            }, 
            'help'       : {
                'summary'    : <string> - Summary - general description like in the comment,
                'parameters' : {
                    'param1' : 'description',
                    'param2' : 'description',
                }, 
                'return'     : <string> - Can be multiline,
            }
        }
    """
    from inspect import getargspec
    result = {
        'name': method.__name__,
        'friendly_name': ' '.join([name.capitalize() for name in method.__name__.split('_')]),
    }
    arg_specs = getargspec(method)
    arguments = {}

    if not arg_specs.defaults:
        if len(arg_specs.args[1:]) > 0:
            arguments['required'] = list(arg_specs.args[1:])
    else:
        if len(arg_specs.args[1:-(len(arg_specs.defaults))]):
            arguments['required'] = list(arg_specs.args[1:-(len(arg_specs.defaults))])
        arguments['optional'] = {}
        for i in range(len(arg_specs.defaults)):
            arguments['optional'][arg_specs.args[-(len(arg_specs.defaults)) + i]] = arg_specs.defaults[i]
    if arguments != {}:
        result['parameters'] = arguments

    doc = method.__doc__.strip() if method.__doc__ else ''
    if ':' in method.__doc__:
        doc = {'summary': method.__doc__[0:doc.find('  :')].strip()}
        params = re.findall(r":param ([^\s]*): (.*)\n", method.__doc__)
        if len(params) > 0:
            doc['parameters'] = {}
            for param in params:
                doc['parameters'][param[0]] = param[1].strip()

        regex = re.compile(r":returns:(.*)", re.MULTILINE|re.DOTALL)
        returns = regex.search(method.__doc__)
        if returns and returns.group(0):
            doc['return'] = returns.group(0).replace(':returns:', '').replace('\n        ', '\n').strip()
    if doc != '':
        result['help'] = doc
    return result


def get_subclasses(klass):
    assert isinstance(klass, type)
    klasses = klass.__subclasses__()
    klasses2 = klasses
    for y in klasses:
        klasses2 += get_subclasses(y)
    return list(set(klasses2))


class SerializableObject(object):
    """
    Serializable object : allow to export an object as a dict or to fill an object from a dict
    """
    def fill(self, _dict, class_list=None):
        for (key, value) in _dict.items():
            if type(value) in [list, dict, set]:
                value = self.recursive_object_check(value, class_list)
            if key != '_id':
                self.__setattr__(key, value)
        return self

    def recursive_object_check(self, elem, class_list):
        if isinstance(elem, list):
            i = 0
            while i < len(elem):
                if type(elem[i]) in [list, dict, set]:
                    elem[i] = self.recursive_object_check(elem[i], class_list)
                i += 1
            return elem
        elif isinstance(elem, dict):
            if class_list and 'type' in elem and 'uuid' in elem and elem['type'] in [_class.__name__ for _class in class_list]:
                for _class in class_list:
                    if elem['type'] == _class.__name__:
                        obj = _class().fill(elem, class_list=class_list)
                        return obj
            else:
                for (key, value) in elem.items():
                    if type(value) in [list, dict, set]:
                        elem[key] = self.recursive_object_check(value, class_list)

        return elem

    def to_dict(self, dic=None):
        if not dic and dic != {}:
            dic = self.__dict__.copy() # we copy the __dict__ otherwise all the values objects, even strings, will be still referencing "self" ones. That means changing a value in the dict will change value of object, we dont want that.
        for (key, value) in dic.items():

            if isinstance(value, SerializableObject):
                dic[key] = value.to_dict()
            elif isinstance(value, list):
                dic[key] = []
                for f in value:
                    if isinstance(f, SerializableObject):
                        dic[key].append(f.to_dict())
                    else:
                        dic[key].append(f)
            elif isinstance(value, dict):
                dic[key] = self.to_dict(dic=value)
        if '_id' in dic:
            del dic['_id']
        return dic

    def __str__(self):
        return self.__class__.__name__ + "   " + str(self.to_dict())

    def __iter__(self):
        return iter([self])

    def safe_info(self, dic=None):
        """
        Returns public information of the object
        """
        if dic is None and dic != {}:
            dic = self.to_dict()
        output = {}
        for (key, value) in dic.items():
            if key[0] != '_':
                if isinstance(value, SerializableObject):
                    output[key] = value.safe_info()
                elif isinstance(value, dict):
                    output[key] = self.safe_info(dic=value)
                elif isinstance(value, list):
                    output[key] = []
                    for f in value:
                        if isinstance(f, SerializableObject):
                            output[key].append(f.safe_info())
                        elif isinstance(f, dict):
                            output[key].append(self.safe_info(dic=f))
                        else:
                            output[key].append(f)
                else:
                    output[key] = value
        return output


def sort_dictionary_list(dict_list, sort_key):
    """
    sorts a list of dictionaries based on the value of the sort_key

    dict_list - a list of dictionaries
    sort_key - a string that  identifies the key to sort the dictionaries with.

    Test sorting a list of dictionaries:
        >>> sort_dictionary_list([{'b' : 1, 'value' : 2}, {'c' : 2, 'value' : 3}, {'a' : 3, 'value' : 1}], 'value')
        [{'a': 3, 'value': 1}, {'b': 1, 'value': 2}, {'c': 2, 'value': 3}]
    """
    if not dict_list or len(dict_list) == 0:
        return dict_list
    dict_list.sort(key=itemgetter(sort_key))
    return dict_list


def get_app_name():
    mod = sys.modules.get('__main__', sys.modules[__name__])
    if '__file__' in dir(mod):
        script_folder = os.path.dirname(os.path.abspath(mod.__file__))
        app_name = os.path.split(mod.__file__)[1].replace('.pyc', '').replace('.py', '')
    else:
        script_folder = sys.path[0] if sys.path[0] != '' else sys.path[1]
        app_name = os.path.split(script_folder)[1].replace('.pyc', '').replace('.py', '')
    return script_folder, app_name


def lazy_load_module(name):
    """
    Lazy load module function.
    Use:
        lazy_load_module(__name__)
    in a __init__.py package file containing sub modules.

    This allows to import the base module, but access those easily without importing each.
    """
    sys.modules[name] = LazyLoader(name)
    return


class LazyLoader:
    """
    Module Wrapper Class
    See here for wrapping module class : http://stackoverflow.com/questions/2447353/getattr-on-a-module
    Also does lazy loading of sub modules.
    """
    def __init__(self, name):
        self.__module_name = name
        self.__wrapped_module = sys.modules[self.__module_name]
        self.__submodule_imports = {}

    def __getattr__(self, name):
        """
        Lazy loading module
        """
        if name.startswith('__'): #importing needs access to some private reserved __*__ functions...
            return getattr(self.__wrapped_module, name)

        if not self.__submodule_imports.get(name, None):
            self.__submodule_imports[name] = importlib.import_module('.'+name, package=self.__module_name)

        return self.__submodule_imports.get(name, None)