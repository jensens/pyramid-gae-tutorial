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
"""Vocabulary support for schema.
"""
from zope.interface.declarations import directlyProvides, implements
from zope.schema.interfaces import ValidationError
from zope.schema.interfaces import IVocabularyRegistry
from zope.schema.interfaces import IVocabulary, IVocabularyTokenized
from zope.schema.interfaces import ITokenizedTerm, ITitledTokenizedTerm

# simple vocabularies performing enumerated-like tasks

_marker = object()

class SimpleTerm(object):
    """Simple tokenized term used by SimpleVocabulary."""

    implements(ITokenizedTerm)

    def __init__(self, value, token=None, title=None):
        """Create a term for value and token. If token is omitted,
        str(value) is used for the token.  If title is provided, 
        term implements ITitledTokenizedTerm.
        """
        self.value = value
        if token is None:
            token = value
        self.token = str(token)
        self.title = title
        if title is not None:
            directlyProvides(self, ITitledTokenizedTerm)

class SimpleVocabulary(object):
    """Vocabulary that works from a sequence of terms."""

    implements(IVocabularyTokenized)

    def __init__(self, terms, *interfaces):
        """Initialize the vocabulary given a list of terms.

        The vocabulary keeps a reference to the list of terms passed
        in; it should never be modified while the vocabulary is used.

        One or more interfaces may also be provided so that alternate
        widgets may be bound without subclassing.
        """
        self.by_value = {}
        self.by_token = {}
        self._terms = terms
        for term in self._terms:
            if term.value in self.by_value:
                raise ValueError(
                    'term values must be unique: %s' % repr(term.value))
            if term.token in self.by_token:
                raise ValueError(
                    'term tokens must be unique: %s' % repr(term.token))
            self.by_value[term.value] = term
            self.by_token[term.token] = term
        if interfaces:
            directlyProvides(self, *interfaces)

    def fromItems(cls, items, *interfaces):
        """Construct a vocabulary from a list of (token, value) pairs.

        The order of the items is preserved as the order of the terms
        in the vocabulary.  Terms are created by calling the class
        method createTerm() with the pair (value, token).

        One or more interfaces may also be provided so that alternate
        widgets may be bound without subclassing.
        """
        terms = [cls.createTerm(value, token) for (token, value) in items]
        return cls(terms, *interfaces)
    fromItems = classmethod(fromItems)

    def fromValues(cls, values, *interfaces):
        """Construct a vocabulary from a simple list.

        Values of the list become both the tokens and values of the
        terms in the vocabulary.  The order of the values is preserved
        as the order of the terms in the vocabulary.  Tokens are
        created by calling the class method createTerm() with the
        value as the only parameter.

        One or more interfaces may also be provided so that alternate
        widgets may be bound without subclassing.
        """
        terms = [cls.createTerm(value) for value in values]
        return cls(terms, *interfaces)
    fromValues = classmethod(fromValues)

    def createTerm(cls, *args):
        """Create a single term from data.

        Subclasses may override this with a class method that creates
        a term of the appropriate type from the arguments.
        """
        return SimpleTerm(*args)
    createTerm = classmethod(createTerm)

    def __contains__(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        try:
            return value in self.by_value
        except TypeError:
            # sometimes values are not hashable
            return False

    def getTerm(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        try:
            return self.by_value[value]
        except KeyError:
            raise LookupError(value)

    def getTermByToken(self, token):
        """See zope.schema.interfaces.IVocabularyTokenized"""
        try:
            return self.by_token[token]
        except KeyError:
            raise LookupError(token)

    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        return iter(self._terms)

    def __len__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        return len(self.by_value)


# registry code

class VocabularyRegistryError(LookupError):
    def __init__(self, name):
        self.name = name
        Exception.__init__(self, str(self))

    def __str__(self):
        return "unknown vocabulary: %r" % self.name


class VocabularyRegistry(object):
    __slots__ = '_map',
    implements(IVocabularyRegistry)

    def __init__(self):
        self._map = {}

    def get(self, object, name):
        """See zope.schema.interfaces.IVocabularyRegistry""" 
        try:
            vtype = self._map[name]
        except KeyError:
            raise VocabularyRegistryError(name)
        return vtype(object)

    def register(self, name, factory):
        self._map[name] = factory

_vocabularies = None

def getVocabularyRegistry():
    """Return the vocabulary registry.

    If the registry has not been created yet, an instance of
    VocabularyRegistry will be installed and used.
    """
    if _vocabularies is None:
        setVocabularyRegistry(VocabularyRegistry())
    return _vocabularies

def setVocabularyRegistry(registry):
    """Set the vocabulary registry."""
    global _vocabularies
    _vocabularies = registry

def _clear():
    """Remove the registries (for use by tests)."""
    global _vocabularies
    _vocabularies = None


try:
    from zope.testing.cleanup import addCleanUp
except ImportError:
    # don't have that part of Zope
    pass
else:
    addCleanUp(_clear)
    del addCleanUp
