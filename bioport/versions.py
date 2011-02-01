import email.Header
import grok
from admin import Admin
from app import RepositoryView
from zope.schema import ValidationError


class Versions(grok.EditForm, RepositoryView):
    grok.context(Admin) 
    template = grok.PageTemplateFile("admin_templates/versions.pt")
    grok.require('bioport.Edit')


    
    def update(self):
        self.versions = self.repository().get_versions(
			user = self.request.get('user'),
            time_from = self.request.get('time_from'),
            time_to = self.request.get("time_to"),
            bioport_id = self.request.get("bioport_id"),
            )

    @grok.action('Undo selected changes', name='undo_selected_changes')
    def undo_selected_changes(self, **data):
        
        selected_versions = self.request.get('selected_versions')
        if not type(selected_versions) == type([]):
            selected_versions = [selected_versions]
        d = {}
        
        for selected_version in selected_versions:
            document_id, version = selected_version.split()
            version = int(version)
            d[document_id] = max(d.get(document_id, 0), version)
            
        for document_id in d:
            version = d[document_id]
            self.repository().undo_version(document_id, version)
            
        self.redirect(self.url() + '?%s' % selected_versions)
