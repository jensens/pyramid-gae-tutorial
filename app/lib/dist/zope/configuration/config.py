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
"""Configuration processor

See README.txt.

$Id: config.py 110550 2010-04-06 06:50:36Z tseaver $
"""
__docformat__ = 'restructuredtext'
import __builtin__
import os.path
import sys

import zope.schema

from keyword import iskeyword
from zope.configuration.exceptions import ConfigurationError
from zope.configuration.interfaces import IConfigurationContext
from zope.configuration.interfaces import IGroupingContext
from zope.interface.adapter import AdapterRegistry
from zope.interface import Interface, implements, providedBy
from zope.configuration import fields


zopens = 'http://namespaces.zope.org/zope'
metans = 'http://namespaces.zope.org/meta'
testns = 'http://namespaces.zope.org/test'

_import_chickens = {}, {}, ("*",) # dead chickens needed by __import__

class ConfigurationContext(object):
    """Mix-in that implements IConfigurationContext

    Subclasses provide a ``package`` attribute and a ``basepath``
    attribute.  If the base path is not None, relative paths are
    converted to absolute paths using the the base path. If the
    package is not none, relative imports are performed relative to
    the package.

    In general, the basepath and package attributes should be
    consistent. When a package is provided, the base path should be
    set to the path of the package directory.

    Subclasses also provide an ``actions`` attribute, which is a list
    of actions, an ``includepath`` attribute, and an ``info``
    attribute.

    The include path is appended to each action and is used when
    resolving conflicts among actions.  Normally, only the a
    ConfigurationMachine provides the actions attribute. Decorators
    simply use the actions of the context they decorate. The
    ``includepath`` attribute is a tuple of names.  Each name is
    typically the name of an included configuration file.

    The ``info`` attribute contains descriptive information helpful
    when reporting errors.  If not set, it defaults to an empty string.

    The actions attribute is a sequence of tuples with items:

      - discriminator, a value that identifies the action. Two actions
        that have the same (non None) discriminator conflict.

      - an object that is called to execute the action,

      - positional arguments for the action

      - keyword arguments for the action

      - a tuple of include file names (defaults to ())

      - an object that has descriptive information about
        the action (defaults to '')

    For brevity, trailing items after the callable in the tuples are
    ommitted if they are empty.

    """

    def __init__(self):
        super(ConfigurationContext, self).__init__()
        self._seen_files = set()
        self._features = set()

    def resolve(self, dottedname):
        """Resolve a dotted name to an object

        Examples:


        >>> c = ConfigurationContext()
        >>> import zope, zope.interface
        >>> c.resolve('zope') is zope
        1
        >>> c.resolve('zope.interface') is zope.interface
        1

        >>> c.resolve('zope.configuration.eek') #doctest: +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        ...
        ConfigurationError:
        ImportError: Module zope.configuration has no global eek

        >>> c.resolve('.config.ConfigurationContext')
        Traceback (most recent call last):
        ...
        AttributeError: 'ConfigurationContext' object has no attribute """ \
                                                                  """'package'
        >>> import zope.configuration
        >>> c.package = zope.configuration
        >>> c.resolve('.') is zope.configuration
        1
        >>> c.resolve('.config.ConfigurationContext') is ConfigurationContext
        1
        >>> c.resolve('..interface') is zope.interface
        1
        >>> c.resolve('unicode')
        <type 'unicode'>
        """

        name = dottedname.strip()
        if not name:
            raise ValueError("The given name is blank")

        if name == '.':
            return self.package

        names = name.split('.')
        if not names[-1]:
            raise ValueError(
                "Trailing dots are no longer supported in dotted names")

        if len(names) == 1:
            # Check for built-in objects
            marker = object()
            obj = getattr(__builtin__, names[0], marker)
            if obj is not marker:
                return obj

        if not names[0]:
            # Got a relative name. Convert it to abs using package info
            if self.package is None:
                raise ConfigurationError(
                    "Can't use leading dots in dotted names, "
                    "no package has been set.")
            pnames = self.package.__name__.split(".")
            pnames.append('')
            while names and not names[0]:
                try:
                    names.pop(0)
                except IndexError:
                    raise ConfigurationError("Invalid global name", name)
                try:
                    pnames.pop()
                except IndexError:
                    raise ConfigurationError("Invalid global name", name)
            names[0:0] = pnames

        # Now we should have an absolute dotted name

        # Split off object name:
        oname, mname = names[-1], '.'.join(names[:-1])

        # Import the module
        if not mname:
            # Just got a single name. Must me a module
            mname = oname
            oname = ''

        try:
            mod = __import__(mname, *_import_chickens)
        except ImportError, v:
            if sys.exc_info()[2].tb_next is not None:
                # ImportError was caused deeper
                raise
            raise ConfigurationError(
                "ImportError: Couldn't import %s, %s" % (mname, v))

        if not oname:
            # see not mname case above
            return mod


        try:
            obj = getattr(mod, oname)
            return obj
        except AttributeError:
            # No such name, maybe it's a module that we still need to import
            try:
                return __import__(mname+'.'+oname, *_import_chickens)
            except ImportError:
                if sys.exc_info()[2].tb_next is not None:
                    # ImportError was caused deeper
                    raise
                raise ConfigurationError(
                    "ImportError: Module %s has no global %s" % (mname, oname))

    def path(self, filename):
        """
        Examples:

        >>> c = ConfigurationContext()
        >>> c.path("/x/y/z") == os.path.normpath("/x/y/z")
        1
        >>> c.path("y/z")
        Traceback (most recent call last):
        ...
        AttributeError: 'ConfigurationContext' object has no attribute """ \
                                                                 """'package'
        >>> import zope.configuration
        >>> c.package = zope.configuration
        >>> import os
        >>> d = os.path.dirname(zope.configuration.__file__)
        >>> c.path("y/z") == d + os.path.normpath("/y/z")
        1
        >>> c.path("y/./z") == d + os.path.normpath("/y/z")
        1
        >>> c.path("y/../z") == d + os.path.normpath("/z")
        1
        """

        filename = os.path.normpath(filename)
        if os.path.isabs(filename):
            return filename

        # Got a relative path, combine with base path.
        # If we have no basepath, compute the base path from the package
        # path.

        basepath = getattr(self, 'basepath', '')

        if not basepath:
            if self.package is None:
                basepath = os.getcwd()
            else:
                basepath = os.path.dirname(self.package.__file__)
                basepath = os.path.abspath(basepath)
            self.basepath = basepath

        return os.path.join(basepath, filename)

    def checkDuplicate(self, filename):
        """Check for duplicate imports of the same file.

        Raises an exception if this file had been processed before.  This
        is better than an unlimited number of conflict errors.

        >>> c = ConfigurationContext()
        >>> c.checkDuplicate('/foo.zcml')
        >>> try:
        ...     c.checkDuplicate('/foo.zcml')
        ... except ConfigurationError, e:
        ...     # On Linux the exact msg has /foo, on Windows \foo.
        ...     str(e).endswith("foo.zcml' included more than once")
        True

        You may use different ways to refer to the same file:

        >>> import zope.configuration
        >>> c.package = zope.configuration
        >>> import os
        >>> d = os.path.dirname(zope.configuration.__file__)
        >>> c.checkDuplicate('bar.zcml')
        >>> try:
        ...   c.checkDuplicate(d + os.path.normpath('/bar.zcml'))
        ... except ConfigurationError, e:
        ...   str(e).endswith("bar.zcml' included more than once")
        ...
        True

        """ #' <-- bow to font-lock
        path = self.path(filename)
        if path in self._seen_files:
            raise ConfigurationError('%r included more than once' % path)
        self._seen_files.add(path)

    def processFile(self, filename):
        """Check whether a file needs to be processed

        Return True if processing is needed and False otherwise. If
        the file needs to be processed, it will be marked as
        processed, assuming that the caller will procces the file if
        it needs to be procssed.

        >>> c = ConfigurationContext()
        >>> c.processFile('/foo.zcml')
        True
        >>> c.processFile('/foo.zcml')
        False

        You may use different ways to refer to the same file:

        >>> import zope.configuration
        >>> c.package = zope.configuration
        >>> import os
        >>> d = os.path.dirname(zope.configuration.__file__)
        >>> c.processFile('bar.zcml')
        True
        >>> c.processFile('bar.zcml')
        False

        """ #' <-- bow to font-lock
        path = self.path(filename)
        if path in self._seen_files:
            return False
        self._seen_files.add(path)
        return True

    def action(self, discriminator, callable=None, args=(), kw={}, order=0):
        """Add an action with the given discriminator, callable and arguments

        For testing purposes, the callable and arguments may be omitted.
        In that case, a default noop callable is used.

        The discriminator must be given, but it can be None, to indicate that
        the action never conflicts.

        Let's look at some examples:

        >>> c = ConfigurationContext()

        Normally, the context gets actions from subclasses. We'll provide
        an actions attribute ourselves:

        >>> c.actions = []

        We'll use a test callable that has a convenient string representation

        >>> from zope.configuration.tests.directives import f

        >>> c.action(1, f, (1, ), {'x': 1})
        >>> c.actions
        [(1, f, (1,), {'x': 1})]

        >>> c.action(None)
        >>> c.actions
        [(1, f, (1,), {'x': 1}), (None, None)]

        Now set the include path and info:

        >>> c.includepath = ('foo.zcml',)
        >>> c.info = "?"
        >>> c.action(None)
        >>> c.actions[-1]
        (None, None, (), {}, ('foo.zcml',), '?')

        Finally, we can add an order argument to crudely control the order
        of execution:

        >>> c.action(None, order=99999)
        >>> c.actions[-1]
        (None, None, (), {}, ('foo.zcml',), '?', 99999)

        """
        action = (discriminator, callable, args, kw,
                  getattr(self, 'includepath', ()),
                  getattr(self, 'info', ''),
                  order,
                  )

        # remove trailing false items
        while (len(action) > 2) and not action[-1]:
            action = action[:-1]

        self.actions.append(action)

    def hasFeature(self, feature):
        """Check whether a named feature has been provided.

        Initially no features are provided

        >>> c = ConfigurationContext()
        >>> c.hasFeature('onlinehelp')
        False

        You can declare that a feature is provided

        >>> c.provideFeature('onlinehelp')

        and it becomes available

        >>> c.hasFeature('onlinehelp')
        True

        """
        return feature in self._features

    def provideFeature(self, feature):
        """Declare thata named feature has been provided.

        See `hasFeature` for examples.
        """
        self._features.add(feature)


