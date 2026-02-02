"""Public API for parallel execution."""

from collections.abc import Callable

from py_parallelizer.executors.multiprocess import MultiprocessExecutor
from py_parallelizer.executors.threader import ThreadedExecutor


class ParallelExecutor:
    """
    Unified interface for parallel execution using threads or processes.

    Use `run_threaded` for I/O-bound tasks, `run_multiprocess` for CPU-bound tasks.
    """

    def __init__(
        self,
        func: Callable,
        n_workers: int | None = None,
        results_func=None,
        verbose: bool = True,
    ) -> None:
        self.func = func
        self.n_workers = n_workers
        self.results_func = results_func
        self.verbose = verbose

    def run_threaded(self, **kwargs) -> tuple[list, bool]:
        """Run the function in parallel using threads.
        **kwargs
          Keyword arguments where each value is a list/iterable of the same length.
          Each combination of arguments at the same index will be passed to the function.
        """
        executor = ThreadedExecutor(
            func=self.func,
            n_workers=self.n_workers,
            verbose=self.verbose,
        )
        return executor.execute(**kwargs)

    def run_multiprocess(self, **kwargs) -> tuple[list, bool]:
        """Run the function in parallel using multiprocessing.
        **kwargs
          Keyword arguments where each value is a list/iterable of the same length.
          Each combination of arguments at the same index will be passed to the function.
        """
        executor = MultiprocessExecutor(
            func=self.func,
            n_workers=self.n_workers,
            verbose=self.verbose,
        )
        return executor.execute(**kwargs)
