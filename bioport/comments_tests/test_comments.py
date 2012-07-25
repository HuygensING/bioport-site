"""
Do a functional test on the app.

:Test-Layer: python
"""

import re

from bioport.tests import FunctionalTestCase
from bioport.tests import messages
from bioport.captcha import ENCRYPTION_KEY
from bioport.crypt import decrypt


class CommentFormTest(FunctionalTestCase):
    def est_comment_form(self):
#        messages_before = len(messages)
        some_bioport_id = self.app.repository().get_bioport_ids()[2]
        browser = self.browser
        browser.open(self.base_url + '/persoon/' + str(some_bioport_id))
        browser.getControl(name='form.submitter').value = 'Me'
        browser.getControl(name='form.email').value = 'someone@example.com'
        browser.getControl(name='form.text').value = 'this is a really accurate biography!'
        # Solve the captcha!
        captcha_crypt = re.findall(r'captcha_text[^>]+value="([^"]+)', self.browser.contents)[0]
        captcha_solution = decrypt(ENCRYPTION_KEY,captcha_crypt)
        browser.getControl('verification').value = captcha_solution
        browser.getControl('Submit').click()
        self.failUnless('this is a really accurate biography!' in browser.contents)
        
#        
#def test_suite():
#    test_suite = unittest.TestSuite()
#    tests = [TestEmailValidation]
#    for test in tests:
#        test_suite.addTest(unittest.makeSuite(test))
#    return test_suite
#
#if __name__ == "__main__":
#    unittest.main(defaultTest='test_suite')