class ConfigurationAdapterRegistry(object):
    """Simple adapter registry that manages directives as adapters

    >>> r = ConfigurationAdapterRegistry()
    >>> c = ConfigurationMachine()
    >>> r.factory(c, ('http://www.zope.com','xxx'))
    Traceback (most recent call last):
    ...
    ConfigurationError: ('Unknown directive', 'http://www.zope.com', 'xxx')
    >>> from zope.configuration.interfaces import IConfigurationContext
    >>> def f():
    ...     pass

    >>> r.register(IConfigurationContext, ('http://www.zope.com', 'xxx'), f)
    >>> r.factory(c, ('http://www.zope.com','xxx')) is f
    1
    >>> r.factory(c, ('http://www.zope.com','yyy')) is f
    Traceback (most recent call last):
    ...
    ConfigurationError: ('Unknown directive', 'http://www.zope.com', 'yyy')
    >>> r.register(IConfigurationContext, 'yyy', f)
    >>> r.factory(c, ('http://www.zope.com','yyy')) is f
    1

    Test the documentation feature:

    >>> r._docRegistry
    []
    >>> r.document(('ns', 'dir'), IFullInfo, IConfigurationContext, None,
    ...            'inf', None)
    >>> r._docRegistry[0][0] == ('ns', 'dir')
    1
    >>> r._docRegistry[0][1] is IFullInfo
    1
    >>> r._docRegistry[0][2] is IConfigurationContext
    1
    >>> r._docRegistry[0][3] is None
    1
    >>> r._docRegistry[0][4] == 'inf'
    1
    >>> r._docRegistry[0][5] is None
    1
    >>> r.document('all-dir', None, None, None, None)
    >>> r._docRegistry[1][0]
    ('', 'all-dir')
    """


    def __init__(self):
        super(ConfigurationAdapterRegistry, self).__init__()
        self._registry = {}
        # Stores tuples of form:
        #   (namespace, name), schema, usedIn, info, parent
        self._docRegistry = []

    def register(self, interface, name, factory):
        r = self._registry.get(name)
        if r is None:
            r = AdapterRegistry()
            self._registry[name] = r

        r.register([interface], Interface, '', factory)

    def document(self, name, schema, usedIn, handler, info, parent=None):
        if isinstance(name, (str, unicode)):
            name = ('', name)
        self._docRegistry.append((name, schema, usedIn, handler, info, parent))

    def factory(self, context, name):
        r = self._registry.get(name)
        if r is None:
            # Try namespace-independent name
            ns, n = name
            r = self._registry.get(n)
            if r is None:
                raise ConfigurationError("Unknown directive", ns, n)

        f = r.lookup1(providedBy(context), Interface)
        if f is None:
            raise ConfigurationError(
                "The directive %s cannot be used in this context" % (name, ))
        return f

