
import grok

class Edit(grok.Permission):
    grok.name('bioport.Edit')
    
class Manage(grok.Permission):
    grok.name('bioport.Manage')
       