#!/usr/bin/env python

import hotshot
import hotshot.stats
import tempfile


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
            
            stats = hotshot.stats.load(file.name)
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


