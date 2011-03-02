##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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
"""Computed attributes based on schema fields
"""
from copy import copy
_marker = object()


class FieldProperty(object):
    """Computed attributes based on schema fields

    Field properties provide default values, data validation and error messages
    based on data found in field meta-data.

    Note that FieldProperties cannot be used with slots. They can only
    be used for attributes stored in instance dictionaries.
    """

    def __init__(self, field, name=None):
        if name is None:
            name = field.__name__

        self.__field = field
        self.__name = name

    def __get__(self, inst, klass):
        if inst is None:
            return self

        value = inst.__dict__.get(self.__name, _marker)
        if value is _marker:
            field = self.__field.bind(inst)
            value = getattr(field, 'default', _marker)
            if value is _marker:
                raise AttributeError(self.__name)

        return value

    def __set__(self, inst, value):
        field = self.__field.bind(inst)
        field.validate(value)
        if field.readonly and inst.__dict__.has_key(self.__name):
            raise ValueError(self.__name, 'field is readonly')
        inst.__dict__[self.__name] = value

    def __getattr__(self, name):
        return getattr(self.__field, name)


class FieldPropertyStoredThroughField(object):

    def __init__(self, field, name=None):
        if name is None:
            name = field.__name__

        self.field = copy(field)
        self.field.__name__ = "__st_%s_st" % self.field.__name__
        self.__name = name

    def setValue(self, inst, field, value):
        field.set(inst, value)

    def getValue(self, inst, field):
        return field.query(inst, _marker)

    def queryValue(self, inst, field, default):
        return field.query(inst, default)

    def __getattr__(self, name):
        return getattr(self.field, name)

    def __get__(self, inst, klass):
        if inst is None:
            return self

        field = self.field.bind(inst)
        value = self.getValue(inst, field)
        if value is _marker:
            value = getattr(field, 'default', _marker)
            if value is _marker:
                raise AttributeError(self.__name)

        return value

    def __set__(self, inst, value):
        field = self.field.bind(inst)
        field.validate(value)
        if field.readonly:
            if self.queryValue(inst, field, _marker) is _marker:
                field.readonly = False
                self.setValue(inst, field, value)
                field.readonly = True
                return
            else:
                raise ValueError(self.__name, 'field is readonly')
        self.setValue(inst, field, value)
