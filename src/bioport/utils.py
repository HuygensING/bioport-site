import hotshot
import hotshot.stats
import tempfile


def profile(log_file):
    """Profile some callable.

    This decorator uses the hotshot profiler to profile some callable (like
    a function or method) and prints the profile result on screen.

    Example usage:

    class Foo:
    
        @profile
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
            stats.strip_dirs()
            stats.sort_stats('cumulative')
            stats.print_stats(30)

            return ret
        return _inner

    return _outer


