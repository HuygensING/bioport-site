"""
Do a functional test on the app.

:Test-Layer: python
"""

import unittest

from bioport.tests import FunctionalTestCase
from bioport.tests import messages
from lxml.etree import fromstring
from zope.publisher.interfaces import NotFound
from zope.testbrowser.testing import Browser

class GoogleSitemapTest(FunctionalTestCase):

    def test_google_sitemap(self):
        messages_before = len(messages)
        bioport_ids = self.app.repository(user=None).get_bioport_ids()
        browser = self.browser
        browser.open(self.base_url + '/sitemaps/')
        tree = fromstring(browser.contents)
        first_sitemap_element = tree.xpath(".//*[local-name() = 'loc']")[0]
        sitemap_url = first_sitemap_element.text
        browser.open(sitemap_url)
        for bioid in bioport_ids:
            self.failUnless(bioid in browser.contents)
        tree = fromstring(browser.contents)
        for url in tree.xpath(".//*[local-name() = 'loc']/text()"):
            browser.open(url)

class PersoonXmlTest(FunctionalTestCase):

    def test_xml_representation(self):
        browser = self.browser
        bioport_ids = self.app.repository(user=None).get_bioport_ids()
        for p_id in bioport_ids:
            url = self.base_url + '/persoon/xml/' + p_id
            browser.open(url)
            self.assertEqual(browser.headers.type, 'text/xml')

    def test_xml_index(self):
        browser = self.browser
        url = self.base_url + '/personenxml/'
        browser.open(url)
        bioport_ids = self.app.repository(user=None).get_bioport_ids()
        for bioid in bioport_ids:
            self.failUnless('persoon/xml/' + bioid in browser.contents)


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
        bioport_ids = self.app.repository(user=None).get_bioport_ids()
        for p_id in bioport_ids:
            url = self.base_url + '/persoon/something/' + p_id
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
#class SearchTest(FunctionalTestCase):
#    def setUp(self):
#        self.browser = Browser()
#        self.browser.handleErrors = False
#    
#    def test_search_form(self):
#        self.browser.open('http://localhost/app/zoek')
        
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


