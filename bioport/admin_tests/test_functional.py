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
        
        repository = app.repository(user='unittest user')
        repository.db.metadata.create_all()
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
        repository.download_biographies(source=repository.get_source(u'knaw_test'))
        

class SimpleSampleFunctionalTest(FunctionalTestCase):
    """ This the app in ZODB. """
    def test_if_pages_work(self):
        
        browser = self.browser
        some_bioport_id = self.app.repository(user='unittest user').get_bioport_ids()[2]
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
                
    
    def test_edit_names(self):
        #we had an error when, after identifying, there are more names in the merged_biography than in the bioport_biography...
        browser = Browser('http://localhost/app/admin/persons')
        #get some bioport_ids
        bioport_ids = re.findall('[0-9]{8}', browser.contents)
        bioport_ids = list(set(bioport_ids))
        bioport_ids.sort()
        bioport_id1 = bioport_ids[0]
        bioport_id2 = bioport_ids[1]
        
        #create a bioport biography for one of the persons
        browser = Browser('http://localhost/app/admin/persoon?bioport_id=%s' % bioport_id1)
        browser.getControl(name='personname', index=0).value = 'changed name0'
        browser.getControl(name='name_new').value='new name1'
        browser.getForm().getControl(name='form.actions.save_everything').click()
        
        self.assertEqual(browser.getControl(name='personname', index=0).value , 'changed name0')
        self.assertEqual(browser.getControl(name='personname', index=1).value , 'new name1')
        
       
        
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
        
        #remakrts bioport editor
        browser.open(edit_url)
        form = browser.getForm(index=0)
        s = 'Given the existence as uttered forth in the public works of Puncher and Wattmann of a personal God quaquaquaqua'
        form.getControl(name='remarks_bioport_editor').value=s
        form.getControl(name='form.actions.save_everything').click()
        browser.open(edit_url)
        form = browser.getForm(index=0)
        self.assertEqual(form.getControl(name='remarks_bioport_editor').value, s)
        assert re.findall('quaquaquaqua', browser.contents, re.DOTALL)
        browser.open(public_url)
        
        s = "Questo e' il ballo del qua qua e di un papero che sa fare solo <a href='qua'>qua</a> qua qua piu qua qua qua"

        browser.open(edit_url)
        form = browser.getForm(index=0)
        form.getControl(name='remarks').value=s
        form.getControl(name='form.actions.save_everything').click()
        browser.open(edit_url)
        form = browser.getForm(index=0)
        self.assertEqual(form.getControl(name='remarks').value, s)
        browser.open(public_url)
        assert re.findall("sa fare solo <a href='qua'>qua</a> qua qua", browser.contents, re.DOTALL), browser.contents
 
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
    
