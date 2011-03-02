##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
"""Configuration-specific schema fields

$Id: fields.py 110550 2010-04-06 06:50:36Z tseaver $
"""
__docformat__ = 'restructuredtext'
import os, re, warnings
from zope import schema
from zope.schema.interfaces import IFromUnicode
from zope.schema.interfaces import ConstraintNotSatisfied
from zope.configuration.exceptions import ConfigurationError
from zope.interface import implements
from zope.configuration.interfaces import InvalidToken

PYIDENTIFIER_REGEX = u'\\A[a-zA-Z_]+[a-zA-Z0-9_]*\\Z'
pyidentifierPattern = re.compile(PYIDENTIFIER_REGEX)

class PythonIdentifier(schema.TextLine):
    r"""This field describes a python identifier, i.e. a variable name.

    Let's look at an example:

    >>> class FauxContext(object):
    ...     pass
    >>> context = FauxContext()
    >>> field = PythonIdentifier().bind(context)

    Let's test the fromUnicode method:

    >>> field.fromUnicode(u'foo')
    u'foo'
    >>> field.fromUnicode(u'foo3')
    u'foo3'
    >>> field.fromUnicode(u'_foo3')
    u'_foo3'

    Now let's see whether validation works alright

    >>> for value in (u'foo', u'foo3', u'foo_', u'_foo3', u'foo_3', u'foo3_'):
    ...     field._validate(value)
    >>>
    >>> from zope import schema
    >>>
    >>> for value in (u'3foo', u'foo:', u'\\', u''):
    ...     try:
    ...         field._validate(value)
    ...     except schema.ValidationError:
    ...         print 'Validation Error'
    Validation Error
    Validation Error
    Validation Error
    Validation Error

    """
    implements(IFromUnicode)

    def fromUnicode(self, u):
        return u.strip()

    def _validate(self, value):
        super(PythonIdentifier, self)._validate(value)
        if pyidentifierPattern.match(value) is None:
            raise schema.ValidationError(value)

class GlobalObject(schema.Field):
    """An object that can be accessed as a module global.

    Examples:

    First, we need to set up a stub name resolver:

    >>> d = {'x': 1, 'y': 42, 'z': 'zope'}
    >>> class fakeresolver(dict):
    ...     def resolve(self, n):
    ...         return self[n]

    >>> fake = fakeresolver(d)


    >>> g = GlobalObject(value_type=schema.Int())
    >>> gg = g.bind(fake)
    >>> gg.fromUnicode("x")
    1
    >>> gg.fromUnicode("   x  \\n  ")
    1
    >>> gg.fromUnicode("y")
    42
    >>> gg.fromUnicode("z")
    Traceback (most recent call last):
    ...
    WrongType: ('zope', (<type 'int'>, <type 'long'>), '')

    >>> g = GlobalObject(constraint=lambda x: x%2 == 0)
    >>> gg = g.bind(fake)
    >>> gg.fromUnicode("x")
    Traceback (most recent call last):
    ...
    ConstraintNotSatisfied: 1
    >>> gg.fromUnicode("y")
    42
    >>> g = GlobalObject()
    >>> gg = g.bind(fake)
    >>> gg.fromUnicode('*')
    >>>

    """

    implements(IFromUnicode)

    def __init__(self, value_type=None, **kw):
        self.value_type = value_type
        super(GlobalObject, self).__init__(**kw)

    def _validate(self, value):
        super(GlobalObject, self)._validate(value)
        if self.value_type is not None:
            self.value_type.validate(value)

    def fromUnicode(self, u):
        name = str(u.strip())

        # special case, mostly for interfaces
        if name == '*':
            return None

        try:
            value = self.context.resolve(name)
        except ConfigurationError, v:
            raise schema.ValidationError(v)

        self.validate(value)
        return value

