#!/usr/bin/env python

import os
import time    
import app
import grok
import logging
from app import Batcher, RepositoryView

from common import format_date, format_dates, format_number
from names.common import from_ymd, to_ymd
from names.name import Naam
from permissions import *
from plone.memoize import forever
from z3c.batching.batch import Batch
from zope import schema
from zope.interface import Interface
from zope.session.interfaces import ISession

import bioport_repository
from bioport_repository.repository import Repository

from gerbrandyutils import normalize_url, run_in_thread


class IAdminSettings(Interface):
    SVN_REPOSITORY = schema.TextLine(title=u'URL of svn repository', required=False)
    SVN_REPOSITORY_LOCAL_COPY = schema.TextLine(title=u'path to local copy of svn repository', required=False)
   
    DB_CONNECTION = schema.TextLine(title=u'Database connection (e.g. "mysql://root@localhost/bioport_test" )', required=False)
    LIMIT = schema.Decimal(title=u'Dont download more than this amount of biographies per source (used for testing)', required=False)

    IMAGES_CACHE_LOCAL = schema.TextLine(title=u'Local path to the place where images are kept', required=False) 
    IMAGES_CACHE_URL = schema.TextLine(title=u'URL to the place where images are kept', required=False) 
    EMAIL_FROM_ADDRESS = schema.TextLine(title=u'''Emails sent by the site will have this email address as source''', required=False)
    CONTACT_DESTINATION_ADDRESS = schema.TextLine(title=u'''Emails sent by the site will be sent to this email address''', required=False)


class IHomePageSettings(Interface):
    dutch_home_html = schema.Text(title=u'Dutch html for the homepage')
    english_home_html = schema.Text(title=u'English html for the homepage')


class Admin(grok.Container):

    grok.require('bioport.Edit')
    grok.implements(IAdminSettings, IHomePageSettings)
    grok.template('admin_index')
    
    SVN_REPOSITORY = None
    SVN_REPOSITORY_LOCAL_COPY = None
    DB_CONNECTION = None
    LIMIT = None
    IMAGES_CACHE_LOCAL = None
    IMAGES_CACHE_URL = None
    EMAIL_FROM_ADDRESS = 'test@example.com'
    CONTACT_DESTINATION_ADDRESS = 'destination@example.com'
    dutch_home_html = english_home_html = 'Biografisch Portaal van Netherlands'
    
    @forever.memoize
    def repository(self, user):
        return Repository(
            svn_repository=self.SVN_REPOSITORY, 
            svn_repository_local_copy=self.SVN_REPOSITORY_LOCAL_COPY,
            db_connection=self.DB_CONNECTION,
            images_cache_local=self.IMAGES_CACHE_LOCAL,
            images_cache_url=self.IMAGES_CACHE_URL,
            user=user,
#            ZOPE_SESSIONS=False, #use z3c.saconfig package
            ) 

    def __getstate__(self):
        #we cannot (And dont want to) pickle the repository -- like this we exclude it
        try:
            del self.__dict__['_repo']
        except KeyError:
            pass
        return self.__dict__
    
    def format_date(self, s):
        return format_date(s)
    
    def format_dates(self, s1, s2, **args):
        return  format_dates(s1, s2, **args)
    
    def format_number(self, s):
        return format_number(s)

    def get_auteurs(self, **args):
        return self.repository().get_authors()   
    

class Edit(grok.EditForm,RepositoryView):

    grok.require('bioport.Manage')
    grok.template('edit')
    grok.context(Admin)
    form_fields = grok.Fields(IAdminSettings)
    
    def _redirect_with_msg(self, msg, base_url=None):
        if base_url is None:
            base_url = self.url()
        source_id = self.request.get('source_id')
        url = "%(base_url)s?source_id=%(source_id)s&msg=%(msg)s" % locals()
        url = normalize_url(url)
        return self.redirect(url)

    @grok.action('Find biography contradictions')
    def find_biography_contradictions(self, **data): 
        started = time.time()
        total = self.repository().db.count_persons()
        processed = self.repository().db.find_biography_contradictions()
        elapsed_time = time.time() - started
        msg = "Found %s contradictions out of %s persons in %0.3f secs" % \
              (processed, total, elapsed_time)
        self._redirect_with_msg(msg)

    @grok.action(u"Edit Admin settings", name="edit_settings")
    def edit_admin(self, **data):
        self.applyData(self.context, **data)
        repository = self.repository()
        #repository.db.metadata.create_all()
        #self.redirect(self.url(self))
   
#    @grok.action('Fill the similarity Cache', name='fill_similarity_cache') 
#    def fill_similarity_cache(self, **data):
#        self.repository().db.fill_similarity_cache()
    
    @grok.action('Refresh the similarity cache', name='refresh_similarity_cache')
    def refresh_similarity_cache(self, **data): 
        refresh = bool(self.request.get('refresh'))
        sid = self.request.get('source_id', None)
        self.repository().db.fill_similarity_cache(refresh=refresh, source_id=sid)
        self._redirect_with_msg('finished')
        
