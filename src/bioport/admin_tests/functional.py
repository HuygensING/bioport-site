"""
Do a functional test on the app.

:Test-Layer: python
"""
from bioport.app import Bioport
from bioport.tests import FunctionalLayer
from zope.app.testing.functional import FunctionalTestCase
from zope.testbrowser import Browser
import os
import re
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
        
        link = browser.getLink('Gevanceerd')
        link.click()
        form = browser.getForm()
        form.getControl(name='form.DB_CONNECTION').value = 'mysql://root@localhost/bioport_test'
        form.getControl(name='form.LIMIT').value = '20'
        form.submit('Edit')
        
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
        browser.open('http://localhost:8080/app/admin/sources', 'action=update_source&source_id=knaw_test')
        
                
    def test_if_pages_work(self):
        
        browser = self.browser
        some_bioport_id = self.app.repository().get_bioport_ids()[2]
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
                assert 0, 'error opening %s?%s' % (self.base_url + '/' + url, data.encode('utf8'))
    def test_admin_workflow(self):
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
        form.getControl(name='sex').value=['1']
        form.getControl(name='baptism_y').value='555'
        form.getControl(name='birth_text').value='ongeveer rond 200 geboren'
        form.getControl(name='birth_y').value=''
        form.getControl(name='state_floruit_from_y').value='1222'
        form.getControl(name='status').value=['2']
        form.getControl(name='remarks').value='het opmerkingen veld'
        form.getControl(name='form.actions.save_everything').click()

        browser.open(public_url)
        assert re.findall('man', browser.contents, re.DOTALL), browser.contents
        assert re.findall('<td class="datum">\s*?555\s*?</td>', browser.contents, re.DOTALL)
        assert re.findall('ongeveer rond 200', browser.contents, re.DOTALL), browser.contents
        assert re.findall('1222', browser.contents, re.DOTALL), browser.contents
        
        #changes in, e.g., birth events, should turn up in the master list
        browser = Browser('http://localhost/app/admin')
        link = browser.getLink('Bewerk personen')
        link.click()
        #XXX but the next test might fail if we do not have one of the first persons...
        assert re.findall('ongeveer rond 200', browser.contents, re.DOTALL)
