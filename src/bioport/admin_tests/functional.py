"""
Do a functional test on the app.

:Test-Layer: python
"""
from bioport.app import Bioport
from bioport.tests import FunctionalLayer
from zope.app.testing.functional import FunctionalTestCase
from zope.testbrowser.testing import Browser
import os
import re
from settings import DB_CONNECTION
class SampleFunctionalTest(FunctionalTestCase):
    layer = FunctionalLayer
class SimpleSampleFunctionalTest(SampleFunctionalTest):
    """ This the app in ZODB. """
    def setUp(self):
        SampleFunctionalTest.setUp(self)
        #set up
        root = self.getRootFolder()
        self.app = app = root['app'] = Bioport()
        
        #define the db connection
        self.base_url = 'http://localhost/app'
        self.browser = browser = Browser('http://localhost/app/admin')
        browser.handleErrors = False #show some information when an arror occurs
        print self.base_url + '/admin/edit'
#        link = browser.getLink(url=self.base_url + '/admin/edit')
#        link.click()
        browser.open(self.base_url + '/admin/edit')
        form = browser.getForm()
        form.getControl(name='form.DB_CONNECTION').value = DB_CONNECTION
        form.getControl(name='form.LIMIT').value = '20'
        form.submit('Edit')
        
        self.app.repository(user=None).db.metadata.create_all()
        #add a source
        this_dir = os.path.dirname(__file__)
        source_url = 'file://%s' % os.path.join(this_dir, 'data/knaw/list.xml')
        browser.open('http://localhost/app/admin/sources') 
        form = browser.getForm()
        form.getControl(name='source_id').value = 'knaw_test'
        form.getControl(name='url').value = source_url
        try:
            form.submit()
        except:
            #we get an arror because it already exists -- 
            #XXX we need to properly handle that error
            pass
        #download the biographies for this source
        repository = app.repository(user=None)
        repository.download_biographies(source=repository.get_source('knaw_test'))
        
    def tearDown(self):
        self.app.repository(user=None).db.metadata.drop_all()
    def test_if_pages_work(self):
        
        browser = self.browser
        some_bioport_id = self.app.repository(user=None).get_bioport_ids()[2]
        for url in [
            '',
            'personen',
            ('persoon', 'bioport_id=%s' % some_bioport_id),
            'admin',
            'admin/sources',
            'admin/mostsimilar',
            'admin/persons',
            ('admin/persoon', 'bioport_id=%s' % some_bioport_id),
            'admin/locations',
            ]:
            print 'opening', url
            if type(url) == type(('', '')):
                url, data = url
            else:
                data = ''
            try:
	            browser.open(self.base_url + '/' + url, data.encode('utf8'))
            except:
                raise
                assert 0, 'error opening %s?%s' % (self.base_url + '/' + url, data.encode('utf8'))
            print '... ok'
    def test_personidentify_workflow(self):
        browser = Browser('http://localhost/app/admin')
        
        link = browser.getLink('Identificeer personen')
        link.click()
        
        #search for the first person
        form = browser.getForm(index=0)
        form.getControl(name='search_term').value='hilbrand'
        form.getControl(name='form.actions.search_persons').click()
        assert 'Hilbrand' in browser.contents, browser.contents
        
        #choose it and put it in the list
        browser.getLink('kies').click()
       
        #we now selected the person
        #we can find the name of the person, followed by a 'verwijder' link
        assert re.findall('Hilbrand.*verwijder', browser.contents, re.DOTALL), browser.contents
        
        
        #the page remembered the serach term
        form = browser.getForm()
        self.assertEqual(form.getControl(name='search_term').value, 'hilbrand')
        
        #search for a second person, using a wildcard pattern
        form.getControl(name='search_term').value =  'Heyns*'
        form.getControl(name='form.actions.search_persons').click()
        
        #choose it as well
        browser.getLink('kies').click()
        
        assert re.findall('Hilbrand.*verwijder', browser.contents, re.DOTALL), browser.contents
        assert re.findall('Heyns.*verwijder', browser.contents, re.DOTALL), browser.contents
        #remove the frist person
        browser.getLink('verwijder keuze').click()
        
        assert not re.findall('Hilbrand.*verwijder', browser.contents, re.DOTALL), browser.contents
        assert re.findall('Heyns.*verwijder', browser.contents, re.DOTALL), browser.contents
        
        
        #choose another person
        form = browser.getForm()
        form.getControl(name='search_term').value= 'kraemer'
        form.getControl(name='form.actions.search_persons').click()
        browser.getLink('kies').click()
        
        
        #identify the two
        browser.getLink('identiek').click()
        
        #now the two items names are identifed (but how to check?)
    def test_most_similar_workflow(self): 
        pass
    def test_edit_workflow(self):
        """ test creating a bioport instance into Zope """

        
        browser = Browser('http://localhost/app/admin')
        link = browser.getLink('Bewerk personen')
        link.click()
        
        #click on one of the "bewerk" links
        link = browser.getLink('bewerk gegevens', index=0)
        link.click()
        
        assert 'Bewerk gegevens van' in browser.contents, browser.contents
        edit_url = browser.url
        #remove the birth date
        form = browser.getForm()
        form.getControl(name='birth_y').value=''
        form.getControl(name='birth_text').value=''
        form.getControl(name='form.actions.save_event_birth').click()
       
        
        #go the the public view 
        browser.getLink('getoond').click()
        public_url = browser.url
        #now we should have an empty birth date
        assert re.findall('Geboren.*?<td class="datum">\s*?</td>', browser.contents, re.DOTALL), browser.contents
       
        browser.open(edit_url)
        form = browser.getForm()
        form.getControl(name='birth_y').value='1111'
        form.getControl(name='form.actions.save_event_birth').click()
        browser.open(public_url)
        assert re.findall('Geboren.*?<td class="datum">\s*?1111\s*?</td>', browser.contents, re.DOTALL)
        
        
        browser.open(edit_url)
        form = browser.getForm()
        form.getControl(name='death_y').value='2222'
        form.getControl(name='death_m').value=['2']
        form.getControl(name='death_d').value=['1']
        form.getControl(name='form.actions.save_event_death').click()
        form = browser.getForm()
        self.assertEqual(form.getControl(name='death_y').value,'2222')
        self.assertEqual(form.getControl(name='death_m').value,['2'])
        self.assertEqual(form.getControl(name='death_d').value,['1'])
        browser.open(public_url)
        assert re.findall('Gestorven.*?<td class="datum">\s*?1 februari 2222\s*?</td>', browser.contents, re.DOTALL), browser.contents
        
        browser.open(edit_url)
        form = browser.getForm()
        form.getControl(name='funeral_y').value='3333'
        form.getControl(name='form.actions.save_event_funeral').click()
        browser.open(public_url)
        assert re.findall('<td class="datum">\s*?3333\s*?</td>', browser.contents, re.DOTALL)
        
        browser.open(edit_url)
        form = browser.getForm()
        form.getControl(name='baptism_y').value='4444'
        form.getControl(name='form.actions.save_event_baptism').click()
        browser.open(public_url)
        assert re.findall('<td class="datum">\s*?4444\s*?</td>', browser.contents, re.DOTALL)
        
        #geslacht
        browser.open(edit_url)
        form = browser.getForm()
        form.getControl(name='sex').value=['2']
        form.getControl(name='form.actions.save_sex').click()
        browser.open(public_url)
        assert re.findall('vrouw', browser.contents, re.DOTALL)
 
        """does the 'save everyting' button indeed save everything? """
        browser.open(edit_url)
        form = browser.getForm()
        vals = [
            ('sex', ['1']),
            ('baptism_y', '555'),
            ('birth_text', 'ladida'),
            ('birth_y', ''),
            ('state_floruit_from_y', '2000'),
            ('status', ['1']),
            ('remarks', 'ongeveer rond'),
        ]
        for k, v in vals:
            try:
	            form.getControl(name=k).value = v
            except:
                print '********', k, v
                raise
        form.getControl(name='form.actions.save_everything').click()
        form = browser.getForm()
        for k,v in vals:
            self.assertEqual(form.getControl(name=k).value, v)
            
        browser.open(public_url)
        assert re.findall('man', browser.contents, re.DOTALL), browser.contents
        assert re.findall('<td class="datum">\s*?%s\s*?</td>' % dict(vals)['baptism_y'], browser.contents, re.DOTALL)
        assert re.findall(dict(vals)['birth_text'], browser.contents, re.DOTALL), browser.contents
        
        #changes in, e.g., birth events, should turn up in the master list
        browser = Browser('http://localhost/app/admin/persons')
        #XXX but the next test might fail if we do not have one of the first persons...