#    @grok.action('Create non-existing tables')
#    def reset_database(self, **data):
#        self.repository().db.metadata.create_all()
        
        
#    @grok.action('Fill geolocations table')
#    def fill_geolocations_table(self, **data): 
#        self.repository().db._update_geolocations_table()
#        self.redirect(self.url(self))
        
#   @grok.action('Fill categories table')
#   def fill_categories_table(self, **data): 
#        self.repository().db._update_category_table()
#        self.redirect(self.url(self))

    @grok.action('update persons')        
    def update_persons(self, **args):
        total = self.repository().db.update_persons()
        self._redirect_with_msg("%s persons updated." % total)
        
    @grok.action('recompute_soundexes')
    def tmp_update_soundexes(self, **data):
        self.repository().db.tmp_update_soundexes()
    @grok.action('add category kunstatnaars to all rkdartists')
    def tmp_add_category_to_rkdartists(self, **data):
        repo = self.repository()
        persons = repo.get_persons(source_id='rkdartists')
        logging.info('add categoery 3 to rkdartsts')
        i = 0
        for p in persons:
            i += 1
            logging.info('progress: %s/%s' % (i, len(persons)))
            bioport_bio = p.get_bioport_biography()
            bioport_bio.set_category(bioport_bio.get_category_ids() + [3])  
            repo.save_biography(bioport_bio)

    @grok.action('identify all similarity pairs with a score score of 1.0')            
    def tmp_identify_rkdartists(self):
        logging.info('identifying all pairs with a similarity score of 1.0')
        i = 0
        ls = self.repository().get_most_similar_persons(size=1000)
        for (score, p1, p2) in ls:
            i += 1
            if score == 1.0:
                logging.info('identifying %s and %s [%s] (%s/%s)' % (p1, p2, score, i, len(ls)))
                self.repository().identify(p1, p2)
            else:
                logging.info('done')
                return
#    @grok.action('add_biodes')
#    def add_biodes(self, **data):
#        from biodes import BioDes
#        self.__parent__.__parent__['biodes'] = BioDes()
       
#    @grok.action('Set state of edited persons to bewerkte(JG: DELETE THIS BUTTON WHEN DONE)')
#    def set_state_to_bewerkt(self, **data):
#        from bioport_repository.upgrade import upgrade_persons
#        upgrade_persons(self.repository())
    
#    @grok.action('refill table with identical dbnl ids')
#    def refill_identical_dbnl_ids(self, **data):
#        from bioport_repository.tmp import update_vdaa_and_nnbw_doubles
#        repository = self.repository()
#        update_vdaa_and_nnbw_doubles.update_table_dbnl_ids(repo=repository)

#    @grok.action('identify vdaa and nnbw doubles')
#    def identify_vdaa_etc(self, **args):
#        from bioport_repository.tmp.update_vdaa_and_nnbw_doubles import identify_doubles
#        identify_doubles(repo =self.repository())

#    @grok.action('Fix identification error')
#    def fix_identification_error(self, **data):
#        #reload nnbw/10908
#        ls = [('nnbw', 'nnbw/10908', 'http://www.inghist.nl/media/bioport/bronnen/nnbw/bio/10908.xml'),
#         ('vdaa', 'vdaa/a0060', 'http://www.inghist.nl/media/bioport/bronnen/vdaa/bio/a0060.xml'),
#        ]
#        repo = self.repository()
#        for source_id, bio_id, biourl in ls:
#            bio = bioport_repository.biography.Biography(source_id=source_id, repository=repo)
#            bio.from_url(biourl)
#            repo.add_biography(bio)        
            
#    @grok.action('tmp_fixup_category_doublures ')
#    def tmp_fixup_category_doublures(self, **data):
#        self.repository().db.tmp_fixup_category_doublures()
        
#    @grok.action('tmp_identify_misdaad_recht')
#    def tmp_identify_misdaad_recht(self, **data):
#        self.repository().db.tmp_identify_misdaad_recht()
        
#    @grok.action('tmp_fix_weird_categeries')
#    def tmp_fix_weird_categeries(self, **data):
#        self.repository().db.tmp_fix_weird_categeries()
        
#    @grok.action('give blnps a categorie')
#    def tmp_give_blnps_a_category(self, **data):
#        self.repository().db.tmp_give_blnps_a_category()      
        
        
class Display(grok.DisplayForm):
    grok.require('bioport.Edit')
    grok.context(Admin)
    form_fields = grok.Fields(IAdminSettings)
 

class Index(grok.View):
    grok.require('bioport.Edit')
    

class Biographies(grok.View, RepositoryView):

    grok.require('bioport.Edit')
    grok.context(Admin)
    
    def get_biographies(self):
        return self.repository().get_biographies()


class Biography(grok.View):
    grok.require('bioport.Edit')


class Persons(app.Personen,RepositoryView):
    grok.require('bioport.Edit')
    @grok.action('zoek', name="search_persons")

    def search_persons(self):
        self.persons = self.get_persons()

    def get_persons(self):
        return app.Personen.get_persons(self, hide_invisible=False)

        
