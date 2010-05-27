"""
Inspired by http://adbonline.anu.edu.au/help-advsearch.htm#abd
This module converts human-written sentences expressing dates or date ranges
into distionaries that represent the query, that can be further
elaburated and fed to BioPortRepository.
Output fields (all integer types):
    year_min 
    year_max
    month_min
    month_max
    day_min
    day_max
We assume european dates: day/month/year

:Test-Layer: python
"""
from bioport.tests import FunctionalTestCase
import unittest
import re


def get_search_query(original_search_text, lang='en'):
    # Strip out redundant spaces
    search_text = original_search_text.strip()
    search_text = re.sub(' +', ' ', search_text)
    startend = split_start_end(search_text)
    if startend:
        pass
    res = parse_search_query(search_text, lang=lang)
    return build_result(res, res)

def parse_search_query(search_text, lang='en'):
    if is_month(search_text):
        # one month name only
        month = resolve_month(search_text)
        return {'month': month}
    if search_text.isdigit():
        # we have a raw number, let's treat it as a year
        named_tokens = dict(year=search_text)
        return named_tokens
    tokens = split_in_n_tokens(search_text, 3)
    if tokens:
        named_tokens = dict(day=tokens[0], month=resolve_month(tokens[1], lang=lang), year=tokens[2])
        return named_tokens
    tokens = split_in_n_tokens(search_text, 2)
    if tokens:
        if not tokens[0]:
            import pdb; pdb.set_trace()
        # Here we might have day-month or month-year
        if is_month(tokens[1]):
            named_tokens = dict(day=tokens[0], month=resolve_month(tokens[1], lang=lang))
        else:
            named_tokens = dict(month=resolve_month(tokens[0], lang=lang), year=tokens[1])
        return named_tokens

def split_start_end(search_text):
    pass

def is_month(text):
    try:
        resolve_month(text)
        return True
    except MonthParseException:
        return False

month_names = {
    'en': {
        'jan':1,
        'january':1,
        'february':2,
        'feb':2,
        'march':3,
        'mar':3,
        'april':4,
        'apr':4,
        'may':5,
        'may':5,
        'june':6,
        'jun':6,
        'july':7,
        'jul':7,
        'august':8,
        'aug':8,
        'september':9,
        'sep':9,
        'october':10,
        'oct':10,
        'november':11,
        'nov':11,
        'december':12,
        'dec':12,
    }
}
def resolve_month(month_string, lang='en'):
    if month_string.isdigit():
        month_int = int(month_string)
        if 1 <= month_int <=12:
            return month_int
        else:
            raise MonthParseException("Out of bounds month: %i" % month_int)
    try:
        return month_names[lang][month_string.lower()]
    except KeyError:
        raise MonthParseException("Invalid month name: %s" % month_string)

class MonthParseException(Exception):
    "Raised in case of error during month parsing"

def build_result(data_from, data_to=None):
    "Convert two dicts with strings in one dict that represents the query"
    if not data_to:
        data_to = data_from
    query = {}
    data = [('min', data_from), ('max', data_to)]
    for suffix, datadict in data:
        if 'year' in datadict:
            query['year_' + suffix] = int(datadict['year'])
        if 'month' in datadict:
            query['month_' + suffix] = int(datadict['month'])
        if 'day' in datadict:
            query['day_' + suffix] = int(datadict['day'])
    return query

def split_in_n_tokens(text, how_many_tokens):
    """
    This function returns the three tokens if text
    happens to be a three tokens string separated by
    - / or blank
    """
    for sep in '-/ ':
        result = text.split(sep)
        if len(result) == how_many_tokens:
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
            'year_min': 1978, 'year_max': 1978,
            'month_min': 10, 'month_max': 10,
            'day_min' : 12, 'day_max' : 12,
        }
        self.run_test('12/10/1978', expected_result)
        self.run_test('12-10-1978', expected_result)
        self.run_test('12 10 1978', expected_result)
        self.run_test('12 october 1978', expected_result)
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
        self.run_test('13/2/1970 to 12/10/1978', expected_result)
        self.run_test('between 13/2/1970 and 12/10/1978', expected_result)

