##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gerbrandy S.R.L.
# 
# This file is part of bioport.
# 
# bioport is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/gpl-3.0.html>.
##########################################################################

from setuptools import setup

version = '2.0.0'

setup(
    name='bioport',
    version=version,
    packages=['bioport'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'grok',
        'grokui.admin',
        'z3c.testsetup',
        'grokcore.startup',
        'plone.memoize',
        #                        'zope.app.cache==3.4.0',
        #        'zope.app.cache',

        'zope.app.testing',
        'zope.testbrowser',
        'megrok.chameleon',
        'z3c.batching',
        'MySQL-python',
        'sqlalchemy',
        'python-Levenshtein',
        #                        'zope.sendmail==3.5',
        'zope.sendmail',
        'captchaimage',  # This probably requires libfreetype6-dev
        'FormEncode',
        'collective.monkeypatcher',
        'bioport_repository',
        'names',
        'gerbrandyutils',
        'mobile.sniffer',
    ],

    entry_points="""
      [console_scripts]
      bioport-debug = grokcore.startup:interactive_debug_prompt
      bioport-ctl = grokcore.startup:zdaemon_controller
      [paste.app_factory]
      main = grokcore.startup:application_factory
      """,
)
