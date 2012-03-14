#from zope.app.publication.zopepublication import ZopePublication
#from zope.publisher.interfaces import Retry
#from sqlalchemy.exc import OperationalError
#
#
#original = ZopePublication.handleException
#def patchedhandleException(self, object, request, exc_info, retry_allowed=True):
#    if retry_allowed and isinstance(exc_info[1], OperationalError):
#        if "server has gone away" in getattr(exc_info[1], 'message', None):
#            raise Retry(exc_info)
#
#    return original(self, object, request, exc_info, retry_allowed=True)
