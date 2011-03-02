# -*- coding: utf-8 -*-
##############################################################################
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
"""Schema Fields
"""

__docformat__ = 'restructuredtext'

import re
import decimal
from datetime import datetime, date, timedelta, time
from zope.event import notify

from zope.interface import classImplements, implements, Interface
from zope.interface.interfaces import IInterface, IMethod

from zope.schema.interfaces import IField
from zope.schema.interfaces import IMinMaxLen, IText, ITextLine
from zope.schema.interfaces import ISourceText
from zope.schema.interfaces import IInterfaceField
from zope.schema.interfaces import IBytes, IASCII, IBytesLine, IASCIILine
from zope.schema.interfaces import IBool, IInt, IFloat, IDatetime, IFrozenSet
from zope.schema.interfaces import IChoice, ITuple, IList, ISet, IDict
from zope.schema.interfaces import IPassword, IDate, ITimedelta
from zope.schema.interfaces import IObject, IBeforeObjectAssignedEvent
from zope.schema.interfaces import ITime, IDecimal
from zope.schema.interfaces import IURI, IId, IDottedName, IFromUnicode
from zope.schema.interfaces import ISource, IBaseVocabulary
from zope.schema.interfaces import IContextSourceBinder

from zope.schema.interfaces import ValidationError, InvalidValue
from zope.schema.interfaces import WrongType, WrongContainedType, NotUnique
from zope.schema.interfaces import SchemaNotProvided, SchemaNotFullyImplemented
from zope.schema.interfaces import InvalidURI, InvalidId, InvalidDottedName
from zope.schema.interfaces import ConstraintNotSatisfied

from zope.schema._bootstrapfields import Field, Container, Iterable, Orderable
from zope.schema._bootstrapfields import Text, TextLine, Bool, Int, Password
from zope.schema._bootstrapfields import MinMaxLen
from zope.schema.fieldproperty import FieldProperty
from zope.schema.vocabulary import getVocabularyRegistry
from zope.schema.vocabulary import VocabularyRegistryError
from zope.schema.vocabulary import SimpleVocabulary


# Fix up bootstrap field types
Field.title = FieldProperty(IField['title'])
Field.description = FieldProperty(IField['description'])
Field.required = FieldProperty(IField['required'])
Field.readonly = FieldProperty(IField['readonly'])
# Default is already taken care of
classImplements(Field, IField)

MinMaxLen.min_length = FieldProperty(IMinMaxLen['min_length'])
MinMaxLen.max_length = FieldProperty(IMinMaxLen['max_length'])

classImplements(Text, IText)
classImplements(TextLine, ITextLine)
classImplements(Password, IPassword)
classImplements(Bool, IBool)
classImplements(Bool, IFromUnicode)
classImplements(Int, IInt)


class SourceText(Text):
    __doc__ = ISourceText.__doc__
    implements(ISourceText)
    _type = unicode


class Bytes(MinMaxLen, Field):
    __doc__ = IBytes.__doc__
    implements(IBytes, IFromUnicode)

    _type = str

    def fromUnicode(self, u):
        """
        >>> b = Bytes(constraint=lambda v: 'x' in v)

        >>> b.fromUnicode(u" foo x.y.z bat")
        ' foo x.y.z bat'
        >>> b.fromUnicode(u" foo y.z bat")
        Traceback (most recent call last):
        ...
        ConstraintNotSatisfied:  foo y.z bat

        """
        v = str(u)
        self.validate(v)
        return v


class ASCII(Bytes):
    __doc__ = IASCII.__doc__
    implements(IASCII)

    def _validate(self, value):
        """
        >>> ascii = ASCII()

        Make sure we accept empty strings:

        >>> empty = ''
        >>> ascii._validate(empty)

        and all kinds of alphanumeric strings:

        >>> alphanumeric = "Bob\'s my 23rd uncle"
        >>> ascii._validate(alphanumeric)

        >>> umlauts = "Köhlerstraße"
        >>> ascii._validate(umlauts)
        Traceback (most recent call last):
        ...
        InvalidValue
        """
        super(ASCII, self)._validate(value)
        if not value:
            return
        if not max(map(ord, value)) < 128:
            raise InvalidValue


