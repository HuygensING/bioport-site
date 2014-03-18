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

from htmlentitydefs import name2codepoint        
maanden = [ 
    'januari', 
    'februari', 
    'maart',
    'april',
    'mei',
    'juni',
    'juli', 
    'augustus', 
    'september', 
    'oktober', 
    'november', 
    'december',
    ]

months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
]
        

def format_date(s, show_year_only=False):
    """return a nicely formatted date
        
    arguments:
        s - a string - specifically a date in ISO format: YYYY-MM-DD
    returns:
        a string
    """
    if s is None: 
        return ''
    ss = str(s)
        
    if ss.startswith('-'):
        #this is a year before christ
        bce = True
        ss = ss[1:]
    else:
        bce = False
    ss = ss.split('-')
    if show_year_only and 1 <= len(ss) <= 3:
        y = ss[0]
        result = '%s' % int(y)
    elif len(ss) == 1:
        y = ss[0]
        result = '%s' % int(y)
    elif len(ss) == 2:
        y = ss[0]
        m = ss[1]
        result = '%s %s' % (maanden[int(m) - 1], int(y))
    elif len(ss) == 3:
        y = ss[0]
        m = ss[1]
        d = ss[2]
        result = '%s %s %s' % (int(d), maanden[int(m) - 1], int(y))
    else:
        assert 0, '%s is not a valid date in ISO format' % s
    if bce:
        result += ' v Chr.'
    return result

def format_dates( date1='', date2='', show_year_only=False, parenthesis=True):    
    if date1 or date2:
        #try to format the dates prettily
        try:
            date1 = format_date(date1, show_year_only=show_year_only)
        except:
            pass
        try:
            date2 = format_date(date2, show_year_only=show_year_only)
        except:
            pass
        
        result = '%s-%s' % (date1 or '?', date2 or '?')
        if parenthesis:
            result = '(%s)' % result
        return result
    

def splitthousands(s, sep=','):  
    if len(s) <= 3: return s  
    return splitthousands(s[:-3], sep) + sep + s[-3:]

def format_number(s):
    s = str(s)
    return splitthousands(s, sep='.')

def html2unicode(s):
    #replace html characters with unicode codepoints
    for k in name2codepoint.keys():
        s = s.replace('&%s;' % k,unichr( name2codepoint[k]))
    return s