class GlobalInterface(GlobalObject):
    """An interface that can be accessed from a module.

    First, we need to set up a stub name resolver:

    >>> class Foo(object): pass

    >>> from zope.interface import Interface
    >>> class IFoo(Interface): pass

    >>> d = {'Foo': Foo, 'IFoo': IFoo}
    >>> class fakeresolver(dict):
    ...     def resolve(self, n):
    ...         return self[n]

    >>> fake = fakeresolver(d)

    Now verify constraints are checked correctly.

    >>> g = GlobalInterface()
    >>> gg = g.bind(fake)
    >>> gg.fromUnicode('IFoo')
    <InterfaceClass zope.configuration.fields.IFoo>
    >>> gg.fromUnicode('  IFoo  ')
    <InterfaceClass zope.configuration.fields.IFoo>
    >>> gg.fromUnicode('Foo')
    Traceback (most recent call last):
    ...
    WrongType: ('An interface is required', <class 'zope.configuration.fields.Foo'>, '')
    """

    def __init__(self, **kw):
        super(GlobalInterface, self).__init__(schema.InterfaceField(), **kw)

class Tokens(schema.List):
    """A list that can be read from a space-separated string

    Consider GlobalObject tokens:

    Examples:

    First, we need to set up a stub name resolver:

    >>> d = {'x': 1, 'y': 42, 'z': 'zope', 'x.y.x': 'foo'}
    >>> class fakeresolver(dict):
    ...     def resolve(self, n):
    ...         return self[n]

    >>> fake = fakeresolver(d)


    >>> g = Tokens(value_type=GlobalObject())
    >>> gg = g.bind(fake)
    >>> gg.fromUnicode("  \\n  x y z  \\n")
    [1, 42, 'zope']

    >>> g = Tokens(value_type=
    ...            GlobalObject(value_type=
    ...                         schema.Int(constraint=lambda x: x%2 == 0)))
    >>> gg = g.bind(fake)
    >>> gg.fromUnicode("x y")
    Traceback (most recent call last):
    ...
    InvalidToken: 1 in x y

    >>> gg.fromUnicode("z y")
    Traceback (most recent call last):
    ...
    InvalidToken: ('zope', (<type 'int'>, <type 'long'>), '') in z y
    >>> gg.fromUnicode("y y")
    [42, 42]
    >>>

    """
    implements(IFromUnicode)

    def fromUnicode(self, u):
        u = u.strip()
        if u:
            vt = self.value_type.bind(self.context)
            values = []
            for s in u.split():
                try:
                    v = vt.fromUnicode(s)
                except schema.ValidationError, v:
                    raise InvalidToken("%s in %s" % (v, u))
                else:
                    values.append(v)
        else:
            values = []

        self.validate(values)

        return values

class Path(schema.Text):
    r"""A file path name, which may be input as a relative path

    Input paths are converted to absolute paths and normalized.

    Let's look at an example:

    First, we need a "context" for the field that has a path
    function for converting relative path to an absolute path.

    We'll be careful to do this in an os-independent fashion.

    >>> class FauxContext(object):
    ...    def path(self, p):
    ...       return os.path.join(os.sep, 'faux', 'context', p)

    >>> context = FauxContext()
    >>> field = Path().bind(context)

    Lets try an absolute path first:

    >>> p = unicode(os.path.join(os.sep, 'a', 'b'))
    >>> n = field.fromUnicode(p)
    >>> n.split(os.sep)
    [u'', u'a', u'b']

    This should also work with extra spaces around the path:

    >>> p = "   \n   %s   \n\n   " % p
    >>> n = field.fromUnicode(p)
    >>> n.split(os.sep)
    [u'', u'a', u'b']

    Now try a relative path:

    >>> p = unicode(os.path.join('a', 'b'))
    >>> n = field.fromUnicode(p)
    >>> n.split(os.sep)
    [u'', u'faux', u'context', u'a', u'b']


    """

    implements(IFromUnicode)

    def fromUnicode(self, u):
        u = u.strip()
        if os.path.isabs(u):
            return os.path.normpath(u)

        return self.context.path(u)


