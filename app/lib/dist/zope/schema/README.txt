==============
Zope 3 Schemas
==============

Introduction
------------

*This package is intended to be independently reusable in any Python
project. It is maintained by the* `Zope Toolkit project <http://docs.zope.org/zopetoolkit/>`_.

Schemas extend the notion of interfaces to detailed descriptions of Attributes
(but not methods). Every schema is an interface and specifies the public
fields of an object. A *field* roughly corresponds to an attribute of a
python object. But a Field provides space for at least a title and a
description. It can also constrain its value and provide a validation method.
Besides you can optionally specify characteristics such as its value being
read-only or not required.

Zope 3 schemas were born when Jim Fulton and Martijn Faassen thought
about Formulator for Zope 3 and ``PropertySets`` while at the `Zope 3
sprint`_ at the Zope BBQ in Berlin. They realized that if you strip
all view logic from forms then you have something similar to interfaces. And
thus schemas were born.

.. _Zope 3 sprint: http://dev.zope.org/Zope3/ZopeBBQ2002Sprint

.. contents::

Simple Usage
------------

Let's have a look at a simple example. First we write an interface as usual,
but instead of describing the attributes of the interface with ``Attribute``
instances, we now use schema fields:

  >>> import zope.interface
  >>> import zope.schema

  >>> class IBookmark(zope.interface.Interface):
  ...     title = zope.schema.TextLine(
  ...         title=u'Title',
  ...         description=u'The title of the bookmark',
  ...         required=True)
  ...
  ...     url = zope.schema.URI(
  ...         title=u'Bookmark URL',
  ...         description=u'URL of the Bookmark',
  ...         required=True)
  ...

Now we create a class that implements this interface and create an instance of
it:

  >>> class Bookmark(object):
  ...     zope.interface.implements(IBookmark)
  ...
  ...     title = None
  ...     url = None

  >>> bm = Bookmark()

We would now like to only add validated values to the class. This can be done
by first validating and then setting the value on the object. The first step
is to define some data:

  >>> title = u'Zope 3 Website'
  >>> url = 'http://dev.zope.org/Zope3'

Now we, get the fields from the interface:

  >>> title_field = IBookmark.get('title')
  >>> url_field = IBookmark.get('url')

Next we have to bind these fields to the context, so that instance-specific
information can be used for validation:

  >>> title_bound = title_field.bind(bm)
  >>> url_bound = url_field.bind(bm)

Now that the fields are bound, we can finally validate the data:

  >>> title_bound.validate(title)
  >>> url_bound.validate(url)

If the validation is successful, ``None`` is returned. If a validation error
occurs a ``ValidationError`` will be raised; for example:

  >>> url_bound.validate(u'http://zope.org/foo')
  Traceback (most recent call last):
  ...
  WrongType: (u'http://zope.org/foo', <type 'str'>, 'url')

  >>> url_bound.validate('foo.bar')
  Traceback (most recent call last):
  ...
  InvalidURI: foo.bar

Now that the data has been successfully validated, we can set it on the
object:

  >>> title_bound.set(bm, title)
  >>> url_bound.set(bm, url)

That's it. You still might think this is a lot of work to validate and set a
value for an object. Note, however, that it is very easy to write helper
functions that automate these tasks. If correctly designed, you will never
have to worry explicitly about validation again, since the system takes care
of it automatically.


What is a schema, how does it compare to an interface?
------------------------------------------------------

A schema is an extended interface which defines fields.  You can validate that
the attributes of an object conform to their fields defined on the schema.
With plain interfaces you can only validate that methods conform to their
interface specification.

So interfaces and schemas refer to different aspects of an object
(respectively its code and state).

A schema starts out like an interface but defines certain fields to
which an object's attributes must conform.  Let's look at a stripped
down example from the programmer's tutorial:

    >>> import re

    >>> class IContact(zope.interface.Interface):
    ...     """Provides access to basic contact information."""
    ...
    ...     first = zope.schema.TextLine(title=u"First name")
    ...
    ...     last = zope.schema.TextLine(title=u"Last name")
    ...
    ...     email = zope.schema.TextLine(title=u"Electronic mail address")
    ...
    ...     address = zope.schema.Text(title=u"Postal address")
    ...
    ...     postalCode = zope.schema.TextLine(
    ...         title=u"Postal code",
    ...         constraint=re.compile("\d{5,5}(-\d{4,4})?$").match)

