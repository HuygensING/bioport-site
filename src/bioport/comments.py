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


