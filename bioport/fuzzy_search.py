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
        if first_token in ('after', 'before', 'na', 'voor'): # XXX translate me
            date_to_parse = search_text[len(first_token) + 1:]
            date_dict = parse_search_query(date_to_parse)
            if first_token in ('after', 'na'):
                return build_result(date_dict, None)
            if first_token in ('before', 'voor'):
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
        return search_text.replace('van', '').split(' tot ')
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
    month = month_string.lower()
    if month in month_names['en']:
        return month_names['en'][month]
    elif month in month_names['nl']:
        return month_names['nl'][month]
    else:
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
                                 querydict.get('year_max'), lang=lang)
    min_date = build_date_string(querydict.get('day_min'),
                                 querydict.get('month_min'),
                                 querydict.get('year_min'), lang=lang)
    if not min_date:
        return {'en': "before ", 'nl': 'voor '}[lang] + max_date # XXX translate me
    if not max_date:
        return {'en': "after ", 'nl': 'na '}[lang] + min_date # XXX translate me
    if min_date == max_date:
        if 'day_max' in querydict:
            prefix = {'en':'on', 'nl':'op'}[lang] 
        else:
            prefix = 'in' 
        return prefix + " " + min_date
    tpl = {'en': "from %s to %s", 'nl': "van %s tot %s"}[lang]
    return tpl % (min_date, max_date) #XXX translate me

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
