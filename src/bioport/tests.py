import os

import bioport
import z3c.testsetup

from zope.app.testing.functional import FunctionalTestCase as baseFunctionalTestCase
from zope.app.testing.functional import ZCMLLayer
from zope.interface import implements
from zope.sendmail.interfaces import IMailDelivery
from zope.testbrowser.testing import Browser

from bioport_repository.source import Source 


DB_CONNECTION =  'mysql://jge:MilanO8@localhost/bioport_test'

ftesting_zcml = os.path.join(
    os.path.dirname(bioport.__file__), 'ftesting.zcml')
FunctionalLayer = ZCMLLayer(ftesting_zcml, __name__, 'FunctionalLayer',
                            allow_teardown=True)

test_suite = z3c.testsetup.register_all_tests('bioport')


class FunctionalTestCase(baseFunctionalTestCase):
 
    layer = FunctionalLayer
 
    def setUp(self):
        # XXX this setup should be in the layer
        super(FunctionalTestCase, self).setUp()
        #set up
        root = self.getRootFolder()
        self.app = app = root['app'] = bioport.app.Bioport()
        
        #define the db connection
        self.base_url = 'http://localhost/app'
        self.browser = browser = Browser()
        browser.handleErrors = False #show some information when an arror occurs
        app['admin'].DB_CONNECTION = DB_CONNECTION
        app['admin'].LIMIT = 20
        self.repo = repository = app.repository(user=None)
        self.repo.db.metadata.drop_all()
        repository.db.metadata.create_all()
        this_dir = os.path.dirname(bioport.__file__)
        url = 'file://%s' % os.path.join(this_dir, 'admin_tests/data/knaw/list.xml')
        repository.add_source(Source(u'knaw_test',url,'test'))
        repository.download_biographies(source=repository.get_source('knaw_test'))
    def tearDown(self):
        self.repo.db.metadata.drop_all()


messages = []

class FakeMailDelivery(object):
 
    implements(IMailDelivery)
 
    def send(self, source, dest, body):
        messages.append(dict(
            source=source, dest=dest, body=body
        ))
        return 'fake-message-id-%i@example.com' % len(messages)
 
