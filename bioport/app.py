import datetime
import grok
import os
import random
import zope.interface
from chameleon.zpt.template import PageTemplateFile
from common import (format_date, format_dates, format_number, 
                    html2unicode, maanden, months)
from interfaces import IBioport
from names.common import to_ymd
from plone.memoize import ram
from plone.memoize.instance import memoize
from time import time
from z3c.batching.batch import Batch
from bioport import BioportMessageFactory as _
from zope.i18n import translate
try:
    from zope.i18n.interfaces import IUserPreferredLanguages  # after python 2.6 upgrade
except ImportError:
    from zope.app.publisher.browser import IUserPreferredLanguages  # before python 2.6 upgrade
from urllib import urlencode
import types
from fuzzy_search import get_search_query
from fuzzy_search import en_to_nl_for_field
from fuzzy_search import make_description
import simplejson
from zope.publisher.interfaces import NotFound, INotFound



class RepositoryView:
    def repository(self):
        principal = self.request.principal
        user = principal and principal.id
        return self.context.repository(user=user)
    
    def get_sources(self):
        return self.repository().get_sources()
    
    def get_person(self,bioport_id):
        return self.repository().get_person(bioport_id)
    
    def get_status_value(self, k, default=None):
        return self.repository().get_status_value(k, default)
    
    def get_status_values(self):
        return self.repository().get_status_values()
    
    @ram.cache(lambda *args: time() // (60 * 60))
    def count_persons(self):
        #XXX cache this
        i = self.repository().db.count_persons()
        i = format_number(i)
        return i
    
    @ram.cache(lambda *args: time() // (60 * 60))
    def count_biographies(self):
        try:
            return self.context._count_biographies
        except AttributeError:
            i = self.repository().db.count_biographies()
            #XXX turned of caching, need to find some "update once a day" solution
            i = format_number(i)
            return i
            self.context._count_biographies = format_number(i)
        return self.context._count_biographies
       
    def menu_items(self):
        items = [
                (self.application_url(), _('home')),
                (self.application_url('zoek'), _('zoeken')),
                (self.application_url('personen') + '?beginletter=a',
                 _('bladeren')),
                (self.application_url('about'), _('project')),
        ]

        adapter = IUserPreferredLanguages(self.request)
        lang = adapter.getPreferredLanguages()[0]
        if lang != 'en':
            items += [(self.application_url('blog'), _('blog')),
                    (self.application_url('agenda'), _('agenda')),]
        items += [
#                (self.url('colofon'), 'colofon'),
                (self.application_url('links'), _('links')),
                (self.application_url('faq'), _('vragen')),
                (self.application_url('contact'), _('contact')),
        ]    
        return items
    def today(self):
        today = datetime.date.today()
        adapter = IUserPreferredLanguages(self.request)
        lang = adapter.getPreferredLanguages()[0]
        if lang == 'en':
            month = months[today.month-1]
            return '%s %s' % (month, today.day) 
        else:
            month = maanden[today.month-1]
            return '%s %s' % (today.day, month)
    
class Batcher: 
    def update(self, **kw):
        self.start = int(self.request.get('start', 0))
        self.size = int(self.request.get('size', 30))
        
    def batch_url(self, start=None, size=None):
        
        #next two lines replaces data = self.request.form
        #which magickally resolves a unicode error
        data = {}
        data.update(self.request.form)
        if start != None:
            data['start'] = start
        if size != None:
            data['size'] = size
        return self.url(data= data)    
 
class Bioport(grok.Application, grok.Container):
    zope.interface.implements(IBioport)
              
    SVN_REPOSITORY = None
    SVN_REPOSITORY_LOCAL_COPY = None
    DB_CONNECTION = None
    debug=False

    def __init__(self, db_connection=None):
        super(Bioport,self).__init__() #cargoculting from ingforms 
        from admin import Admin
        self['admin'] = Admin()
        self['admin'].DB_CONNECTION = db_connection
        from biodes import BioDes
        self['biodes'] = BioDes()
    
    def format_dates(self, s1, s2, **args):
        return  format_dates(s1, s2, **args)

    def repository(self, user):
        return self['admin'].repository(user=user)
    
    def format_number(self, s):
        return format_number(s)


class BioportNotFound(grok.View, RepositoryView):

    grok.context(INotFound)
    grok.name("index.html")
    static = None

    def __init__(self, notfound_exception, request):
        " Put the context back to the last found element "
        self.notfound_exception = notfound_exception
        return super(BioportNotFound, self).__init__(notfound_exception.ob, request)
    def update(self):
        self.request.response.setStatus(404)

class Index(grok.View, RepositoryView):

    def get_homepage_html(self):
        adapter = IUserPreferredLanguages(self.request)
        language = adapter.getPreferredLanguages()[0]
        if language == 'en':
            return self.context['admin'].english_home_html
        else:
            return self.context['admin'].dutch_home_html
            


class Popup_Template(grok.View):
    
    #make the .             template avaible for everything
    grok.context(zope.interface.Interface)
    
class Main_Template(grok.View, RepositoryView):
    #make the main template avaible for everything
    grok.context(zope.interface.Interface)


class Admin_Template(grok.View):
    #make the main template avaible for everything
    grok.context(zope.interface.Interface)   

class Language_Chooser(grok.View):
    "A UI control to switch between English and Dutch"
    grok.context(zope.interface.Interface)
    
    def get_current_language(self):
        adapter = IUserPreferredLanguages(self.request)
        return adapter.getPreferredLanguages()[0]

    def get_other_language(self):
        current_language = self.get_current_language()
        return {'en': 'nl', 'nl': 'en'}[current_language]

    def other_language_name(self):
        lang = self.get_other_language()
        return {'en': 'english',
                'nl': 'nederlands'}[lang]

    def other_language_url(self):
        lang = self.get_other_language()
        if lang == 'nl': # convert en --> nl
            new_application_url = self.application_url()[:-3]
        else: # convert nl --> en
            new_application_url = self.application_url() + '/en'
        old_application_url = self.application_url()
        current_url = self.request.getURL()
        new_url = new_application_url + current_url[len(old_application_url):]
        if self.request.form:
            # XXX - converting the string to UTF-8 seems to be a working fix for when
            # a name with non-ascii characters is submitted through the search form.
            params = self.request.form.copy()
            for x, y in params.iteritems():
                if type(y) in [types.ListType]:
                    params[x] = [z.encode("utf-8") for z in y]
                else:
                    params[x] = y.encode("utf-8")
            encoded_params = urlencode(params)
            # /XXX

            new_url += '?' + encoded_params
        if new_url.endswith("@@index"):
            new_url = new_url[:-len('@@index')]    
        return new_url


class SiteMacros(grok.View):
    grok.context(zope.interface.Interface)   
    
class Personen(grok.View,RepositoryView, Batcher):
    
    def update(self):
        Batcher.update(self)
        
    @memoize
    def get_persons(self, **args):
        """get Persons - with restrictions given by request"""
        self.qry = qry = args
        #request.form has unicode keys - make strings
        for k in [
            'bioport_id', 
            'beginletter',
            'category',
            'geboortejaar_min',
            'geboortejaar_max',
            'geboorteplaats',
            'geslacht',
#        has_illustrations=None, #boolean: does this person have illustrations?
#        is_identified=None,
            'order_by', 
            'search_term',
            'search_name',
            'search_soundex',
            'size',
            'source_id',
            'source_id2',
            'start',
            'status',
            'sterfjaar_min', 
            'sterfjaar_max',
            'sterfplaats',
            'has_contradictions',
#        start=None,
#        size=None,
             ]:
            if k in self.request.keys():
                qry[k] = self.request[k]
                
        repository = self.repository()
        current_language = IUserPreferredLanguages(self.request).getPreferredLanguages()[0]
        try:
            geboorte_fuzzy_text = self.request.form.get('geboorte_fuzzy_text', None)
            if geboorte_fuzzy_text:
                geborte_query = get_search_query(geboorte_fuzzy_text, current_language)
                qry.update(en_to_nl_for_field(geborte_query, 'geboorte'))
            sterf_fuzzy_text = self.request.form.get('sterf_fuzzy_text', None)
            if sterf_fuzzy_text:
                sterf_query = get_search_query(sterf_fuzzy_text, current_language)
                qry.update(en_to_nl_for_field(sterf_query, 'sterf'))
            levend_fuzzy_text = self.request.form.get('levend_fuzzy_text', None)
            if levend_fuzzy_text:
                levend_query = get_search_query(levend_fuzzy_text, current_language)
                qry.update(en_to_nl_for_field(levend_query, 'levend'))
            has_contradictions = self.request.form.get('has_contradictions', None)
            if has_contradictions == 'on':
                qry['has_contradictions'] = True
            else:
                qry['has_contradictions'] = False
        except ValueError:
            url = self.url('zoek') # XXX change me to 'zoek' when done
            dict_of_strings = dict([(k,v.encode('utf8')) 
                                    for k, v in self.request.form.items()])
            url += '?' + urlencode(dict_of_strings)
            self.request.response.redirect(url)
        persons = repository.get_persons_sequence(**qry)
        try:
            batch = Batch(persons,  start=self.start, size=self.size)
        except IndexError:
            batch = Batch(persons,size= self.size)
        batch.grand_total = len(persons)
        self.batch = batch
        return batch

        
    def search_description(self):
        """return a description for the user of the search parameters in the request"""
#        beginletter=None,
#        category=None,
#        geboortejaar_min=None,
#        geboortejaar_max=None,
#        geboorteplaats = None,
#        geslacht=None,
#        has_illustrations=None, #boolean: does this person have illustrations?
#        is_identified=None,
#        match_term=None, #use for myqsl 'matching' (With stopwords and stuff)
#        order_by='sort_key', 
#        place=None,
#        search_term=None,  #
#        search_name=None, #use for mysql REGEXP matching
#        search_soundex=None,
#        source_id=None,
#        sterfjaar_min=None,
#        sterfjaar_max=None,
#        sterfplaats = None,
#        start=None,
#        size=None,
#        status=None,
#        where_clause=None,
        current_language = IUserPreferredLanguages(self.request).getPreferredLanguages()[0]
        _between = translate(_(u'between'),target_language=current_language)
        _and = translate(_(u'and'), target_language=current_language)
        _after = translate(_(u'after'),target_language=current_language)
        _before = translate(_(u'before'),target_language=current_language)
        repository = self.repository()
        result= ''
        request = self.request
        born_description = get_born_description(self.request)
        died_description = get_died_description(self.request)
        alive_description = get_alive_description(self.request)

        geboorteplaats = request.get('geboorteplaats')
        if born_description or geboorteplaats:
            result += ' ' + translate(_(u'born'),
                                      target_language=current_language)
            if born_description:
                result += ' ' + born_description
            if geboorteplaats:
                result += ' in  <em>%s</em>' % geboorteplaats

        sterfplaats = request.get('sterfplaats')
        if died_description or sterfplaats:
            result += ' ' + translate(_(u'died'),target_language=current_language)
            if died_description:
                result += ' ' + died_description
            if sterfplaats:
                result += ' in <em>%s</em>' % sterfplaats
                
        if alive_description:
            result += ' ' + translate(_(u'alive'),target_language=current_language)
            result += ' ' + alive_description

        source_id = request.get('source_id')
        if source_id:
            source_name = repository.get_source(source_id).description
            result += ' %s <em>%s</em>' % (translate(_(u'from'),
                                                      target_language=current_language),
             source_name)
            
        if request.get('search_name'):
            whose_name_is_like = translate(_(u'whose_name_is_like'),target_language=current_language)
            result += ' ' + whose_name_is_like
            result += ' <em>%s</em>' % request.get('search_name')
            
        if request.get('search_term'):
            result += u' met het woord <em>%s</em> in de tekst' % request.get('search_term')
            
#        if request.get('search_soundex'):
#            result += u' wier naam lijkt op <em>%s</em>' % request.get('search_soundex')
        
        if request.get('category'):
            category_name_untranslated = repository.db.get_category(request.get('category')).name
            category_name = translate(_(category_name_untranslated),
                                      target_language=current_language)
            result += ' %s <em>%s</em>' % (
                translate(_("of_the_category"), target_language=current_language), #uit de rubriek
                             category_name)
        
        #NB: in the template, we show the alphabet only if the search description is emtpy
        #uncommenting the following lines messes up this logic    
#        if request.get('beginletter'):
#            result += ' met een achternaam beginnend met een <em>%s</em>' % request.get('beginletter')
        geslacht_id = request.get('geslacht', None)
        gender_name = {'1': '<em>' + translate(_("men"),
                                      target_language=current_language) + '</em>',
                       '2': '<em>' + translate(_("women"),
                                      target_language=current_language) + '</em>',}
        _persons = translate(_("persons"), target_language=current_language)
        geslacht = gender_name.get(geslacht_id, _persons)
            
        if result:
            result = '%s %s %s.' % (
                    translate(_("you_searched_for"), target_language=current_language),
                    geslacht, result)
        result = unicode(result)
        return result
    def batch_navigation(self, batch):
        return '<a href="%s">%s</a>' % (self.batch_url(start=batch.start), batch[0].naam().geslachtsnaam())

    def navigation_box_data(self):
        """  This function returns a list of 3-tuples representing pages
             of paged results. They have the form
             (url of a page, first name on that page, last name on that page)
        """ 
        ls = []
        for batch in self.batch.batches:
            url = self.batch_url(start=batch.start)
            n1 = batch.firstElement.geslachtsnaam() or batch.firstElement.naam()
            n2 = batch.lastElement.geslachtsnaam() or batch.lastElement.naam()
            ls.append((url, n1, n2))
        return ls

    def get_navigation_box(self):
        "This function returns the html for the navigation box"
        template_filename = os.path.join(
                      os.path.dirname(__file__),
                      'app_templates',
                      'navigation_block.cpt')
        template = PageTemplateFile(template_filename)
        
        return template(view=self, request=self.request)
    

class BioPortIdTraverser(object):
    """ Mixin class that makes a view traversable with an
        integer id.
    """
    bioport_id = None # will be available after traversal
    def publishTraverse(self, request, name):
       # We won't traverse more than once
       # allowing view_url/some_id but not view_url/something/some_id
       if len(request.getTraversalStack()) > 0 or not name.isdigit():
           raise NotFound(self.context, name)
       self.bioport_id = name
       return self


class PersoonXml(BioPortIdTraverser, grok.View,RepositoryView):
    def render(self):
        redirects_to = self.repository().redirects_to(self.bioport_id)
        if redirects_to:
            self.bioport_id = redirects_to
        person  = self.repository().get_person(bioport_id=self.bioport_id)
        self.request.response.setHeader('Content-Type','text/xml; charset=utf-8')
        return person.get_merged_biography().to_string()


class Persoon(BioPortIdTraverser, grok.View, RepositoryView):

    def publishTraverse(self, request, name):
       if name == 'xml':
           return PersoonXml(self.context, self.request)
       return super(Persoon, self).publishTraverse(request, name)

    def update(self, **args):
        self.bioport_id = self.bioport_id or self.request.get('bioport_id')
        redirects_to = self.repository().redirects_to(self.bioport_id)
        if redirects_to:
            self.bioport_id = redirects_to
        if not self.bioport_id:
            self.bioport_id = random.choice(self.repository().get_bioport_ids())
            self.redirect(self.url(self) + '/'+ self.bioport_id)
        self.person  = self.repository().get_person(bioport_id=self.bioport_id) 
        self.biography  = self.merged_biography = self.person.get_merged_biography()
        self.bioport_biography =  self.repository().get_bioport_biography(self.person) 
        
    def get_event(self, type, biography=None):
        if not biography:
            biography = self.merged_biography
        
        event_el = biography.get_event(type)
        if event_el is not None:

            # we construct a convenient object
            class EventWrapper:
                def __init__(self, el, _between, _and, _after, _before):
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
                    start = self.notBefore_formatted
                    stop = self.notAfter_formatted

                    if start and stop:
                        self.when_formatted = "%(_between)s %(start)s %(_and)s %(stop)s" % locals()
                    elif start:
                        self.when_formatted = "%(_after)s %(start)s" % locals()
                    elif stop:
                        self.when_formatted = "%(_before)s %(stop)s" % locals()
                    # ...else, stick with single formatted date

                def __str__(self):
                    string = []
                    for attr in dir(self):
                        if attr.startswith('_'):
                            continue
                        value = getattr(self, attr)
                        string.append("%s=%s" %(attr, value))
                    return '; '.join(string)

            current_lang = IUserPreferredLanguages(self.request).getPreferredLanguages()[0]
            _between = translate(_(u'between'), target_language=current_lang)
            _and = translate(_(u'and'), target_language=current_lang)
            _after = translate(_(u'after'), target_language=current_lang)
            _before = translate(_(u'before'), target_language=current_lang)
            return EventWrapper(event_el, _between, _and, _after, _before)
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
    
    def get_biographies(self):
        bios = self.person.get_biographies()
        bios = [bio for bio in bios if bio.source_id != 'bioport' and bio.source_id != 'portraits']
        return bios
    
    def get_portraits(self):
        bios = self.person.get_biographies()
        bios = [bio for bio in bios if bio.source_id == 'portraits']
        return bios
        
    def maanden(self):
        return maanden
        
    def is_admin(self):
        from zope.security import checkPermission
        return checkPermission('bioport.Manage', self.context)
        

#class Zoek(grok.View, RepositoryView):
#    pass

def get_born_description(request):
    """ Inspect the request and build a natural language description 
        of the searched born date"""
    current_language = IUserPreferredLanguages(request).getPreferredLanguages()[0]
    geboorte_fuzzy_text = request.form.get('geboorte_fuzzy_text')
    if geboorte_fuzzy_text:
        try:
            qry = get_search_query(geboorte_fuzzy_text)
        except ValueError, e:
            return _("Unable to parse birth date. Please rephrase it")
        return make_description(qry, lang=current_language)

def get_died_description(request):
    """ Inspect the request and build a natural language description 
        of the searched death date"""
    current_language = IUserPreferredLanguages(request).getPreferredLanguages()[0]
    sterf_fuzzy_text = request.form.get('sterf_fuzzy_text', None)
    if sterf_fuzzy_text:
        try:
            qry = get_search_query(sterf_fuzzy_text)
        except ValueError, e:
            return _("Unable to parse death date. Please rephrase it.")
        return make_description(qry, lang=current_language)

def get_alive_description(request):
    """ Inspect the request and build a natural language description 
        of the searched 'alive' date"""
    current_language = IUserPreferredLanguages(request).getPreferredLanguages()[0]
    levend_fuzzy_text = request.form.get('levend_fuzzy_text', None)
    if levend_fuzzy_text:
        try:
            qry = get_search_query(levend_fuzzy_text)
        except ValueError, e:
            return _("Unable to parse alive date. Please rephrase it.")
        return make_description(qry, lang=current_language)


class Zoek(grok.View, RepositoryView):
    def get_born_description(self):
        return get_born_description(self.request)
    def get_died_description(self):
        return get_died_description(self.request)
    def get_alive_description(self):
        return get_alive_description(self.request)


class Zoek_places(grok.View, RepositoryView):
    """The JSON used in the search form of the main site.
    It return a JSON like this:
    
    {'sterf' : ['a','b','c',...],
     'geboorte' : ['a','b','c',...]
    }
    """

    def render(self):
        repo = self.repository()
        sterf_places = repo.get_places('sterf')
        geboorte_places = repo.get_places('geboorte')
        result = {'sterf': sterf_places, 'geboorte': geboorte_places}
        self.request.response.setHeader('Content-Type', 'text/x-json; charset=UTF-8')
        oneday = datetime.datetime.now() + datetime.timedelta(days=1)
        expires = oneday.strftime('%a, %d %b %Y %H:%M:%S GMT')
        self.request.response.setHeader('Expires', expires)
        self.request.response.setHeader('Cache-Control', 'max-age=86400')
        return simplejson.dumps(result)
        

class Zoek_places_admin(grok.View, RepositoryView):
    """The JSON used in various search forms of the admin inrface.
    Return a JSON comprehending *all* places as a JSON list which 
    looks like this:
    
    ['a','b','c',...]
    """

    def render(self):
        self.request.response.setHeader('Content-Type', 'text/x-json; charset=UTF-8')
        repo = self.repository()
        sterf_places = repo.get_places('sterf')
        geboorte_places = repo.get_places('geboorte')
        result = set(sterf_places + geboorte_places)
        result = list(result) 
        result.sort()
        return simplejson.dumps(result)



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
    @ram.cache(lambda *args: time() // (60 * 60 * 24))
    def get_persons(self):
        """get 3 persons whose birthdate is today"""
        #get the month and day of today
        today = datetime.date.today().strftime('-%m-%d')
        #query the database for persons born on this date
        persons = self.repository().get_persons(where_clause='geboortedatum like "____%s"' % today, has_illustrations=True, hide_foreigners=True)
        if len(persons) < 3:
            #if we have less then 3 people, we cheat a bit and take someone who died today
            persons += self.repository().get_persons(where_clause='sterfdatum like "____%s"' % today, has_illustrations=True, hide_foreigners=True)
             
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
    

    
class About(grok.View, RepositoryView):
    pass

class Agenda(grok.View, RepositoryView):
    pass

class English(grok.View, RepositoryView):
    pass

class FAQ(grok.View, RepositoryView):
    pass

class Images_XML(grok.View, RepositoryView):
    grok.name('images.xml')
    def render(self):
        self.request.response.setHeader('Content-Type', 'text/xml')
        return self.render_response()

    @ram.cache(lambda *args: time() // (60 * 60) + random.randint(1,10))
    def render_response(self):
        
        persons = self.repository().get_persons(has_illustrations=True, order_by='random', size=20)
        
        result = """<?xml version="1.0"?><root>"""
        for person in persons:
            illustrations = person.get_merged_biography().get_illustrations()
            if not illustrations:
                #if the database is up to date, it should not happen that we find persons without an illustration
                #as a result of a call to get_persons(has_illustrations=True)
                #but it can happen ...
                continue
            illustration = illustrations[0]
            if not illustration.has_image():
                continue
            result += '<image src="%s" title="%s" url="%s/%s" />\n' % (
                           illustration.image_home_url, 
#                           urllib.quote(unicode( person.name()).encode('utf8')), 
                           html2unicode(unicode(person.name())),
                           self.url('persoon'),
                           person.bioport_id,
                           )
        result += '</root>'
        return result

class BelowBios(grok.ViewletManager):
    grok.name('belowbios')
    grok.context(Bioport)
    
class Collecties(grok.View, RepositoryView):
    pass

class Instellingen(grok.View, RepositoryView):
    pass

class Stichting(grok.View, RepositoryView):
    pass

class RedactieRaad(grok.View, RepositoryView):
    pass

class Links(grok.View,RepositoryView):
    pass
class Blog(grok.View,RepositoryView):
    pass

class SiteMaps(grok.View,RepositoryView):
    MAX_PER_FILE = 2000
    def render(self):
        self.request.response.setHeader('Content-Type','text/xml; charset=utf-8')
        if hasattr(self, 'start_index'):
           return self.render_sitemap(self.start_index)
        all_records = self.repository().get_persons_sequence()
        num_records = len(all_records)
        out = '<?xml version="1.0" encoding="UTF-8"?>\n'
        out += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for start in xrange(0, num_records, self.MAX_PER_FILE):
            sitemap_file_name = "sitemap-%i" % start
            sitemap_url = self.application_url() + '/sitemaps/' + sitemap_file_name
            out += '  <sitemap>\n'
            out += '    <loc>%s</loc>\n' % sitemap_url
            out += '  </sitemap>\n'
        out += '</sitemapindex>\n'
        return out
    def render_sitemap(self, start_index):
        all_records = self.repository().get_persons_sequence()
        application_url = self.application_url()
        out = '<?xml version="1.0" encoding="UTF-8"?>\n'
        out += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for person in all_records[start_index:start_index + self.MAX_PER_FILE]:
            person_url = application_url + '/persoon/' + person.id
            out += '  <url>\n'
            out += '    <loc>%s</loc>\n' % person_url
            out += '  </url>\n'
        out += '</urlset>\n'
        return out

    def publishTraverse(self, request, name):
        if name[:8] == 'sitemap-':
            self.start_index = int(name[8:])
            return self


##
# Removes HTML or XML character references and entities from a text string.
# Borrowed from http://effbot.org/zone/re-sub.htm#unescape-html
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

import re, htmlentitydefs
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

class PersonenXML(grok.View,RepositoryView):
    def render(self):
        all_records = self.repository().get_persons_sequence()
        session = self.repository().db.get_session()
#        results = session.execute("SELECT bioport_id, timestamp, naam FROM person")
        out = ['<?xml version="1.0" encoding="UTF-8"?>\n']
        out.append('<list>\n')
#        for person_id, timestamp, name in results: # XXX potentially inefficient
        for person in self.repository().get_persons(): #[:10]:
            person_id = person.record.bioport_id
            timestamp = person.record.timestamp
            name = person.record.naam
            if name:
                if not type(name) in (unicode,):
                    name = name.decode('latin1')
                
                if '&' in name: 
                    name = name.replace('&', '&amp;')
#                    name = unescape(name).encode('utf8')
            url = self.url('persoon') + '/xml/' + person_id
            changed = timestamp.isoformat()
            out.append(u'<a href="%(url)s" last_changed="%(changed)s">%(name)s</a>\n'
                    % dict(name=name, url=url, changed=changed) )
        out.append('</list>\n')
        self.request.response.setHeader('Content-Type','text/xml; charset=utf-8')
        return ''.join(out)


class GoogleWebmasterSilvio(grok.View):
    """This view tells Google that Silvio (silviot@gmail.com)
       is authorized to use https://www.google.com/webmasters/
       for this site
    """
    grok.name('googlee0ed19dd49699977.html')
    def render(self):
        return "google-site-verification: googlee0ed19dd49699977.html"

class Robots_txt(grok.View):
    grok.name('robots.txt')
    def render(self):
        self.request.response.setHeader('Content-Type','text/plain')
        return "User-agent: *\nAllow: /\n"

    
from zope.interface.common.interfaces import IException
 

class ErrorHandler(grok.View, RepositoryView):
    grok.context(IException)
    grok.name('index.html')

    def repository(self):
        return self.__parent__.__parent__.repository()

    def get_traceback_message(self):
        if self.request.principal.id == 'zope.anybody':
            return ""
        else:
            import traceback
            return traceback.format_exc()


#from zope.publisher.interfaces import INotFound
#from zope.location import LocationProxy

#class PageNotFound(grok.View, RepositoryView):

#    grok.context(INotFound)
#    grok.name('index.html')
#    grok.require("zope.Public")

#    def application_url(self):
#        return ""

#    def repository(self, *args, **kwargs):
#        try:
#            return self.__parent__.__parent__.repository('')
#        except:
#            return self.__parent__.__parent__.repository()

#    @apply
#    def context():
#        # This is done to avoid redefining context in the __init__, after
#        # calling Page.__init__. This way, the error is directly located.

#        def fset(self, error):
#            self._context = LocationProxy(error, error.ob, "Not found")

#        def fget(self):
#            return self._context

#        return property(fget, fset)

#    def update(self):
#        self.request.response.setStatus(404)