class Source(grok.EditForm,RepositoryView):
    grok.require('bioport.Edit')

    def _redirect_with_msg(self, msg, base_url=None):
        if base_url is None:
            base_url = self.url()
        source_id = self.request.get('source_id')
        url = "%(base_url)s?source_id=%(source_id)s&msg=%(msg)s" % locals()
        url = normalize_url(url)
        return self.redirect(url)

    def update(self, source_id=None):
        repository = self.repository()
        self.source =repository.get_source(source_id) 
        
    def format_time(self, t):
        return Sources.format_time(t)
        
    @grok.action('Save settings', name='save_settings')    
    def save_settings(self,**args):
        source = self.source
        url = self.request.get('url')
        description = self.request.get('description')
        quality = self.request.get('quality')
        default_status = self.request.get('default_status')
        source.set_value(url=url)
        if description is not None:
            source.set_value(description=description) 
        if quality is not None:
            source.set_quality(int(quality))
        if default_status is not None:
            source.default_status = default_status
    
        self.repository().save_source(source)
        self._redirect_with_msg('Settings saved')
            
    @grok.action('Update', name='update_source')    
    def update_source(self, **data):
        source = self.source
        self.repository().download_biographies(source, limit=int(self.context.LIMIT))
    
    @grok.action('Download biographies', name='download_biographies')    
    def download_biographies(self, **data):
        source = self.source
        total, skipped = self.repository().download_biographies(source=source)
        msg = "Biographies downloaded successfully (total=%s, skipped=%s)" % (total, skipped)
        self._redirect_with_msg(msg)

    @grok.action('Download Illustrations', name='download_illustrations')    
    def download_illustrations(self, **data): 
        source = self.source
        total, skipped = self.repository().download_illustrations(source, 
                                limit=int(self.context.LIMIT), overwrite=False)
        msg = "Illustrations downloaded successfully (total=%s, skipped=%s)" % (total, skipped)
        self._redirect_with_msg(msg)
        
    @grok.action('Delete biographies', name='delete_biographies')    
    def delete_biographies(self, **data):
        source = self.source
        self.repository().delete_biographies(source)  
        msg = "Biographies deleted successfully"
        self._redirect_with_msg(msg)
    
    @grok.action('Delete this source', name='delete_this_source')
    def delete_this_source(self, **data): 
        source_id = self.request.get('source_id')
        self.repository().delete_source(bioport_repository.source.Source(source_id, '', ''))
        parent = os.path.dirname(self.url())
        msg = "Removed source with id' %s'" % source_id
        url = os.path.join(parent, 'sources')
        return self._redirect_with_msg(msg, url)

    @grok.action('Refresh similarity table', name='refresh_similarity_cache')
    def refresh_similarity_cache(self, **data): 
        self.repository().db.fill_similarity_cache(refresh=True, 
                                                   source_id=self.source.id)
        self._redirect_with_msg("Similarity table refreshed")


class Sources(grok.View,RepositoryView):
    
    grok.require('bioport.Manage')

    def update(self, action=None, source_id=None, url=None, description=None):
        if action == 'source_delete':
            self.source_delete(source_id)
        elif action=='add_source':
            self.add_source(source_id, url, description)   
 
    def source_delete(self, source_id):
        repo = self.repository() 
        source = self.repository().get_source(source_id)
        repo.commit(source)
        repo.delete_source(source)
        
        msg = 'Deleted source with id %s ' % source_id
        print msg
        return msg
    
    def add_source(self, source_id, url, description=None):
        src = bioport_repository.source.Source(source_id, url, description)
        self.repository().add_source(src)
        
    @staticmethod
    def format_time(t):
        if t is None:
            return None
        t = float(t)
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(t))
        

