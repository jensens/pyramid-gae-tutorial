##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Deprecation Support

This module provides utilities to ease the development of backward-compatible
code.

$Id: deprecation.py 70794 2006-10-19 04:29:42Z baijum $
"""
__docformat__ = "reStructuredText"
import sys
import types
import warnings

import zope.deprecation


class ShowSwitch(object):
    """Simple stack-based switch."""

    def __init__(self):
        self.stack = []

    def on(self):
        self.stack.pop()

    def off(self):
        self.stack.append(False)

    def reset(self):
        self.stack = []

    def __call__(self):
        return self.stack == []

    def __repr__(self):
        return '<ShowSwitch %s>' %(self() and 'on' or 'off')


ogetattr = object.__getattribute__
class DeprecationProxy(object):

    def __init__(self, module):
        self.__original_module = module
        self.__deprecated = {}

    def deprecate(self, names, message):
        """Deprecate the given names."""
        if not isinstance(names, (tuple, list)):
            names = (names,)
        for name in names:
            self.__deprecated[name] = message

    def __getattribute__(self, name):
        if name == 'deprecate' or name.startswith('_DeprecationProxy__'):
            return ogetattr(self, name)

        if name == '__class__':
            return types.ModuleType
        
        if name in ogetattr(self, '_DeprecationProxy__deprecated'):
            if zope.deprecation.__show__():
                warnings.warn(
                    name + ': ' + self.__deprecated[name],
                    DeprecationWarning, 2)

        return getattr(ogetattr(self, '_DeprecationProxy__original_module'),
                       name)

    def __setattr__(self, name, value):
        if name.startswith('_DeprecationProxy__'):
            return object.__setattr__(self, name, value)

        setattr(self.__original_module, name, value)

    def __delattr__(self, name):
        if name.startswith('_DeprecationProxy__'):
            return object.__delattr__(self, name)

        delattr(self.__original_module, name)
        
class DeprecatedModule(object):

    def __init__(self, module, msg):
        self.__original_module = module
        self.__msg = msg

    def __getattribute__(self, name):
        if name.startswith('_DeprecatedModule__'):
            return ogetattr(self, name)

        if name == '__class__':
            return types.ModuleType
        
        if zope.deprecation.__show__():
            warnings.warn(self.__msg, DeprecationWarning, 2)

        return getattr(ogetattr(self, '_DeprecatedModule__original_module'),
                       name)

    def __setattr__(self, name, value):
        if name.startswith('_DeprecatedModule__'):
            return object.__setattr__(self, name, value)
        setattr(self.__original_module, name, value)

    def __delattr__(self, name):
        if name.startswith('_DeprecatedModule__'):
            return object.__delattr__(self, name)
        delattr(self.__original_module, name)

class DeprecatedGetProperty(object):

    def __init__(self, prop, message):
        self.message = message
        self.prop = prop

    def __get__(self, inst, klass):
        if zope.deprecation.__show__():
            warnings.warn(self.message, DeprecationWarning, 2)
        return self.prop.__get__(inst, klass)

class DeprecatedGetSetProperty(DeprecatedGetProperty):

    def __set__(self, inst, prop):
        if zope.deprecation.__show__():
            warnings.warn(self.message, DeprecationWarning, 2)
        self.prop.__set__(inst, prop)

class DeprecatedGetSetDeleteProperty(DeprecatedGetSetProperty):

    def __delete__(self, inst):
        if zope.deprecation.__show__():
            warnings.warn(self.message, DeprecationWarning, 2)
        self.prop.__delete__(inst)

def DeprecatedMethod(method, message):

    def deprecated_method(self, *args, **kw):
        if zope.deprecation.__show__():
            warnings.warn(message, DeprecationWarning, 2)
        return method(self, *args, **kw)

    return deprecated_method


def deprecated(specifier, message):
    """Deprecate the given names."""

    # A string specifier (or list of strings) means we're called
    # top-level in a module and are to deprecate things inside this
    # module
    if isinstance(specifier, (str, unicode, list, tuple)):
        globals = sys._getframe(1).f_globals
        modname = globals['__name__']

        if not isinstance(sys.modules[modname], DeprecationProxy):
            sys.modules[modname] = DeprecationProxy(sys.modules[modname])
        sys.modules[modname].deprecate(specifier, message)


    # Anything else can mean the specifier is a function/method,
    # module, or just an attribute of a class
    elif isinstance(specifier, types.FunctionType):
        return DeprecatedMethod(specifier, message)
    elif isinstance(specifier, types.ModuleType):
        return DeprecatedModule(specifier, message)
    else:
        prop = specifier
        if hasattr(prop, '__get__') and hasattr(prop, '__set__') and \
               hasattr(prop, '__delete__'):
            return DeprecatedGetSetDeleteProperty(prop, message)
        elif hasattr(prop, '__get__') and hasattr(prop, '__set__'):
            return DeprecatedGetSetProperty(prop, message)
        elif hasattr(prop, '__get__'):
            return DeprecatedGetProperty(prop, message)

class deprecate(object):
    """Deprecation decorator"""

    def __init__(self, msg):
        self.msg = msg

    def __call__(self, func):
        return DeprecatedMethod(func, self.msg)

def moved(to_location, unsupported_in=None):
    old = sys._getframe(1).f_globals['__name__']
    message = '%s has moved to %s.' % (old, to_location)
    if unsupported_in:
        message += " Import of %s will become unsupported in %s" % (
            old, unsupported_in)
    
    warnings.warn(message, DeprecationWarning, 3)
    __import__(to_location)

    fromdict = sys.modules[to_location].__dict__
    tomod = sys.modules[old]
    tomod.__doc__ = message
    todict = tomod.__dict__

    for name, v in fromdict.iteritems():
        if name not in tomod.__dict__:
            setattr(tomod, name, v)

    
