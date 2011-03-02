##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Component Architecture Tests

$Id: tests.py 70794 2006-10-19 04:29:42Z baijum $
"""

from zope.testing import doctest
from zope.testing import renormalizing
import os
import re
import shutil
import sys
import tempfile
import unittest
import warnings
import zope.deprecation

# Used in doctests
from deprecation import deprecated
demo1 = 1
deprecated('demo1', 'demo1 is no more.')

demo2 = 2
deprecated('demo2', 'demo2 is no more.')

demo3 = 3
deprecated('demo3', 'demo3 is no more.')

demo4 = 4
def deprecatedemo4():
    """Demonstrate that deprecate() also works in a local scope."""
    deprecated('demo4', 'demo4 is no more.')

def warn(message, type_, stacklevel):
    print "From tests.py's showwarning():"
    
    frame = sys._getframe(stacklevel)
    path = frame.f_globals['__file__']
    file = open(path)
    lineno = frame.f_lineno
    for i in range(lineno):
        line = file.readline()

    print "%s:%s: %s: %s\n  %s" % (
        path,
        frame.f_lineno,
        type_.__name__,
        message,
        line.strip(),
        )


def setUpCreateModule(test):
    d = test.globs['tmp_d'] = tempfile.mkdtemp('deprecation')

    def create_module(modules=(), **kw):
        modules = dict(modules)
        modules.update(kw)
        for name, src in modules.iteritems():
            pname = name.split('.')
            if pname[-1] == '__init__':
                os.mkdir(os.path.join(d, *pname[:-1]))
                name = '.'.join(pname[:-1])
            open(os.path.join(d, *pname)+'.py', 'w').write(src)
            test.globs['created_modules'].append(name)

    test.globs['created_modules'] = []
    test.globs['create_module'] = create_module

    zope.deprecation.__path__.append(d)

def tearDownCreateModule(test):
    zope.deprecation.__path__.pop()
    shutil.rmtree(test.globs['tmp_d'])
    for name in test.globs['created_modules']:
        sys.modules.pop(name, None)

def setUp(test):
    test.globs['saved_warn'] = warnings.warn
    warnings.warn = warn
    setUpCreateModule(test)

def tearDown(test):
    tearDownCreateModule(test)
    warnings.warn = test.globs['saved_warn']
    del object.__getattribute__(sys.modules['zope.deprecation.tests'],
                                '_DeprecationProxy__deprecated')['demo4']

def test_suite():
    checker = renormalizing.RENormalizing([
        (re.compile('\\\\'), '/'),   # convert Windows paths to Unix paths
        ])

    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt',
                             setUp=setUp, tearDown=tearDown,
                             optionflags=doctest.ELLIPSIS,
                             checker=checker,
                             ),
        ))

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
