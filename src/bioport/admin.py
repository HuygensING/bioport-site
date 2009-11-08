
import grok
from BioPortRepository.repository import Repository
import BioPortRepository
from BioPortRepository.common import  BioPortException
from NamenIndex.common import to_ymd, from_ymd
from NamenIndex.naam import Naam
from common import RepositoryInterface, format_date, format_dates
from zope.interface import Interface
from zope import schema
import app
from permissions import *
from z3c.batching.batch import  Batch

class IAdminSettings(Interface):           
    SVN_REPOSITORY = schema.TextLine(title=u'URL of svn repository', required=False)
    SVN_REPOSITORY_LOCAL_COPY = schema.TextLine(title=u'path to local copy of svn repository', required=False)
   
    DB_CONNECTION = schema.TextLine(title=u'Database connection (e.g. "mysql://root@localhost/bioport_test" )', required=False)
    LIMIT = schema.Decimal(title=u'Dont download more than this amount of biographies per source (used for testing)', required=False)

    
class Admin(grok.Container,  RepositoryInterface):
    grok.implements(IAdminSettings)
    grok.template('admin_index')
    
    SVN_REPOSITORY = None
    SVN_REPOSITORY_LOCAL_COPY = None
    DB_CONNECTION = None
    LIMIT = None
    def get_repository(self):
        repo = Repository(
            svn_repository=self.SVN_REPOSITORY, 
            svn_repository_local_copy=self.SVN_REPOSITORY_LOCAL_COPY,
            database=self.DB_CONNECTION,
            ZOPE_SESSIONS=False, #use z3c.saconfig package
        ) 
        return repo
    
    def repository(self):
        return self.get_repository()
    
    def format_date(self, s):
        return format_date(s)
    def format_dates(self, s1, s2):
        return  format_dates(s1, s2)
    
class Edit(grok.EditForm):
    grok.template('edit')
    grok.context(Admin)
    form_fields = grok.Fields(IAdminSettings)
    @grok.action(u"Edit Admin settings", name="edit_settings")
    def edit_admin(self, **data):
        self.applyData(self.context, **data)
        self.context.get_repository().db.metadata.create_all()
        self.redirect(self.url(self))
    
#    @grok.action('reset database (LOOK OUT)', name="reset_database")
#    def reset_database(self, **data):
#        self.context.get_repository().db.metadata.drop_all()
#        self.context.get_repository().db.metadata.create_all()
#        self.redirect(self.url(self))
        
    @grok.action('Fill the similarity Cache', name='fill_similarity_cache') 
    def fill_similarity_cache(self, **data):
        self.context.repository().db.fill_similarity_cache()
        self.redirect(self.url(self))
       
       
    @grok.action('Refresh the similar persons cache')
    def fill_most_similar_persons_cache(self, **data):
        self.context.repository().db.fill_most_similar_persons_cache(refresh=True)
        self.redirect(self.url(self))
        
        
    @grok.action('Create non-existing tables')
    def reset_database(self, **data):
        self.context.get_repository().db.metadata.create_all()
        self.redirect(self.url(self))
        
    @grok.action('Refresh the similarity cache [I.E. EMPTYING IT FIRST]')
    def refresh_similirity_cache(self, **data): 
        self.context.repository().db.fill_similarity_cache(refresh=True)
        self.redirect(self.url(self))
        
    @grok.action('Fill geolocations table')
    def refresh_similirity_cache(self, **data): 
        self.context.repository().db._update_geolocations_table()
        self.redirect(self.url(self))
        
class Display(grok.DisplayForm):
    grok.context(Admin)
    form_fields = grok.Fields(IAdminSettings)
 
class Index(grok.View):
    pass
    
class Biographies(grok.View):
    grok.context(Admin)
    
    def get_biographies(self):
        return self.context.get_repository().get_biographies()

class Biography_Identify(grok.View):
    pass

class Biography(grok.View):
    pass


class Persons(app.Personen):
    pass

