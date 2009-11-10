"""
Do a Python test on the app.

:Test-Layer: python
"""

import unittest
#!/home/jelle/projects_active/bioport/virtualenv_python2.4/bin/python

from bioport import app
from bioport.app import Bioport, Index, Personen
from zope.publisher.browser import TestRequest


#class SimpleSampleTest(unittest.TestCase):
#    "Test the Sample application"
#    def setUp(self):
#        self.app = Bioport(db_connection='mysql://root@localhost/bioport_test')
#        self.app['admin'].repository().db.metadata.create_all()
#    def tearDown(self):
#        self.app['admin'].repository().db.metadata.drop_all()
#    def test1(self):
#        "Test that something works"
#        self.assertEqual(list(self.app.keys()), ['admin'])
#        request = TestRequest()
#        Index(self.app, request)()
#        
#    def test_personen(self):
#        request = TestRequest()
#        personen = Personen(self.app, request)
#        personen.update()
#        personen.get_persons()
#        request.form[u'beginletter'] = u'a'
#        personen = Personen(self.app, request)
#        personen.update()
#        personen.get_persons()
#        personen()
