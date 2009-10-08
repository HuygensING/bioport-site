import grok
from admin import Admin
import zope.interface


class Bioport(grok.Application, grok.Container):
    def __init__(self):
        super(Bioport,self).__init__() #cargoculting from ingforms
        self['admin'] = Admin()

class Index(grok.View):
    pass # see app_templates/index.pt

class Main_Template(grok.View):
    grok.context(zope.interface.Interface)
    