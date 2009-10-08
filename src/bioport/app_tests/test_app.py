"""
Do a Python test on the app.

:Test-Layer: python
"""

import unittest
#!/home/jelle/projects_active/bioport/virtualenv_python2.4/bin/python

from bioport import app
from bioport.app import Bioport, Index
from zope.publisher.browser import TestRequest


class SimpleSampleTest(unittest.TestCase):
    "Test the Sample application"

    def test1(self):
        "Test that something works"
        grokapp = Bioport()
        self.assertEqual(list(grokapp.keys()), ['admin'])
        request = TestRequest()
        Index(grokapp, request)()
        