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

import email.Header
import grok
from zope import schema
from zope.component import getUtility
from zope.interface import Interface
from zope.schema import ValidationError
from zope.sendmail.interfaces import IMailDelivery

from app import Bioport
from app import RepositoryView
from bioport import BioportMessageFactory as _
from bioport.captcha import CaptchaWidget
from bioport.mail_validation import check_email

grok.context(Bioport)


class InvalidEmailError(ValidationError):
    """Dit is geen geldig email adres"""


def email_validator(value):
    if not check_email(value):
        raise InvalidEmailError(value)
    return True


class IContact(Interface):
    name = schema.TextLine(title=_(u"Naam"))
    sender = schema.TextLine(title=_(u"Emailadres"), constraint=email_validator)
    text = schema.Text(title=_(u"Tekst"))
    verification = schema.Text(title=_(u"Vul de letters in in het vakje"))


class ContactForm(grok.AddForm, RepositoryView):
    template = grok.PageTemplateFile("contact_templates/bare_edit_form.pt")
    form_fields = grok.AutoFields(IContact)
    form_fields["verification"].custom_widget = CaptchaWidget

    @grok.action('Submit')
    def submit(self, **kwargs):
        """Process input and send email"""
        default_subject = 'reactie biografisch portaal van %s' % kwargs['name']
        subject = self.request.form.get('subject') or default_subject
        #        subject = 'reactie biografisch portaal van %s' % kwargs['name']
        _email_from = self.context['admin'].EMAIL_FROM_ADDRESS
        email_to = self.context['admin'].CONTACT_DESTINATION_ADDRESS
        content = '%s\n---------\n\n%s' % (kwargs['text'], default_subject)
        if self.request.form.get('subject'):
            content += '\n%s' % self.request.get('subject')
        send_email(kwargs['sender'], email_to, subject, content)
        self.redirect(self.application_url() + '/contactok')


class Contact(grok.View, RepositoryView):
    pass


class ContactOk(grok.View, RepositoryView):
    pass


def send_email(sender, recipient, subject, body):
    msg = email.MIMEText.MIMEText(body.encode('latin-1'), 'plain', 'latin-1')
    msg["From"] = 'no-reply@huygens.knaw.nl'
    msg["Reply-To"] = sender
    msg["To"] = recipient
    msg["Subject"] = email.Header.Header(subject, 'latin-1')
    mailer = getUtility(IMailDelivery, 'bioport.mailer')
    mailer.send(sender, [recipient], msg.as_string())
