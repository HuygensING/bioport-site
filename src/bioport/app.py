import grok
import zope.interface
from z3c.batching.batch import  Batch
import random
from common import  maanden, format_date, format_dates
from NamenIndex.common import to_ymd, from_ymd

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
    
    
class Batcher: 
    def update(self, **kw):
        self.batch_start = int(self.request.get('batch_start', 0))
        self.batch_size = int(self.request.get('batch_size', 30))
    def batch_url(self, start=0):
        data = self.request.form
        data['batch_start'] = start 
        return self.url(data= data)       
class Bioport(grok.Application, grok.Container):
              
    SVN_REPOSITORY = None
    SVN_REPOSITORY_LOCAL_COPY = None
    DB_CONNECTION = None
    debug=False
    def __init__(self, db_connection=None):
        super(Bioport,self).__init__() #cargoculting from ingforms 
        from admin import Admin
        self['admin'] = Admin()
        self['admin'].DB_CONNECTION = db_connection
    def format_dates(self, s1, s2):
        return  format_dates(s1, s2)

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
    pass # see app_templates/index.pt

class Popup_Template(grok.View):
    #make the main template avaible for everything
    grok.context(zope.interface.Interface)
    
class Main_Template(grok.View):
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
            'batch_start',
            'batch_size',
            'beginletter',
            'geslacht',
            'order_by', 
            'search_term',
            'source_id',
            'bioport_id', 
            'status',
              ]:
            if k in self.request.keys():
	            qry[k] = self.request[k]
        if qry.get('search_term'):
            qry['search_term'] = qry['search_term']
        
        ls = self.repository().get_persons(**qry)
        self.qry = qry
        batch = Batch(ls, start=self.batch_start, size=self.batch_size)
        batch.grand_total = len(ls)
        return batch


    
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
                    self.place = el.find('place') is not None and el.find('place').text or ''
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
	                    self.text = el.text
	                    self.idno = el.get('idno')
	            result.append(StateWrapper(el))
        return result
    def get_state(self, type, biography=None):
        states = self.get_states(type, biography)
        if states:
	        return states[0]
        
    def maanden(self):
        return maanden
    
class Zoek(grok.View):
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
        
        batch = Batch(ls, start=self.batch_start, size=self.batch_size)
        batch.grand_total = len(ls)
        return batch



class Bronnen(grok.View):
    pass
class Colofon(grok.View):
    pass
