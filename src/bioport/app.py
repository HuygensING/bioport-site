import grok
import zope.interface
from z3c.batching.batch import  Batch
import random
import datetime
from common import  maanden, format_date, format_dates, format_number, html2unicode
from NamenIndex.common import to_ymd, from_ymd
import urllib
class RepositoryView:
    def repository(self):
        principal = self.request.principal
        user = principal and principal.id
        return self.context.repository(user=user)
    
    def get_sources(self):
        return self.repository().get_sources()
    
    def get_person(self,bioport_id):
        return self.repository().get_person(bioport_id)
    
    def get_status_values(self, k=None):
        return self.repository().get_status_values(k)
    
    def count_persons(self):
        try:
            return self.context._count_persons
        except AttributeError:
            i = self.repository().db.count_persons()
            #XXX turned of caching, need to find some "update once a day" solution
            return i
            self.context._count_persons = format_number(i)
        return self.context._count_persons
    
    def count_biographies(self):
        try:
            return self.context._count_biographies
        except AttributeError:
            i = self.repository().db.count_biographies()
            #XXX turned of caching, need to find some "update once a day" solution
            return i
            self.context._count_biographies = format_number(i)
        return self.context._count_biographies
       
    def menu_items(self):
        return [
                (self.application_url(), 'home'),
                (self.url('zoek'), 'zoeken'),
                (self.url('about'), 'project'),
                (self.url('agenda'), 'agenda'),
                (self.url('colofon'), 'colofon'),
                (self.url('contact'), 'contact'),
                (self.url('faq'), 'faq'),
                (self.url('english'), 'english'),
        ]    
    
class Batcher: 
    def update(self, **kw):
        self.start = int(self.request.get('start', 0))
        self.size = int(self.request.get('size', 30))
        
    def batch_url(self, start=None, size=None):
        data = self.request.form
        if start != None:
            data['start'] = start
        if size != None:
            data['size'] = size
        return self.url(data= data)    
 
class Bioport(grok.Application, grok.Container):
              
    SVN_REPOSITORY = None
    SVN_REPOSITORY_LOCAL_COPY = None
    DB_CONNECTION = None
    debug=True
    def __init__(self, db_connection=None):
        super(Bioport,self).__init__() #cargoculting from ingforms 
        from admin import Admin
        self['admin'] = Admin()
        self['admin'].DB_CONNECTION = db_connection
    
    def format_dates(self, s1, s2, **args):
        return  format_dates(s1, s2, **args)

    def repository(self, user):
        return self['admin'].repository(user=user)

#    
class BioPortTraverser(object):
    
    #CODE for construction traverse_subpath from 
    #  http://grok.zope.org/documentation/how-to/traversing-subpaths-in-views 

    def publishTraverse(self, request, name):
       self._traverse_subpath = request.getTraversalStack() + [name]
       request.setTraversalStack([])
       return self 
    def traverse_subpath(self):
       return getattr(self, '_traverse_subpath', [])
       
    def traverse_subpath_helper(self, i, default=None):
        p = self.traverse_subpath()
        if i < len(p):
            return p[i]
        else:
            return default   
        
class Index(grok.View, RepositoryView):
    def today(self):
        today = datetime.date.today()
        month = maanden[today.month-1]
        return '%s %s' % (today.day, month)
        

class Popup_Template(grok.View):
    #make the main template avaible for everything
    grok.context(zope.interface.Interface)
    
class Main_Template(grok.View, RepositoryView):
    #make the main template avaible for everything
    grok.context(zope.interface.Interface)

class Admin_Template(grok.View):
    #make the main template avaible for everything
    grok.context(zope.interface.Interface)   

class SiteMacros(grok.View):
    grok.context(zope.interface.Interface)   
    
class Personen(BioPortTraverser,grok.View,RepositoryView, Batcher):
    
    def update(self):
        Batcher.update(self)
    def get_persons(self):
        qry = {}
        #request.form has unicode keys - make strings
        for k in [
            'bioport_id', 
            'beginletter',
            'category',
            'geslacht',
            'order_by', 
            'search_term',
            'search_name',
            'size',
            'source_id',
            'start',
            'status',
              ]:
            if k in self.request.keys():
                qry[k] = self.request[k]
        
        ls = self.repository().get_persons(**qry)
        self.qry = qry
        batch = Batch(ls, start=self.start, size=self.size)
        batch.grand_total = len(ls)
        return batch

    def batch_navigation(self, batch):
		return '<a href="%s">%s</a>' % (self.batch_url(start=batch.start), batch[0].naam().geslachtsnaam())
    
