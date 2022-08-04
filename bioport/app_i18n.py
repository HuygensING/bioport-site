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

import grok

from app import Bioport
from interfaces import IBioport
from interfaces import IEnglishRequest

try:
    from zope.i18n.interfaces import IUserPreferredLanguages  # after python 2.6 upgrade
except ImportError:
    from zope.app.publisher.browser import IUserPreferredLanguages  # before python 2.6 upgrade
from zope.component import adapts
from zope.interface import alsoProvides
from zope.interface import implements
from zope.traversing.browser.absoluteurl import AbsoluteURL
from zope.traversing.browser.interfaces import IAbsoluteURL


class BioportTraverser(grok.Traverser):
    """This traverser ensures that an english version of the site is available at /en"""
    grok.context(Bioport)

    def traverse(self, name):
        if name == 'en':
            preferred_languages = IUserPreferredLanguages(self.request)
            preferred_languages.setPreferredLanguages(['en'])
            alsoProvides(self.request, IEnglishRequest)
            return self.context


def language_switch(object, event):
    """This is registered in zcml as a pre-traversal hook on Bioport"""
    context = object
    request = event.request
    preferred_languages = IUserPreferredLanguages(request)
    preferred_languages.setPreferredLanguages(['nl'])


class EnglishAbsoluteURL(AbsoluteURL):
    """This ensures that english requests will provide english urls"""
    adapts(IBioport, IEnglishRequest)
    implements(IAbsoluteURL)

    def __call__(self):
        return super(EnglishAbsoluteURL, self).__call__() + '/en'
