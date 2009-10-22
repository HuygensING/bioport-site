
import grok
from BioPortRepository.repository import Repository
import BioPortRepository
from BioPortRepository.common import  BioPortException
from BioDes.common import to_ymd, from_ymd
from common import FormatUtilities, RepositoryInterface
from zope.interface import Interface
from zope import schema
from app import Personen
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
       
    @grok.action('Refresh the similiarty cache')
    def refresh_similirity_cache(self, **data): 
        self.context.repository().db.fill_similarity_cache(refresh=True)
        self.redirect(self.url(self))
        
    @grok.action('Create tables')
    def reset_database(self, **data):
        self.context.get_repository().db.metadata.create_all()
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
            
class Identify(grok.View):
    def update(self, bioport_ids):
        repo = self.context.repository()
        persons = [BioPortRepository.person.Person(id, repository=repo) for id in bioport_ids]
        repo.identify(persons)
        
        self.bioport_ids = bioport_ids
        self.persons = persons
        msg = 'Identified %s' % bioport_ids
        self.redirect(self.url(self.__parent__, 'mostsimilar', data={'msg':msg}))
             
class IdentifyMoreInfo(grok.View):
    def update(self, bioport_ids):
        repo = self.context.repository()
        persons = [BioPortRepository.person.Person(id, repository=repo) for id in bioport_ids]
        self.bioport_ids = bioport_ids
        self.persons = persons

class AntiIdentify(grok.View):      
    #Given that we only redirect, this should not be a a view
     def update(self, bioport_ids):
        repo = self.context.repository()
        persons = [BioPortRepository.person.Person(id, repository=repo) for id in bioport_ids]
        p1, p2 = persons
        repo.antiidentify(p1, p2)
        
        self.bioport_ids = bioport_ids
        self.persons = persons
        msg = 'Anti-identified %s' % bioport_ids
        self.redirect(self.url(self.__parent__, 'mostsimilar', data={'msg':msg}))
                      
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
class MostSimilar(grok.View):
    pass


class Persoon(grok.EditForm):
    """This should really be an "Edit" view on a "Person" Model
    
    But I am in an incredible hurry and have no time to learn :-("""
    def update(self, **args):
        self.bioport_id = self.request.get('bioport_id')         
        if not self.bioport_id:
            #XXX make a userfrienlider error
            assert 0, 'need bioport_id in the request'
            
        self.person  = self.context.get_person(id=self.bioport_id)  
        self.biography  = self.person.get_merged_biography()
            
    def ymd(self, s):
        """take a string of the form "YYYY-MM-DD" (or "YYYY"), terurn a tuple (year, month, date) of three integers"""
        return to_ymd(s)

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
        y = self.request.get('birth_y')
        m = self.request.get('birth_m')
        d = self.request.get('birth_d')
        ymd = from_ymd(y, m, d)
        self.set_value('geboortedatum', ymd)
        
            
    @grok.action('bewaar veranderingen', name='save_sterfdatum')
    def save_sterfdatum(self):
        y = self.request.get('death_y')
        m = self.request.get('death_m')
        d = self.request.get('death_d')
        ymd = from_ymd(y, m, d)
        self.set_value('sterfdatum', ymd)      
        
    @grok.action('bewaar veranderingen', name='save_geboorteplaats')  
    def save_geboorteplaats(self):
         s = self.request.get('geboorteplaats')
         self.set_value('geboorteplaats', s)
         
    @grok.action('bewaar veranderingen', name='save_sterfplaats')  
    def save_sterfplaats(self):
         s = self.request.get('sterfplaats')
         self.set_value('sterfplaats', s)
         
    @grok.action('verander naam', name='change_name')  
    def change_name(self):
         self.redirect(self.url(self.__parent__, 'changename', data={'bioport_id':self.bioport_id}))
         
    @grok.action('bewaar veranderingen', name='save_sterfplaats')  
    def save_everyting(self):
        self.save_geboortedatum()
        self.save_sterfdatum()
        self.save_geboorteplaats()
        self.save_sterfplaats()
    
class ChangeName(grok.EditForm): 
    
    def update(self, **args):
        self.bioport_id = self.request.get('bioport_id')         
        if not self.bioport_id:
            #XXX make a userfrienlider error
            assert 0, 'need bioport_id in the request'
        self.person  = self.context.get_person(id=self.bioport_id)  
        self.biography  = self.person.get_merged_biography()
        self.naam  = self.biography.get_names()[0] 
       
    @grok.action('bewaar veranderingen', name='save_changes') 
    def save_changes(self):
        pass