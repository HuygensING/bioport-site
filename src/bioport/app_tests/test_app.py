"""
Do a functional test on the app.

:Test-Layer: python
"""
from bioport.tests import FunctionalTestCase
from bioport.tests import messages
from lxml.etree import fromstring
from zope.publisher.interfaces import NotFound

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
        for id in bioport_ids:
            self.failUnless(id in browser.contents)
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


class AppTest(FunctionalTestCase):
    def test_raise_404(self):
        browser = self.browser
        bioport_ids = self.app.repository(user=None).get_bioport_ids()
        for p_id in bioport_ids:
            url = self.base_url + '/persoon/something/' + p_id
            self.assertRaises(NotFound, browser.open, url)

