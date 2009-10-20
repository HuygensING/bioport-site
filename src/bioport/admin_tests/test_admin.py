"""
Do a Python test on the app.

:Test-Layer: python
"""

import unittest
#!/home/jelle/projects_active/bioport/virtualenv_python2.4/bin/python

from bioport.admin import Admin, Biographies, Sources, Source, Edit
from bioport.app import Bioport
from zope.publisher.browser import TestRequest
import BioPortRepository
import os
class SimpleSampleTest(unittest.TestCase):
    "Test the Sample application"

    def setUp(self):
        grokapp = Bioport()
        
        admin = grokapp['admin']
        admin.SVN_REPOSITORY = '/home/jelle/projects_active/bioport/bioport_repository'
        admin.SVN_REPOSITORY_LOCAL_COPY = '/home/jelle/projects_active/bioport/bioport_repository_local_copy'
        admin.DB_CONNECTION = 'mysql://root@localhost/bioport_test'
        self.app = grokapp
        self.admin = admin
        self.admin.get_repository().db.metadata.create_all()
        
    def tearDown(self):
        self.admin.get_repository().db.metadata.drop_all()
    def test1(self):
        "Test that something works"
        assert self.admin.get_repository()
        
    def test_biographies(self):
        
        request = TestRequest()
        Biographies(Admin(), request)()
    
    def test_sources(self):
        request = TestRequest()
        sources = Sources(self.admin, request)
        url = os.path.join(os.path.dirname(BioPortRepository.__file__), 'tests', 'data','knaw', 'list.xml')
        sources.add_source(source_id='knaw', url=url)
        
        source = Source(Admin(), request)
        source.update(source_id='knaw', url=url)
        sources.update(action='update_source', source_id='knaw')
        
    def test_edit(self):
        request = TestRequest()
        edit = Edit(self.admin, request)
        edit.reset_database