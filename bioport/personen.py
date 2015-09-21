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

import  grok
from zope.i18n import translate
import simplejson

from z3c.batching.batch import Batch
from bioport import BioportMessageFactory as _
from bioport.app import RepositoryView, Batcher, Bioport, get_born_description, get_died_description, get_alive_description
from fuzzy_search import get_search_query
from fuzzy_search import en_to_nl_for_field
# from fuzzy_search import make_description

try:
    from zope.i18n.interfaces import IUserPreferredLanguages  # after python 2.6 upgrade
except ImportError:
    from zope.app.publisher.browser import IUserPreferredLanguages  # before python 2.6 upgrade
from names.common import to_ymd

grok.templatedir('app_templates')
grok.context(Bioport)


class _Personen(RepositoryView):
    def get_persons(self, **args):
        """get Persons - with restrictions given by request"""
        qry = {}
        # request.form has unicode keys - make strings
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
            'hide_invisible',
            'order_by',
            'religion',
#            'search_family_name',
#            'search_family_name_exact',
            'search_term',
#            'search_name',
#            'search_name_exact',
#            'search_soundex',
            'size',
            'source_id',
            'source_id2',
            'start',
            'status',
#            'sterfjaar_min',
#            'sterfjaar_max',
            'sterfplaats',
            'has_contradictions',
            'url_biography',
#        start=None,
#        size=None,
             ]:
            if k in self.request.keys():
                qry[k] = self.request[k]
            if k in args:
                qry[k] = args[k]

#        logging.info('query %s \n args %s \n request: %s' % (str(qry), str(args), str(self.request)))
        current_language = IUserPreferredLanguages(self.request).getPreferredLanguages()[0]

        request = self.request
        form = request.form

        search_name = form.get('search_name')
        if form.get('search_name_exact') and not search_name.startswith('"'):
            # search for the exact phrase
            search_name = '"%s"' % search_name

        if search_name:
            qry['search_name'] = search_name

        search_family_name = form.get('search_family_name')
        if form.get('search_family_name_exact') and not search_family_name.startswith('"'):
            # search for the exact phrase
            search_family_name = '"%s"' % search_family_name

        if search_family_name:
            qry['search_name'] = search_family_name
            qry['search_family_name_only'] = True

        geboorte_fuzzy_text = form.get('geboorte_fuzzy_text', None)
        if geboorte_fuzzy_text:
            geborte_query = get_search_query(geboorte_fuzzy_text, current_language)
            qry.update(en_to_nl_for_field(geborte_query, 'geboorte'))
        sterf_fuzzy_text = form.get('sterf_fuzzy_text', None)
        if sterf_fuzzy_text:
            sterf_query = get_search_query(sterf_fuzzy_text, current_language)
            qry.update(en_to_nl_for_field(sterf_query, 'sterf'))
        levend_fuzzy_text = form.get('levend_fuzzy_text', None)
        if levend_fuzzy_text:
            levend_query = get_search_query(levend_fuzzy_text, current_language)
            qry.update(en_to_nl_for_field(levend_query, 'levend'))

        has_contradictions = form.get('has_contradictions', None)
        if has_contradictions == 'on':
            qry['has_contradictions'] = True

        # parameters from the API
        qry.update(parse_api_args(form))
        persons = self.repository().get_persons_sequence(**qry)
        return persons


class Personen(grok.View, _Personen, Batcher):
    def publishTraverse(self, request, name):
        if name == 'biodes':
            return PersonenXML(self.context, self.request)
        elif name == 'json':
            return PersonenJSON(self.context, self.request)
        return super(Personen, self).publishTraverse(request, name)

    def get_persons(self, **args):
        """get persons batch"""
        # ignore the start and size parameters when querying the database
        # (they are used for batching, but we need the whole result set for navigating)
        args['start'] = None
        args['size'] = None
        persons = _Personen.get_persons(self, **args)

        try:
            batch = Batch(persons, start=self.start, size=self.size)
        except IndexError:
            batch = Batch(persons, size=self.size)

        batch.grand_total = len(persons)
        self.batch = batch
        return batch

    def update(self):
        Batcher.update(self)

    def search_description(self):
        """return a description for the user of the search parameters in the request"""

        current_language = IUserPreferredLanguages(self.request).getPreferredLanguages()[0]
        _between = translate(_(u'between'), target_language=current_language)
        _and = translate(_(u'and'), target_language=current_language)
        _after = translate(_(u'after'), target_language=current_language)
        _before = translate(_(u'before'), target_language=current_language)
        repository = self.repository()
        result = ''
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
            result += ' ' + translate(_(u'died'), target_language=current_language)
            if died_description:
                result += ' ' + died_description
            if sterfplaats:
                result += ' in <em>%s</em>' % sterfplaats

        if alive_description:
            result += ' ' + translate(_(u'alive'), target_language=current_language)
            result += ' ' + alive_description

        source_id = request.get('source_id')
        if source_id:
            source_name = repository.get_source(source_id).description
            result += ' %s <em>%s</em>' % (translate(_(u'from'),
                                                      target_language=current_language),
             source_name)

        if request.get('search_name'):
            whose_name_is_like = translate(_(u'whose_name_is_like'), target_language=current_language)
            result += ' ' + whose_name_is_like
            result += ' <em>%s</em>' % request.get('search_name')

        if request.get('search_family_name'):
            whose_family_name_is_like = translate(_(u'whose_family_name_is_like'), target_language=current_language)
            result += ' ' + whose_family_name_is_like
            result += ' <em>%s</em>' % request.get('search_family_name')

        if request.get('search_term'):
            result += u' met het woord <em>%s</em> in de tekst' % request.get('search_term')

