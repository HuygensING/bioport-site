##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gerbrandy S.R.L.
#
# This file is part of bioport.
#
# bioport is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/gpl-3.0.html>.
##########################################################################

import datetime
import os
import random
import time
import types
import re
import htmlentitydefs
from urllib import urlencode

import grok
import zope.interface
from zope.interface.common.interfaces import IException
from zope.i18n import translate
from plone.memoize import ram
from sqlalchemy.exc import OperationalError
import simplejson
from fuzzy_search import get_search_query
from fuzzy_search import make_description

from zope.publisher.interfaces import NotFound, INotFound
from zope.authentication.interfaces import IAuthentication
from zope.authentication.interfaces import PrincipalLookupError
from zope import component
try:
    from zope.i18n.interfaces import IUserPreferredLanguages  # after python 2.6 upgrade
except ImportError:
    from zope.app.publisher.browser import IUserPreferredLanguages  # before python 2.6 upgrade

from mobile.sniffer.detect import detect_mobile_browser
from mobile.sniffer.utilities import get_user_agent

from common import (format_date, format_dates, format_number,
                    html2unicode, maanden, months)
from interfaces import IBioport
from names.common import to_ymd
from bioport import BioportMessageFactory as _
from bioport_repository.db_definitions import SOURCE_TYPE_PORTRAITS


class Bioport(grok.Application, grok.Container):
    zope.interface.implements(IBioport)

    debug = False

    def __init__(self, dsn=None):
        super(Bioport, self).__init__()
        from admin import Admin
        self['admin'] = Admin()
        from biodes import BioDes
        self['biodes'] = BioDes()

    def format_dates(self, s1, s2, **args):
        return format_dates(s1, s2, **args)

    def repository(self):
        return self['admin'].repository()

    def format_number(self, s):
        return format_number(s)


