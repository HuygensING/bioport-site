
import grok
from BioPortRepository.repository import Repository
from BioPortRepository.common import  BioPortException
from zope.interface import Interface
from zope import schema

class IAdminSettings(Interface):           
    SVN_REPOSITORY = schema.TextLine(title=u'URL of svn repository')
    SVN_REPOSITORY_LOCAL_COPY = schema.TextLine(title=u'path to local copy of svn repository')
   

class Admin(grok.Container):
    grok.template('admin_index')
    SVN_REPOSITORY = '/home/jelle/projects_active/bioport/bioport_repository'
    SVN_REPOSITORY_LOCAL_COPY = '/home/jelle/projects_active/bioport/bioport_repository_local_copy'
    
    grok.implements(IAdminSettings)
    
    def get_repository(self):
        repo = Repository(
            svn_repository=self.SVN_REPOSITORY, 
            svn_repository_local_copy=self.SVN_REPOSITORY_LOCAL_COPY,
        ) 
        return repo
    
    def repository(self):
        return self.get_repository()
    
class Edit(grok.EditForm):
    grok.context(Admin)
    form_fields = grok.Fields(IAdminSettings)
    @grok.action(u"Edit Admin settings")
    def edit_admin(self, **data):
        self.applyData(self.context, **data)
        
class Display(grok.DisplayForm):
    grok.context(Admin)
    form_fields = grok.Fields(IAdminSettings)
 
class Index(grok.View):
    pass
    
class Biographies(grok.View):
    grok.context(Admin)
    
    def get_biographies(self):
        return self.context.get_repository().get_biographies()

class Biography_Identify(grok.View):
    pass

class Biography(grok.View):
    pass

class Person(grok.View):
    pass
class Persons(grok.View):
    pass
class Source(grok.View):
    #CODE for construction traverse_subpath from 
    #  http://grok.zope.org/documentation/how-to/traversing-subpaths-in-views 
    def publishTraverse(self, request, name):
       self._traverse_subpath = request.getTraversalStack() + [name]
       request.setTraversalStack([])
       return self
    def traverse_subpath(self):
       return getattr(self, '_traverse_subpath', [])
       
    def traverse_subpath_helper(self, i, default=None):
        p = self.traverse_subpath()
        if i < len(p):
            return p[i]
        else:
            return default

    def update(self, source_id=None, url='', description='', quality=0):
        if source_id:
            source = self.context.repository().get_source(source_id) 
            source.set_value(url=url, description=description) 
            if quality and quality != source.get_value('quality'):
                source.set_quality(int(quality))
    
            source.save()
            
            msg = 'Changed source %s' % source.id
            print msg
            print quality
            print source.quality 
            
class Sources(grok.View):
    

    def update(self, action=None, source_id=None):
        if action == 'update_source':
            self.update_source(source_id)
        elif action == 'source_delete':
            self.source_delete(source_id)
    
    def update_source(self, source_id):
            source = self.context.repository().get_source(source_id) 
            assert source
            try:
                source.download_data()
                msg = 'Downloaded data for source with id %s' % source.id
    
    
            except BioPortException, error:
                msg = 'An error occurred: %s' % (error)
            return msg
#            self.redirect('%s?msg=%s' % (self.url(), msg))

    def source_delete(self, source_id):
        repo = self.context.repository() 
        source = self.context.repository().get_source(source_id)
        repo.commit(source)
        repo.delete_source(source)
        
        msg = 'Deleted source with id %s ' % source_id
        print msg
        return msg