class MostSimilar(grok.Form,RepositoryView, Batcher):

    grok.require('bioport.Edit')

    def update(self):
        self.start = int(self.request.get('start', 0))
        self.size = int(self.request.get('size', 20))
        self.similar_to = self.request.get('bioport_id') or \
                          self.request.get('similar_to', None) or \
                          getattr(self, 'similar_to', None)
        self.redirect_to = None
        self.most_similar_persons = self.repository().get_most_similar_persons(
           start=self.start, 
           size=self.size, 
           bioport_id=self.similar_to,
           source_id=self.request.get('source_id'),
           search_name=self.request.get('search_name'),
           status=self.request.get('status'),
           )
        
    def goback(self,  data = None):
        #do not repeat the form actions
        #XXX this is a hack - we should really only have POST request changing the data (in that case, whatever is left her ein the request is harmless)
        for k in data.keys():
            if k.startswith('form'):
                del data[k]
        for k,v in data.items():
            if v in [None, 'None' ]:
                del data[k]
        redirect_url = self.url(data=data)
        if self.redirect_to is not None:
            redirect_url = '?'.join([self.redirect_to, redirect_url.split('?')[1]])
            
        self.redirect(redirect_url) 
    
    def data(self, **args):
        data = {}
        for k in ['source_id', 'search_name', 'status', 'bioport_id']:
            if self.request.get(k): 
                data[k] = self.request[k]
        for k in args:
            data[k] = args[k]
        return data
        
    @grok.action('identificeer', name='identify')
    def identify(self):
        bioport_ids = self.request.get('bioport_ids')
        repo = self.repository()
        persons = [self.get_person(id) for id in bioport_ids]
        assert len(persons) == 2
        new_person = repo.identify(persons[0], persons[1])
        
        self.bioport_ids = bioport_ids        
        person1_href = '<a href="./persoon?bioport_id=%s">%s</a>' % (bioport_ids[0], bioport_ids[0])
        person2_href = '<a href="./persoon?bioport_id=%s">%s</a>' % (bioport_ids[1], bioport_ids[1])
        new_person_href = '<a href="./persoon?bioport_id=%s">%s</a>' % (new_person.id, new_person.name())
        
        # check for contradictions and construct a message for the browser
        contradictions = new_person.get_biography_contradictions()      
        warning_msg = ''
        # XXX - this should be translated in dutch
        if contradictions:      
            warning_msg = "Contradictory biograhies found for %s.<br />" % new_person_href
            warning_msg += "<ul>"
            for contr in contradictions:
                warning_msg += "<li>"
                warning_msg += contr.type + ": "
                warning_msg += '<span style="font-weight:normal">'
                warning_msg += ', '.join('%s (<i style="font-weight:normal">%s</i>)' %(x, y) for x, y in contr.values)
                warning_msg += "<br />"
                warning_msg += '</span>'
                warning_msg += "</li>"
            warning_msg += "</ul>"
            warning_msg += 'Click <a accesskey="b" href="./persoon?bioport_id=%s">here</a> to edit.' % new_person.id
            # XXX - something I'm really ashamed of; needed because otherwise
            # grok raises an encoding error when visualizing the page. 
            # When a character != ASCII is encountered is replaced by "?"
            # Hopefully someday I'll understand unicode and avoid this crap.
            warning_msg = warning_msg.encode("ascii", "replace")
            
        # XXX - this should be translated in dutch
        if persons[0].status != persons[1].status:
            get_status = self.repository().get_status_value
            status_1 = get_status(persons[0].status, '--')
            status_2 = get_status(persons[1].status, '--')
            status_new = get_status(new_person.status, '')
            warning_msg2 = '%s and %s had different statuses (<i>%s</i> and <i>%s</i>). ' \
                         % (person1_href, person2_href, status_1, status_2)
            warning_msg2 += "New person status is <i>%s</i> " % status_new
            warning_msg2 += '(<a accesskey="b" href="./persoon?bioport_id=%s">edit</a>).' % new_person.get_bioport_id()
            # XXX - something I'm really ashamed of; needed because otherwise
            # grok raises an encoding error when visualizing the page. 
            # When a character != ASCII is encountered is replaced by "?"
            # Hopefully someday I'll understand unicode and avoid this crap.
            warning_msg2 = warning_msg2.encode("ascii", "replace")
            if warning_msg:
                warning_msg = [warning_msg, warning_msg2]
            else:
                warning_msg = warning_msg2

        #redirect the user to where we were
        data = self.request.form
        data['msg'] = 'identified %s and %s. ' % (person1_href, person2_href)
        if warning_msg:
            data['warning_msg'] = warning_msg
        if data.has_key('bioport_ids'):
            del data['bioport_ids']
        self.goback(data = data)
        
    @grok.action('anti-identificeer', name='antiidentify')
    def antiidentify(self):
        bioport_ids = self.request.get('bioport_ids')
        repo = self.repository()
        persons = [bioport_repository.person.Person(id, repository=repo) for id in bioport_ids]
        p1, p2 = persons
        repo.antiidentify(p1, p2)

        self.bioport_ids = bioport_ids
        self.persons = persons
        msg = 'Anti-Identified <a href="../persoon?bioport_id=%s">%s</a> and <a href="../persoon?bioport_id=%s">%s</a>' % (
                bioport_ids[0], persons[0].get_bioport_id(), bioport_ids[1], persons[1].get_bioport_id())

        #redirect the user to where wer were
        data = self.request.form
        data['msg'] =  msg
#        request.form.set('msg', msg)
        self.goback(data = data)
   
    @grok.action('Moeilijk geval', name='deferidentification')
    def deferidentification(self):
        bioport_ids = self.request.get('bioport_ids') 
        repo = self.repository()
        persons = [bioport_repository.person.Person(id, repository=repo) for id in bioport_ids]
        p1, p2 = persons
        repo.defer_identification(p1, p2)
        
        self.bioport_ids = bioport_ids
        self.persons = persons
        msg = '<a href="../persoon?bioport_id=%s">%s</a> and <a href="../persoon?bioport_id=%s">%s</a> in de lijst met moeilijke gevallen gezet' % (
                     bioport_ids[0], persons[0].get_bioport_id(), bioport_ids[1], persons[1].get_bioport_id())
        
        #redirect the user to where wer were
        data = self.request.form
        data['msg'] =  msg
        self.goback( data = data)
             
    @grok.action('zoek', name="search_persons")
    def search_persons(self):
        self.persons = self.get_persons()
        
    @grok.action('similar persons', name='similar_persons')
    def get_similar_persons(self):
        self._get_similar_persons()
        
    def _get_similar_persons(self):
        if len(self.selected_persons) == 1:
            person = self.selected_persons[0]
            ls = self.repository().get_most_similar_persons(bioport_id=person.bioport_id)
            def other_person(i):
                score, p1, p2 = i
                if person.bioport_id == p1.bioport_id:
                    return p2
                else:
                    return p1
            ls = map(other_person, ls)
            
            batch = Batch(ls, start=self.start, size=self.size)
            self.persons = batch 
            self.persons.grand_total = len(ls)

            