class RepositoryView:
    def repository(self):
        return self.context.repository()

    def get_sources(self):
        return self.repository().get_sources()

    def get_person(self, bioport_id):
        return self.repository().get_person(bioport_id)

    def get_status_value(self, k, default=None):
        return self.repository().get_status_value(k, default)

    def get_status_values(self):
        return self.repository().get_status_values()

    def get_source_types(self):
        return self.repository().get_source_types()

    @ram.cache(lambda *args: time.time() // (60 * 60))
    def count_persons(self):
        try:
            i = self.repository().db.count_persons()
            i = format_number(i)
            return i
        except OperationalError:
            return 0

    @ram.cache(lambda *args: time.time() // (60 * 60))
    def count_biographies(self):
        try:
            i = self.repository().db.count_biographies()
            # XXX turned of caching, need to find some "update once a day" solution
            i = format_number(i)
            return i
        except OperationalError:
            return 0

    def menu_items(self):
        items = [
            (self.application_url(), _('home')),
            (self.application_url('zoek'), _('zoeken')),
            (self.application_url('personen') + '?beginletter=a', _('bladeren')),
            (self.application_url('about'), _('project')),
        ]

        adapter = IUserPreferredLanguages(self.request)
        lang = adapter.getPreferredLanguages()[0]
        if lang != 'en':
            items += [(self.application_url('blog'), _('blog')),
                    (self.application_url('agenda'), _('agenda')), ]
        items += [
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
            month = months[today.month - 1]
            return '%s %s' % (month, today.day)
        else:
            month = maanden[today.month - 1]
            return '%s %s' % (today.day, month)

    def print_dates_of_person(self, person):
        date1, date2 = person.get_dates_for_overview()
        return format_dates(date1, date2)

    def getPrincipals(self):
        self._principal_registry = component.getUtility(IAuthentication)
        principals = self._principal_registry.getPrincipals('')
        return principals

    def getPrincipal(self, id):  # @ReservedAssignment
        self._principal_registry = component.getUtility(IAuthentication)
        try:
            return self._principal_registry.getPrincipal(id)
        except PrincipalLookupError:
            return None

    def is_handheld(self):
        # Get HTTP_USER_AGENT from HTTP request object
        class FakeRequest:
            def __init__(self, request):
                self.other = request
        ua = get_user_agent(FakeRequest(self.request))
        if ua:
            # Apply reg
            if detect_mobile_browser(ua):
                # Redirect the visitor from a web site to a mobile site
                return True
            else:
                # A regular web site visitor
                return False
        else:
            # User agent header is missing from HTTP request
            return False


class Batcher:
    def update(self, **kw):
        self.start = int(self.request.get('start', 0) or 0)
        self.size = int(self.request.get('size', 30) or 0)

    def batch_url(self, start=None, size=None):
        # next two lines replaces data = self.request.form
        # which magickally resolves a unicode error
        data = {}
        data.update(self.request.form)
        if start is not None:
            data['start'] = start
        if size is not None:
            data['size'] = size
        return self.url(data=data)


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

    # make the .             template avaible for everything
    grok.context(zope.interface.Interface)


class Main_Template(grok.View, RepositoryView):
    # make the main template avaible for everything
    grok.context(zope.interface.Interface)


class Admin_Template(grok.View):
    # make the main template avaible for everything
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
        if lang == 'nl':  # convert en --> nl
            new_application_url = self.application_url()[:-3]
        else:  # convert nl --> en
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


class BioPortIdTraverser(object):
    """ Mixin class that makes a view traversable with an
        integer id.
    """
    bioport_id = None  # will be available after traversal

    def publishTraverse(self, request, name):
        # We won't traverse more than once
        # allowing view_url/some_id but not view_url/something/some_id
        if len(request.getTraversalStack()) > 0 or not name.isdigit():
            raise NotFound(self.context, name)
        self.bioport_id = long(name)
        return self


class PersoonXml(BioPortIdTraverser, grok.View, RepositoryView):
    def render(self):
        redirects_to = self.repository().redirects_to(self.bioport_id)
        if redirects_to:
            self.bioport_id = redirects_to
        print type(self.bioport_id)
        person = self.repository().get_person(bioport_id=self.bioport_id)
        self.request.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
        return person.get_merged_biography().to_string()


class PersoonJson(BioPortIdTraverser, grok.View, RepositoryView):
    def render(self):
        redirects_to = self.repository().redirects_to(self.bioport_id)
        if redirects_to:
            self.bioport_id = redirects_to
        person = self.repository().get_person(bioport_id=self.bioport_id)
        self.request.response.setHeader('Content-Type', 'application/json; charset=utf-8')
        return simplejson.dumps(person.get_merged_biography().to_dict())


class Resolver(grok.View, RepositoryView):
    """be as smart as possible about the values in the request, and redirect to a person (if found)

    at the moment, we parse the following request args:
        url - try to find a person that refers to the the biography at this url
    perhaps in the future:
        priref -
        pica -
        ecc.
    """
    def render(self):
        # if true, we want to return a json-padded javascript. Otherwise, we redirect to a suitable page
        return_jsonp = self.request.get('callback')
        url = self.request.get('url')
        if url:
            bioport_id = self.repository().get_bioport_id(url_biography=url)
            if not bioport_id:
                # perhaps do this cleaner, use urllib.urlencode
                # the problem here is that in our db, we often have urls stored as
                #     http://[urlencoded_url]
                # (and not as urlllib.urlencode('http:///.....')
                url = url.replace(' ', '%20')
                url = url.replace(',', '%2C')
                bioport_id = self.repository().get_bioport_id(url_biography=url)

        else:
            bioport_id = None
        if bioport_id:
            url = os.path.join(self.application_url(), 'persoon', str(bioport_id))
        if return_jsonp:
            if bioport_id:
                person = self.repository().get_person(bioport_id=bioport_id)
                bios = person.get_biographies()
                bios = [x for x in bios if x.source_id != 'bioport']
                min_number = self.request.get('min_number_of_biographies', '0')
                if not min_number.isdigit():
                    min_number = 0
                min_number = int(min_number)
                if len(bios) >= min_number:
                    dct = {
                        'bioport_id': bioport_id,
                        'url': url,
                        'number_of_biographies': len(bios),
                        'name': person.name(),
                    }
                else:
                    dct = {}
            else:
                dct = {}
            self.request.response.setHeader('Content-Type', 'application/javascript; charset=UTF-8')
            s = '%s(%s)' % (self.request.get('callback'), simplejson.dumps(dct))
            s = s.encode('utf8')  # need to encode, otherwise zope complains about mime-type
            return s
        else:
            # redirect to the person, if we can
            if bioport_id:
                self.request.response.redirect(url)
            else:
                # XXX would be nice to give some feedback if the thing is not found
                self.request.response.redirect(os.path.join(self.application_url()))


class Persoon(BioPortIdTraverser, grok.View, RepositoryView):

    def publishTraverse(self, request, name):
        if name in ['biodes', 'xml']:
            return PersoonXml(self.context, self.request)
        elif name in ['json']:
            return PersoonJson(self.context, self.request)
        return super(Persoon, self).publishTraverse(request, name)

    def update(self, **args):
        if not self.bioport_id and self.request.get('bioport_id'):
            self.bioport_id = long(self.request.get('bioport_id'))
            # XXX redirect, not show
        redirects_to = self.repository().redirects_to(self.bioport_id)
        if redirects_to != self.bioport_id:
            # this is an 'old'bioport_id that has been identified with the bioport_id at redirects_to
            self.redirect(self.url(self) + '/' + str(redirects_to))
        if not self.bioport_id:
            self.bioport_id = random.choice(self.repository().get_bioport_ids())
            self.redirect(self.url(self) + '/' + str(self.bioport_id))

        self.person = self.repository().get_person(bioport_id=self.bioport_id)
        if not self.person:
            message = 'Geen biografie gevonden met deze id: %s' % self.bioport_id
            qs = urlencode({'message': message})
            return self.request.response.redirect(os.path.join(self.application_url(), 'person_not_found') + '?' + qs)
        self.biography = self.merged_biography = self.person.get_merged_biography()
        self.bioport_biography = self.repository().get_bioport_biography(self.person)

    def get_event(self, type, biography=None):  # @ReservedAssignment
        if not biography:
            biography = self.merged_biography

        event_el = biography.get_event(type)
        if event_el is not None:

            # we construct a convenient object
            class EventWrapper:
                def __init__(self, el, _between, _and, _after, _before):
                    self.when = el.get('when')
                    try:
                        self.when_ymd = to_ymd(self.when)
                        self.when_formatted = format_date(self.when)
                    except:
                        self.when_formatted = self.when

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
                    start = self.notBefore_formatted
                    stop = self.notAfter_formatted

                    if not self.date_text:
                        if start and stop:
                            self.when_formatted = "%(_between)s %(start)s %(_and)s %(stop)s" % locals()
                        elif start:
                            self.when_formatted = "%(_after)s %(start)s" % locals()
                        elif stop:
                            self.when_formatted = "%(_before)s %(stop)s" % locals()
                    else:
                        self.when_formatted = ''
                    # ...else, stick with single formatted date

                def __str__(self):
                    string = []
                    for attr in dir(self):
                        if attr.startswith('_'):
                            continue
                        value = getattr(self, attr)
                        string.append("%s=%s" % (attr, value))
                    return '; '.join(string)

            current_lang = IUserPreferredLanguages(self.request).getPreferredLanguages()[0]
            _between = translate(_(u'between'), target_language=current_lang)
            _and = translate(_(u'and'), target_language=current_lang)
            _after = translate(_(u'after'), target_language=current_lang)
            _before = translate(_(u'before'), target_language=current_lang)
            return EventWrapper(event_el, _between, _and, _after, _before)
        else:
            return None

    def get_references(self):
        return [ReferenceWrapper(index, el_reference) for (index, el_reference) in self.bioport_biography.get_references()]

    def get_extrafields(self):
        return [ExtraFieldWrapper(index, el_extrafields) for (index, el_extrafields) in enumerate(self.bioport_biography.get_extrafields())]

    def get_illustrations(self):
        return [IllustrationWrapper(index, el) for (index, el) in self.bioport_biography.get_figures()]

    def get_states(self, type=None, biography=None):  # @ReservedAssignment
        if not biography:
            biography = self.merged_biography
        result = []
        for el in biography.get_states(type):
            if el is not None:
                result.append(StateWrapper(el, type=type))
        return result

    def get_state(self, type, biography=None):  # @ReservedAssignment
        states = self.get_states(type, biography)
        if states:
            return states[0]

    def get_religion_values(self):
        return self.repository().get_religion_values()

    def get_religion(self):
        el = self.bioport_biography.get_religion()
        if el is not None:
            return ReligionWrapper(el, self.repository())

    def get_categories(self):
        return [StateWrapper(x) for x in self.bioport_biography.get_states(type='category')]

    def get_editable_states(self):
        return [StateWrapper(state) for state in self.bioport_biography.get_states()
                if state.get('type') not in ['floruit', 'category', 'religion']]

    def get_biographies(self):
        bios = self.person.get_biographies()
        bios = [
            bio for bio in bios if
            bio.source_id != 'bioport' and
            bio.get_source().source_type != SOURCE_TYPE_PORTRAITS and
            bio.source_id != 'na'
        ]
        return bios

    def get_portraits(self):
        bios = self.person.get_biographies()
        bios = [bio for bio in bios if bio.get_source().source_type == SOURCE_TYPE_PORTRAITS]
        return bios

    def get_archives(self):
        bios = self.person.get_biographies()
        bios = [bio for bio in bios if bio.source_id == 'na']
        return bios

    def maanden(self):
        return maanden

    def is_admin(self):
        from zope.security import checkPermission
        return checkPermission('bioport.Manage', self.context)


class PersonNotFound(BioPortIdTraverser, grok.View, RepositoryView):
    def update(self):
        self.message = self.request.get('message')


def get_born_description(request):
    """ Inspect the request and build a natural language description
        of the searched born date"""
    current_language = IUserPreferredLanguages(request).getPreferredLanguages()[0]
    geboorte_fuzzy_text = request.form.get('geboorte_fuzzy_text')
    if geboorte_fuzzy_text:
        try:
            qry = get_search_query(geboorte_fuzzy_text)
        except ValueError:
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
        except ValueError:
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
        except ValueError:
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
    It returns a JSON like this:

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
    """The JSON used in various search forms of the admin interface.
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


class Birthdays_Box(grok.View, RepositoryView):

    @ram.cache(lambda *args: time.time() // (60 * 60 * 24))  # cache exactly one day
    def get_persons(self):
        """get 3 persons whose birthdate is today"""
        # get the month and day of today
        today = datetime.date.today().strftime('%m%d')
        # query the datase for persons born on this date that have an illustration
        persons = self.repository().get_persons(where_clause='birthday = "%s"' % today, has_illustrations=True, hide_foreigners=True, size=3)

        persons = [p for p in persons if p.has_illustrations]
        if len(persons) < 3:
            # if we have less then 3 people, we cheat a bit and take someone who died today
            persons += self.repository().get_persons(where_clause='deathday = "%s"' % today, has_illustrations=True, hide_foreigners=True, size=3)
            persons = [p for p in persons if [ill for ill in p.get_merged_biography().get_illustrations() if ill.has_image()]]

        for person in persons:
            illustrations = person.get_merged_biography().get_illustrations()
            illustration = illustrations and illustrations[0]
            person.illustration = illustration
        return persons[:3]


class Birthdays(grok.View, RepositoryView):
    def get_persons_born_today(self):
        # get the month and day of today
        today = datetime.date.today().strftime('%m%d')
        # query the database for persons born on this date
        persons = self.repository().get_persons(where_clause='birthday = "%s"' % today)
#         persons = self.repository().get_persons(where_clause='CAST(geboortedatum_min AS CHAR) like "____%s%%" and geboortedatum_min = geboortedatum_max' % today)
        return persons

    def get_persons_dead_today(self):
        # get the month and day of today
        today = datetime.date.today().strftime('%m%d')
        # query the database for persons born on this date
        persons = self.repository().get_persons(where_clause='deathday = "%s"' % today)
        return persons


class Images_XML(grok.View, RepositoryView):
    grok.name('images.xml')

    def render(self):
        self.request.response.setHeader('Content-Type', 'text/xml')
        return self.render_response()

    @ram.cache(lambda *args: time.time() // (60 * 60) + random.randint(1, 10))
    def render_response(self):
        persons = self.repository().get_persons(has_illustrations=True, order_by='random', size=20)
        result = """<?xml version="1.0"?><root>"""
        for person in persons:
            illustrations = person.get_merged_biography().get_illustrations()
            illustration = illustrations[0]
            if not illustration.has_image():
                continue
            result += '<image src="%s" title="%s" url="%s/%s" />\n' % (
                illustration.image_home_url,
                html2unicode(unicode(person.name())),
                self.url('persoon'), person.bioport_id,)
        result += '</root>'
        return result


class BelowBios(grok.ViewletManager):
    grok.name('belowbios')
    grok.context(Bioport)


class SiteMaps(grok.View, RepositoryView):
    MAX_PER_FILE = 2000

    def render(self):
        self.request.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
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
            person_url = application_url + '/persoon/' + str(person.id)
            out += '  <url>\n'
            out += '    <loc>%s</loc>\n' % person_url
            out += '  </url>\n'
        out += '</urlset>\n'
        return out

    def publishTraverse(self, request, name):
        if name[:8] == 'sitemap-':
            self.start_index = int(name[8:])
            return self


# #
# Removes HTML or XML character references and entities from a text string.
# Borrowed from http://effbot.org/zone/re-sub.htm#unescape-html
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

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
        return text  # leave as is
    return re.sub("&#?\w+;", fixup, text)


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
        self.request.response.setHeader('Content-Type', 'text/plain')
        return "User-agent: *\nAllow: /\n"


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


class PeopleWhoLivedMoreThanHundredYears(grok.View, RepositoryView):
    def render(self):
        db = self.repository().db
        from bioport_repository.db_definitions import PersonRecord
        with db.get_session_context() as session:
            query = session.query(PersonRecord).filter(PersonRecord.sterfdatum_min - PersonRecord.geboortedatum_max > 100)
            result = ''
            for person in query.all():
                result = '%s (leefde tenminste %s jaar)' % (person.get_bioport_id(), person.sterfdatum_min - person.geboortedatum_max)
        return result


class RelationWrapper:
    def __init__(self, index, el_relation, el_person):
        self.index = index
        self.type = el_relation.get('name')
        self.name = el_person[0].text
        self.el_relation = el_relation
        self.el_relation_index = el_relation.getparent().index(el_relation)
        self.el_person = el_person
        self.el_person_index = el_person.getparent().index(el_person)


class ReferenceWrapper:
    def __init__(self, index, el_reference):
        self.text = el_reference.text
        self.url = el_reference.get('target')
        self.element = el_reference
        self.index = index


class ExtraFieldWrapper:
    def __init__(self, index, el_extrafield):
        self.value = el_extrafield.text
        self.key = el_extrafield.get('target')
        self.element = el_extrafield
        self.index = index


class IllustrationWrapper:
    def __init__(self, index, el_figure):
        head = ''
        if el_figure.find('head') is not None:
            head = el_figure.find('head').text
        self.url = el_figure.find('graphic').get('url')
        self.text = head
        self.element = el_figure
        self.index = index


class ReligionWrapper:
    def __init__(self, el, repo=None):
        self.repo = repo
        self.idno = el.get('idno')

    @property
    def name(self, repo=None):
        if self.idno:
            if repo:
                self.repo = repo
            return dict(self.repo.get_religion_values())[int(self.idno)]


class StateWrapper:
    def __init__(self, el, type=None):  # @ReservedAssignment
        self.frm = el.get('from')
        self.frm_ymd = to_ymd(self.frm)
        self.to = el.get('to')
        self.to_ymd = to_ymd(self.to)
        self.type = type or el.get('type')
        self.place = el.find('place') is not None and el.find('place').text or ''
        self.text = el.text
        self.idno = el.get('idno')
        self.element = el
        self.index = el.getparent().index(el)

    def has_content(self):
        if self.frm or self.to or self.text or self.place or self.idno:
            return True
        else:
            return False
