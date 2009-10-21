
class FormatUtilities:
    def format_date(self, s):
        """return a nicely formatted date
        
        arguments:
            s - a string - specifically a date in ISO format: YYYY-MM-DD
        returns:
            a string
        """
        if s is None: return ''
        s = str(s)
        
        
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
        
    def format_dates(self, date1='', date2=''):    
        if date1 or date2:
            return '(%s-%s)' % (self.format_date(date1), self.format_date(date2))
