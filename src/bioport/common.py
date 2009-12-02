        
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
        

def format_date( s):
    """return a nicely formatted date
        
    arguments:
        s - a string - specifically a date in ISO format: YYYY-MM-DD
    returns:
        a string
    """
    if s is None: 
        return ''
    s = str(s)
        

    ss = s.split('-')
    if len(ss) == 1:
        y = s
        return '%s' % int(y)
    elif len(ss) == 2:
        y = ss[0]
        m = ss[1]
        return '%s %s' % (maanden[int(m) - 1], int(y))
    elif len(ss) == 3:
        y = ss[0]
        m = ss[1]
        d = ss[2]
        return '%s %s %s' % (int(d), maanden[int(m) - 1], int(y))
    else:
        raise

def format_dates( date1='', date2=''):    
    if date1 or date2:
        #try to format the dates prettily
        try:
            date1 = format_date(date1)
        except:
            pass
        try:
            date2 = format_date(date2)
        except:
            pass
        return '(%s-%s)' % (date1 or '?', date2 or '?')
def splitthousands(s, sep=','):  
    if len(s) <= 3: return s  
    return splitthousands(s[:-3], sep) + sep + s[-3:]

def format_number(s):
    s = str(s)
    return splitthousands(s, sep='.')