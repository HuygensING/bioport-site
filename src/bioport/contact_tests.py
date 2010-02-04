"""
Do a functional test on the app.

:Test-Layer: python
"""
from bioport.tests import FunctionalTestCase
from bioport.tests import messages

class ContactFormTest(FunctionalTestCase):
    def test_contact_form(self):
        self.app['admin'].EMAIL_FROM_ADDRESS = 'admin@example.com'
        self.browser.open(self.base_url + '/contact')
        self.browser.getControl('Naam').value = 'Me'
        self.browser.getControl('Mailadres').value = 'me@example.com'
        self.browser.getControl('Tekst').value = 'Hey'
        self.browser.getControl('Submit').click()
        self.failUnless('me@example.com' in messages[-1]['dest'])
        self.failUnlessEqual(messages[-1]['source'], 'admin@example.com')

