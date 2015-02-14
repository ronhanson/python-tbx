#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Templating Utils
:author: Ronan Delacroix
"""
import re
import jinja2
from functools import wraps
import uuid

def create_jinja_env(template_path):
    """
    Creates a Jinja2 environment with a specific template path.
    """
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path),
        block_start_string='{%',
        block_end_string='%}',
        variable_start_string='${',
        variable_end_string='}',
        comment_start_string='{#',
        comment_end_string='#}',
        line_statement_prefix=None,
        line_comment_prefix=None,
        trim_blocks=True,
        lstrip_blocks=True,
        newline_sequence='\n'
    )
    jinja_env.filters['regexreplace'] = regex_replace
    jinja_env.globals.update(uuidgen=uuidgen)
    return jinja_env


def render_template(env, filename, values={}):
    """
    Render a jinja template
    """
    tmpl = env.get_template(filename)
    return tmpl.render(values)


def template(filename):
    """
    Decorator
    """
    def method_wrapper(method):

        @wraps(method)
        def jinja_wrapper(*args, **kwargs):
            ret = method(*args, **kwargs)
            return render_template(filename, ret)

        return jinja_wrapper

    return method_wrapper


def regex_replace(s, find, replace):
    """
    A non-optimal implementation of a regex filter (used as jinja filter)
    """
    return re.sub(find, replace, s)


def uuidgen():
    """
    Jinja filter to create random UUIDs
    """
    return uuid.uuid4()