import grok
from bioport.app import Bioport
from bioport.app import RepositoryView

import zope.interface

class BioDes(grok.Container):
    grok.template('index')
    def repository(self, user):
        return self.__parent__.repository(user)
    
class Beschrijving(grok.View, RepositoryView):
    pass

class Index(grok.View, RepositoryView):
    pass

class Persoonsnaam(grok.View, RepositoryView):
    pass

class Schemas(grok.View, RepositoryView):
    pass

class Voorbeelden(grok.View, RepositoryView):
    pass
class Partners(grok.View, RepositoryView):
    pass