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
    try:
        if startend:
            start, end = startend
            startdict = parse_search_query(start)
            enddict = parse_search_query(end)
            return build_result(startdict, enddict)
        first_token = search_text.split()[0].lower()
        if first_token in ('after', 'before'): # XXX translate me
            date_to_parse = search_text[len(first_token) + 1:]
            date_dict = parse_search_query(date_to_parse)
            if first_token == 'after':
                return build_result(date_dict, None)
            if first_token == 'before':
                return build_result(None, date_dict)
        res = parse_search_query(search_text, lang=lang)
        if not res:
            raise ValueError
    except KeyboardInterrupt:
        raise
    except Exception, e:
        raise ValueError("No data could be extracted from " + original_search_text)
    return build_result(res, res)

def parse_search_query(original_search_text, lang='en'):
    # Strip out redundant spaces
    search_text = original_search_text.strip()
    search_text = re.sub(' +', ' ', search_text)
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
        # Here we might have day-month or month-year
        if is_month(tokens[1]):
            named_tokens = dict(day=tokens[0], month=resolve_month(tokens[1], lang=lang))
        else:
            named_tokens = dict(month=resolve_month(tokens[0], lang=lang), year=tokens[1])
        return named_tokens

def split_start_end(search_text):
    if search_text.find(' to ')>0:
        return search_text.replace('from', '').split(' to ')
    if search_text.find(' and ')>0:
        return search_text.replace('between', '').split(' and ')
    if search_text.find(' tot ')>0:
        return search_text.replace('from', '').split(' tot ')
    if search_text.find(' en ')>0:
        return search_text.replace('tussen', '').split(' en ')


def is_month(text):
    try:
        resolve_month(text)
        return True
    except MonthParseException:
        return False


# dictionary to lookup month numbers from names
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
    },
    'nl': {
        'januari':1,
        'jan':1,
        'februari':2,
        'feb':2,
        'maart':3,
        'mar':3,
        'april':4,
        'apr':4,
        'mei':5,
        'juni':6,
        'jun':6,
        'juli':7,
        'jul':7,
        'augustus':8,
        'aug':8,
        'september':9,
        'sep':9,
        'oktober':10,
        'okt':10,
        'november':11,
        'nov':11,
        'december':12,
        'dec':12,
    }
}

month_number_to_names = {}
# reverse the above dictionary to lookup month names by number
# we pick the longest name as the canonical one
for lang in month_names:
    rev = {}
    for name, num in month_names[lang].items():
        if num not in rev or len(rev[num])<len(name):
            rev[num] = name
    month_number_to_names[lang] = rev

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

_marker = []
def build_result(data_from, data_to=_marker):
    "Convert two dicts with strings in one dict that represents the query"
    if data_to is _marker:
        data_to = data_from
    query = {}
    data = [('min', data_from), ('max', data_to)]
    for suffix, datadict in data:
        if datadict and 'year' in datadict:
            query['year_' + suffix] = int(datadict['year'])
        if datadict and 'month' in datadict:
            query['month_' + suffix] = int(datadict['month'])
        if datadict and 'day' in datadict:
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


def en_to_nl_for_field(thedict, searchtype):
    """
    thedict looks like 
    {'month_max': 1, 'year_min': 1800, 'year_max': 1900}
    and will be converted (assuming searchtype='sterf') to
    {'sterfmaand_max': 1, 'sterfjaar_min': 1800, 'sterfjaar_max': 1900}
    searchtype should be either 'sterf' or 'geboorten'
    """
    return dict([
    (searchtype + name.replace('year', 'jaar').replace('month', 'maand')
        .replace('day', 'dag'), value)
    for name, value in thedict.items()
    ])

def make_description(querydict, lang='en'):
    " Provide a textual description for a dict of (day|month|year)_(min|max) "
    max_date = build_date_string(querydict.get('day_max'),
                                 querydict.get('month_max'),
                                 querydict.get('year_max'))
    min_date = build_date_string(querydict.get('day_min'),
                                 querydict.get('month_min'),
                                 querydict.get('year_min'))
    if not min_date:
        return "before " + max_date # XXX translate me
    if not max_date:
        return "after " + min_date # XXX translate me
    if min_date == max_date:
        if 'day_max' in querydict:
            prefix = 'on' # XXX translate me
        else:
            prefix = 'in' # XXX translate me
        return prefix + " " + min_date
    return "from %s to %s" % (min_date, max_date) #XXX translate me

def build_date_string(day, month, year, lang='en'):
    if not year:
        year = ''
    if not (day or month or year):
        return ''
    if not day and not month:
        return str(year)
    month_name = month_number_to_names[lang][month]
    if not day:
        return ("%s %s" % (month_name, year)).strip()
    return ("%s %s %s" % (day, month_name, year)).strip()

class TranslateNamesToDutchTest(unittest.TestCase):
    def test_names(self):
        orig = {'month_max': 1, 'year_min': 1800, 'year_max': 1900}
        res = en_to_nl_for_field(orig, 'sterf')
        self.assertEqual(res,
            {'sterfmaand_max': 1, 'sterfjaar_min': 1800, 'sterfjaar_max': 1900})

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

    def test_make_description_after_year(self):
        querydict = {'year_min': 1978}
        res = make_description(querydict, lang='en')
        self.assertEqual(res, "after 1978")

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

    def test_make_description_no_days(self):
        querydict = {
            'year_min': 1978, 'year_max': 1982,
            'month_min': 10, 'month_max': 3,
        }
        res = make_description(querydict, lang='en')
        self.assertEqual(res, "from october 1978 to march 1982")

    def test_before_year(self):
        expected_result = {'year_max': 1978}
        self.run_test('before  1978 ', expected_result)

    def test_after_year(self):
        expected_result = {'year_min': 1978}
        self.run_test(' after 1978 ', expected_result)

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
        self.run_test('from 13/feb/1970 to 12/10/1978', expected_result)
        self.run_test('13/2/1970 to 12/10/1978', expected_result)
        self.run_test('between 13/2/1970 and 12-10-1978', expected_result)
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



