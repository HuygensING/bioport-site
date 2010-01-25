        
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

def format_dates( date1='', date2='', show_year_only=False):    
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
        return '%s-%s' % (date1 or '?', date2 or '?')
        return '(%s-%s)' % (date1 or '?', date2 or '?')

def splitthousands(s, sep=','):  
    if len(s) <= 3: return s  
    return splitthousands(s[:-3], sep) + sep + s[-3:]

def format_number(s):
    s = str(s)
    return splitthousands(s, sep='.')