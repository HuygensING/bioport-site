"""
This module converts human-written sentences expressing dates or date ranges
into distionaries that represent the query, that can be further
elaburated and fed to BioPortRepository.
Output fields (all integer types):
    year_min 
    year_max
    month
    day


:Test-Layer: python
"""
from bioport.tests import FunctionalTestCase
import unittest
import re


def get_search_query(original_search_text):
    # Strip out redundant spaces
    search_text = original_search_text.strip()
    re.sub(search_text, ' +', ' ')
    result = {}
    if search_text.isdigit():
        # we have a raw number, let's treat it as a year
        result['year_max'] = int(search_text)
        result['year_min'] = int(search_text)
    elif search_text.count('/') == 2:
        # two slashes: we have a full date
        day, month, year = search_text.split('/')
        result['day'] = int(day)
        result['month'] = int(month)
        result['year_min'] = int(year)
        result['year_max'] = int(year)
    return result


class FuzzySearchTest(unittest.TestCase):
    def run_test(self, query_text, expected_query):
        effective_query = get_search_query(query_text)
        self.assertEqual(expected_query, effective_query)
    def test_single_year(self):
        expected_result = {'year_min': 1920, 'year_max': 1920}
        self.run_test('  1920 ', expected_result)
    def test_complete_date(self):
        expected_result = {
            'year_min': 1978,
            'year_max': 1978,
            'month': 10,
            'day' : 12,
        }
        self.run_test('12/10/1978', expected_result)

