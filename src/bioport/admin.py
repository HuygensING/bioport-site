
import grok
from BioPortRepository.repository import Repository
import BioPortRepository
from BioPortRepository.common import  BioPortException
from NamenIndex.common import to_ymd, from_ymd
from NamenIndex.naam import Naam
from common import FormatUtilities, RepositoryInterface
from zope.interface import Interface
from zope import schema
from app import Personen
from permissions import *

class IAdminSettings(Interface):           
    SVN_REPOSITORY = schema.TextLine(title=u'URL of svn repository')
    SVN_REPOSITORY_LOCAL_COPY = schema.TextLine(title=u'path to local copy of svn repository')
   
    DB_CONNECTION = schema.TextLine(title=u'Database connection (e.g. "mysql://root@localhost/bioport_test" )')
    LIMIT = schema.Decimal(title=u'Dont download more than this amount of biographies per source (used for testing)')

    
class Admin(grok.Container,  FormatUtilities, RepositoryInterface):
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


class Persons(Personen):
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
            
#class Identify(grok.View):
#    def update(self, bioport_ids):
#        repo = self.context.repository()
#        persons = [BioPortRepository.person.Person(id, repository=repo) for id in bioport_ids]
#        assert len(persons) == 2
#        repo.identify(persons[0], persons[1])
#        
#        self.bioport_ids = bioport_ids
#        self.persons = persons
#        msg = 'Identified <a href="../persoon?bioport_id=%s">%s</a> and <a href="../persoon?bioport_id=%s">%s</a>' % (
#                     bioport_ids[0],  bioport_ids[0], bioport_ids[1],  bioport_ids[1])
#        self.redirect(self.url(self.__parent__, 'mostsimilar', data={'msg':msg}))


        
               
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
        self.redirect(self.url(self.__parent__, 'mostsimilar', data={'msg':msg}))
        
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
        self.redirect(self.url(self.__parent__, 'mostsimilar', data={'msg':msg}))
        
        
   
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
        self.redirect(self.url(self.__parent__, 'mostsimilar', data={'msg':msg}))      
        
             
class IdentifyMoreInfo(grok.View):
    def update(self, bioport_ids):
        repo = self.context.repository()
        persons = [BioPortRepository.person.Person(id, repository=repo) for id in bioport_ids]
        self.bioport_ids = bioport_ids
        self.persons = persons

class Persoon(grok.EditForm):
    """This should really be an "Edit" view on a "Person" Model
    
    But I am in an incredible hurry and have no time to learn :-("""
    def update(self, **args):
        self.bioport_id = self.request.get('bioport_id')         
        if not self.bioport_id:
            #XXX make a userfrienlider error
            assert 0, 'need bioport_id in the request'
            
        self.person  = self.context.get_person(id=self.bioport_id)  
        self.merged_biography  = self.person.get_merged_biography()
        self.bioport_biography = self.context.repository().get_bioport_biography(self.person) 
    def ymd(self, s):
        """take a string of the form "YYYY-MM-DD" (or "YYYY"), terurn a tuple (year, month, date) of three integers"""
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
    def get_value(self, k):
        if k in ['geboortedatum', 'sterfdatum']:
            return self.ymd(self.merged_biography.get_value(k, ''))
        else:
            return self.merged_biography.get_value(k, '')
    def status_value(self, k):
        """return 'bioport' if the value is added by the editors of the biographical portal
        return 'merged' if the value comes from the merged_biography"""
        if self.bioport_biography.get_value(k):
            return 'bioport'
        elif self.merged_biography.get_value(k):
            return 'merged'
        else:
            return ''    

    def set_value(self, k, v):
        """set the value in the bioport biography for key "k" to the value v
        
        and redirect"""
        repository = self.context.repository()
        bio = repository.get_bioport_biography(self.person)
        bio.set_value(k, v)
        repository.save_biography(bio)
        msg = 'saved values'
        self.redirect(self.url(self, data={'msg':msg, 'bioport_id':self.bioport_id}))
            
    @grok.action('bewaar veranderingen', name='save_geboortedatum')
    def save_geboortedatum(self):
        self._save_geboortedatum()
        
    def _save_geboortedatum(self):
        y = self.request.get('birth_y')
        m = self.request.get('birth_m')
        d = self.request.get('birth_d')
        if y:
            ymd = from_ymd(y, m, d)
            self.set_value('geboortedatum', ymd)
        
            
    @grok.action('bewaar veranderingen', name='save_sterfdatum')
    def save_sterfdatum(self):
        self._save_sterfdatum()
    def _save_sterfdatum(self):
        y = self.request.get('death_y')
        m = self.request.get('death_m')
        d = self.request.get('death_d')
        if y:
            ymd = from_ymd(y, m, d)
            self.set_value('sterfdatum', ymd)      
            
    @grok.action('bewaar veranderingen', name='save_geboorteplaats')  
    def save_geboorteplaats(self):
        self._save_geboorteplaats()
    def _save_geboorteplaats(self):
         s = self.request.get('geboorteplaats')
         self.set_value('geboorteplaats', s)
         
    @grok.action('bewaar veranderingen', name='save_sterfplaats')  
    def save_sterfplaats(self):
        self._save_sterfplaats()
    def _save_sterfplaats(self):
        
         s = self.request.get('sterfplaats')
         self.set_value('sterfplaats', s)
         
    @grok.action('verander naam', name='change_name')  
    def change_name(self):
         self.redirect(self.url(self.__parent__, 'changename', data={'bioport_id':self.bioport_id}))
         
    @grok.action('bewaar veranderingen', name='save_everything')  
    def save_everyting(self):
        self._save_geboortedatum()
        self._save_geboorteplaats()
        self._save_sterfdatum()
        self._save_sterfplaats()
    
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
    
    
    
     