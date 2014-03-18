##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gebrandy S.R.L.
# 
# This file is part of bioport.
# 
# bioport is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/gpl-3.0.html>.
##########################################################################

"""
Do a Python test on the app.

:Test-Layer: python
"""
import unittest
import os

from bioport.admin import Sources, Source, Persoon
from zope.publisher.browser import TestRequest
import bioport_repository
from bioport.tests import FunctionalTestCase


class SimpleSampleTest(FunctionalTestCase):
    "Test the Sample application"

    def setUp(self):
        super(SimpleSampleTest, self).setUp()
        self.admin = self.app['admin']
        self.repo = self.admin.repository()  # user='unittest user')
        self.repo.db.SIMILARITY_TRESHOLD = 0.0

        url = os.path.join(os.path.dirname(bioport_repository.__file__),
                         'tests', 'data', 'knaw', 'list.xml')
        source = bioport_repository.source.Source(id='knaw', url=url, repository=self.repo)
        self.repo.add_source(source)
        self.repo.download_biographies(source)

    def test_sources(self):
        request = TestRequest()
        sources = Sources(self.admin, request)
        source = Source(self.admin, request)
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
