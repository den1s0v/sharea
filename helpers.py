from contextlib import contextmanager
from timeit import default_timer as timer


class Checkpointer:
    """
    Measures time between hits.
    Dev tip: requires the `from timeit import default_timer as timer`
    """

    def __init__(self):
        self.first = timer()
        self.last = self.first

    def reset_now(self):
        self.__init__()

    def hit(self, label=None) -> float:
        now = timer()
        delta = now - self.last
        if label:
            print((label or 'Checkpoint') + ':', "%.4f" % delta, 's')
        self.last = now
        return delta

    def since_start(self, label=None, hit=False) -> float:
        now = timer()
        delta = now - self.first
        if label:
            print(label or 'Total:', "%.4f" % delta, 's')
        if hit:
            self.last = now
        return delta


@contextmanager
def duration_report(label: str = '', report_on_start = True):
    if report_on_start:
        print(f'Starting {label} ...')
    start_time = timer()
    try:
        yield
    finally:
        delta = timer() - start_time
        print(f'Finished {label} in', "%.4f" % delta, 's')
        print()