class NewFieldsTestCase(FunctionalTestCase):    
 
    def _open_edit_url(self):  
        browser = Browser('http://localhost/app/admin')
        browser.handleErrors = False
        link = browser.getLink('Bewerk personen')
        link.click()
        
        #click on one of the "bewerk" links
        link = browser.getLink('bewerk gegevens', index=0)
        link.click()
        return browser    
    
    def test_edit_references(self):
        browser = self._open_edit_url()
        edit_url = browser.url
   
        def get_identifiers():
            """helper function returns all identifiers of relations in the edit form"""
            ls = re.findall('name="reference_.*?_url"', browser.contents)
            ls = [s.split('_')[1] for s in ls]
            ls = [s for s in ls if s.isdigit()]
            ls = list(set(ls))
            return ls
        
        #add a reference 
        browser.open(edit_url)
        browser.getControl(name='reference_new_url').value = "http://url1"
        browser.getControl(name='reference_new_text').value = 'url1'
        browser.getControl(name='form.actions.save_everything').click()
        
        #now we should have a new element in the form with our new relation info
        assert len(get_identifiers()) == 1
        identifier = get_identifiers()[0]
        self.assertEqual(browser.getControl(name='reference_%s_url' % identifier).value, 'http://url1')
        self.assertEqual(browser.getControl(name='reference_%s_text' % identifier).value , 'url1')
        
        #add a second reference 
        browser.getControl(name='reference_new_url').value = "http://url2"
        browser.getControl(name='reference_new_text').value = 'url2'
        browser.getControl(name='form.actions.save_everything').click()        
       
        #now we should have two references (identified by their indices) 
        self.assertEqual(len(get_identifiers()), 2)
        
        #delete a reference
        identifier = get_identifiers()[1]
        browser.getControl(name='reference_%s_delete' % identifier).value = '1'
        browser.getControl(name='form.actions.save_everything').click()        
        
        #now we should have one reference again, now
        self.assertEqual(len(get_identifiers()), 1)
        
        #we can now edit this reference, and should see the changes
        identifier = get_identifiers()[0]
        browser.getControl(name='reference_%s_url' % identifier).value = "http://url3"
        browser.getControl(name='reference_%s_text' % identifier).value = 'url3'
        browser.getControl(name='form.actions.save_everything').click()       
        
        self.assertEqual(browser.getControl(name='reference_%s_url' % identifier).value, 'http://url3')
        self.assertEqual(browser.getControl(name='reference_%s_text' % identifier).value , 'url3')
    def test_edit_religion(self):
        browser = self._open_edit_url()
        #add a state
        browser.getControl(name='religion_id').value = ['1']
        browser.getControl(name='form.actions.save_everything').click()
        self.assertEqual(browser.getControl(name='religion_id').value , ['1'])
        browser.getControl(name='religion_id').value = ['']
        browser.getControl(name='form.actions.save_everything').click()
        self.assertEqual(browser.getControl(name='religion_id').value , [''])
   
        
