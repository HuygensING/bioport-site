"""
Do a functional test on the app.

:Test-Layer: python
"""
import sys
from bioport.app import Bioport
from zope.testbrowser.testing import Browser
import os
import re
from bioport.tests import DSN
from bioport.tests import FunctionalTestCase
from zope.app.testing.functional import FunctionalTestCase as baseFunctionalTestCase
from bioport.tests import FunctionalLayer


class AdminPanelFunctionalTest(FunctionalTestCase):

    layer = FunctionalLayer
    
    def test_admin_panel(self):
        #set up
        root = self.getRootFolder()
        self.app = app = root['app'] 
        
         #define the db connection
        self.base_url = 'http://localhost/app'
        browser = Browser()
        browser.handleErrors = False #show some information when an arror occurs
        browser.open('http://localhost/app/admin')
#        link = browser.getLink(url=self.base_url + '/admin/edit')
#        link.click()
        browser.open(self.base_url + '/admin/edit')
        form = browser.getForm(index=0)
        form.getControl(name='form.DB_CONNECTION').value = DSN
        form.getControl(name='form.LIMIT').value = '20'
        form.submit('Save')
        
        self.app.repository(user=None).db.metadata.create_all()
        #add a source
        this_dir = os.path.dirname(__file__)
        source_url = 'file://%s' % os.path.join(this_dir, 'data/knaw/list.xml')
        browser.open('http://localhost/app/admin/sources') 
        form = browser.getForm(index=0)
        form.getControl(name='source_id').value = u'knaw_test'
        form.getControl(name='url').value = source_url
        try:
            form.submit()
        except:
            #we get an arror because it already exists -- 
            #XXX we need to properly handle that error
            pass
        #download the biographies for this source
        repository = app.repository(user=None)
        repository.download_biographies(source=repository.get_source(u'knaw_test'))
        

