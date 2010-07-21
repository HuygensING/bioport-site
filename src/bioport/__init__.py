# this directory is a package
from zope.i18nmessageid import MessageFactory
BioportMessageFactory = MessageFactory('bioport')

from logger import setup as logger_setup
logger_setup()
del logger_setup
