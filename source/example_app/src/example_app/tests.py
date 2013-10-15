# -*- coding: utf-8 -*-
import unittest
import doctest
from pprint import pprint
from interlude import interact
from plone.testing import layered
from .testing import APPENGINE_LAYER, WEBTEST_LAYER

optionflags = doctest.NORMALIZE_WHITESPACE | \
              doctest.ELLIPSIS | \
              doctest.REPORT_ONLY_FIRST_FAILURE | \
              doctest.REPORT_UDIFF

TESTFILES = [
    ('models.rst', APPENGINE_LAYER),
    ('views.rst', WEBTEST_LAYER),
]

def test_suite():
    return unittest.TestSuite([
        layered(doctest.DocFileSuite(
            filename,
            optionflags=optionflags,
            globs={'interact': interact,
                   'pprint': pprint, },
        ), layer)  for filename, layer in TESTFILES
    ])


