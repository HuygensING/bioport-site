import email.Header
import grok
from app import Bioport
from app import RepositoryView
from bioport.captcha import CaptchaWidget
from bioport.mail_validation import check_email
from zope import schema
from zope.component import getUtility
from zope.interface import Interface
from zope.sendmail.interfaces import IMailDelivery
from zope.schema import ValidationError

grok.context(Bioport)

class InvalidEmailError(ValidationError):
    "Dit is geen geldig email adres"

def email_validator(value):
    if not check_email(value):
        raise InvalidEmailError(value)
    return True

class IContact(Interface):
    name = schema.TextLine(title=u"Naam")
    sender = schema.TextLine(title=u"Emailadres", constraint=email_validator)
    text = schema.Text(title=u"Tekst")
    verification = schema.Text(title=u"Vul de letters in in het vakje")

class ContactForm(grok.AddForm, RepositoryView):
    form_fields = grok.AutoFields(IContact)
    form_fields["verification"].custom_widget = CaptchaWidget
    @grok.action('Submit')
    def submit(self, **kwargs):
        "Process input and send email"
        subject = kwargs['name'] + ' has submitted some feedback'
        email_from = self.context['admin'].EMAIL_FROM_ADDRESS
        email_to = self.context['admin'].CONTACT_DESTINATION_ADDRESS
        send_email(kwargs['sender'], email_to, subject, kwargs['text']) 
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