class SimpleSampleFunctionalTest(FunctionalTestCase):
    """ This the app in ZODB. """
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
            if type(url) == type(('', '')):
                url, data = url
            else:
                data = ''
            try:
                browser.open(self.base_url + '/' + url, data.encode('utf8'))
            except:
                raise
                assert 0, 'error opening %s?%s' % (self.base_url + '/' + url, data.encode('utf8'))
                
    def test_personidentify_workflow(self):
        browser = Browser('http://localhost/app/admin/persoonidentify')
        browser.handleErrors = False
        
        #search for the first person
        form = browser.getForm(index=0)
        form.getControl(name='search_name').value='hilbrand'
        form.getControl(name='form.actions.search_persons').click()
        assert 'Hilbrand' in browser.contents, browser.contents
        
        #choose it and put it in the list
        browser.getLink('kies').click()
       
        #we now selected the person
        #we can find the name of the person, followed by a 'verwijder' link
        assert re.findall('Hilbrand.*verwijder', browser.contents, re.DOTALL), browser.contents
        
        
        #the page remembered the serach term
        form = browser.getForm()
        self.assertEqual(form.getControl(name='search_name').value, 'hilbrand')
        
        #search for a second person, using a wildcard pattern
        form.getControl(name='search_name').value =  'heyns*'
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
        form.getControl(name='search_name').value= 'kraemer'
        form.getControl(name='form.actions.search_persons').click()
        browser.getLink('kies').click()
        
        
        #identify the two
        link = browser.getLink(id='identify')
        link_url = link.url
        bioport_id1, bioport_id2 = link.url.split('bioport_ids=')[1:]
        bioport_id1 = bioport_id1[:bioport_id1.find('&')]
        bioport_id2 = bioport_id2[:bioport_id2.find('&')]
        link.click()
        
        #now the two items names are identifed
        #if we go to the first url, it should redirect us to the second url
        self.assertNotEqual(bioport_id1, bioport_id2)
        browser1 = Browser('http://localhost/app/persoon/%s' % bioport_id1)
        browser2 = Browser('http://localhost/app/persoon/%s' % bioport_id2)
        #one of the two pages should have redirected to the other - both will now have the same url
        self.assertEqual(browser1.url , browser2.url)
        
    def test_most_similar_workflow(self): 
        pass
        
    def test_edit_workflow(self):
        """ test creating a bioport instance into Zope """
        browser = Browser('http://localhost/app/admin')
        browser.handleErrors = False
        link = browser.getLink('Bewerk personen')
        link.click()
        
        #click on one of the "bewerk" links
        link = browser.getLink('bewerk gegevens', index=0)
        link.click()
        edit_url = browser.url
        #remove the birth date
        form = browser.getForm(index=0)
        form.getControl(name='birth_y').value=''
        form.getControl(name='birth_text').value=''
        form.getControl(name='personname'). value = 'xxx'
        form.getControl(name='form.actions.save_everything').click()
       
        #go the the public view 
        browser.getLink('getoond').click()
        public_url = browser.url

       
        browser.open(edit_url)
        form = browser.getForm(index=0)
        form.getControl(name='birth_y').value='1111'
        form.getControl(name='form.actions.save_everything').click()
        browser.open(public_url)
        assert re.findall('1111', browser.contents, re.DOTALL)
        
        
        browser.open(edit_url)
        form = browser.getForm(index=0)
        form.getControl(name='death_y').value='2222'
        form.getControl(name='death_m').value=['2']
        form.getControl(name='death_d').value='1'
        form.getControl(name='form.actions.save_everything').click()
        form = browser.getForm(index=0)
        self.assertEqual(form.getControl(name='death_y').value,'2222')
        self.assertEqual(form.getControl(name='death_m').value,['2'])
        self.assertEqual(form.getControl(name='death_d').value,'1')
        browser.open(public_url)
        assert re.findall('1 februari 2222', browser.contents, re.DOTALL), browser.contents
        
        browser.open(edit_url)
        form = browser.getForm(index=0)
        form.getControl(name='funeral_y').value='3333'
        form.getControl(name='form.actions.save_everything').click()
        browser.open(public_url)
        assert re.findall('3333', browser.contents, re.DOTALL)
        
        browser.open(edit_url)
        form = browser.getForm(index=0)
        form.getControl(name='baptism_y').value='4444'
        form.getControl(name='form.actions.save_everything').click()
        browser.open(public_url)
        assert re.findall('4444', browser.contents, re.DOTALL)
        
        #geslacht
        browser.open(edit_url)
        form = browser.getForm(index=0)
        form.getControl(name='sex').value=['2']
        form.getControl(name='form.actions.save_everything').click()
        browser.open(public_url)
        assert re.findall('vrouw', browser.contents, re.DOTALL)
 
        #snippet
#        browser.open(edit_url)
#        form = browser.getForm(index=0)
#        form.getControl(name='snippet').value=['test for snippet']
#        form.getControl(name='form.actions.save_snippet').click()
#        browser.open(public_url)
#        assert re.findall('test for snippet', browser.contents, re.DOTALL)
        
        """does the 'save everyting' button indeed save everything? """
        browser.open(edit_url)
        form = browser.getForm(index=0)
        vals = [
            ('sex', ['1']),
            ('baptism_y', '555'),
            ('birth_text', 'ladida'),
            ('birth_y', ''),
            ('state_floruit_from_y', '2000'),
            ('status', ['1']),
        ]
        for k, v in vals:
            try:
                form.getControl(name=k, index=0).value = v
            except:
                print '********', k, v
                raise
        form.getControl(name='form.actions.save_everything').click()
        form = browser.getForm(index=0)
        for k,v in vals:
            self.assertEqual(form.getControl(name=k).value, v)
            
        browser.open(public_url)
        assert re.findall('man', browser.contents, re.DOTALL), browser.contents
        assert re.findall('%s' % dict(vals)['baptism_y'], browser.contents, re.DOTALL)
        assert re.findall(dict(vals)['birth_text'], browser.contents, re.DOTALL), browser.contents
        
        #changes in, e.g., birth events, should turn up in the master list
        browser = Browser('http://localhost/app/admin/persons')
        #XXX but the next test might fail if we do not have one of the first persons...
        
        
        
def test_suite():
    test_suite = unittest.TestSuite()
    tests = [AdminPanelFunctionalTest,
             SimpleSampleFunctionalTest,
            ]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')    