#        if request.get('search_soundex'):
#            result += u' wier naam lijkt op <em>%s</em>' % request.get('search_soundex')

        if request.get('category'):
            category_name_untranslated = repository.db.get_category(request.get('category')).name
            category_name = translate(_(category_name_untranslated),
                                      target_language=current_language)
            result += ' %s <em>%s</em>' % (
                translate(_("of_the_category"), target_language=current_language),  # uit de rubriek
                             category_name)
        if request.get('religion'):
            religion = dict(repository.get_religion_values()).get(int(request.get('religion')))
            if religion:
#                religion = religion[1]
                religion = translate(_(religion),
                                          target_language=current_language)
                result += ' %s <em>%s</em>' % (
                    translate(_("of_the_religion"), target_language=current_language),  # uit de rubriek
                             religion)

        if request.get('bioport_id'):
            result += ' %s <em>%s</em>' % (translate(_("with_bioport_id"), target_language=current_language), request.get('bioport_id'))

        # NB: in the template, we show the alphabet only if the search description is emtpy
        # uncommenting the following lines messes up this logic
#        if request.get('beginletter'):
#            result += ' met een achternaam beginnend met een <em>%s</em>' % request.get('beginletter')
#
        geslacht_id = request.get('geslacht', None)
        gender_name = {'1': '<em>' + translate(_("men"),
                                      target_language=current_language) + '</em>',
                       '2': '<em>' + translate(_("women"),
                                      target_language=current_language) + '</em>', }
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
#
#    def get_navigation_box(self):
#        "This function returns the html for the navigation box"
#        template_filename = os.path.join(
#                      os.path.dirname(__file__),
#                      'app_templates',
#                      'navigation_block.cpt')
#        template = PageTemplateFile(template_filename)
#
#        return template(view=self, request=self.request)


class PersonenXML(grok.View, _Personen):
    def get_persons(self, **args):
        form = self.request.form
        size = form.get('size')
        if not size:
            args['size'] = 100
        return _Personen.get_persons(self, **args)

    def render(self):

        detail = self.request.get('detail', 'full')
        out = ['<?xml version="1.0" encoding="UTF-8"?>\n']

        out.append('<list>\n')
        # if the argument 'format' is 'links', we just give links
        persons = self.get_persons()
        if detail == 'full':
            if len(persons):
                for person in  persons:
                    out.append(person.get_merged_biography().to_string())
        else:
            if len(persons):
                for person in  persons:
                    person_id = person.record.bioport_id
                    timestamp = person.record.timestamp
                    name = person.record.naam
                    if name:
                        if not type(name) in (unicode,):
                            name = name.decode('latin1')

                        if '&' in name:
                            name = name.replace('&', '&amp;')
        #                    name = unescape(name).encode('utf8')
                    url = self.url('persoon') + '/xml/' + str(person_id)
                    if timestamp:
                        changed = timestamp.isoformat()
                    else:
                        changed = ''
                    out.append(u'<a href="%(url)s" last_changed="%(changed)s">%(name)s</a>\n'
                            % dict(name=name, url=url, changed=changed))
        out.append('</list>\n')
        self.request.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
        return ''.join(out)

class PersonenJSON(PersonenXML):
    def render(self):
        persons = self.get_persons()
        out = []
        if len(persons):
            for person in  persons:
                out.append(person.get_merged_biography().to_dict())
        self.request.response.setHeader('Content-Type', 'application/json; charset=utf-8')
        return simplejson.dumps(out)

def parse_api_args(qry):
    """
    if qry['birth_min'] is defined, return a dictionary that can be passed to the get_persons fucntion of the repository
    same for 'birth_max', 'death_min', 'death_max'
    """
    result = {}
    if qry.get('birth_min'):
        y, m, d = to_ymd(qry['birth_min'])
        result['geboortejaar_min'] = y
        result['geboortemaand_min'] = m
        result['geboortedag_min'] = d

    if qry.get('birth_max'):
        y, m, d = to_ymd(qry['birth_max'])
        result['geboortejaar_max'] = y
        result['geboortemaand_max'] = m
        result['geboortedag_max'] = d

    if qry.get('death_min'):
        y, m, d = to_ymd(qry['death_min'])
        result['sterfjaar_min'] = y
        result['sterfmaand_min'] = m
        result['sterfjaar_min'] = d
    if qry.get('death_max'):
        y, m, d = to_ymd(qry['death_max'])
        result['sterfjaar_max'] = y
        result['sterfmaand_max'] = m
        result['sterfdag_max'] = d

    if qry.get('birth_place'):
        result['geboorteplaats'] = qry['birth_place']
    if qry.get('death_place'):
        result['sterfplaats'] = qry['death_place']
    if qry.get('sex'):
        qry['geslacht'] = qry.get('sex')
    return result

