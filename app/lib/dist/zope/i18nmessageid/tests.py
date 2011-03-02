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
"""Message ID tests.
"""
import unittest
from doctest import DocFileSuite
from doctest import DocTestSuite

class PickleEqualityTests(unittest.TestCase):
    def setUp(self):
        # set the C version up as the used version
        import zope.i18nmessageid.message
        self.oldMessage = zope.i18nmessageid.message.Message

    def tearDown(self):
        # set the original version back up as the used version
        import zope.i18nmessageid.message
        zope.i18nmessageid.message.Message = self.oldMessage

    def test_message_pickling(self):
        from zope.i18nmessageid.message import pyMessage as Message
        robot = Message(u"robot-message", 'futurama', u"${name} is a robot.")

        self.assertEqual(robot, u'robot-message')
        self.failUnless(isinstance(robot, unicode))
        self.assertEqual(robot.default, u'${name} is a robot.')
        self.assertEqual(robot.mapping, None)

        # Only the python implementation has a _readonly attribute
        self.assertEqual(robot._readonly, True)
        self.assertRaises(
            TypeError,
            robot.__setattr__, 'domain', "planetexpress")
        self.assertRaises(
            TypeError,
            robot.__setattr__, 'default', u"${name} is not a robot.")
        self.assertRaises(
            TypeError,
            robot.__setattr__, 'mapping', {u'name': u'Bender'})
        
        new_robot = Message(robot, mapping={u'name': u'Bender'})
        self.assertEqual(new_robot, u'robot-message')
        self.assertEqual(new_robot.domain, 'futurama')
        self.assertEqual(new_robot.default, u'${name} is a robot.')
        self.assertEqual(new_robot.mapping, {u'name': u'Bender'})

        callable, args = new_robot.__reduce__()
        self.failUnless(callable is Message)
        self.assertEqual(
            args,
            (u'robot-message', 'futurama', u'${name} is a robot.',
             {u'name': u'Bender'}))

        fembot = Message(u'fembot')
        callable, args = fembot.__reduce__()
        self.failUnless(callable is Message)
        self.assertEqual(args, (u'fembot', None, None, None))

        import zope.i18nmessageid.message
        zope.i18nmessageid.message.Message = Message

        # First check if pickling and unpickling from pyMessage to
        # pyMessage works
        from pickle import dumps, loads
        pystate = dumps(new_robot)
        pickle_bot = loads(pystate)
        self.assertEqual(pickle_bot, u'robot-message')
        self.assertEqual(pickle_bot.domain, 'futurama')
        self.assertEqual(pickle_bot.default, u'${name} is a robot.')
        self.assertEqual(pickle_bot.mapping, {u'name': u'Bender'})
        self.assertEqual(pickle_bot._readonly, True)

        from zope.i18nmessageid.message import pyMessage
        self.failUnless(pickle_bot.__reduce__()[0] is pyMessage)
        del pickle_bot

        # Second check if cMessage is able to load the state of a pyMessage
        from _zope_i18nmessageid_message import Message
        zope.i18nmessageid.message.Message = Message
        c_bot = loads(pystate) 
        self.assertEqual(c_bot, u'robot-message')
        self.assertEqual(c_bot.domain, 'futurama')
        self.assertEqual(c_bot.default, u'${name} is a robot.')
        self.assertEqual(c_bot.mapping, {u'name': u'Bender'})
        self.failIf(hasattr(c_bot, '_readonly'))
        from _zope_i18nmessageid_message import Message as cMessage
        self.failUnless(c_bot.__reduce__()[0] is cMessage)

        # Last check if pyMessage can load a state of cMessage
        cstate = dumps(c_bot)
        del c_bot
        from zope.i18nmessageid.message import pyMessage as Message
        zope.i18nmessageid.message.Message = Message
        py_bot = loads(cstate)
        self.assertEqual(py_bot, u'robot-message')
        self.assertEqual(py_bot.domain, 'futurama')
        self.assertEqual(py_bot.default, u'${name} is a robot.')
        self.assertEqual(py_bot.mapping, {u'name': u'Bender'})
        self.assertEqual(py_bot._readonly, True)
        self.failUnless(py_bot.__reduce__()[0] is pyMessage)

        # Both pickle states should be equal
        self.assertEqual(pystate, cstate)

try:
    from _zope_i18nmessageid_message import Message as import_test
    def test_suite():
        return unittest.TestSuite((
	    DocTestSuite('zope.i18nmessageid.message'),
	    DocFileSuite('messages.txt', package='zope.i18nmessageid'),
            unittest.makeSuite(PickleEqualityTests),
	    ))
except ImportError: # pragma: no cover
    # couldnt import C version
    def test_suite():
        return unittest.TestSuite((
	    DocTestSuite('zope.i18nmessageid.message'),
	    DocFileSuite('messages.txt', package='zope.i18nmessageid'),
	    ))
    