class ConfigurationMachine(ConfigurationAdapterRegistry, ConfigurationContext):
    """Configuration machine

    Example:

    >>> machine = ConfigurationMachine()
    >>> ns = "http://www.zope.org/testing"

    Register a directive:

    >>> machine((metans, "directive"),
    ...         namespace=ns, name="simple",
    ...         schema="zope.configuration.tests.directives.ISimple",
    ...         handler="zope.configuration.tests.directives.simple")

    and try it out:

    >>> machine((ns, "simple"), a=u"aa", c=u"cc")

    >>> machine.actions
    [(('simple', u'aa', u'xxx', 'cc'), f, (u'aa', u'xxx', 'cc'))]

    A more extensive example can be found in the unit tests.
    """

    implements(IConfigurationContext)

    package = None
    basepath = None
    includepath = ()
    info = ''

    def __init__(self):
        super(ConfigurationMachine, self).__init__()
        self.actions = []
        self.stack = [RootStackItem(self)]
        self.i18n_strings = {}
        _bootstrap(self)

    def begin(self, __name, __data=None, __info=None, **kw):
        if __data:
            if kw:
                raise TypeError("Can't provide a mapping object and keyword "
                                "arguments")
        else:
            __data = kw
        self.stack.append(self.stack[-1].contained(__name, __data, __info))

    def end(self):
        self.stack.pop().finish()

    def __call__(self, __name, __info=None, **__kw):
        self.begin(__name, __kw, __info)
        self.end()

    def getInfo(self):
        return self.stack[-1].context.info

    def setInfo(self, info):
        self.stack[-1].context.info = info

    def execute_actions(self, clear=True, testing=False):
        """Execute the configuration actions

        This calls the action callables after resolving conflicts

        For example:

        >>> output = []
        >>> def f(*a, **k):
        ...    output.append(('f', a, k))
        >>> context = ConfigurationMachine()
        >>> context.actions = [
        ...   (1, f, (1,)),
        ...   (1, f, (11,), {}, ('x', )),
        ...   (2, f, (2,)),
        ...   ]
        >>> context.execute_actions()
        >>> output
        [('f', (1,), {}), ('f', (2,), {})]

        If the action raises an error, we convert it to a
        ConfigurationExecutionError.

        >>> output = []
        >>> def bad():
        ...    bad.xxx
        >>> context.actions = [
        ...   (1, f, (1,)),
        ...   (1, f, (11,), {}, ('x', )),
        ...   (2, f, (2,)),
        ...   (3, bad, (), {}, (), 'oops')
        ...   ]
        >>> try:
        ...    v = context.execute_actions()
        ... except ConfigurationExecutionError, v:
        ...    pass
        >>> print v
        exceptions.AttributeError: 'function' object has no attribute 'xxx'
          in:
          oops


        Note that actions executed before the error still have an effect:

        >>> output
        [('f', (1,), {}), ('f', (2,), {})]


        """
        try:
            for action in resolveConflicts(self.actions):
                (discriminator, callable, args, kw, includepath, info, order
                 ) = expand_action(*action)
                if callable is None:
                    continue
                try:
                    callable(*args, **kw)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    if testing:
                        raise
                    t, v, tb = sys.exc_info()
                    raise ConfigurationExecutionError(t, v, info), None, tb
        finally:
            if clear:
                del self.actions[:]


class ConfigurationExecutionError(ConfigurationError):
    """An error occurred during execution of a configuration action
    """

    def __init__(self, etype, evalue, info):
        self.etype, self.evalue, self.info = etype, evalue, info

    def __str__(self):
        return "%s: %s\n  in:\n  %s" % (self.etype, self.evalue, self.info)