class BytesLine(Bytes):
    """A Text field with no newlines."""

    implements(IBytesLine)

    def constraint(self, value):
        # TODO: we should probably use a more general definition of newlines
        return '\n' not in value


class ASCIILine(ASCII):
    __doc__ = IASCIILine.__doc__

    implements(IASCIILine)

    def constraint(self, value):
        # TODO: we should probably use a more general definition of newlines
        return '\n' not in value


class Float(Orderable, Field):
    __doc__ = IFloat.__doc__
    implements(IFloat, IFromUnicode)
    _type = float

    def __init__(self, *args, **kw):
        super(Float, self).__init__(*args, **kw)

    def fromUnicode(self, u):
        """
        >>> f = Float()
        >>> f.fromUnicode("1.25")
        1.25
        >>> f.fromUnicode("1.25.6") #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError: invalid literal for float(): 1.25.6
        """
        v = float(u)
        self.validate(v)
        return v


class Decimal(Orderable, Field):
    __doc__ = IDecimal.__doc__
    implements(IDecimal, IFromUnicode)
    _type = decimal.Decimal

    def __init__(self, *args, **kw):
        super(Decimal, self).__init__(*args, **kw)

    def fromUnicode(self, u):
        """
        >>> f = Decimal()
        >>> import decimal
        >>> isinstance(f.fromUnicode("1.25"), decimal.Decimal)
        True
        >>> float(f.fromUnicode("1.25"))
        1.25
        >>> f.fromUnicode("1.25.6")
        Traceback (most recent call last):
        ...
        ValueError: invalid literal for Decimal(): 1.25.6
        """
        try:
            v = decimal.Decimal(u)
        except decimal.InvalidOperation:
            raise ValueError('invalid literal for Decimal(): %s' % u)
        self.validate(v)
        return v


class Datetime(Orderable, Field):
    __doc__ = IDatetime.__doc__
    implements(IDatetime)
    _type = datetime

    def __init__(self, *args, **kw):
        super(Datetime, self).__init__(*args, **kw)


class Date(Orderable, Field):
    __doc__ = IDate.__doc__
    implements(IDate)
    _type = date

    def _validate(self, value):
        super(Date, self)._validate(value)
        if isinstance(value, datetime):
            raise WrongType(value, self._type, self.__name__)


class Timedelta(Orderable, Field):
    __doc__ = ITimedelta.__doc__
    implements(ITimedelta)
    _type = timedelta


class Time(Orderable, Field):
    __doc__ = ITime.__doc__
    implements(ITime)
    _type = time