class Source(grok.EditForm):
    def get_repository(self):
        repository = self.context.repository()
        return repository
    
    def update(self, source_id=None, description=None, url=None, quality=None):
        if source_id:
            repository = self.get_repository()
            source = repository.get_source(source_id) 
            if url is not None:
                source.set_value(url=url)
            if description is not None:
                source.set_value(description=description) 
            if quality is not None:
                source.set_quality(int(quality))
    
            repository.save_source(source)
            
            msg = 'Changed source %s' % source.id
            print msg
            
        
               
class Sources(grok.View):
    

    def update(self, action=None, source_id=None, url=None, description=None):
        if action == 'update_source':
            self.update_source(source_id)
            self.redirect(self.url())
        elif action == 'source_delete':
            self.source_delete(source_id)
        elif action=='add_source':
            self.add_source(source_id, url, description)   
            
    def update_source(self, source_id):
        repo = self.context.repository()
        source =repo.get_source(source_id)
        repo.update_source(source, limit=int(self.context.LIMIT))
        
    def download_data(self, source_id):
        repository = self.context.repository()
        source = repository.get_source(id=source_id)
        repository.download_biographies(source=source)
        self.redirect(self.url())
    def add_source(self, source_id, url, description=None):
        source = self.context.repository().add_source(BioPortRepository.source.Source(source_id, url, description))
 
    def source_delete(self, source_id):
        repo = self.context.repository() 
        source = self.context.repository().get_source(source_id)
        repo.commit(source)
        repo.delete_source(source)
        
        msg = 'Deleted source with id %s ' % source_id
        print msg
        return msg
    
class MostSimilar(grok.Form):
    #grok.require('bioport.EditRepository')
    def update(self):
        self.start = int(self.request.get('start', 0))
        self.size = int(self.request.get('size', 20))

    @grok.action('identificeer', name='identify')
    def identify(self):
        bioport_ids = self.request.get('bioport_ids')
        repo = self.context.repository()
        persons = [BioPortRepository.person.Person(id, repository=repo) for id in bioport_ids]
        assert len(persons) == 2
        repo.identify(persons[0], persons[1])
        
        self.bioport_ids = bioport_ids
        self.persons = persons
        msg = 'Identified <a href="../persoon?bioport_id=%s">%s</a> and <a href="../persoon?bioport_id=%s">%s</a>' % (
                     bioport_ids[0],  bioport_ids[0], bioport_ids[1],  bioport_ids[1])
        
        #redirect the user to where wer were
        data={'msg':msg, 'start':self.request.get('start', 0)}
        self.redirect(self.url(self.__parent__, 'mostsimilar', data = data))
        
    @grok.action('anti-identificieer', name='antiidentify')
    def antiidentify(self):
        bioport_ids = self.request.get('bioport_ids')
        repo = self.context.repository()
        persons = [BioPortRepository.person.Person(id, repository=repo) for id in bioport_ids]
        p1, p2 = persons
        repo.antiidentify(p1, p2)
        
        self.bioport_ids = bioport_ids
        self.persons = persons
        msg = 'Anti-Identified <a href="../persoon?bioport_id=%s">%s</a> and <a href="../persoon?bioport_id=%s">%s</a>' % (
                     bioport_ids[0], persons[0].get_bioport_id(), bioport_ids[1], persons[1].get_bioport_id())
        
        #redirect the user to where wer were
        data={'msg':msg, 'start':self.request.get('start', 0)}
        self.redirect(self.url(self.__parent__, 'mostsimilar', data = data))
        
   
    @grok.action('Moeilijk geval', name='deferidentification')
    def deferidentification(self):
        bioport_ids = self.request.get('bioport_ids') 
        repo = self.context.repository()
        persons = [BioPortRepository.person.Person(id, repository=repo) for id in bioport_ids]
        p1, p2 = persons
        repo.defer_identification(p1, p2)
        
        self.bioport_ids = bioport_ids
        self.persons = persons
        msg = 'Deferred identification of <a href="../persoon?bioport_id=%s">%s</a> and <a href="../persoon?bioport_id=%s">%s</a>' % (
                     bioport_ids[0], persons[0].get_bioport_id(), bioport_ids[1], persons[1].get_bioport_id())
        
        #redirect the user to where wer were
        data={'msg':msg, 'start':self.request.get('start', 0)}
        self.redirect(self.url(self.__parent__, 'mostsimilar', data = data))
             
