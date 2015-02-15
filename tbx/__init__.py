#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2014 Ronan Delacroix
TBX Lazy Sub-module Loading
:author: Ronan Delacroix
"""
from . import code
code.lazy_load_module(__name__)