class Choice(Field):
    """Choice fields can have a value found in a constant or dynamic set of
    values given by the field definition.
    """
    implements(IChoice, IFromUnicode)

    def __init__(self, values=None, vocabulary=None, source=None, **kw):
        """Initialize object."""
        if vocabulary is not None:
            assert (isinstance(vocabulary, basestring)
                    or IBaseVocabulary.providedBy(vocabulary))
            assert source is None, (
                "You cannot specify both source and vocabulary.")
        elif source is not None:
            vocabulary = source

        assert not (values is None and vocabulary is None), (
               "You must specify either values or vocabulary.")
        assert values is None or vocabulary is None, (
               "You cannot specify both values and vocabulary.")

        self.vocabulary = None
        self.vocabularyName = None
        if values is not None:
            self.vocabulary = SimpleVocabulary.fromValues(values)
        elif isinstance(vocabulary, (unicode, str)):
            self.vocabularyName = vocabulary
        else:
            assert (ISource.providedBy(vocabulary) or
                    IContextSourceBinder.providedBy(vocabulary))
            self.vocabulary = vocabulary
        # Before a default value is checked, it is validated. However, a
        # named vocabulary is usually not complete when these fields are
        # initialized. Therefore signal the validation method to ignore
        # default value checks during initialization of a Choice tied to a
        # registered vocabulary.
        self._init_field = (bool(self.vocabularyName) or
                            IContextSourceBinder.providedBy(self.vocabulary))
        super(Choice, self).__init__(**kw)
        self._init_field = False

    source = property(lambda self: self.vocabulary)

    def bind(self, object):
        """See zope.schema._bootstrapinterfaces.IField."""
        clone = super(Choice, self).bind(object)
        # get registered vocabulary if needed:
        if IContextSourceBinder.providedBy(self.vocabulary):
            clone.vocabulary = self.vocabulary(object)
            assert ISource.providedBy(clone.vocabulary)
        elif clone.vocabulary is None and self.vocabularyName is not None:
            vr = getVocabularyRegistry()
            clone.vocabulary = vr.get(object, self.vocabularyName)
            assert ISource.providedBy(clone.vocabulary)

        return clone

    def fromUnicode(self, str):
        """
        >>> from vocabulary import SimpleVocabulary
        >>> t = Choice(
        ...     vocabulary=SimpleVocabulary.fromValues([u'foo',u'bar']))
        >>> IFromUnicode.providedBy(t)
        True
        >>> t.fromUnicode(u"baz")
        Traceback (most recent call last):
        ...
        ConstraintNotSatisfied: baz
        >>> t.fromUnicode(u"foo")
        u'foo'
        """
        self.validate(str)
        return str

    def _validate(self, value):
        # Pass all validations during initialization
        if self._init_field:
            return
        super(Choice, self)._validate(value)
        vocabulary = self.vocabulary
        if vocabulary is None:
            vr = getVocabularyRegistry()
            try:
                vocabulary = vr.get(None, self.vocabularyName)
            except VocabularyRegistryError:
                raise ValueError("Can't validate value without vocabulary")
        if value not in vocabulary:
            raise ConstraintNotSatisfied(value)


class InterfaceField(Field):
    __doc__ = IInterfaceField.__doc__
    implements(IInterfaceField)

    def _validate(self, value):
        super(InterfaceField, self)._validate(value)
        if not IInterface.providedBy(value):
            raise WrongType("An interface is required", value, self.__name__)


def _validate_sequence(value_type, value, errors=None):
    """Validates a sequence value.

    Returns a list of validation errors generated during the validation. If
    no errors are generated, returns an empty list.

    value_type is a field. value is the sequence being validated. errors is
    an optional list of errors that will be prepended to the return value.

    To illustrate, we'll use a text value type. All values must be unicode.

            >>> field = TextLine(required=True)

        To validate a sequence of various values:

            >>> errors = _validate_sequence(field, ('foo', u'bar', 1))
            >>> errors
            [WrongType('foo', <type 'unicode'>, ''), WrongType(1, <type 'unicode'>, '')]

        The only valid value in the sequence is the second item. The others
        generated errors.

        We can use the optional errors argument to collect additional errors
        for a new sequence:

        >>> errors = _validate_sequence(field, (2, u'baz'), errors)
        >>> errors
        [WrongType('foo', <type 'unicode'>, ''), WrongType(1, <type 'unicode'>, ''), WrongType(2, <type 'unicode'>, '')]

    """
    if errors is None:
        errors = []
    if value_type is None:
        return errors
    for item in value:
        try:
            value_type.validate(item)
        except ValidationError, error:
            errors.append(error)
    return errors


def _validate_uniqueness(value):
    temp_values = []
    for item in value:
        if item in temp_values:
            raise NotUnique(item)

        temp_values.append(item)


class AbstractCollection(MinMaxLen, Iterable):
    value_type = None
    unique = False

    def __init__(self, value_type=None, unique=False, **kw):
        super(AbstractCollection, self).__init__(**kw)
        # whine if value_type is not a field
        if value_type is not None and not IField.providedBy(value_type):
            raise ValueError("'value_type' must be field instance.")
        self.value_type = value_type
        self.unique = unique

    def bind(self, object):
        """See zope.schema._bootstrapinterfaces.IField."""
        clone = super(AbstractCollection, self).bind(object)
        # binding value_type is necessary for choices with named vocabularies,
        # and possibly also for other fields.
        if clone.value_type is not None:
            clone.value_type = clone.value_type.bind(object)
        return clone

    def _validate(self, value):
        super(AbstractCollection, self)._validate(value)
        errors = _validate_sequence(self.value_type, value)
        if errors:
            raise WrongContainedType(errors, self.__name__)
        if self.unique:
            _validate_uniqueness(value)


