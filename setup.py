from setuptools import setup, find_packages

version = '2.0.0'

setup(name='bioport',
      version=version,
      description="",
      long_description="""\
""",
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[], 
      keywords="",
      author="",
      author_email="",
      url="",
      license="",
      package_dir={'': 'src'},
      packages=find_packages('src'),
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
                        # Add extra requirements here
                        'collective.monkeypatcher',
                        'bioport_repository'
                        ],
      entry_points = """
      [console_scripts]
      bioport-debug = grokcore.startup:interactive_debug_prompt
      bioport-ctl = grokcore.startup:zdaemon_controller
      [paste.app_factory]
      main = grokcore.startup:application_factory
      """,
      )