'''
    def test_edit_categories(self):    
        browser = self._open_edit_url()
        edit_url = browser.url
        #add a state
        browser.getControl(name='category_id', index=0).value = ['1']
        browser.getControl(name='category_id', index=1).value = ['2']
        browser.getControl(name='form.actions.save_everything').click()
        
        self.assertEqual(browser.getControl(name='category_id', index=0).value , ['1'])
        self.assertEqual(browser.getControl(name='category_id', index=1).value , ['2'])
        
        browser.getControl(name='category_id', index=0).value = ['']
        browser.getControl(name='form.actions.save_everything').click()
        self.assertEqual(browser.getControl(name='category_id', index=0).value , ['2'])
        self.assertEqual(browser.getControl(name='category_id', index=1).value , [''])
        
    def test_edit_states(self):
        browser = self._open_edit_url()
        edit_url = browser.url
        
        def get_identifiers():
            ls = re.findall('name="state_.*?_text"', browser.contents)
            ls = [s.split('_')[1] for s in ls]
            ls = [s for s in ls if s.isdigit()]
            ls = list(set(ls)) 
            return ls
   
        #add a state
        self.assertEqual(len(get_identifiers()), 0)
        
        browser.getControl(name='state_new_text').value = "Amor, ch'a nullo amato amar perdona"
        browser.getControl(name='state_new_from_y').value = '1265'
        browser.getControl(name='state_new_to_y').value = '1321'
        browser.getControl(name='state_new_to_m').value = ['9']
        browser.getControl(name='state_new_to_d').value = '14'
        browser.getControl(name='form.actions.save_everything').click()
        
        #now we should have a new element in the form with our new state info
        #try to get the index of the new state
        #these are names of states
        ls = get_identifiers() 
        self.assertEqual(len(ls),  1)
        index = ls[0]
        self.assertEqual(browser.getControl(name='state_%s_from_y' % index).value, '1265')
        self.assertEqual(browser.getControl(name='state_%s_text' % index).value, "Amor, ch'a nullo amato amar perdona") 
        
        #add a second state 
        browser.getControl(name='state_new_text').value = 'A marriage'
        browser.getControl(name='state_new_from_y').value = '1800'
        browser.getControl(name='state_new_to_y').value = '1900'
        browser.getControl(name='form.actions.save_everything').click()        
       
        #now we should have two states (identified by their indices) 
        ls = get_identifiers() 
        self.assertEqual(len(ls),  2)
        index = ls[0]
        
        #delete an event
        identifier = ls[0]
        browser.getControl(name='state_%s_delete' % identifier).value = '1'
        browser.getControl(name='form.actions.save_everything').click()        
        
        #now we should have one state again, now
        ls = get_identifiers() 
        self.assertEqual(len(ls), 1)
        
        #we can now edit this state, and should see the changes
        identifier = ls[0]
        browser.getControl(name='state_%s_text' % identifier).value = 'A'
        browser.getControl(name='state_%s_from_y' % identifier).value = '1111'
        browser.getControl(name='state_%s_to_y' % identifier ).value = '2222'
        browser.getControl(name='state_%s_place' % identifier).value = 'B'
        browser.getControl(name='form.actions.save_everything').click()       
        self.assertEqual( browser.getControl(name='state_%s_text' % identifier).value , 'A')
        self.assertEqual( browser.getControl(name='state_%s_from_y' % identifier).value , '1111')
        self.assertEqual( browser.getControl(name='state_%s_to_y' % identifier).value , '2222')
        self.assertEqual( browser.getControl(name='state_%s_place' % identifier).value , 'B')
        
    def test_edit_relations(self):
        browser = Browser('http://localhost/app/admin')
        browser.handleErrors = False
        link = browser.getLink('Bewerk personen')
        link.click()
        
        #click on one of the "bewerk" links
        link = browser.getLink('bewerk gegevens', index=0)
        link.click()
        edit_url = browser.url
   
        #add a relation 
        browser.open(edit_url)
        browser.getControl(name='relation_new_name').value = "Your Momma is FAT!"
        browser.getControl(name='relation_new_type').value = ['mother']
        browser.getControl(name='form.actions.save_everything').click()
        
        def get_identifiers():
            """helper function returns all identifiers of relations in the edit form"""
            ls = re.findall('name="relation_.*?_name"', browser.contents)
            ls = [s.split('_')[1] for s in ls]
            ls = [s for s in ls if s.isdigit()]
            ls = list(set(ls))
            return ls
        
        #now we should have a new element in the form with our new relation info
        assert len(get_identifiers()) == 1
        identifier = get_identifiers()[0]
        self.assertEqual(browser.getControl(name='relation_%s_name' % identifier).value, 'Your Momma is FAT!')
        self.assertEqual(browser.getControl(name='relation_%s_type' % identifier).value , ['mother'])
        
        #add a second relation 
        browser.getControl(name='relation_new_name').value = "Your Poppa is fat TOO!"
        browser.getControl(name='relation_new_type').value = ['father']
        browser.getControl(name='form.actions.save_everything').click()        
       
        #now we should have two states (identified by their indices) 
        self.assertEqual(len(get_identifiers()), 2)
        
        #delete an event
        identifier = get_identifiers()[0]
        browser.getControl(name='relation_%s_delete' % identifier).value = '1'
        browser.getControl(name='form.actions.save_everything').click()        
        
        #now we should have one relation again, now
        self.assertEqual(len(get_identifiers()), 1)
        
        #we can now edit this relation, and should see the changes
        identifier = get_identifiers()[0]
        browser.getControl(name='relation_%s_name' % identifier).value = 'Ow, no, she be skinny'
        browser.getControl(name='relation_%s_type' % identifier).value = ['sister']
        browser.getControl(name='form.actions.save_everything').click()       
        
        identifier = get_identifiers()[0]
        self.assertEqual(browser.getControl(name='relation_%s_name' % identifier).value, 'Ow, no, she be skinny')
        self.assertEqual(browser.getControl(name='relation_%s_type' % identifier).value , ['sister'])
        
'''        
def test_suite():
    test_suite = unittest.TestSuite()
    tests = [AdminPanelFunctionalTest,
             SimpleSampleFunctionalTest,
             NewFieldsTestCase,
            ]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')    
