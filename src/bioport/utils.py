#!/usr/bin/env python
# coding=utf8

import hotshot
import tempfile
try:
    import pstats
except ImportError:
    pstats = None  # might be missing on some Linuxes


if pstats is not None:
    def profile(sort=('time', 'calls'), lines=30, strip_dirs=False):
        """A decorator which profiles a callable.

        Example usage:

        >>> class Foo:
        ...
        ...     @profile()
        ...     def bar(self):
        ...          return "ciao"
        ... 
        >>> Foo().bar()
                 1 function calls in 0.000 CPU seconds

           Ordered by: cumulative time

           ncalls  tottime  percall  cumtime  percall filename:lineno(function)
                1    0.000    0.000    0.000    0.000 <stdin>:2(bar)
                0    0.000             0.000          profile:0(profiler)


        'ciao'
        >>> 
        """
        def _outer(f):
            def _inner(*args, **kwargs):
                #
                file = tempfile.NamedTemporaryFile()
                prof = hotshot.Profile(file.name)
                try:
                    ret = prof.runcall(f, *args, **kwargs)
                finally:
                    prof.close()

                stats = pstats.Stats(file.name)
                if strip_dirs:
                    stats.strip_dirs()
                if isinstance(sort, tuple):
                    stats.sort_stats(*sort)
                else:
                    stats.sort_stats(sort)
                stats.print_stats(lines)

                return ret
            return _inner

        return _outer



import urllib
import urlparse

def normalize_url(s, charset='utf-8'):
    """Sometimes you get an URL by a user that just isn't a real
    URL because it contains unsafe characters like ' ' and so on.  This
    function can fix some of the problems in a similar way browsers
    handle data entered by the user:

    >>> normalize_url(u'http://de.wikipedia.org/wiki/Elf (Begriffsklärung)')
    'http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29'

    :param charset: The target charset for the URL if the url was
                    given as unicode string.
    """
    if isinstance(s, unicode):
        s = s.encode(charset, 'ignore')
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
    path = urllib.quote(path, '/%')
    qs = urllib.quote_plus(qs, ':&=')
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))