class IdentifyMoreInfo(grok.View):
    def update(self, bioport_ids):
        repo = self.context.repository()
        persons = [BioPortRepository.person.Person(id, repository=repo) for id in bioport_ids]
        self.bioport_ids = bioport_ids
        self.persons = persons

class Persoon(app.Persoon, grok.EditForm):
    """This should really be an "Edit" view on a "Person" Model
    
    But I am in an incredible hurry and have no time to learn :-("""
    def update(self, **args):
        self.bioport_id = self.request.get('bioport_id')         
        if not self.bioport_id:
            #XXX make a userfrienlider error
            assert 0, 'need bioport_id in the request'
            
        self.person  = self.context.get_person(id=self.bioport_id)  
        self.merged_biography  = self.person.get_merged_biography()
        self.repository = self.context.repository()
        self.bioport_biography =  self.repository.get_bioport_biography(self.person) 
        event_birth = self.bioport_biography.get_event('birth')
        if event_birth is not None:
            self.birth_notBefore = to_ymd(event_birth.get('notBefore') )
            self.birth_notAfter = to_ymd(event_birth.get('notAfter')) 
        else:
            self.birth_notBefore = ''
            self.birth_notAfter = ''
            
    def to_ymd(self, s):
        return to_ymd(s)
    
    def get_bioport_namen(self):
        return self.bioport_biography.get_namen()
    def get_non_bioport_namen(self):
        namen = self.merged_biography.get_names()
        namen = [naam for naam in namen if naam.to_string() not in [n.to_string() for n in self.get_bioport_namen()]]
        return namen
    
    def get_namen(self):
        namen = self.merged_biography.get_names()
        return namen
    

    def get_value(self, k, biography=None):
        if not biography:
            biography = self.merged_biography
        if k in ['geboortedatum', 'sterfdatum']:
            return to_ymd(biography.get_value(k, ''))
        else:
            return biography.get_value(k, '')
        
    def status_value(self, event_id, attr):
        """return 'bioport' if the value is added by the editors of the biographical portal
        return 'merged' if the value comes from the merged_biography"""
        bioport_event = self.get_event(event_id, biography=self.bioport_biography)
#        merged_event = self.get_event(self.merged_biography)
        if getattr(bioport_event, attr, None):
            return 'bioport'
        else:
            return 'merged'
        
        if self.bioport_biography.get_value(k):
            return 'bioport'
        elif self.merged_biography.get_value(k):
            return 'merged'
        else:
            return ''    
        
    def validate_event(self, action, data):
        pass
    def _get_event_date_from_request(self, prefix):
        y = self.request.get('%s_y' % prefix)
        m = self.request.get('%s_m' % prefix)
        d = self.request.get('%s_d' % prefix)
        ymd = from_ymd(y, m, d)
        return ymd or ''
    
    def _set_event(self, type):
        when = self._get_event_date_from_request('%s' % type )
        notBefore = self._get_event_date_from_request('%s_notBefore' % type)
        notAfter = self._get_event_date_from_request('%s_notAfter' % type)
        date_text = self.request.get('%s_text' % type)
        place = self.request.get('%s_place' % type)
        self.bioport_biography._add_or_update_event(type, when=when, date_text=date_text, notBefore=notBefore, notAfter=notAfter, place=place)
           
    @grok.action('bewaar veranderingen', name="save_event_birth", validator=validate_event)
    def save_event_birth(self):
        self._set_event('birth')
        self.repository.save_biography(self.bioport_biography)
        msg = 'saved geboortedatum'
        self.redirect(self.url(self, data={'msg':msg, 'bioport_id':self.bioport_id}))
        
           
    @grok.action('bewaar veranderingen', name='save_event_death')
    def save_event_death(self):
        self._set_event('death')
        self.repository.save_biography(self.bioport_biography)
        msg = 'saved sterdatum'
        self.redirect(self.url(self, data={'msg':msg, 'bioport_id':self.bioport_id}))
        
    @grok.action('bewaar veranderingen', name='save_event_baptism')
    def save_event_baptism(self):
        self._set_event('baptism')
        self.repository.save_biography(self.bioport_biography)
        msg = 'doopdatum veranderd'
        self.redirect(self.url(self, data={'msg':msg, 'bioport_id':self.bioport_id}))
            
    @grok.action('bewaar veranderingen', name='save_event_funeral')
    def save_event_funeral(self):
        self._set_event('funeral')
        self.repository.save_biography(self.bioport_biography)
        msg = 'begraafdatum veranderd'
        self.redirect(self.url(self, data={'msg':msg, 'bioport_id':self.bioport_id}))
            
         
    @grok.action('verander naam', name='change_name')  
    def change_name(self):
         self.redirect(self.url(self.__parent__, 'changename', data={'bioport_id':self.bioport_id}))
         
    @grok.action('bewaar alle veranderingen', name='save_everything')  
    def save_everything(self):
        self._set_event('birth')
        self._set_event('death')
        self._set_event('funeral')
        self._set_event('baptism')
        self.repository.save_biography(self.bioport_biography)
        msg = 'saved values'
        print self.bioport_biography.to_string()
        self.redirect(self.url(self, data={'msg':msg, 'bioport_id':self.bioport_id}))
    
    