class Persoon(BioPortTraverser, grok.View,RepositoryView): #, BioPortTraverser):
    def update(self, **args):
        self.bioport_id = self.traverse_subpath_helper(0) or self.request.get('bioport_id')
        redirects_to = self.repository().redirects_to(self.bioport_id)
        if redirects_to:
            self.bioport_id = redirects_to
        if not self.bioport_id:
            self.bioport_id = random.choice(self.repository().get_bioport_ids())
            self.redirect(self.url(self) + '/'+ self.bioport_id)
        self.person  = self.repository().get_person(bioport_id=self.bioport_id) 
        self.biography  = self.merged_biography = self.person.get_merged_biography()

    def get_event(self, type, biography=None):
        if not biography:
            biography = self.merged_biography
        event_el = biography.get_event(type)
        if event_el is not None:
            #we construct a convenient object
            class EventWrapper:
                def __init__(self, el):
                    self.when = el.get('when')
                    self.when_ymd = to_ymd(self.when) 
                    self.when_formatted = format_date(self.when)
                    self.notBefore = el.get('notBefore')
                    self.notBefore_ymd = to_ymd(self.notBefore) 
                    self.notBefore_formatted = format_date(self.notBefore)
                    self.notAfter = el.get('notAfter')
                    self.notAfter_ymd = to_ymd(self.notAfter) 
                    self.notAfter_formatted = format_date(self.notAfter)
                    self.date_text = el.find('date') is not None and el.find('date').text or ''
                    self.place =  el.find('place') is not None and el.find('place').text or ''
                    self.place_id = el.get('place_id')
                    self.type = el.get('type')
            return EventWrapper(event_el)
        else:
            return None      
    
    def get_states(self,type, biography=None):
        if not biography:
            biography = self.merged_biography
        result = []
        for el in  biography.get_states(type):
            if el is not None:
                class StateWrapper:
                    def __init__(self, el):
                        self.frm = el.get('from')
                        self.frm_ymd  = to_ymd(self.frm)
                        self.to = el.get('to')
                        self.to_ymd = to_ymd(self.to)
                        self.type = type
                        self.place = el.find('place') is not None and el.find('place').text or ''
                        self.text = el.text
                        self.idno = el.get('idno')
                        self.element = el
                    def has_content(self):
                        if self.frm or self.to or self.text or self.place or self.idno:
                            return True
                        else:
                            return False
                result.append(StateWrapper(el))
        return result
    def get_state(self, type, biography=None):
        states = self.get_states(type, biography)
        if states:
            return states[0]
        
    def maanden(self):
        return maanden
    
class Zoek(grok.View, RepositoryView):
    pass


class Auteurs(grok.View,RepositoryView, Batcher):
    def update(self):
        Batcher.update(self)
    def get_auteurs(self, **args):

        d = {}
        #request.form has unicode keys - make strings
        for k in self.request.form:
            d[str(k)] = self.request.form[k]
        
        ls = self.repository().get_authors(**d) 
        
        batch = Batch(ls, start=self.start, size=self.size)
        batch.grand_total = len(ls)
        return batch



class Bronnen(grok.View, RepositoryView):
    pass
class Colofon(grok.View, RepositoryView):
    pass

class Birthdays_Box(grok.View, RepositoryView):
    def get_persons(self):
        #get the month and day of today
        today = datetime.date.today().strftime('-%m-%d')
        #query the database for persons born on this date
        persons = self.repository().get_persons(where_clause='geboortedatum like "____%s"' % today, has_illustrations=True)
        return persons[:3]

class Birthdays(grok.View, RepositoryView):
    def get_persons_born_today(self):
        #get the month and day of today
        today = datetime.date.today().strftime('-%m-%d')
        #query the database for persons born on this date
        persons = self.repository().get_persons(where_clause='geboortedatum like "____%s"' % today)
        return persons

    def get_persons_dead_today(self):
        #get the month and day of today
        today = datetime.date.today().strftime('-%m-%d')
        #query the database for persons born on this date
        persons = self.repository().get_persons(where_clause='sterfdatum like "____%s"' % today)
        return persons
    def today(self):
        today = datetime.date.today()
        month = maanden[today.month-1]
        return '%s %s' % (today.day, month)
    
class About(grok.View, RepositoryView):
    pass

class Agenda(grok.View, RepositoryView):
    pass
class Contact(grok.View, RepositoryView):
    pass
class English(grok.View, RepositoryView):
    pass
class FAQ(grok.View, RepositoryView):
    pass
class Images_XML(grok.View, RepositoryView):
    grok.name('images.xml')
    def render(self):
        self.request.response.setHeader('Content-Type', 'text/xml')
        
        persons = self.repository().get_persons(has_illustrations=True, order_by='random', size=20)
        
        result = """<?xml version="1.0"?><root>"""
        for person in persons:
            illustration = person.get_merged_biography().get_illustrations()[0]
            result += '<image src="%s" title="%s" url="%s/%s" />\n' % (
                           illustration.cached_url(), 
#                           urllib.quote(unicode( person.name()).encode('utf8')), 
                           html2unicode(unicode(person.name())),
                           self.url('persoon'),
                           person.bioport_id,
                           )
        result += '</root>'
        return result
    
class Collecties(grok.View, RepositoryView):
    pass

class Instellingen(grok.View, RepositoryView):
    pass

class Stichting(grok.View, RepositoryView):
    pass

class RedactieRaad(grok.View, RepositoryView):
    pass