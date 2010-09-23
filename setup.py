from setuptools import setup, find_packages

version = '2.0.0'

setup(name='bioport',
      version=version,
      packages=['bioport'],
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        'grok',
                        'grokui.admin',
                        'z3c.testsetup',
                        'grokcore.startup',
                        'plone.memoize==1.0.4',
                        'zope.app.cache==3.4.0',
                        'megrok.chameleon',
                        'z3c.batching',
                        'MySQL-python',
                        'sqlalchemy',
                        'python-Levenshtein',
                        'zope.sendmail==3.5',
                        'captchaimage', # This probably requires libfreetype-dev
                        'FormEncode',
                        'collective.monkeypatcher',
                        'bioport_repository',
                        'names',
                        'gerbrandyutils',
                        ],
      entry_points = """
      [console_scripts]
      bioport-debug = grokcore.startup:interactive_debug_prompt
      bioport-ctl = grokcore.startup:zdaemon_controller
      [paste.app_factory]
      main = grokcore.startup:application_factory
      """,
      )