##############################################################################
# Stack items

class IStackItem(Interface):
    """Configuration machine stack items

    Stack items are created when a directive is being processed.

    A stack item is created for each directive use.
    """

    def contained(name, data, info):
        """Begin processing a contained directive

        The data are a dictionary of attribute names mapped to unicode
        strings.

        The info argument is an object that can be converted to a
        string and that contains information about the directive.

        The begin method returns the next item to be placed on the stack.
        """

    def finish():
        """Finish processing a directive
        """

class SimpleStackItem(object):
    """Simple stack item

    A simple stack item can't have anything added after it.  It can
    only be removed.  It is used for simple directives and
    subdirectives, which can't contain other directives.

    It also defers any computation until the end of the directive
    has been reached.
    """

    implements(IStackItem)

    def __init__(self, context, handler, info, *argdata):
        newcontext = GroupingContextDecorator(context)
        newcontext.info = info
        self.context = newcontext
        self.handler = handler
        self.argdata = argdata

    def contained(self, name, data, info):
        raise ConfigurationError("Invalid directive %s" % str(name))

    def finish(self):
        # We're going to use the context that was passed to us, which wasn't
        # created for the directive.  We want to set it's info to the one
        # passed to us while we make the call, so we'll save the old one
        # and restore it.
        context = self.context
        args = toargs(context, *self.argdata)
        actions = self.handler(context, **args)
        if actions:
            # we allow the handler to return nothing
            for action in actions:
                context.action(*action)

class RootStackItem(object):

    def __init__(self, context):
        self.context = context

    def contained(self, name, data, info):
        """Handle a contained directive

        We have to compute a new stack item by getting a named adapter
        for the current context object.

        """
        factory = self.context.factory(self.context, name)
        if factory is None:
            raise ConfigurationError("Invalid directive", name)
        adapter = factory(self.context, data, info)
        return adapter

    def finish(self):
        pass

class GroupingStackItem(RootStackItem):
    """Stack item for a grouping directive

    A grouping stack item is in the stack when a grouping directive is
    being processed.  Grouping directives group other directives.
    Often, they just manage common data, but they may also take
    actions, either before or after contained directives are executed.

    A grouping stack item is created with a grouping directive
    definition, a configuration context, and directive data.

    To see how this works, let's look at an example:

    We need a context. We'll just use a configuration machine

    >>> context = ConfigurationMachine()

    We need a callable to use in configuration actions.  We'll use a
    convenient one from the tests:

    >>> from zope.configuration.tests.directives import f

    We need a handler for the grouping directive. This is a class
    that implements a context decorator.  The decorator must also
    provide ``before`` and ``after`` methods that are called before
    and after any contained directives are processed.  We'll typically
    subclass ``GroupingContextDecorator``, which provides context
    decoration, and default ``before`` and ``after`` methods.


    >>> class SampleGrouping(GroupingContextDecorator):
    ...    def before(self):
    ...       self.action(('before', self.x, self.y), f)
    ...    def after(self):
    ...       self.action(('after'), f)

    We'll use our decorator to decorate our initial context, providing
    keyword arguments x and y:

    >>> dec = SampleGrouping(context, x=1, y=2)

    Note that the keyword arguments are made attributes of the
    decorator.

    Now we'll create the stack item.

    >>> item = GroupingStackItem(dec)

    We still haven't called the before action yet, which we can verify
    by looking at the context actions:

    >>> context.actions
    []

    Subdirectives will get looked up as adapters of the context.

    We'll create a simple handler:

    >>> def simple(context, data, info):
    ...     context.action(("simple", context.x, context.y, data), f)
    ...     return info

    and register it with the context:

    >>> context.register(IConfigurationContext, (testns, 'simple'), simple)

    This handler isn't really a propert handler, because it doesn't
    return a new context.  It will do for this example.

    Now we'll call the contained method on the stack item:

    >>> item.contained((testns, 'simple'), {'z': 'zope'}, "someinfo")
    'someinfo'

    We can verify thet the simple method was called by looking at the
    context actions. Note that the before method was called before
    handling the contained directive.

    >>> from pprint import PrettyPrinter
    >>> pprint=PrettyPrinter(width=60).pprint

    >>> pprint(context.actions)
    [(('before', 1, 2), f),
     (('simple', 1, 2, {'z': 'zope'}), f)]

    Finally, we call finish, which calls the decorator after method:

    >>> item.finish()

    >>> pprint(context.actions)
    [(('before', 1, 2), f),
     (('simple', 1, 2, {'z': 'zope'}), f),
     ('after', f)]


    If there were no nested directives:

    >>> context = ConfigurationMachine()
    >>> dec = SampleGrouping(context, x=1, y=2)
    >>> item = GroupingStackItem(dec)
    >>> item.finish()

    Then before will be when we call finish:

    >>> pprint(context.actions)
    [(('before', 1, 2), f), ('after', f)]

    """

    implements(IStackItem)

    def __init__(self, context):
        super(GroupingStackItem, self).__init__(context)

    def __callBefore(self):
        actions = self.context.before()
        if actions:
            for action in actions:
                self.context.action(*action)
        self.__callBefore = noop

    def contained(self, name, data, info):
        self.__callBefore()
        return RootStackItem.contained(self, name, data, info)

    def finish(self):
        self.__callBefore()
        actions = self.context.after()
        if actions:
            for action in actions:
                self.context.action(*action)

def noop():
    pass

