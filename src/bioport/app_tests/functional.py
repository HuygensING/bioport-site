"""
Do a functional test on the app.

:Test-Layer: python
"""
from bioport.app import Bioport
from bioport.tests import FunctionalLayer
from zope.app.testing.functional import FunctionalTestCase
class SampleFunctionalTest(FunctionalTestCase):
    layer = FunctionalLayer
class SimpleSampleFunctionalTest(SampleFunctionalTest):
    """ This the app in ZODB. """
    def test_simple(self):
        """ test creating a bioport instance into Zope """
        root = self.getRootFolder()
        root['instance'] = Bioport()
        self.assertEqual(root.get('instance').__class__, Bioport)
        