class Bool(schema.Bool):
    """A boolean value

    Values may be input (in upper or lower case) as any of:
       yes, no, y, n, true, false, t, or f.

    >>> Bool().fromUnicode(u"yes")
    1
    >>> Bool().fromUnicode(u"y")
    1
    >>> Bool().fromUnicode(u"true")
    1
    >>> Bool().fromUnicode(u"no")
    0
    """

    implements(IFromUnicode)

    def fromUnicode(self, u):
        u = u.lower()
        if u in ('1', 'true', 'yes', 't', 'y'):
            return True
        if u in ('0', 'false', 'no', 'f', 'n'):
            return False
        raise schema.ValidationError

class MessageID(schema.Text):
    """Text string that should be translated.

    When a string is converted to a message ID, it is also
    recorded in the context.

    >>> class Info(object):
    ...     file = 'file location'
    ...     line = 8

    >>> class FauxContext(object):
    ...     i18n_strings = {}
    ...     info = Info()

    >>> context = FauxContext()
    >>> field = MessageID().bind(context)

    There is a fallback domain when no domain has been specified.

    Exchange the warn function so we can make test whether the warning
    has been issued

    >>> warned = None
    >>> def fakewarn(*args, **kw):
    ...     global warned
    ...     warned = args

    >>> import warnings
    >>> realwarn = warnings.warn
    >>> warnings.warn = fakewarn

    >>> i = field.fromUnicode(u"Hello world!")
    >>> i
    u'Hello world!'
    >>> i.domain
    'untranslated'
    >>> warned
    ("You did not specify an i18n translation domain for the '' """ \
        """field in file location",)

    >>> warnings.warn = realwarn

    With the domain specified:

    >>> context.i18n_strings = {}
    >>> context.i18n_domain = 'testing'

    We can get a message id:

    >>> i = field.fromUnicode(u"Hello world!")
    >>> i
    u'Hello world!'
    >>> i.domain
    'testing'

    In addition, the string has been registered with the context:

    >>> context.i18n_strings
    {'testing': {u'Hello world!': [('file location', 8)]}}

    >>> i = field.fromUnicode(u"Foo Bar")
    >>> i = field.fromUnicode(u"Hello world!")
    >>> from pprint import PrettyPrinter
    >>> pprint=PrettyPrinter(width=70).pprint
    >>> pprint(context.i18n_strings)
    {'testing': {u'Foo Bar': [('file location', 8)],
                 u'Hello world!': [('file location', 8),
                                   ('file location', 8)]}}

    >>> from zope.i18nmessageid import Message
    >>> isinstance(context.i18n_strings['testing'].keys()[0], Message)
    1

    Explicit Message IDs

    >>> i = field.fromUnicode(u'[View-Permission] View')
    >>> i
    u'View-Permission'
    >>> i.default
    u'View'

    >>> i = field.fromUnicode(u'[] [Some] text')
    >>> i
    u'[Some] text'
    >>> i.default is None
    True
    """

    implements(IFromUnicode)

    __factories = {}

    def fromUnicode(self, u):
        context = self.context
        domain = getattr(context, 'i18n_domain', '')
        if not domain:
            domain = 'untranslated'
            warnings.warn(
                "You did not specify an i18n translation domain for the "\
                "'%s' field in %s" % (self.getName(), context.info.file )
                )
        v = super(MessageID, self).fromUnicode(u)

        # Check whether there is an explicit message is specified
        default = None
        if v.startswith('[]'):
            v = v[2:].lstrip()
        elif v.startswith('['):
            end = v.find(']')
            default = v[end+2:]
            v = v[1:end]

        # Convert to a message id, importing the factory, if necessary
        factory = self.__factories.get(domain)
        if factory is None:
            import zope.i18nmessageid
            factory = zope.i18nmessageid.MessageFactory(domain)
            self.__factories[domain] = factory

        msgid = factory(v, default)

        # Record the string we got for the domain
        i18n_strings = context.i18n_strings
        strings = i18n_strings.get(domain)
        if strings is None:
            strings = i18n_strings[domain] = {}
        locations = strings.setdefault(msgid, [])
        locations.append((context.info.file, context.info.line))

        return msgid