class ComplexStackItem(object):
    """Complex stack item

    A complex stack item is in the stack when a complex directive is
    being processed.  It only allows subdirectives to be used.

    A complex stack item is created with a complex directive
    definition (IComplexDirectiveContext), a configuration context,
    and directive data.

    To see how this works, let's look at an example:

    We need a context. We'll just use a configuration machine

    >>> context = ConfigurationMachine()

    We need a callable to use in configuration actions.  We'll use a
    convenient one from the tests:

    >>> from zope.configuration.tests.directives import f

    We need a handler for the complex directive. This is a class
    with a method for each subdirective:

    >>> class Handler(object):
    ...   def __init__(self, context, x, y):
    ...      self.context, self.x, self.y = context, x, y
    ...      context.action('init', f)
    ...   def sub(self, context, a, b):
    ...      context.action(('sub', a, b), f)
    ...   def __call__(self):
    ...      self.context.action(('call', self.x, self.y), f)

    We need a complex directive definition:

    >>> class Ixy(Interface):
    ...    x = zope.schema.TextLine()
    ...    y = zope.schema.TextLine()
    >>> definition = ComplexDirectiveDefinition(
    ...        context, name="test", schema=Ixy,
    ...        handler=Handler)
    >>> class Iab(Interface):
    ...    a = zope.schema.TextLine()
    ...    b = zope.schema.TextLine()
    >>> definition['sub'] = Iab, ''

    OK, now that we have the context, handler and definition, we're
    ready to use a stack item.

    >>> item = ComplexStackItem(definition, context, {'x': u'xv', 'y': u'yv'},
    ...                         'foo')

    When we created the definition, the handler (factory) was called.

    >>> context.actions
    [('init', f, (), {}, (), 'foo')]

    If a subdirective is provided, the ``contained`` method of the stack item
    is called. It will lookup the subdirective schema and call the
    corresponding method on the handler instance:

    >>> simple = item.contained(('somenamespace', 'sub'),
    ...                         {'a': u'av', 'b': u'bv'}, 'baz')
    >>> simple.finish()

    Note that the name passed to ``contained`` is a 2-part name, consisting of
    a namespace and a name within the namespace.

    >>> from pprint import PrettyPrinter
    >>> pprint=PrettyPrinter(width=60).pprint

    >>> pprint(context.actions)
    [('init', f, (), {}, (), 'foo'),
     (('sub', u'av', u'bv'), f, (), {}, (), 'baz')]

    The new stack item returned by contained is one that doesn't allow
    any more subdirectives,

    When all of the subdirectives have been provided, the ``finish``
    method is called:

    >>> item.finish()

    The stack item will call the handler if it is callable.

    >>> pprint(context.actions)
    [('init', f, (), {}, (), 'foo'),
     (('sub', u'av', u'bv'), f, (), {}, (), 'baz'),
     (('call', u'xv', u'yv'), f, (), {}, (), 'foo')]


    """

    implements(IStackItem)

    def __init__(self, meta, context, data, info):
        newcontext = GroupingContextDecorator(context)
        newcontext.info = info
        self.context = newcontext
        self.meta = meta

        # Call the handler contructor
        args = toargs(newcontext, meta.schema, data)
        self.handler = self.meta.handler(newcontext, **args)

    def contained(self, name, data, info):
        """Handle a subdirective
        """

        # Look up the subdirective meta data on our meta object
        ns, name = name
        schema = self.meta.get(name)
        if schema is None:
            raise ConfigurationError("Invalid directive", name)
        schema = schema[0] # strip off info
        handler = getattr(self.handler, name)
        return SimpleStackItem(self.context, handler, info, schema, data)

    def finish(self):

        # when we're done, we call the handler, which might return more actions

        # Need to save and restore old info

        try:
            actions = self.handler()
        except AttributeError, v:
            if v[0] == '__call__':
                return # noncallable
            raise
        except TypeError:
            return # non callable

        if actions:
            # we allow the handler to return nothing
            for action in actions:
                self.context.action(*action)

##############################################################################
# Helper classes

class GroupingContextDecorator(ConfigurationContext):
    """Helper mix-in class for building grouping directives

    See the discussion (and test) in GroupingStackItem.
    """

    implements(IConfigurationContext, IGroupingContext)

    def __init__(self, context, **kw):
        self.context = context
        for name, v in kw.items():
            setattr(self, name, v)

    def __getattr__(self, name,
                    getattr=getattr, setattr=setattr):
        v = getattr(self.context, name)
        # cache result in self
        setattr(self, name, v)
        return v

    def before(self):
        pass

    def after(self):
        pass

##############################################################################
# Directive-definition

class DirectiveSchema(fields.GlobalInterface):
    """A field that contains a global variable value that must be a schema
    """

class IDirectivesInfo(Interface):
    """Schema for the ``directives`` directive
    """

    namespace = zope.schema.URI(
        title=u"Namespace",
        description=u"The namespace in which directives' names will be defined",
        )

class IDirectivesContext(IDirectivesInfo, IConfigurationContext):
    pass

class DirectivesHandler(GroupingContextDecorator):
    """Handler for the directives directive

    This is just a grouping directive that adds a namespace attribute
    to the normal directive context.

    """
    implements(IDirectivesContext)


class IDirectiveInfo(Interface):
    """Information common to all directive definitions have
    """

    name = zope.schema.TextLine(
        title = u"Directive name",
        description = u"The name of the directive being defined",
        )

    schema = DirectiveSchema(
        title = u"Directive handler",
        description = u"The dotted name of the directive handler",
        )

class IFullInfo(IDirectiveInfo):
    """Information that all top-level directives (not subdirectives) have
    """

    handler = fields.GlobalObject(
        title = u"Directive handler",
        description = u"The dotted name of the directive handler",
        )

    usedIn = fields.GlobalInterface(
        title = u"The directive types the directive can be used in",
        description = (u"The interface of the directives that can contain "
                       u"the directive"
                       ),
        default = IConfigurationContext,
        )

