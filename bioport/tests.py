import os

import bioport
import z3c.testsetup

from zope.app.testing.functional import FunctionalTestCase as baseFunctionalTestCase
from zope.app.testing.functional import ZCMLLayer
from zope.interface import implements
from zope.sendmail.interfaces import IMailDelivery
from zope.testbrowser.testing import Browser

from bioport_repository.source import Source

from bioport_repository.tests.config import DSN, IMAGES_CACHE_LOCAL

ftesting_zcml = os.path.join(
    os.path.dirname(bioport.__file__), 'ftesting.zcml')


class MyLayer(ZCMLLayer):
    def setUp(self):
        """ Prevent zope.sendmail to start its thread during tests, or this will
        confuse the coverage analyzer"""
        from zope.sendmail import zcml
        zcml.queuedDelivery = lambda *args, **kwargs :None
        ZCMLLayer.setUp(self)

FunctionalLayer = MyLayer(ftesting_zcml, __name__, 'FunctionalLayer', allow_teardown=True)

test_suite = z3c.testsetup.register_all_tests('bioport')


class FunctionalTestCase(baseFunctionalTestCase):

    layer = FunctionalLayer

    def setUp(self):
        # XXX this setup should be in the layer
        baseFunctionalTestCase.setUp(self)
        # set up
        root = self.getRootFolder()
        self.app = app = root['app'] = bioport.app.Bioport()
        # define the db connection
        self.base_url = 'http://localhost/app'
        self.browser = browser = Browser()
        browser.handleErrors = False  # show some information when an arror occurs
        app['admin'].DB_CONNECTION = DSN
        app['admin'].LIMIT = 20
        app['admin'].IMAGES_CACHE_LOCAL = IMAGES_CACHE_LOCAL

        self.repo = repository = app.repository()
        self.repo.db.metadata.drop_all()
        repository.db.metadata.create_all()
        self.repo.db.clear_cache()
        this_dir = os.path.dirname(bioport.__file__)
        url = 'file://%s' % os.path.join(this_dir, 'admin_tests/data/knaw/list.xml')
        repository.add_source(Source(u'knaw_test', url, 'test'))

        repository.download_biographies(source=repository.get_source(u'knaw_test'))
        # add some categories as well
        repository.db.get_session().execute("insert into category (id, name) values (1, 'category1')")
        repository.db.get_session().execute("insert into category (id, name) values (2, 'category2')")

        if not os.path.exists(IMAGES_CACHE_LOCAL):
            os.mkdir(IMAGES_CACHE_LOCAL)

    def tearDown(self):
        baseFunctionalTestCase.tearDown(self)
        self.repo.db.metadata.drop_all()


messages = []


class FakeMailDelivery(object):

    implements(IMailDelivery)

    def send(self, source, dest, body):
        messages.append(dict(
            source=source, dest=dest, body=body
        ))
        return 'fake-message-id-%i@example.com' % len(messages)