class Tuple(AbstractCollection):
    """A field representing a Tuple."""
    implements(ITuple)
    _type = tuple


class List(AbstractCollection):
    """A field representing a List."""
    implements(IList)
    _type = list


class Set(AbstractCollection):
    """A field representing a set."""
    implements(ISet)
    _type = set

    def __init__(self, **kw):
        if 'unique' in kw: # set members are always unique
            raise TypeError(
                "__init__() got an unexpected keyword argument 'unique'")
        super(Set, self).__init__(unique=True, **kw)


class FrozenSet(AbstractCollection):
    implements(IFrozenSet)
    _type = frozenset

    def __init__(self, **kw):
        if 'unique' in kw: # set members are always unique
            raise TypeError(
                "__init__() got an unexpected keyword argument 'unique'")
        super(FrozenSet, self).__init__(unique=True, **kw)


def _validate_fields(schema, value, errors=None):
    if errors is None:
        errors = []
    # Interface can be used as schema property for Object fields that plan to
    # hold values of any type.
    # Because Interface does not include any Attribute, it is obviously not
    # worth looping on its methods and filter them all out.
    if schema is Interface:
        return errors
    # if `value` is part of a cyclic graph, we need to break the cycle to avoid
    # infinite recursion.
    #
    # (use volatile attribute to avoid persistency/conflicts)
    if hasattr(value, '_v_schema_being_validated'):
        return errors
    # Mark the value as being validated.
    value._v_schema_being_validated = True
    # (If we have gotten here, we know that `value` provides an interface
    # other than zope.interface.Interface;
    # iow, we can rely on the fact that it is an instance
    # that supports attribute assignment.)
    try:
        for name in schema.names(all=True):
            if not IMethod.providedBy(schema[name]):
                try:
                    attribute = schema[name]
                    if IField.providedBy(attribute):
                        # validate attributes that are fields
                        attribute.validate(getattr(value, name))
                except ValidationError, error:
                    errors.append(error)
                except AttributeError, error:
                    # property for the given name is not implemented
                    errors.append(SchemaNotFullyImplemented(error))
    finally:
        delattr(value, '_v_schema_being_validated')
    return errors


class Object(Field):
    __doc__ = IObject.__doc__
    implements(IObject)

    def __init__(self, schema, **kw):
        if not IInterface.providedBy(schema):
            raise WrongType

        self.schema = schema
        super(Object, self).__init__(**kw)

    def _validate(self, value):
        super(Object, self)._validate(value)

        # schema has to be provided by value
        if not self.schema.providedBy(value):
            raise SchemaNotProvided

        # check the value against schema
        errors = _validate_fields(self.schema, value)
        if errors:
            raise WrongContainedType(errors, self.__name__)

    def set(self, object, value):
        # Announce that we're going to assign the value to the object.
        # Motivation: Widgets typically like to take care of policy-specific
        # actions, like establishing location.
        event = BeforeObjectAssignedEvent(value, self.__name__, object)
        notify(event)
        # The event subscribers are allowed to replace the object, thus we need
        # to replace our previous value.
        value = event.object
        super(Object, self).set(object, value)


class BeforeObjectAssignedEvent(object):
    """An object is going to be assigned to an attribute on another object."""

    implements(IBeforeObjectAssignedEvent)

    def __init__(self, object, name, context):
        self.object = object
        self.name = name
        self.context = context


