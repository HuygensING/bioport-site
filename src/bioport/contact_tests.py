"""
Do a functional test on the app.

:Test-Layer: python
"""
from bioport.tests import FunctionalTestCase
from bioport.tests import messages
from bioport.contact import ENCRYPTION_KEY
from bioport.crypt import decrypt
import re

class ContactFormTest(FunctionalTestCase):
    def test_contact_form(self):
        messages_before = len(messages)
        self.app['admin'].EMAIL_FROM_ADDRESS = 'admin@example.com'
        self.browser.open(self.base_url + '/contact')
        self.browser.getControl('Naam').value = 'Me'
        self.browser.getControl('Mailadres').value = 'me@example.com'
        self.browser.getControl('Tekst').value = 'Hey'
        self.browser.getControl('verification').value = 'wrongvalue'
        self.browser.getControl('Submit').click()
        self.failUnlessEqual(len(messages), messages_before)
        # Solve the captcha!
        captcha_crypt = re.findall(r'captcha_text[^>]+value="([^"]+)', self.browser.contents)[0]
        captcha_solution = decrypt(ENCRYPTION_KEY,captcha_crypt)
        self.browser.getControl('verification').value = captcha_solution
        self.browser.getControl('Submit').click()
        self.failUnless('me@example.com' in messages[-1]['dest'])
        self.failUnlessEqual(messages[-1]['source'], 'admin@example.com')