class DBNL_Ids(MostSimilar, Batcher):

    def update(self):
        self.start = int(self.request.get('start', 0))
        self.size = int(self.request.get('size', 20))
        self.source = self.request.get('source')
        self.redirect_to = None
        fun = self.repository().db.get_persons_with_identical_dbnl_ids
        ls, grand_total = fun(start=self.start, size=self.size, source=self.source)
        self.get_persons_with_identical_dbnl_ids= ls
        self.grand_total = grand_total
   
   
class Persoon(app.Persoon, grok.EditForm, RepositoryView):
    """
    XXX
    This should really be an "Edit" view on a "Person" Model   
    But I am in an incredible hurry and have no time to learn :-(
    """
  
    grok.require('bioport.Edit')
    def update(self, **args):
        self.bioport_id = self.bioport_id or self.request.get('bioport_id')
        if not self.bioport_id:
            # XXX make a userfrienlider error
            assert 0, 'need bioport_id in the request'
        repository = self.repository() 
        self.person = self.get_person(bioport_id=self.bioport_id)  
        if not self.person:
            id = repository.redirects_to(self.bioport_id)
            if id != self.bioport_id:
                self.bioport_id = id
                self.person  = self.get_person(bioport_id=self.bioport_id)  
                
        assert self.person, 'NO PERSON FOUND WITH THIS ID %s' % self.bioport_id
        
        # XXX note that the following line creates a bioport biography if it 
        # did not exist yet (and saves it)
        # XXX this might be too much ofa  side effect for only viewing the page...
        self.bioport_biography =  repository.get_bioport_biography(self.person) 
        self.merged_biography  = self.person.get_merged_biography()

#        self.occupations = self.get_states(type='occupation')
#        self.occupations_with_id = [s for s in self.occupations if s.idno]
        self.categories = self.get_states(type='category')
        self.history_counter = 1
        http_referer = self.request.get('HTTP_REFERER', '')
        http_referer = http_referer.split('?')[0]
        http_referer = http_referer.split('/')
        if 'persoon' in http_referer or 'changename' in http_referer: 
            self.history_counter = self.session_get('history_counter', 1) + 1
        self.session_set('history_counter', self.history_counter)
        
    def get_contradictions(self):
        return self.person.get_biography_contradictions()       
        
    def session_get(self, k, default=None): 
        return ISession(self.request)['bioport'].get(k, default)
    
    def session_set(self, k, v):
        ISession(self.request)['bioport'][k] = v
        
    def title(self):
        n = self.person.naam()
        if n:
            return unicode(n)
        else:
            return '' 

    def url(self, object=None, name=None, data=None, hash=None):
        url = app.Persoon.url(self, object, name, data)
        if hash:
            if '?' in url: 
                url = url.replace('?', '#%s?' % hash)
            else:
                url = '%s#%s' % (url, hash)
        return url
        
    def sex_options(self):
        return [('1', 'man'), ('2', 'vrouw'), ('0', 'onbekend')]
    
    def to_ymd(self, s):
        return to_ymd(s)
    
    def get_bioport_namen(self):
        return self.bioport_biography.get_namen()
    
    def get_non_bioport_namen(self):
        namen = self.merged_biography.get_names()
        namen = [naam for naam in namen if naam.to_string() not in [n.to_string() for n in self.get_bioport_namen()]]
        return namen
    
    def is_identified(self):
        return len([b for b in self.person.get_biographies() if b.get_source().id != 'bioport']) > 1
    
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
        """return 'bioport' if the value is added by the editors of the 
        biographical portal return 'merged' if the value comes from the 
        merged_biography.
        """
        bioport_event = self.get_event(event_id, biography=self.bioport_biography)
        if bioport_event is None:
            bioport_event = self.get_state(event_id)
