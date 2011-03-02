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
"""Deprecation Package

$Id: __init__.py 70794 2006-10-19 04:29:42Z baijum $
"""
__docformat__ = "reStructuredText"

from zope.deprecation.deprecation import deprecated, deprecate, ShowSwitch
from zope.deprecation.deprecation import moved

# This attribute can be used to temporarly deactivate deprecation
# warnings, so that backward-compatibility code can import other
# backward-compatiblity components without warnings being produced.

__show__ = ShowSwitch()
