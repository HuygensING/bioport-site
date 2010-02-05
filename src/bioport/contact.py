import email.Header
import grok
from app import Bioport
from app import RepositoryView
from zope import schema
from zope.component import getUtility
from zope.interface import Interface
from zope.sendmail.interfaces import IMailDelivery
from bioport.captcha import CaptchaWidget

grok.context(Bioport)

class IContact(Interface):
    name = schema.TextLine(title=u"Naam")
    sender = schema.TextLine(title=u"Mailadres")
    text = schema.Text(title=u"Tekst")
    verification = schema.Text(title=u"verification")

class ContactForm(grok.AddForm, RepositoryView):
    form_fields = grok.AutoFields(IContact)
    form_fields["verification"].custom_widget = CaptchaWidget
    @grok.action('Submit')
    def submit(self, **kwargs):
        "Process input and send email"
        subject = kwargs['name'] + ' has submitted some feedback'
        email_from = self.context['admin'].EMAIL_FROM_ADDRESS
        send_email(email_from, kwargs['sender'], subject, kwargs['text']) 
        self.redirect(self.application_url() + '/contactok')


class Contact(grok.View, RepositoryView):
    pass

class ContactOk(grok.View, RepositoryView):
    pass


def send_email(sender, recipient, subject, body):
    msg = email.MIMEText.MIMEText(body.encode('UTF-8'), 'plain', 'UTF-8')
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = email.Header.Header(subject, 'UTF-8')
    mailer = getUtility(IMailDelivery, 'bioport.mailer')
    mailer.send(sender, [recipient], msg.as_string())

