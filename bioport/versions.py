##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gebrandy S.R.L.
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
            amount=self.request.get('amount'),
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
