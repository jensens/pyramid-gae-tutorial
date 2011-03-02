==========================
Zope configuration system
==========================

The zope configuration system provides an extensible system for
supporting variouse kinds of configurations.

It is based on the idea of configuration directives. Users of the
configuration system provide configuration directives in some
language that express configuration choices. The intent is that the
language be pluggable.  An XML language is provided by default.

Configuration is performed in three stages. In the first stage,
directives are processed to compute configuration actions.
Configuration actions consist of:

- A discriminator

- A callable

- Positional arguments

- Keyword arguments

The actions are essentially delayed function calls.  Two or more
actions conflict if they have the same discriminator.  The
configuration system has rules for resolving conflicts. If conflicts
cannot be resolved, an error will result.  Conflict resolution
typically discards all but one of the conflicting actions, so that
the remaining action of the originally-conflicting actions no longer
conflicts.  Non-conflicting actions are executed in the order that
they were created by passing the positional and non-positional
arguments to the action callable.

The system is extensible. There is a meta-configuration language for
defining configuration directives. A directive is defined by
providing meta data about the directive and handler code to process
the directive.  There are four kinds of directives:

- Simple directives compute configuration actions.  Their handlers
  are typically functions that take a context and zero or more
  keyword arguments and return a sequence of configuration actions.

  To learn how to create simple directives, see `tests/test_simple.py`.


- Grouping directives collect information to be used by nested
  directives. They are called with a context object which they adapt
  to some interface that extends IConfigurationContext.

  To learn how to create grouping directives, look at the
  documentation in zopeconfigure.py, which provides the implementation
  of the zope `configure` directive.

  Other directives can be nested in grouping directives.

  To learn how to implement nested directives, look at the
  documentation in `tests/test_nested.py`.

- Complex directives are directives that have subdirectives.  
  Subdirectives have handlers that are simply methods of complex
  directives. Complex diretives are handled by factories, typically
  classes, that create objects that have methods for handling
  subdirectives. These objects also have __call__ methods that are
  called when processing of subdirectives is finished.

  Complex directives only exist to support old directive
  handlers. They will probably be deprecated in the future.

- Subdirectives are nested in complex directives. They are like
  simple directives except that they hane handlers that are complex
  directive methods.

  Subdirectives, like complex directives only exist to support old
  directive handlers. They will probably be deprecated in the future.
