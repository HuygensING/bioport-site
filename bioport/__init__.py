# this directory is a package
from zope.i18nmessageid import MessageFactory
BioportMessageFactory = MessageFactory('bioport')


#
#  Provide a global utility for having one repository around
#

import grok
from bioport_repository.repository import Repository
from zope import interface
class IRepository(interface.Interface):
    pass
    
class SiteRepository(grok.GlobalUtility):
    grok.implements(IRepository)
    def __init__(self):
        pass
    def repository(self, data):
        """
        arguments:
            data must have properties that define the repository
        """
        #
        # This implementation is very very ugly
        #     mostly because it is implemented as a quick hack
        #     by porting it from a property of the admin object in the ZODB
        #     to a global utility
        
        try:
            return self._repository
        except AttributeError:
            self._repository =  Repository(
                svn_repository=data.SVN_REPOSITORY, 
                svn_repository_local_copy=data.SVN_REPOSITORY_LOCAL_COPY,
                dsn=data.DB_CONNECTION,
                images_cache_local=data.IMAGES_CACHE_LOCAL,
                images_cache_url=data.IMAGES_CACHE_URL,
    #            user=user, 
    #            ZOPE_SESSIONS=False, #use z3c.saconfig package
                ) 
            return self._repository