class IStandaloneDirectiveInfo(IDirectivesInfo, IFullInfo):
    """Info for full directives defined outside a directives directives
    """

def defineSimpleDirective(context, name, schema, handler,
                          namespace='', usedIn=IConfigurationContext):
    """Define a simple directive

    Define and register a factory that invokes the simple directive
    and returns a new stack item, which is always the same simple stack item.

    If the namespace is '*', the directive is registered for all namespaces.

    for example:

    >>> context = ConfigurationMachine()
    >>> from zope.configuration.tests.directives import f
    >>> class Ixy(Interface):
    ...    x = zope.schema.TextLine()
    ...    y = zope.schema.TextLine()
    >>> def s(context, x, y):
    ...    context.action(('s', x, y), f)

    >>> defineSimpleDirective(context, 's', Ixy, s, testns)

    >>> context((testns, "s"), x=u"vx", y=u"vy")
    >>> context.actions
    [(('s', u'vx', u'vy'), f)]

    >>> context(('http://www.zope.com/t1', "s"), x=u"vx", y=u"vy")
    Traceback (most recent call last):
    ...
    ConfigurationError: ('Unknown directive', 'http://www.zope.com/t1', 's')

    >>> context = ConfigurationMachine()
    >>> defineSimpleDirective(context, 's', Ixy, s, "*")

    >>> context(('http://www.zope.com/t1', "s"), x=u"vx", y=u"vy")
    >>> context.actions
    [(('s', u'vx', u'vy'), f)]

    """

    namespace = namespace or context.namespace
    if namespace != '*':
        name = namespace, name

    def factory(context, data, info):
        return SimpleStackItem(context, handler, info, schema, data)
    factory.schema = schema

    context.register(usedIn, name, factory)
    context.document(name, schema, usedIn, handler, context.info)

def defineGroupingDirective(context, name, schema, handler,
                            namespace='', usedIn=IConfigurationContext):
    """Define a grouping directive

    Define and register a factory that sets up a grouping directive.

    If the namespace is '*', the directive is registered for all namespaces.

    for example:

    >>> context = ConfigurationMachine()
    >>> from zope.configuration.tests.directives import f
    >>> class Ixy(Interface):
    ...    x = zope.schema.TextLine()
    ...    y = zope.schema.TextLine()

    We won't bother creating a special grouping directive class. We'll
    just use GroupingContextDecorator, which simply sets up a grouping
    context that has extra attributes defined by a schema:

    >>> defineGroupingDirective(context, 'g', Ixy,
    ...                         GroupingContextDecorator, testns)

    >>> context.begin((testns, "g"), x=u"vx", y=u"vy")
    >>> context.stack[-1].context.x
    u'vx'
    >>> context.stack[-1].context.y
    u'vy'

    >>> context(('http://www.zope.com/t1', "g"), x=u"vx", y=u"vy")
    Traceback (most recent call last):
    ...
    ConfigurationError: ('Unknown directive', 'http://www.zope.com/t1', 'g')

    >>> context = ConfigurationMachine()
    >>> defineGroupingDirective(context, 'g', Ixy,
    ...                         GroupingContextDecorator, "*")

    >>> context.begin(('http://www.zope.com/t1', "g"), x=u"vx", y=u"vy")
    >>> context.stack[-1].context.x
    u'vx'
    >>> context.stack[-1].context.y
    u'vy'

    """

    namespace = namespace or context.namespace
    if namespace != '*':
        name = namespace, name

    def factory(context, data, info):
        args = toargs(context, schema, data)
        newcontext = handler(context, **args)
        newcontext.info = info
        return GroupingStackItem(newcontext)
    factory.schema = schema

    context.register(usedIn, name, factory)
    context.document(name, schema, usedIn, handler, context.info)


class IComplexDirectiveContext(IFullInfo, IConfigurationContext):
    pass

class ComplexDirectiveDefinition(GroupingContextDecorator, dict):
    """Handler for defining complex directives

    See the description and tests for ComplexStackItem.
    """

    implements(IComplexDirectiveContext)

    def before(self):

        def factory(context, data, info):
            return ComplexStackItem(self, context, data, info)
        factory.schema = self.schema

        self.register(self.usedIn, (self.namespace, self.name), factory)
        self.document((self.namespace, self.name), self.schema, self.usedIn,
                      self.handler, self.info)

def subdirective(context, name, schema):
    context.document((context.namespace, name), schema, context.usedIn,
                     getattr(context.handler, name, context.handler),
                     context.info, context.context)
    context.context[name] = schema, context.info

##############################################################################
# Features

class IProvidesDirectiveInfo(Interface):
    """Information for a <meta:provides> directive"""

    feature = zope.schema.TextLine(
        title = u"Feature name",
        description = u"""The name of the feature being provided

        You can test available features with zcml:condition="have featurename".
        """,
        )

def provides(context, feature):
    """Declare that a feature is provided in context.

    >>> c = ConfigurationContext()
    >>> provides(c, 'apidoc')
    >>> c.hasFeature('apidoc')
    True

    Spaces are not allowed in feature names (this is reserved for providing
    many features with a single directive in the futute).

    >>> provides(c, 'apidoc onlinehelp')
    Traceback (most recent call last):
      ...
    ValueError: Only one feature name allowed

    >>> c.hasFeature('apidoc onlinehelp')
    False

    """
    if len(feature.split()) > 1:
        raise ValueError("Only one feature name allowed")
    context.provideFeature(feature)


##############################################################################
# Argument conversion

