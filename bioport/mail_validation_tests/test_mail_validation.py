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
Do a Python test on the app.

:Test-Layer: python
"""
import unittest
from bioport.mail_validation import check_email 

class TestEmailValidation(unittest.TestCase):

    def test_email_validation_correct(self):
        self.failUnless(check_email('me@example.com'))
        self.failUnless(check_email('me+can_have-some:special_chars@example.com'))
        self.failUnless(check_email('E.J.vanderVeldt1@uu.nl'))

    def test_email_validation_incorrect(self):
        self.failIf(check_email('meexample.com'))
        self.failIf(check_email('@ll.com'))
        
        
def test_suite():
    test_suite = unittest.TestSuite()
    tests = [TestEmailValidation]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')    