#        merged_event = self.get_event(self.merged_biography)
        if getattr(bioport_event, attr, None):
            return 'bioport'
        else:
            return 'merged'
            
    def validate_event(self, action, data):
        # XXX ???
        pass
    
    def _get_date_from_request(self, prefix):
        y = self.request.get('%s_y' % prefix)
        m = self.request.get('%s_m' % prefix)
        d = self.request.get('%s_d' % prefix)
        ymd = from_ymd(y, m, d)
        return ymd or ''
    
    def _set_event(self, type):
        when = self._get_date_from_request('%s' % type )
        notBefore = self._get_date_from_request('%s_notBefore' % type)
        notAfter = self._get_date_from_request('%s_notAfter' % type)
        date_text = self.request.get('%s_text' % type)
        place = self.request.get('%s_place' % type)
        self.bioport_biography.add_or_update_event(type, when=when, 
                                       date_text=date_text, notBefore=notBefore, 
                                       notAfter=notAfter, place=place)
        
    def _save_state(self, type):
        frm = self._get_date_from_request(prefix='state_%s_from' % type)
        to = self._get_date_from_request(prefix='state_%s_to' % type)
        text = self.request.get('state_%s_text' % type)
        place = self.request.get('state_%s_place' % type)
        self.bioport_biography.add_or_update_state(type, frm=frm, to=to, 
                                                   text=text, place=place)
        
    @grok.action('bewaar rubriek', name="save_category")
    def save_category(self):
        self._set_category()
        self.save_biography()
        self.msg = 'rubriek bewaard' 
    
    def _set_category(self):
        category_ids = self.request.get('category_id', [])
        if type(category_ids) != type([]):
            category_ids = [category_ids]
        category_ids = [id for id in category_ids if id]
        self.bioport_biography.set_category(category_ids)
           
        self.save_biography()
            
        new_category_ids = self.request.get('new_category_id')
        if type(new_category_ids) != type([]):
            new_category_ids = [new_category_ids]
#        print 'new categories', new_category_ids 
        new_category_ids = [s for s in new_category_ids if s ]
        for new_category_id in new_category_ids:
            name = self.repository().get_category(new_category_id).name 
            self.bioport_biography.add_state(type='category', idno=new_category_id, text=name)
            
        self.save_biography()
        
        self.categories = self.get_states(type='category')
        
    def save_biography(self):
        if not self.person.status:
            self.person.status = 2 #set status to bewerkt
#        self.repository().save_person(self.person)
        self.repository().save_biography(self.bioport_biography)
        #we need to reload merged_biography because changes are not automatically picked up
        self.person = self.repository().get_person(self.bioport_id)
        self.merged_biography  = self.person.get_merged_biography()

    @grok.action('bewaar geslacht', name="save_sex")
    def save_sex(self):
        self._set_sex()
        self.save_biography()
        self.msg = 'geslacht bewaard' 
        
    def _set_sex(self): 
        self.bioport_biography.set_value('geslacht', self.request.get('sex'))
        
    @grok.action('bewaar geboorte', name="save_event_birth", validator=validate_event)
    def save_event_birth(self):
        self._set_event('birth')
        self.save_biography()
        self.msg = 'geboortedatum bewaard'
           
    @grok.action('bewaar dood', name='save_event_death')
    def save_event_death(self):
        self._set_event('death')
        self.save_biography()
        self.msg = 'sterfdatum bewaard'
        
    @grok.action('bewaar doop', name='save_event_baptism')
    def save_event_baptism(self):
        self._set_event('baptism')
        self.save_biography()
        self.msg = 'doopdatum veranderd'
            
    @grok.action('bewaar begrafenis', name='save_event_funeral')
    def save_event_funeral(self):
        self._set_event('funeral')
        self.save_biography()
        self.msg = 'begraafdatum veranderd'
         
    @grok.action('verander naam', name='change_name')  
    def change_name(self):
        self.redirect(self.url(self.__parent__, 'changename', data={'bioport_id':self.bioport_id}))
    
    @grok.action('bewaar actief', name='save_state_floruit')
    def save_state_floruit(self): 
        self._save_state('floruit')
        self.save_biography()
        self.msg = 'actief veranderd'
        
    @grok.action('bewaar status', name='save_status')
    def save_status(self): 
        self._set_status()
        self.msg = 'status veranderd'
        self.save_biography()
    
    def _set_status(self):
        status = self.request.get('status')
        if status: 
            status = int(status)
        self.person.status = status 
        self.repository().save_person(self.person)
        
    @grok.action('bewaar opmerkingen', name='save_remarks')
    def save_remarks(self): 
        self._save_remarks()
        self.msg = 'opmerkingen bewaard'
    
    def _save_remarks(self): 
        self.person.remarks = self.request.get('remarks')
        self.repository().save_person(self.person)
       
    @grok.action('bewaar snippet', name='save_snippet')
    def save_snippet(self): 
        self._save_snippet()
        self.save_biography()
        self.msg = 'snippet bewaard'
    
    def _save_snippet(self): 
        for k in self.request.keys():
            if k.split('_')[0] == 'snippet':
                bio_id = k.split('_')[1]
                snippet = self.request.get(k)
                self.bioport_biography.set_snippet(bio_id, snippet)
                
    @grok.action('bewaar alle veranderingen', name='save_everything')  
    def save_everything(self):
        self._save_snippet()
        self._set_event('birth')
        self._set_event('death')
        self._set_event('funeral')
        self._set_event('baptism')
        self._set_sex()
