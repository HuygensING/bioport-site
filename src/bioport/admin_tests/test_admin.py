"""
Do a Python test on the app.

:Test-Layer: python
"""

import unittest
#!/home/jelle/projects_active/bioport/virtualenv_python2.4/bin/python

from bioport.admin import Admin, Biographies, Sources, Source
from bioport.app import Bioport
from zope.publisher.browser import TestRequest
import BioPortRepository
import os
class SimpleSampleTest(unittest.TestCase):
    "Test the Sample application"

    def test1(self):
        "Test that something works"
        grokapp = Bioport()
        
        admin = grokapp['admin']
        admin.SVN_REPOSITORY = '/home/jelle/projects_active/bioport/bioport_repository'
        admin.SVN_REPOSITORY_LOCAL_COPY = '/home/jelle/projects_active/bioport/bioport_repository_local_copy'

        assert admin.get_repository()
    def test_biographies(self):
        
        request = TestRequest()
        Biographies(Admin(), request)()
        
    def test_sources(self):
        request = TestRequest()
        sources = Sources(Admin(), request)
        source = Source(Admin(), request)
        url = os.path.join(os.path.dirname(BioPortRepository.__file__), 'tests', 'data','knaw', 'list.xml')
        source.update(source_id='knaw', url=url)
        sources.update(action='update_source', source_id='knaw')