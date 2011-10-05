"""
Do a Python test on the app.

:Test-Layer: python
"""
import unittest
import os

from bioport.admin import Sources, Source, Persoon
from bioport.app import Bioport
from zope.publisher.browser import TestRequest
import bioport_repository
from bioport_repository.tests.config import DSN

class SimpleSampleTest(unittest.TestCase):
    "Test the Sample application"

    def setUp(self):
        grokapp = Bioport()
        admin = grokapp['admin']
        admin.DB_CONNECTION = DSN
        self.app = grokapp
        self.admin = admin
        self.repo = repo = self.admin.repository(user='unittest user')
        self.repo.db.metadata.drop_all()
        repo.db.SIMILARITY_TRESHOLD = 0.0
        repo.db.metadata.create_all()
        url = os.path.join(os.path.dirname(bioport_repository.__file__), 
                         'tests', 'data','knaw', 'list.xml')
        source = bioport_repository.source.Source(id='knaw', url=url, repository=self.repo) 
        repo.add_source(source)
        self.repo.download_biographies(source)
               
    def tearDown(self):
        self.repo.db.metadata.drop_all()
        
    def test_sources(self):
        request = TestRequest()
        sources = Sources(self.admin, request)
        source = Source(self.admin, request)
        knaw_source = self.repo.get_source('knaw')
        source.update(source_id='knaw')
        sources.update(action='update_source', source_id='knaw')
    
    def test_persoon(self):
        bioport_id = self.repo.get_persons()[1].get_bioport_id()
    
        request = TestRequest(
              bioport_id=bioport_id, 
              state_new_text='testtext',
              state_new_type='unknown',
              )
        persoon = Persoon(self.admin, request)
        persoon.update()
        self.assertEqual(len(persoon.get_states(type='test')), 0)
        persoon._set_state(add_new=True, identifier='new', type='test')
        persoon.save_biography()
        self.assertEqual(len(persoon.get_states(type='test')), 1)
        self.assertEqual(len(persoon.get_editable_states()), 1)
        
def test_suite():
    test_suite = unittest.TestSuite()
    tests = [SimpleSampleTest]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')    

