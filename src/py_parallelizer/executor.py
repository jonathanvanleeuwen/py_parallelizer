"""Public API for parallel execution."""

from collections.abc import Callable

from py_parallelizer.executors.multiprocess import MultiprocessExecutor
from py_parallelizer.executors.threader import ThreadedExecutor


class ParallelExecutor:
    """
    A unified class for parallel execution using either threads or processes.

    Use `run_threaded` for I/O-bound tasks (network requests, file operations, etc.).
    Use `run_multiprocess` for CPU-bound tasks (heavy computation).

    Both methods share the same interface and return results in the same order as input.

    Examples
    --------
    Basic usage with threading:

    >>> import time
    >>> def square(number: int, sleep: float) -> int:
    ...     time.sleep(sleep)
    ...     return number ** 2
    >>> numbers = range(5)
    >>> sleep_times = [0.1] * 5
    >>> results, interrupted = ParallelExecutor(square).run_threaded(
    ...     number=numbers, sleep=sleep_times
    ... )

    Using multiprocessing for CPU-bound tasks:

    >>> results, interrupted = ParallelExecutor(square).run_multiprocess(
    ...     number=numbers, sleep=sleep_times
    ... )

    With a results processing function:

    >>> import math
    >>> results, interrupted = ParallelExecutor(
    ...     square, results_func=math.sqrt, n_workers=4, verbose=False
    ... ).run_threaded(number=numbers, sleep=sleep_times)
    """

    def __init__(
        self,
        func: Callable,
        n_workers: int | None = None,
        verbose: bool = True,
    ):
        """
        Initialize the ParallelExecutor with common configuration.

        Parameters
        ----------
        func : Callable
            The function to execute for each set of arguments.
        n_workers : int | None, optional
            Number of workers (threads/processes) to use. Defaults to CPU count - 1.
        results_func : Callable | None, optional
            Optional function to process each result in the main thread/process.
        verbose : bool, optional
            Whether to show progress bar. Defaults to True.
        """
        self.func = func
        self.n_workers = n_workers
        self.verbose = verbose

    def run_threaded(self, **kwargs) -> tuple[list, bool]:
        """
        Run the function in parallel using threads.

        Best suited for I/O-bound tasks (network requests, file operations, etc.).
        For CPU-bound tasks, use run_multiprocess instead.

        Parameters
        ----------
        **kwargs
            Keyword arguments where each value is a list/iterable of the same length.
            Each combination of arguments at the same index will be passed to the function.

        Returns
        -------
        tuple[list, bool]
            A tuple containing:
            - results: List of results in the same order as input arguments.
              Incomplete results are None if interrupted.
            - interrupted: True if execution was interrupted by KeyboardInterrupt.
        """
        executor = ThreadedExecutor(
            func=self.func,
            n_workers=self.n_workers,
            verbose=self.verbose,
            **kwargs,
        )
        return executor.execute()

    def run_multiprocess(self, **kwargs) -> tuple[list, bool]:
        """
        Run the function in parallel using multiprocessing.

        Best suited for CPU-bound tasks (heavy computation).
        For I/O-bound tasks, use run_threaded instead.

        Note
        ----
        Use `if __name__ == "__main__":` when calling from a script,
        to avoid recursive spawning of subprocesses on Windows.

        Parameters
        ----------
        **kwargs
            Keyword arguments where each value is a list/iterable of the same length.
            Each combination of arguments at the same index will be passed to the function.

        Returns
        -------
        tuple[list, bool]
            A tuple containing:
            - results: List of results in the same order as input arguments.
              Incomplete results are None if interrupted.
            - interrupted: True if execution was interrupted by KeyboardInterrupt.
        """
        executor = MultiprocessExecutor(
            func=self.func,
            n_workers=self.n_workers,
            verbose=self.verbose,
            **kwargs,
        )
        return executor.execute()
