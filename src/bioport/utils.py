import hotshot
import hotshot.stats
import tempfile


def profile(sort='cumulative', lines=30, strip_dirs=False):
    """Profile some callable.

    This decorator uses the hotshot profiler to profile some callable (like
    a function or method) and prints the profile result on screen.

    Example usage:

    class Foo:
    
        @profile()
        def bar(self):
            ...
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
            stats.sort_stats(sort)
            stats.print_stats(lines)

            return ret
        return _inner

    return _outer


