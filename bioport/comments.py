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
from bioport.app import Bioport
from bioport.app import BelowBios
from zope.interface import Interface
from zope import schema
from bioport.captcha import CaptchaWidget
from zope.location import locate

class Comments(grok.Viewlet):
    grok.context(Bioport)
    grok.viewletmanager(BelowBios)
    def update(self):
        locate(self.view.person, self.view, '') # The form needs this if person is the context
        self.form = CommentsForm(self.view.person, self.request)
        self.comments = self.view.person.get_comments()


class IComments(Interface):
    submitter = schema.TextLine(title=u"Naam")
    email = schema.TextLine(title=u"Mailadres")
    text = schema.Text(title=u"Tekst")
    verification = schema.Text(title=u"verification")

class CommentsForm(grok.AddForm):
    grok.context(Interface) # Person has no interfaces!
    form_fields = grok.AutoFields(IComments)
    form_fields["verification"].custom_widget = CaptchaWidget
    @grok.action('Submit')
    def submit(self, **kwargs):
        del(kwargs['verification'])
        self.context.add_comment(**kwargs)


