"""
Do a functional test on the app.

:Test-Layer: python
"""
from bioport.tests import FunctionalTestCase
from bioport.tests import messages
from bioport.captcha import ENCRYPTION_KEY
from bioport.crypt import decrypt
import re
import unittest


class ContactFormTest(FunctionalTestCase):

    def setUp(self):
        super(ContactFormTest, self).setUp()
        self.app['admin'].EMAIL_FROM_ADDRESS = 'admin@example.com'
        self.app['admin'].CONTACT_DESTINATION_ADDRESS = 'admin-destination@example.com'
        
    def solve_captcha(self):
        # Solve the captcha!
        captcha_crypt = re.findall(r'captcha_text[^>]+value="([^"]+)', self.browser.contents)[0]
        captcha_solution = decrypt(ENCRYPTION_KEY,captcha_crypt)
        self.browser.getControl('Vul de letters').value = captcha_solution
        
    def fill_form(self):
        self.browser.getControl('Naam').value = 'Me'
        self.browser.getControl('Emailadres').value = 'me@example.com'
        self.browser.getControl('Tekst').value = 'Hey'
        
    def test_contact_form_wrong_captcha(self):
        messages_before = len(messages)
        self.browser.open(self.base_url + '/contact')
        self.fill_form()
        self.browser.getControl('Vul de letters').value = 'wrongvalue'
#        captcha_crypt = re.findall(r'captcha_text[^>]+vaContactFormTestlue="([^"]+)', self.browser.contents)[0]
        captcha_crypt = re.findall(r'captcha_text[^>]+value="([^"]+)', self.browser.contents)[0]
        self.browser.getControl('Submit').click()
        self.failUnlessEqual(len(messages), messages_before)
        new_captcha_crypt = re.findall(r'captcha_text[^>]+value="([^"]+)', self.browser.contents)[0]
        self.failIfEqual(new_captcha_crypt, captcha_crypt)
        
    def test_contact_form_good(self):
#        messages_before = len(messages)
        self.browser.open(self.base_url + '/contact')
        self.fill_form()
        self.browser.getControl('Emailadres').value = 'E.J.vanderVeldt1@uu.nl'
        self.solve_captcha()
        self.browser.getControl('Submit').click()
        self.failUnless('admin-destination@example.com' in messages[-1]['dest'])
        self.failUnlessEqual(messages[-1]['source'], 'E.J.vanderVeldt1@uu.nl')
        self.failUnlessEqual(messages[-1]['dest'],
                             ['admin-destination@example.com'])
                             
    def test_contact_form_bad_email(self):
        messages_before = len(messages)
        self.browser.open(self.base_url + '/contact')
        self.fill_form()
        self.browser.getControl('Emailadres').value = 'bademail.example.com'
        self.solve_captcha()
        self.browser.getControl('Submit').click()
        self.assertEqual(len(messages), messages_before)


def test_suite():
    test_suite = unittest.TestSuite()
    tests = [ContactFormTest]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')    
    
