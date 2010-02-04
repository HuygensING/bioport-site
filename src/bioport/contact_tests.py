"""
Do a Python test on the app.

:Test-Layer: python
"""
import sys
import unittest
from zope.component import getAdapter
from bioport.app import Bioport
from zope.publisher.browser import TestRequest

class ContactFormTest(unittest.TestCase):
    def setUp(self):
        self.app = Bioport()
    def test_contact_form(self):
        pass

