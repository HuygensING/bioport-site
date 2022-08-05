##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gerbrandy S.R.L.
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
Do a functional test on the app.

:Test-Layer: python
"""

import unittest
import urllib

from lxml.etree import fromstring
from zope.publisher.interfaces import NotFound
from zope.testbrowser.testing import Browser

from bioport.tests import FunctionalTestCase
from bioport.tests import messages


class GoogleSitemapTest(FunctionalTestCase):

    def test_google_sitemap(self):
        _messages_before = len(messages)
        #        user = 'unittest user'
        bioport_ids = self.app.repository().get_bioport_ids()
        browser = self.browser
        browser.open(self.base_url + '/sitemaps/')
        tree = fromstring(browser.contents)
        first_sitemap_element = tree.xpath(".//*[local-name() = 'loc']")[0]
        sitemap_url = first_sitemap_element.text
        browser.open(sitemap_url)
        for bioid in bioport_ids:
            self.failUnless(str(bioid) in browser.contents)
        tree = fromstring(browser.contents)
        for url in tree.xpath(".//*[local-name() = 'loc']/text()"):
            browser.open(url)


class PersoonXmlTest(FunctionalTestCase):

    def test_xml_representation(self):
        browser = self.browser
        bioport_ids = self.app.repository().get_bioport_ids()
        for p_id in bioport_ids:
            url = self.base_url + '/persoon/xml/' + str(p_id)
            browser.open(url)
            self.assertEqual(browser.headers.type, 'text/xml')

    def test_biodes_index(self):
        browser = self.browser
        url = self.base_url + '/personen/biodes'
        browser.open(url)
        browser.open(url + '?detail=list')
        bioport_ids = self.app.repository().get_bioport_ids()
        for bioid in bioport_ids:
            self.failUnless('persoon/xml/' + str(bioid) in browser.contents)

    def test_json_index(self):
        browser = self.browser
        url = self.base_url + '/personen/json'
        browser.open(url)


class AppTest(FunctionalTestCase):

    def test_some_pages(self):
        browser = self.browser
        browser.open(self.base_url)
        browser.open(self.base_url + '/birthdays')
        browser.open(self.base_url + '/birthdays_box')
        browser.open(self.base_url + '/zoek')
        browser.open(self.base_url + '/personen')

    def test_raise_404(self):
        browser = self.browser
        bioport_ids = self.app.repository().get_bioport_ids()
        for p_id in bioport_ids:
            url = self.base_url + '/persoon/something/' + str(p_id)
            self.assertRaises(NotFound, browser.open, url)


class EnglishUrlTest(FunctionalTestCase):

    def setUp(self):
        super(EnglishUrlTest, self).setUp()
        self.browser = Browser()
        self.browser.handleErrors = False

    def test_english_home(self):
        self.browser.open('http://localhost/app/en')

    def test_english_zoek(self):
        self.browser.open('http://localhost/app/zoek')


#
class SearchTest(FunctionalTestCase):

    def test_search_form(self):
        browser = self.browser
        browser.open('http://localhost/app/zoek')

        form = browser.getForm(index=1)
        form.getControl(name='geboorte_fuzzy_text').value = u'na 1800'
        form.submit()

    def xtestt_search_form(self):
        browser = self.browser
        browser.open('http://localhost/app/zoek')

        form = browser.getForm(index=1)
        form.getControl(name='geboorte_fuzzy_text').value = u'na 1800'
        form.submit()


#      
class ResolverTest(FunctionalTestCase):

    def test_resolver(self):
        browser = self.browser
        bio = self.repo.get_biography(local_id='knaw_test/001')
        qs = urllib.urlencode({'url': bio.record.url_biography})
        url = 'http://localhost/app/resolver?callback=somefunction&%s' % qs
        browser.open(url)
        self.assertTrue('"number_of_biographies": 1' in browser.contents)

        # this biography has an url with a space and a comma in it
        bio = self.repo.get_biography(local_id='knaw_test/005')
        qs = urllib.urlencode({'url': bio.record.url_biography})
        url = 'http://localhost/app/resolver?callback=somefunction&%s' % qs
        browser.open(url)
        self.assertTrue('"number_of_biographies": 1' in browser.contents)


def test_suite():
    test_suite = unittest.TestSuite()
    tests = [GoogleSitemapTest,
             PersoonXmlTest,
             AppTest,
             SearchTest,
             ]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
