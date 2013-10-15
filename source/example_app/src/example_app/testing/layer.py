from google.appengine.datastore import datastore_stub_util
from google.appengine.tools.devappserver2.blob_upload \
    import Application as UploadApplication
import logging
import os
from plone.testing import Layer
from pyramid.interfaces import (
    ISessionFactory,
    ISession,
)
from pyramid import testing as pyramid_testing
import sys
import uuid
from webtest import TestApp
from zope.interface import implementer


class AppengineLayer(Layer):
    """Base Appengine Layer
    """

    defaultBases = ()

    def setUp(self):
        import gaefixes
        from google.appengine.ext import testbed
        self.testbed = testbed.Testbed()

    def testSetUp(self):
        self.testbed.activate()
        self.testbed.setup_env(overwrite=True, app_id='testing-server')

        # Create a consistency policy that will simulate the High Replication
        # consistency model.
        policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
                                                                 probability=1)
        self.testbed.init_datastore_v3_stub(consistency_policy=policy)
        self.testbed.init_blobstore_stub()
        self.testbed.init_files_stub()
        self.testbed.init_images_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_app_identity_stub()

        # make the global zca registry and the pyramid threadlocal registry the same.
        # The registry will still be empty since we do not load the
        # pyramid config in this layer.
        pyramid_testing.setUp()

    def tearDown(self):
        del self.testbed

    def testTearDown(self):
        self.testbed.deactivate()


APPENGINE_LAYER = AppengineLayer()


class WebtestLayer(Layer):
    """Base Appengine Layer
    """

    defaultBases = (APPENGINE_LAYER,)

    def testSetUp(self):
        from main import app_config
        config = app_config()
        application = config.make_wsgi_app()
        upload_application = UploadApplication(application)
        self.webtest = TestApp(application)
        self.uploadtest = TestApp(upload_application)
        self.app = self.webtest.app
        self.registry = self.app.registry
        self.config = pyramid_testing.setUp(registry=self.registry)

        @implementer(ISessionFactory)
        def testing_session_factory(instance=None):
            return self.session

        self.registry.registerUtility(testing_session_factory,
                                      ISessionFactory)

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self._session = pyramid_testing.DummySession()
        return self._session

    def testTearDown(self):
        if hasattr(self, '_session'):
            del self._session
        pyramid_testing.tearDown()

WEBTEST_LAYER = WebtestLayer()