#        self._set_occupation()
        self._set_category()
        self._save_state('floruit')
        self._set_status()
        self._save_remarks()
        self._save_names()
        self.save_biography()
        self.msg = 'alle ingevulde waarden bewaard'
        
    def _save_names(self):
        names = self.request.get('personname')
        if isinstance(names, (str, unicode)):
            names = [names]
        x = 0
        for fullname in names:
            nameobj = Naam(volledige_naam=fullname)
            if self.bioport_biography.get_namen():
                self.bioport_biography._replace_name(nameobj, x)
            else:
                self.bioport_biography._add_a_name(nameobj)
            x += 1

    @grok.action('voeg toe', name='add_name') 
    def add_name(self):
        name_new =  self.request.get('name_new')
        if name_new:
            name = Naam(
    #            repositie = self.request.get('prepositie'),
    #            voornaam = self.request.get('voornaam'),
    #            intrapositie = self.request.get('intrapositie'),
    #            geslachtsnaam = self.request.get('geslachtsnaam'),
    #            postpositie = self.request.get('postpositie'),
                volledige_naam = name_new,
            )
        
            #add the namen van de "merged biographies" als we dat nog niet hebben gedaan
            if not self.bioport_biography.get_namen():
                for naam in self.merged_biography.get_names():
                    self.bioport_biography._add_a_name(naam)
            
            self.bioport_biography._add_a_name(name)
            self.save_biography()
            self.msg = 'added a name'
        else:
            self.msg = 'geen naam ingevuld'

        id = self.request.get("bioport_id")
        url = self.url(data={"bioport_id":id, "msg":self.msg})
        self.redirect(url)

    @grok.action('remove name', name='remove_name') 
    def remove_name(self):
        #add the namen van de "merged biographies" als we dat nog niet hebben gedaan
        if not self.bioport_biography.get_namen():
            for naam in self.merged_biography.get_names():
                self.bioport_biography._add_a_name(naam)
        idx = self.request.get('naam_idx')
        idx = int(idx)
        if len(self.bioport_biography.get_namen()) == 1:
            self.msg = 'naam kon niet worden verwijderd: er is tenminste 1 naam nodig'
        else: 
            self.bioport_biography.remove_name(idx)
            self.save_biography()
            self.msg = 'naam verwijderd'

        id = self.request.get("bioport_id")
        url = self.url(data={"bioport_id":id, "msg":self.msg})
        self.redirect(url)

    @grok.action('download_illustration')
    def download_illustration(self, **data): 
        self.msg = ''
        for illustration in self.merged_biography.get_illustrations():
            illustration.download()
            self.msg += 'downloaded %s\n' % illustration
        
    @grok.action('recompute similarities for this person', name="compute_similarity")
    def compute_similarity(self, **data):
        self.msg = 'computed similarity for this person'
        id = self.person.bioport_id
        self.repository().db.fill_similarity_cache(person=self.person, refresh=True)
        self.person = self.repository().get_person(bioport_id = id)
        
#    @grok.action('bewaar beroep', name="save_occupation")
#    def save_occupation(self):
#        self._set_occupation()
#        self.save_biography()
#        self.msg = 'beroep bewaard' 
    
#    def _set_occupation(self):
#        occupation_ids = self.request.get('occupation_id', [])
#        to_delete = []
#        if type(occupation_ids) != type([]):
#            occupation_ids = [occupation_ids]
#        for idx in range(len(occupation_ids)):
#            occupation_id = occupation_ids[idx] 
#            if occupation_id:
#                name = self.repository().get_occupation(occupation_id).name  
#                self.bioport_biography.add_or_update_state(type='occupation', 
#                                    idno=occupation_id, text=name, idx=idx)
#            else:
#                to_delete.append(idx) 
#                
#        to_delete.reverse()
#        for idx in to_delete:
#            self.bioport_biography.remove_state(type='occupation', idx=idx)
#            
#        new_occupation_ids = self.request.get('new_occupation_id')
#        if type(new_occupation_ids) != type([]):
#            new_occupation_ids = [new_occupation_ids]
#        new_occupation_ids = [s for s in new_occupation_ids if s ]
#        for new_occupation_id in new_occupation_ids:
#            name = self.repository().get_occupation(new_occupation_id).name 
#            self.bioport_biography.add_state(type='occupation', idno=new_occupation_id, text=name)


class Debuginfo(Persoon):
    pass
        

class PersoonIdentify(MostSimilar, Persons, Persoon):
    
    grok.require('bioport.Edit')
    
    def update(self, **args):
        self.bioport_ids = self.request.get('bioport_ids', [])
        if type(self.bioport_ids) != type([]):
            self.bioport_ids = [self.bioport_ids]
            
        if self.request.get('new_bioport_id'):
            self.bioport_ids.append(self.request.get('new_bioport_id'))
            
        self.selected_persons = [self.repository().get_person(bioport_id) for bioport_id in self.bioport_ids]
        
        MostSimilar.update(self, **args)
        self.redirect_to = None
        if len(self.bioport_ids) == 1 and \
        not self.request.get('search_name') and \
        not self.request.get('bioport_id'):
            return self._get_similar_persons()
        
        persons = self.persons = self.get_persons()
        #Persoon.update(self, **args        try:
        try:
            batch = Batch(persons,  start=self.start, size=self.size)
        except IndexError:
            batch = Batch(persons,size= self.size)
            
        batch.grand_total = len(persons)
        self.persons = self.batch = batch
        return batch


