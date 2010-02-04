import grok
from app import RepositoryView
from app import Bioport
from zope.interface import Interface
from zope import schema

grok.context(Bioport)


class IContact(Interface):
    naam = schema.TextLine(title=u"Naam")
    mailadres = schema.TextLine(title=u"Mailadres")
    tekst = schema.Text(title=u"Tekst")

class ContactForm(grok.AddForm, RepositoryView):
    form_fields = grok.AutoFields(IContact)
    @grok.action('Submit')
    def submit(self, **kwargs):
        "Process input and send email"

class Contact(grok.View, RepositoryView):
    pass

