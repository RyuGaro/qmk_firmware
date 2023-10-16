"""Utility functions.
"""
import contextlib
import functools
import multiprocessing

from milc import cli


@contextlib.contextmanager
def parallelize():
    """Returns a function that can be used in place of a map() call.

    Attempts to use `mpire`, falling back to `multiprocessing` if it's not
    available. If parallelization is not requested, returns the original map()
    function.
    """

    # Work out if we've already got a config value for parallel searching
    if cli.config.user.parallel_search is None:
        parallel_search = True
    else:
        parallel_search = cli.config.user.parallel_search

    # Non-parallel searches use `map()`
    if not parallel_search:
        yield map
        return

    # Prefer mpire's `WorkerPool` if it's available
    with contextlib.suppress(ImportError):
        from mpire import WorkerPool
        with WorkerPool() as pool:
            yield functools.partial(pool.imap_unordered, progress_bar=True)
        return

    # Otherwise fall back to multiprocessing's `Pool`
    with multiprocessing.Pool() as pool:
        yield pool.imap_unordered


def parallel_map(*args, **kwargs):
    """Effectively runs `map()` but executes it in parallel if necessary.
    """
    with parallelize() as map_fn:
        # This needs to be enclosed in a `list()` as some implementations return
        # a generator function, which means the scope of the pool is closed off
        # before the results are returned. Returning a list ensures results are
        # materialised before any worker pool is shut down.
        return list(map_fn(*args, **kwargs))
