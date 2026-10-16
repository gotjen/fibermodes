
from .simulator import Simulator
import multiprocessing
from functools import partial
import os


def _context():
    # fork() is unsafe in a multi-threaded process (the GUI runs the
    # simulator in a QThread), and Python 3.12+ warns about it. forkserver
    # starts the workers from a single-threaded server process; it is the
    # default on Linux since Python 3.14. spawn is used where forkserver
    # is not available (Windows).
    methods = multiprocessing.get_all_start_methods()
    method = "forkserver" if "forkserver" in methods else "spawn"
    return multiprocessing.get_context(method)


#: Multiprocessing context used to start the pool workers.
MP_CONTEXT = _context()


def applyf(fsim, name):
    fct = getattr(fsim, name)
    return fct(), fsim.__self__._fiber.ne_cache


class PSimulator(Simulator):

    def __init__(self, *args, **kwargs):
        self.pool = None
        self.numProcs = kwargs.pop("processes", 0) or os.cpu_count()

        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        def wrapper():
            if self.pool is not None:
                self.terminate()
            self.pool = MP_CONTEXT.Pool(self.numProcs)

            r = self.pool.imap(partial(applyf, name=name), self._fsims)
            for i, (res, ne_cache) in enumerate(r):
                self.fibers[i].ne_cache = ne_cache
                yield res
            self.pool.close()
            self.pool.join()
            self.pool = None

        return wrapper

    def terminate(self):
        if self.pool is not None:
            self.pool.terminate()
            self.pool.join()
            self.pool = None