``TextLine`` is a field and expresses that an attribute is a single line
of Unicode text.  ``Text`` expresses an arbitrary Unicode ("text")
object.  The most interesting part is the last attribute
specification.  It constrains the ``postalCode`` attribute to only have
values that are US postal codes.

Now we want a class that adheres to the ``IContact`` schema:

    >>> class Contact(object):
    ...     zope.interface.implements(IContact)
    ...
    ...     def __init__(self, first, last, email, address, pc):
    ...         self.first = first
    ...         self.last = last
    ...         self.email = email
    ...         self.address = address
    ...         self.postalCode = pc

Now you can see if an instance of ``Contact`` actually implements the
schema:

    >>> someone = Contact(u'Tim', u'Roberts', u'tim@roberts', u'',
    ...                   u'12032-3492')

    >>> for field in zope.schema.getFields(IContact).values():
    ...     bound = field.bind(someone)
    ...     bound.validate(bound.get(someone))


Data Modeling Concepts
-----------------------

The ``zope.schema`` package provides a core set of field types,
including single- and multi-line text fields, binary data fields,
integers, floating-point numbers, and date/time values.

Selection issues; field type can specify:

- "Raw" data value

  Simple values not constrained by a selection list.

- Value from enumeration (options provided by schema)

  This models a single selection from a list of possible values
  specified by the schema.  The selection list is expected to be the
  same for all values of the type.  Changes to the list are driven by
  schema evolution.

  This is done by mixing-in the ``IEnumerated`` interface into the field
  type, and the Enumerated mix-in for the implementation (or emulating
  it in a concrete class).

- Value from selection list (options provided by an object)

  This models a single selection from a list of possible values
  specified by a source outside the schema.  The selection list
  depends entirely on the source of the list, and may vary over time
  and from object to object.  Changes to the list are not related to
  the schema, but changing how the list is determined is based on
  schema evolution.

  There is not currently a spelling of this, but it could be
  facilitated using alternate mix-ins similar to IEnumerated and
  Enumerated.

- Whether or not the field is read-only

  If a field value is read-only, it cannot be changed once the object is
  created.

- Whether or not the field is required

  If a field is designated as required, assigned field values must always
  be non-missing. See the next section for a description of missing values.

- A value designated as ``missing``

  Missing values, when assigned to an object, indicate that there is 'no
  data' for that field. Missing values are analogous to null values in
  relational databases. For example, a boolean value can be True, False, or
  missing, in which case its value is unknown.

  While Python's None is the most likely value to signify 'missing', some
  fields may use different values. For example, it is common for text fields
  to use the empty string ('') to signify that a value is missing. Numeric
  fields may use 0 or -1 instead of None as their missing value.

  A field that is 'required' signifies that missing values are invalid and
  should not be assigned.

- A default value

  Default field values are assigned to objects when they are first created.


Fields and Widgets
------------------

Widgets are components that display field values and, in the case of
writable fields, allow the user to edit those values.

Widgets:

- Display current field values, either in a read-only format, or in a
  format that lets the user change the field value.

- Update their corresponding field values based on values provided by users.

- Manage the relationships between their representation of a field value
  and the object's field value. For example, a widget responsible for
  editing a number will likely represent that number internally as a string.
  For this reason, widgets must be able to convert between the two value
  formats. In the case of the number-editing widget, string values typed
  by the user need to be converted to numbers such as int or float.

- Support the ability to assign a missing value to a field. For example,
  a widget may present a ``None`` option for selection that, when selected,
  indicates that the object should be updated with the field's ``missing``
  value.



References
----------

- Use case list, http://dev.zope.org/Zope3/Zope3SchemasUseCases

- Documented interfaces, zope/schema/interfaces.py

- Jim Fulton's Programmers Tutorial; in CVS:
  Docs/ZopeComponentArchitecture/PythonProgrammerTutorial/Chapter2