class Dict(MinMaxLen, Iterable):
    """A field representing a Dict."""
    implements(IDict)
    _type = dict
    key_type = None
    value_type = None

    def __init__(self, key_type=None, value_type=None, **kw):
        super(Dict, self).__init__(**kw)
        # whine if key_type or value_type is not a field
        if key_type is not None and not IField.providedBy(key_type):
            raise ValueError("'key_type' must be field instance.")
        if value_type is not None and not IField.providedBy(value_type):
            raise ValueError("'value_type' must be field instance.")
        self.key_type = key_type
        self.value_type = value_type

    def _validate(self, value):
        super(Dict, self)._validate(value)
        errors = []
        try:
            if self.value_type:
                errors = _validate_sequence(self.value_type, value.values(),
                                            errors)
            errors = _validate_sequence(self.key_type, value, errors)

            if errors:
                raise WrongContainedType(errors, self.__name__)

        finally:
            errors = None

    def bind(self, object):
        """See zope.schema._bootstrapinterfaces.IField."""
        clone = super(Dict, self).bind(object)
        # binding value_type is necessary for choices with named vocabularies,
        # and possibly also for other fields.
        if clone.key_type is not None:
            clone.key_type = clone.key_type.bind(object)
        if clone.value_type is not None:
            clone.value_type = clone.value_type.bind(object)
        return clone


_isuri = re.compile(
    # scheme
    r"[a-zA-z0-9+.-]+:"
    # non space (should be pickier)
    r"\S*$").match


class URI(BytesLine):
    """URI schema field
    """

    implements(IURI, IFromUnicode)

    def _validate(self, value):
        """
        >>> uri = URI(__name__='test')
        >>> uri.validate("http://www.python.org/foo/bar")
        >>> uri.validate("DAV:")
        >>> uri.validate("www.python.org/foo/bar")
        Traceback (most recent call last):
        ...
        InvalidURI: www.python.org/foo/bar
        """

        super(URI, self)._validate(value)
        if _isuri(value):
            return

        raise InvalidURI(value)

    def fromUnicode(self, value):
        """
        >>> uri = URI(__name__='test')
        >>> uri.fromUnicode("http://www.python.org/foo/bar")
        'http://www.python.org/foo/bar'
        >>> uri.fromUnicode("          http://www.python.org/foo/bar")
        'http://www.python.org/foo/bar'
        >>> uri.fromUnicode("      \\n    http://www.python.org/foo/bar\\n")
        'http://www.python.org/foo/bar'
        >>> uri.fromUnicode("http://www.python.org/ foo/bar")
        Traceback (most recent call last):
        ...
        InvalidURI: http://www.python.org/ foo/bar
        """
        v = str(value.strip())
        self.validate(v)
        return v


_isdotted = re.compile(
    r"([a-zA-Z][a-zA-Z0-9_]*)"
    r"([.][a-zA-Z][a-zA-Z0-9_]*)*"
    # use the whole line
    r"$").match


class Id(BytesLine):
    """Id field

    Values of id fields must be either uris or dotted names.
    """

    implements(IId, IFromUnicode)

    def _validate(self, value):
        """
        >>> id = Id(__name__='test')
        >>> id.validate("http://www.python.org/foo/bar")
        >>> id.validate("zope.app.content")
        >>> id.validate("zope.app.content/a")
        Traceback (most recent call last):
        ...
        InvalidId: zope.app.content/a
        >>> id.validate("http://zope.app.content x y")
        Traceback (most recent call last):
        ...
        InvalidId: http://zope.app.content x y
        """
        super(Id, self)._validate(value)
        if _isuri(value):
            return
        if _isdotted(value) and "." in value:
            return

        raise InvalidId(value)

    def fromUnicode(self, value):
        """
        >>> id = Id(__name__='test')
        >>> id.fromUnicode("http://www.python.org/foo/bar")
        'http://www.python.org/foo/bar'
        >>> id.fromUnicode(u" http://www.python.org/foo/bar ")
        'http://www.python.org/foo/bar'
        >>> id.fromUnicode("http://www.python.org/ foo/bar")
        Traceback (most recent call last):
        ...
        InvalidId: http://www.python.org/ foo/bar
        >>> id.fromUnicode("      \\n x.y.z \\n")
        'x.y.z'

        """
        v = str(value.strip())
        self.validate(v)
        return v