def toargs(context, schema, data):
    """Marshal data to an argument dictionary using a schema

    Names that are python keywords have an underscore added as a
    suffix in the schema and in the argument list, but are used
    without the underscore in the data.

    The fields in the schema must all implement IFromUnicode.

    All of the items in the data must have corresponding fields in the
    schema unless the schema has a true tagged value named
    'keyword_arguments'.

    Here's an example:

    >>> from zope import schema

    >>> class schema(Interface):
    ...     in_ = zope.schema.Int(constraint=lambda v: v > 0)
    ...     f = zope.schema.Float()
    ...     n = zope.schema.TextLine(min_length=1, default=u"rob")
    ...     x = zope.schema.BytesLine(required=False)
    ...     u = zope.schema.URI()

    >>> context = ConfigurationMachine()
    >>> from pprint import PrettyPrinter
    >>> pprint=PrettyPrinter(width=50).pprint

    >>> pprint(toargs(context, schema,
    ...        {'in': u'1', 'f': u'1.2', 'n': u'bob', 'x': u'x.y.z',
    ...          'u': u'http://www.zope.org' }))
    {'f': 1.2,
     'in_': 1,
     'n': u'bob',
     'u': 'http://www.zope.org',
     'x': 'x.y.z'}

    If we have extra data, we'll get an error:

    >>> toargs(context, schema,
    ...        {'in': u'1', 'f': u'1.2', 'n': u'bob', 'x': u'x.y.z',
    ...          'u': u'http://www.zope.org', 'a': u'1'})
    Traceback (most recent call last):
    ...
    ConfigurationError: ('Unrecognized parameters:', 'a')

    Unless we set a tagged value to say that extra arguments are ok:

    >>> schema.setTaggedValue('keyword_arguments', True)

    >>> pprint(toargs(context, schema,
    ...        {'in': u'1', 'f': u'1.2', 'n': u'bob', 'x': u'x.y.z',
    ...          'u': u'http://www.zope.org', 'a': u'1'}))
    {'a': u'1',
     'f': 1.2,
     'in_': 1,
     'n': u'bob',
     'u': 'http://www.zope.org',
     'x': 'x.y.z'}


    If we ommit required data we get an error telling us what was omitted:

    >>> pprint(toargs(context, schema,
    ...        {'in': u'1', 'f': u'1.2', 'n': u'bob', 'x': u'x.y.z'}))
    Traceback (most recent call last):
    ...
    ConfigurationError: ('Missing parameter:', 'u')

    Although we can omit not-required data:

    >>> pprint(toargs(context, schema,
    ...        {'in': u'1', 'f': u'1.2', 'n': u'bob',
    ...          'u': u'http://www.zope.org', 'a': u'1'}))
    {'a': u'1',
     'f': 1.2,
     'in_': 1,
     'n': u'bob',
     'u': 'http://www.zope.org'}

    And we can ommit required fields if they have valid defaults
    (defaults that are valid values):


    >>> pprint(toargs(context, schema,
    ...        {'in': u'1', 'f': u'1.2',
    ...          'u': u'http://www.zope.org', 'a': u'1'}))
    {'a': u'1',
     'f': 1.2,
     'in_': 1,
     'n': u'rob',
     'u': 'http://www.zope.org'}

    We also get an error if any data was invalid:

    >>> pprint(toargs(context, schema,
    ...        {'in': u'0', 'f': u'1.2', 'n': u'bob', 'x': u'x.y.z',
    ...          'u': u'http://www.zope.org', 'a': u'1'}))
    Traceback (most recent call last):
    ...
    ConfigurationError: ('Invalid value for', 'in', '0')

    """

    data = dict(data)
    args = {}
    for name, field in schema.namesAndDescriptions(True):
        field = field.bind(context)
        n = name
        if n.endswith('_') and iskeyword(n[:-1]):
            n = n[:-1]

        s = data.get(n, data)
        if s is not data:
            s = unicode(s)
            del data[n]

            try:
                args[str(name)] = field.fromUnicode(s)
            except zope.schema.ValidationError, v:
                raise ConfigurationError(
                    "Invalid value for", n, str(v)), None, sys.exc_info()[2]
        elif field.required:
            # if the default is valid, we can use that:
            default = field.default
            try:
                field.validate(default)
            except zope.schema.ValidationError:
                raise ConfigurationError("Missing parameter:", n)
            args[str(name)] = default

    if data:
        # we had data left over
        try:
            keyword_arguments = schema.getTaggedValue('keyword_arguments')
        except KeyError:
            keyword_arguments = False
        if not keyword_arguments:
            raise ConfigurationError("Unrecognized parameters:", *data)

        for name in data:
            args[str(name)] = data[name]

    return args

##############################################################################
# Conflict resolution

def expand_action(discriminator, callable=None, args=(), kw={},
                   includepath=(), info='', order=0):
    return (discriminator, callable, args, kw,
            includepath, info, order)

