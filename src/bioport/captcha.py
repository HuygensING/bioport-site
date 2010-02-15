import captchaimage
import cStringIO
import grok
import Image
import os
from bioport.app import Bioport
from bioport.crypt import decrypt
from bioport.crypt import encrypt
from grokcore.view.util import url
from random import randint
from urllib import urlencode
from zope.app.form.browser.textwidgets import TextWidget
from zope.app.form.interfaces import MissingInputError


ENCRYPTION_KEY = 'A verySecretkey!'
CAPTCHA_LENGTH = 5
CAPTCHA_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVXYWZ123456789'
FONT_FILE = os.path.join(os.path.dirname(__file__), 'FreeSerif.ttf')

class CaptchaError(MissingInputError):
    "Error raised when captcha is not correct"

class CaptchaWidget(TextWidget):
    def getInputValue(self):
        value = super(CaptchaWidget, self).getInputValue()
        solution = decrypt(ENCRYPTION_KEY, self.request.form['captcha_text'])
        if value.upper().replace('0','O') != solution:
            raise CaptchaError(self.context.__name__, self.context.title, 
                              u"Controleer of u de letters goed heeft overgetypt")
        return solution
        
    def __call__(self):
        original_widget = super(CaptchaWidget, self).__call__()
        old_captcha = self.request.form.get('captcha_text', None)
        new_captcha_needed = True
        if old_captcha:
            try:
                self.getInputValue()
                # No error in the previous statement means that the user has already
                # submitted a succesful captcha. No need to return a new one.
                new_captcha_needed = False
            except:
                pass
        if new_captcha_needed:
            solution = get_random_sequence()
            enc_value = encrypt(ENCRYPTION_KEY, solution)
        else:
            enc_value = old_captcha
        base_url = self.application_url()
        image_url = base_url + '/captcha_image?' + urlencode({'key':enc_value})
        my_widget = original_widget 
#        my_widget += '<br>'
        my_widget += ' <img src="%s">' % image_url
        my_widget += ' <input type="hidden" name="captcha_text" value="%s">' % enc_value        
        return my_widget
    
    def application_url(self, name=None):
        """Return the URL of the nearest enclosing `grok.Application`."""
        obj = self.context.context
        while obj is not None:
            if isinstance(obj, grok.Application):
                return url(self.request, obj, name)
            obj = obj.__parent__
        raise ValueError("No application found.")

        

class Captcha_Image(grok.View):
    grok.context(Bioport)
    def render(self):
        text = decrypt(ENCRYPTION_KEY, self.request.get('key'))
        return get_captcha_image(text)

def get_captcha_image(code):
    size_y = 32
    image_data = captchaimage.create_image(
        FONT_FILE, 28, size_y, code)
    file = cStringIO.StringIO()
    Image.fromstring(
        "L", (len(image_data) / size_y, size_y), image_data).save(
        file, "JPEG", quality = 30)
    return file.getvalue()


def get_random_sequence():
    result = ''
    for i in xrange(CAPTCHA_LENGTH):
        result += CAPTCHA_ALPHABET[randint(0,len(CAPTCHA_ALPHABET)-1)]
    return result

