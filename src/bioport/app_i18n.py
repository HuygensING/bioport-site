import grok
from app import Bioport
from zope.app.publisher.browser import IUserPreferredLanguages

class BioportTraverser(grok.Traverser):
    "This traverser ensures that an english version of the site is available at /en"
    grok.context(Bioport)
    def traverse(self, name):
        if name == 'en':
            preferred_languages = IUserPreferredLanguages(self.request)
            preferred_languages.setPreferredLanguages(['en'])
            return self

def language_switch(object, event):
    "This is registered in zcml as a pre-traversal hook on Bioport"
    context = object
    request = event.request
    preferred_languages = IUserPreferredLanguages(request)
    preferred_languages.setPreferredLanguages(['nl'])
    

