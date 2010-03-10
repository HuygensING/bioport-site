import grok
from app import Bioport
from interfaces import IBioport
from interfaces import IEnglishRequest
from zope.app.publisher.browser import IUserPreferredLanguages
from zope.component import adapts
from zope.interface import alsoProvides
from zope.interface import implements
from zope.traversing.browser.absoluteurl import AbsoluteURL
from zope.traversing.browser.interfaces import IAbsoluteURL

class BioportTraverser(grok.Traverser):
    "This traverser ensures that an english version of the site is available at /en"
    grok.context(Bioport)
    def traverse(self, name):
        if name == 'en':
            preferred_languages = IUserPreferredLanguages(self.request)
            preferred_languages.setPreferredLanguages(['en'])
            alsoProvides(self.request, IEnglishRequest)
            return self.context

def language_switch(object, event):
    "This is registered in zcml as a pre-traversal hook on Bioport"
    context = object
    request = event.request
    preferred_languages = IUserPreferredLanguages(request)
    preferred_languages.setPreferredLanguages(['nl'])
    
class EnglishAbsoluteURL(AbsoluteURL):
    adapts(IBioport, IEnglishRequest)
    implements(IAbsoluteURL)
    def __call__(self):
        return super(EnglishAbsoluteURL, self).__call__() + '/en'
    __str__ = __call__
