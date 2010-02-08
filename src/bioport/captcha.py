import grok
from random import randint
from zope.app.form.browser.textwidgets import TextWidget
from bioport.crypt import encrypt
from bioport.crypt import decrypt
from grokcore.view.util import url
from zope.app.form.interfaces import MissingInputError
import captchaimage
import Image
import cStringIO
from urllib import urlencode
from bioport.app import Bioport


ENCRYPTION_KEY = 'A verySecretkey!'
CAPTCHA_LENGTH = 5
CAPTCHA_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVXYWZ123456789'
FONT_FILE = '/usr/share/fonts/truetype/freefont/FreeSerif.ttf'

class CaptchaError(MissingInputError):
    "Error raised when captcha is not correct"

class CaptchaWidget(TextWidget):
    def getInputValue(self):
        value = super(CaptchaWidget, self).getInputValue()
        solution = decrypt(ENCRYPTION_KEY, self.request.form['captcha_text'])
        if value.upper().replace('0','O') != solution:
            raise CaptchaError(self.context.__name__, self.context.title, 
                              u"Please check again the verification letters")
        return solution
        
    def __call__(self):
        original_widget = super(CaptchaWidget, self).__call__()
        old_captcha = self.request.form.get('captcha_text', None)
        if old_captcha:
            enc_value = old_captcha
        else:
            solution = get_random_sequence()
            enc_value = encrypt(ENCRYPTION_KEY, solution)
        base_url = self.application_url()
        image_url = base_url + '/captcha_image?' + urlencode({'key':enc_value})
        my_widget = original_widget + ' <img src="%s">' % image_url
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

