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


import unittest
from fuzzy_search import get_search_query, make_description

class FuzzySearchTest(unittest.TestCase):
    def run_test(self, query_text, expected_query):
        effective_query = get_search_query(query_text)
        self.assertEqual(effective_query, expected_query)

    def test_make_description_only_month(self):
        querydict = {'month_max': 10, 'month_min': 10}
        res = make_description(querydict, lang='en')
        self.assertEqual(res, "in october")

    def test_make_description_before_year(self):
        querydict = {'year_max': 1978}
        res = make_description(querydict, lang='en')
        self.assertEqual(res, "before 1978")
        res = make_description(querydict, lang='nl')
        self.assertEqual(res, "voor 1978")

    def test_make_description_after_year(self):
        querydict = {'year_min': 1978}
        res = make_description(querydict, lang='en')
        self.assertEqual(res, "after 1978")
        res = make_description(querydict, lang='nl')
        self.assertEqual(res, "na 1978")

    def test_make_description_specific_day(self):
        querydict = {
            'year_min': 1978, 'year_max': 1978,
            'month_min': 10, 'month_max': 10,
            'day_min' : 12, 'day_max' : 12,
        }
        res = make_description(querydict, lang='en')
        self.assertEqual(res, "on 12 october 1978")

    def test_make_description_full_range(self):
        querydict = {
            'year_min': 1978, 'year_max': 1982,
            'month_min': 10, 'month_max': 3,
            'day_min' : 12, 'day_max' : 1,
        }
        res = make_description(querydict, lang='en')
        self.assertEqual(res, "from 12 october 1978 to 1 march 1982")
        res = make_description(querydict, lang='nl')
        self.assertEqual(res, "van 12 oktober 1978 tot 1 maart 1982")

    def test_make_description_no_days(self):
        querydict = {
            'year_min': 1978, 'year_max': 1982,
            'month_min': 10, 'month_max': 3,
        }
        res = make_description(querydict, lang='en')
        self.assertEqual(res, "from october 1978 to march 1982")
        res = make_description(querydict, lang='nl')
        self.assertEqual(res, "van oktober 1978 tot maart 1982")

    def test_before_year(self):
        expected_result = {'year_max': 1978}
        self.run_test('before  1978 ', expected_result)
        self.run_test('voor  1978 ', expected_result)

    def test_after_year(self):
        expected_result = {'year_min': 1978}
        self.run_test(' after 1978 ', expected_result)
        self.run_test(' na 1978 ', expected_result)

    def test_single_year(self):
        expected_result = {'year_min': 1920, 'year_max': 1920}
        self.run_test('  1920 ', expected_result)

    def test_complete_date(self):
        expected_result = {
            'year_min': 1978, 'year_max': 1978,
            'month_min': 10, 'month_max': 10,
            'day_min' : 12, 'day_max' : 12,
        }
        self.run_test('12/10/1978', expected_result)
        self.run_test('12-10-1978', expected_result)
        self.run_test('12 10 1978', expected_result)
        self.run_test('12 october 1978', expected_result)
        self.run_test('12 oktober 1978', expected_result)
        self.run_test('12 oct 1978', expected_result)

    def test_month_year_date(self):
        expected_result = {
            'year_min': 1978, 'year_max': 1978,
            'month_min': 10, 'month_max': 10,
        }
        self.run_test('10/1978', expected_result)
        self.run_test('10-1978', expected_result)
        self.run_test(' 10 1978', expected_result)
        self.run_test('october 1978', expected_result)
        self.run_test(' oct  1978', expected_result)

    def test_no_year(self):
        expected_result = {
            'month_min': 10, 'month_max': 10,
            'day_min' : 12, 'day_max' : 12,
        }
        self.run_test('12 october', expected_result)
        self.run_test('12  10', expected_result)

    def test_month_only(self):
        expected_result = {
            'month_min': 10, 'month_max': 10,
        }
        self.run_test(' october', expected_result)
        self.run_test('oct  ', expected_result)
        self.run_test('10  ', expected_result)

    def test_two_complete_dates(self):
        expected_result = {
            'year_min': 1970, 'year_max': 1978,
            'month_min': 2, 'month_max': 10,
            'day_min' : 13, 'day_max' : 12,
        }
        self.run_test('from 13/2/1970 to 12/10/1978', expected_result)
        self.run_test('from 13/feb/1970 to 12/10/1978', expected_result)
        self.run_test('13/2/1970 to 12/10/1978', expected_result)
        self.run_test('between 13/2/1970 and 12-10-1978', expected_result)
        self.run_test('van 13/2/1970 tot 12-10-1978', expected_result)
        self.run_test('tussen 13/2/1970 en 12-10-1978', expected_result)

    def test_two_partial_dates(self):
        expected_result = {
            'month_min': 2, 'month_max': 10,
            'day_min' : 13, 'day_max' : 12,
        }
        self.run_test('from 13/2 to 12/10', expected_result)
        self.run_test('from 13/feb to 12-10', expected_result)
        self.run_test('13/2 to 12/10', expected_result)
        self.run_test('between 13/2 and 12-oct', expected_result)

    def test_two_partial_dates_reversed(self):
        expected_result = {
            'month_min': 10, 'month_max': 2,
            'day_min' : 12, 'day_max' : 13,
        }
        self.run_test('from 12/10 to 13/2', expected_result)
        self.run_test('from 12/oct to 13-2', expected_result)
        self.run_test('12/oct to 13 feb', expected_result)
        self.run_test('between 12-oct and 13/2', expected_result)

    def test_unparsable_should_raise(self):
        self.assertRaises(ValueError, get_search_query, "ERROR")


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FuzzySearchTest, 'test_'),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