class ChangeName(grok.EditForm): 
    
    def update(self, **args):
        self.bioport_id = self.request.get('bioport_id')         
        if not self.bioport_id:
            #XXX make a userfrienlider error
            assert 0, 'need bioport_id in the request'
        self.person  = self.context.get_person(id=self.bioport_id)  
        self.bioport_biography  = self.context.repository().get_bioport_biography(self.person)
        
        if not self.bioport_biography.get_namen():
            for naam in self.person.get_merged_biography().get_names():
                self.bioport_biography._add_a_name(naam)
            self.context.repository().save_biography(self.bioport_biography)
        
        self.idx = self.request.get('idx')         
        if not self.idx or self.idx == u'new':
            self.naam = None
        else:
            self.idx = int(self.idx) 
            self.naam  = self.bioport_biography.get_namen()[self.idx] 
       
    @grok.action('bewaar veranderingen', name='save_changes') 
    def save_changes(self):
        bio = self.bioport_biography
        
        parts = ['prepositie', 'voornaam', 'intrapositie', 'geslachtsnaam', 'postpositie']
        args = dict([(k, self.request.get(k)) for k in parts])
        
        volledige_naam = self.request.get('volledige_naam')
            
        #als de volledige naam niet is veranderd, maar een van de oude velden wel
        #dan, ja, dan wat?
        if volledige_naam in ' '.join(parts):
            volledige_naam = ' '.join(parts)
        
        name = Naam(
            volledige_naam = volledige_naam,
            **args
        )
        repository = self.context.repository()
        bio._replace_name(name, self.idx)
        repository.save_biography(bio)
        msg = 'changed a name'
        
        self.redirect(self.url('persoon',data= {'bioport_id':self.bioport_id, 'msg':msg}))
    
    @grok.action('voeg toe', name='add_name') 
    def add_name(self):
        name = Naam(
            repositie = self.request.get('prepositie'),
            voornaam = self.request.get('voornaam'),
            intrapositie = self.request.get('intrapositie'),
            geslachtsnaam = self.request.get('geslachtsnaam'),
            postpositie = self.request.get('postpositie'),
            volledige_naam = self.request.get('volledige_naam'),
        )
        repository = self.context.repository()
        bio = repository.get_bioport_biography(self.person)
        bio._add_a_name(name)
        repository.save_biography(bio)
        msg = 'added a name'
        
        self.redirect(self.url('persoon',data= {'bioport_id':self.bioport_id, 'msg':msg}))
    
    
class AntiIdentified(grok.View):
    pass

class Identified(grok.View):
    pass

class Deferred(grok.View):
    pass
    
class Uitleg(grok.View): 
    pass
    
class Locations(grok.View):     
    def update(self, **kw):
        self.batch_start = int(self.request.get('batch_start', 0))
        self.batch_size = int(self.request.get('batch_size', 30))
        self.startswith = self.request.get('startswith', None)
        self.name = self.request.get('name', None)
        
    def get_locations(self):
        ls = self.context.repository().db.get_locations(startswith=self.startswith, name=self.name)
        
        batch = Batch(ls, start=self.batch_start, size=self.batch_size)
        batch.grand_total = len(ls)
        return batch
    