class DottedName(BytesLine):
    """Dotted name field.

    Values of DottedName fields must be Python-style dotted names.
    """

    implements(IDottedName)

    def __init__(self, *args, **kw):
        """
        >>> DottedName(min_dots=-1)
        Traceback (most recent call last):
        ...
        ValueError: min_dots cannot be less than zero

        >>> DottedName(max_dots=-1)
        Traceback (most recent call last):
        ...
        ValueError: max_dots cannot be less than min_dots

        >>> DottedName(max_dots=1, min_dots=2)
        Traceback (most recent call last):
        ...
        ValueError: max_dots cannot be less than min_dots

        >>> dotted_name = DottedName(max_dots=1, min_dots=1)

        >>> from zope.interface.verify import verifyObject
        >>> verifyObject(IDottedName, dotted_name)
        True

        >>> dotted_name = DottedName(max_dots=1)
        >>> dotted_name.min_dots
        0

        >>> dotted_name = DottedName(min_dots=1)
        >>> dotted_name.max_dots
        >>> dotted_name.min_dots
        1
        """
        self.min_dots = int(kw.pop("min_dots", 0))
        if self.min_dots < 0:
            raise ValueError("min_dots cannot be less than zero")
        self.max_dots = kw.pop("max_dots", None)
        if self.max_dots is not None:
            self.max_dots = int(self.max_dots)
            if self.max_dots < self.min_dots:
                raise ValueError("max_dots cannot be less than min_dots")
        super(DottedName, self).__init__(*args, **kw)

    def _validate(self, value):
        """
        >>> dotted_name = DottedName(__name__='test')
        >>> dotted_name.validate("a.b.c")
        >>> dotted_name.validate("a")
        >>> dotted_name.validate("   a")
        Traceback (most recent call last):
        ...
        InvalidDottedName:    a

        >>> dotted_name = DottedName(__name__='test', min_dots=1)
        >>> dotted_name.validate('a.b')
        >>> dotted_name.validate('a.b.c.d')
        >>> dotted_name.validate('a')
        Traceback (most recent call last):
        ...
        InvalidDottedName: ('too few dots; 1 required', 'a')

        >>> dotted_name = DottedName(__name__='test', max_dots=0)
        >>> dotted_name.validate('a')
        >>> dotted_name.validate('a.b')
        Traceback (most recent call last):
        ...
        InvalidDottedName: ('too many dots; no more than 0 allowed', 'a.b')

        >>> dotted_name = DottedName(__name__='test', max_dots=2)
        >>> dotted_name.validate('a')
        >>> dotted_name.validate('a.b')
        >>> dotted_name.validate('a.b.c')
        >>> dotted_name.validate('a.b.c.d')
        Traceback (most recent call last):
        ...
        InvalidDottedName: ('too many dots; no more than 2 allowed', 'a.b.c.d')

        >>> dotted_name = DottedName(__name__='test', max_dots=1, min_dots=1)
        >>> dotted_name.validate('a.b')
        >>> dotted_name.validate('a')
        Traceback (most recent call last):
        ...
        InvalidDottedName: ('too few dots; 1 required', 'a')
        >>> dotted_name.validate('a.b.c')
        Traceback (most recent call last):
        ...
        InvalidDottedName: ('too many dots; no more than 1 allowed', 'a.b.c')

        """
        super(DottedName, self)._validate(value)
        if not _isdotted(value):
            raise InvalidDottedName(value)
        dots = value.count(".")
        if dots < self.min_dots:
            raise InvalidDottedName("too few dots; %d required" % self.min_dots,
                                    value)
        if self.max_dots is not None and dots > self.max_dots:
            raise InvalidDottedName("too many dots; no more than %d allowed" %
                                    self.max_dots, value)

    def fromUnicode(self, value):
        v = str(value.strip())
        self.validate(v)
        return v
