import email.Header
import grok
from app import Bioport
from app import RepositoryView
from zope import schema
from zope.component import getUtility
from zope.interface import Interface
from zope.sendmail.interfaces import IMailDelivery
from random import randint
from zope.app.form.browser.textwidgets import TextWidget
from bioport.crypt import encrypt
from bioport.crypt import decrypt
from grokcore.view.util import url
from zope.app.form.interfaces import MissingInputError
grok.context(Bioport)

ENCRYPTION_KEY = 'A verySecretkey!'
CAPTCHA_LENGTH = 5
CAPTCHA_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVXYWZ123456789'

def get_random_sequence():
    result = ''
    for i in xrange(CAPTCHA_LENGTH):
        result += CAPTCHA_ALPHABET[randint(0,len(CAPTCHA_ALPHABET)-1)]
    return result

class IContact(Interface):
    name = schema.TextLine(title=u"Naam")
    sender = schema.TextLine(title=u"Mailadres")
    text = schema.Text(title=u"Tekst")
    verification = schema.Text(title=u"verification")

class CaptchaWidget(TextWidget):
    def getInputValue(self):
        value = super(CaptchaWidget, self).getInputValue()
        solution = decrypt(ENCRYPTION_KEY, self.request.form['captcha_text'])
        if value.upper().replace('0','O') != solution:
            raise MissingInputError(self, None)
        return solution
        
    def __call__(self):
        original_widget = super(CaptchaWidget, self).__call__()
        solution = get_random_sequence()
        enc_value = encrypt(ENCRYPTION_KEY, solution)
        base_url = url( self.request,self.context.context)
        image_url = base_url + '/captcha_image?key=' + enc_value
        my_widget = original_widget + ' <img src="%s">' % image_url
        my_widget = original_widget + ' <input type="hidden" name="captcha_text" value="%s">' % enc_value        
        return my_widget

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