class IdentifyMoreInfo(MostSimilar, Persons, Persoon,RepositoryView):

    grok.require('bioport.Edit')
    
    def update(self, bioport_ids=[]):
        repo = self.repository()
        persons = [bioport_repository.person.Person(id, repository=repo) for id in bioport_ids]
        self.bioport_ids = bioport_ids
        self.persons = persons
        self.start = int(self.request.get('start', 0))
        self.size = None
        self.redirect_to = None
        
    def goback(self,  data = {}):
        #XXX this is a hack - we should really only have POST request changing the data (in that case, whatever is left her ein the request is harmless)
        for k in data.keys():
            if k.startswith('form'):
                del data[k]
        most_similar_persons = self.repository().get_most_similar_persons(start=self.start, size=5)
        score, p1, p2= most_similar_persons[0]
        data.update({'bioport_ids':[p1.bioport_id, p2.bioport_id], 'start':self.start})
        redirect_url = self.url(data=data)
        self.redirect(redirect_url) 
       

class ChangeName(Persoon, grok.EditForm,RepositoryView): 

    grok.require('bioport.Edit')
    
    def update(self, **args):
        Persoon.update(self, **args)
        self.bioport_id = self.request.get('bioport_id')         
        if not self.bioport_id:
            #XXX make a userfrienlider error
            assert 0, 'need bioport_id in the request'
        self.person  = self.get_person(bioport_id=self.bioport_id)  
        self.bioport_biography  = self.repository().get_bioport_biography(self.person)
        
        if not self.bioport_biography.get_namen():
            for naam in self.person.get_merged_biography().get_names():
                self.bioport_biography._add_a_name(naam)
            self.save_biography()
        
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
        
        try:
            self.naam = name = Naam(volledige_naam = volledige_naam, **args)
            repository = self.repository()
            bio._replace_name(name, self.idx)
            repository.save_biography(bio)
            self.msg = 'De veranderingen zijn bewaard'
        except Exception, error:
            # XXX - evil!
            self.msg = unicode(error)
            self.msg += ' Uw veranderingen zijn niet bewaard'
       
 
class AntiIdentified(grok.View, RepositoryView, Batcher):

    grok.require('bioport.Edit')

    def update(self):
        Batcher.update(self)

    def get_antiidentified(self):
        ls = self.repository().get_antiidentified()
        batch = Batch(ls, start=self.start, size=self.size)
        batch.grand_total = len(batch.sequence) 
        return batch 
        

class Identified(grok.View, RepositoryView, Batcher):

    grok.require('bioport.Edit')

    def update(self):
        Batcher.update(self)
    
    def get_identified(self):
        qry = {}
        for k in [
            'start',
            'size',
            'order_by', 
            'search_term',
            'source_id',
            'bioport_id', 
            'beginletter',
            'status',
             ]:
            if k in self.request.keys():
                qry[k] = self.request[k]
        
        ls = self.repository().get_identified(**qry)
        #**qry)
        self.qry = qry
        batch = Batch(ls, start=self.start, size=self.size)
        batch.grand_total = len(ls)
        return batch  


class Deferred(MostSimilar ):  

    grok.require('bioport.Edit')
    
    def update(self, **args):
        self.redirect_to = None
        Batcher.update(self)
        
    def get_deferred(self):
        ls =  self.repository().get_deferred()
        batch = Batch(ls, start=self.start, size=self.size)
        batch.grand_total = len(ls)
        return batch  
    

class Locations(grok.View,RepositoryView):     

    grok.require('bioport.Edit')

    def update(self, **kw):
        self.start = int(self.request.get('start', 0))
        self.size = int(self.request.get('size', 30))
        self.startswith = self.request.get('startswith', None)
        self.name = self.request.get('name', None)
        
    def get_locations(self):
        ls = self.repository().db.get_locations(startswith=self.startswith, name=self.name)
        
        batch = Batch(ls, start=self.start, size=self.size)
        batch.grand_total = len(ls)
        return batch


class EditHomePage(grok.EditForm,RepositoryView):
    grok.require('bioport.Edit')
    grok.template('edit_home_page')
    grok.context(Admin)
    form_fields = grok.Fields(IHomePageSettings)
    
    @grok.action(u"Save homepage", name="edit_homepage")
    def edit_homepage(self, **data):
        self.applyData(self.context, **data)


class ChangeLocation(Locations):    

    grok.require('bioport.Edit')

    def update(self, **kw):
        Locations.update(self)
        self.location = self.request.get('place_id')


class Identify(grok.View):
    grok.require('bioport.Edit')


class UnIdentify(grok.View, RepositoryView):

    grok.require('bioport.Edit')

    def update(self):
        bioport_id = self.bioport_id = self.request.get('bioport_id')
        person = self.repository().get_person(bioport_id)
        if person:
            self.persons = self.repository().unidentify(person)
        else:
            self.persons = []
    

class Log(grok.View,RepositoryView):

    grok.require('bioport.Edit')

    def get_log_messages(self):
        return self.repository().get_log_messages()
  
    
class Uitleg(grok.View): 
    pass
   

class Uitleg_Zoek(grok.View):        
    pass   