def resolveConflicts(actions):
    """Resolve conflicting actions

    Given an actions list, identify and try to resolve conflicting actions.
    Actions conflict if they have the same non-null discriminator.
    Conflicting actions can be resolved if the include path of one of
    the actions is a prefix of the includepaths of the other
    conflicting actions and is unequal to the include paths in the
    other conflicting actions.

    Here are some examples to illustrate how this works:

    >>> from zope.configuration.tests.directives import f
    >>> from pprint import PrettyPrinter
    >>> pprint=PrettyPrinter(width=60).pprint
    >>> pprint(resolveConflicts([
    ...    (None, f),
    ...    (1, f, (1,), {}, (), 'first'),
    ...    (1, f, (2,), {}, ('x',), 'second'),
    ...    (1, f, (3,), {}, ('y',), 'third'),
    ...    (4, f, (4,), {}, ('y',), 'should be last', 99999),
    ...    (3, f, (3,), {}, ('y',)),
    ...    (None, f, (5,), {}, ('y',)),
    ... ]))
    [(None, f),
     (1, f, (1,), {}, (), 'first'),
     (3, f, (3,), {}, ('y',)),
     (None, f, (5,), {}, ('y',)),
     (4, f, (4,), {}, ('y',), 'should be last')]

    >>> try:
    ...     v = resolveConflicts([
    ...        (None, f),
    ...        (1, f, (2,), {}, ('x',), 'eek'),
    ...        (1, f, (3,), {}, ('y',), 'ack'),
    ...        (4, f, (4,), {}, ('y',)),
    ...        (3, f, (3,), {}, ('y',)),
    ...        (None, f, (5,), {}, ('y',)),
    ...     ])
    ... except ConfigurationConflictError, v:
    ...    pass
    >>> print v
    Conflicting configuration actions
      For: 1
        eek
        ack

    """

    # organize actions by discriminators
    unique = {}
    output = []
    for i in range(len(actions)):
        (discriminator, callable, args, kw, includepath, info, order
         ) = expand_action(*(actions[i]))

        order = order or i
        if discriminator is None:
            # The discriminator is None, so this directive can
            # never conflict. We can add it directly to the
            # configuration actions.
            output.append(
                (order, discriminator, callable, args, kw, includepath, info)
                )
            continue


        a = unique.setdefault(discriminator, [])
        a.append(
            (includepath, order, callable, args, kw, info)
            )

    # Check for conflicts
    conflicts = {}
    for discriminator, dups in unique.items():

        # We need to sort the actions by the paths so that the shortest
        # path with a given prefix comes first:
        dups.sort()
        (basepath, i, callable, args, kw, baseinfo) = dups[0]
        output.append(
            (i, discriminator, callable, args, kw, basepath, baseinfo)
            )
        for includepath, i, callable, args, kw, info in dups[1:]:
            # Test whether path is a prefix of opath
            if (includepath[:len(basepath)] != basepath # not a prefix
                or
                (includepath == basepath)
                ):
                if discriminator not in conflicts:
                    conflicts[discriminator] = [baseinfo]
                conflicts[discriminator].append(info)


    if conflicts:
        raise ConfigurationConflictError(conflicts)

    # Now put the output back in the original order, and return it:
    output.sort()
    r = []
    for o in output:
        action = o[1:]
        while len(action) > 2 and not action[-1]:
            action = action[:-1]
        r.append(action)

    return r

class ConfigurationConflictError(ConfigurationError):

    def __init__(self, conflicts):
        self._conflicts = conflicts

    def __str__(self):
        r = ["Conflicting configuration actions"]
        items = self._conflicts.items()
        items.sort()
        for discriminator, infos in items:
            r.append("  For: %s" % (discriminator, ))
            for info in infos:
                for line in unicode(info).rstrip().split(u'\n'):
                    r.append(u"    "+line)

        return "\n".join(r)


##############################################################################
# Bootstap code


def _bootstrap(context):

    # Set enough machinery to register other directives

    # Define the directive (simple directive) directive by calling it's
    # handler directly

    info = 'Manually registered in zope/configuration/config.py'

    context.info = info
    defineSimpleDirective(
        context,
        namespace=metans, name='directive',
        schema=IStandaloneDirectiveInfo,
        handler=defineSimpleDirective)
    context.info = ''

    # OK, now that we have that, we can use the machine to define the
    # other directives. This isn't the easiest way to proceed, but it lets
    # us eat our own dogfood. :)

    # Standalone groupingDirective
    context((metans, 'directive'),
            info,
            name='groupingDirective',
            namespace=metans,
            handler="zope.configuration.config.defineGroupingDirective",
            schema="zope.configuration.config.IStandaloneDirectiveInfo"
            )

    # Now we can use the grouping directive to define the directives directive
    context((metans, 'groupingDirective'),
            info,
            name='directives',
            namespace=metans,
            handler="zope.configuration.config.DirectivesHandler",
            schema="zope.configuration.config.IDirectivesInfo"
            )

    # directive and groupingDirective inside directives
    context((metans, 'directive'),
            info,
            name='directive',
            namespace=metans,
            usedIn="zope.configuration.config.IDirectivesContext",
            handler="zope.configuration.config.defineSimpleDirective",
            schema="zope.configuration.config.IFullInfo"
            )
    context((metans, 'directive'),
            info,
            name='groupingDirective',
            namespace=metans,
            usedIn="zope.configuration.config.IDirectivesContext",
            handler="zope.configuration.config.defineGroupingDirective",
            schema="zope.configuration.config.IFullInfo"
            )

    # Setup complex directive directive, both standalone, and in
    # directives directive
    context((metans, 'groupingDirective'),
            info,
            name='complexDirective',
            namespace=metans,
            handler="zope.configuration.config.ComplexDirectiveDefinition",
            schema="zope.configuration.config.IStandaloneDirectiveInfo"
            )
    context((metans, 'groupingDirective'),
            info,
            name='complexDirective',
            namespace=metans,
            usedIn="zope.configuration.config.IDirectivesContext",
            handler="zope.configuration.config.ComplexDirectiveDefinition",
            schema="zope.configuration.config.IFullInfo"
            )

    # Finally, setup subdirective directive
    context((metans, 'directive'),
            info,
            name='subdirective',
            namespace=metans,
            usedIn="zope.configuration.config.IComplexDirectiveContext",
            handler="zope.configuration.config.subdirective",
            schema="zope.configuration.config.IDirectiveInfo"
            )

    # meta:provides
    context((metans, 'directive'),
            info,
            name='provides',
            namespace=metans,
            handler="zope.configuration.config.provides",
            schema="zope.configuration.config.IProvidesDirectiveInfo"
            )

