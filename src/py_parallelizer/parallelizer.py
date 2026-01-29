import logging
import multiprocessing as mp
import signal
import threading
import time
from abc import ABC, abstractmethod
from queue import Queue
from typing import Callable

import psutil
from tqdm import tqdm

logger = logging.getLogger(__name__)


class TqdmLoggingHandler(logging.Handler):
    """
    Setup logging handler class for the progressbar to work with logging module
    """

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


logger.addHandler(TqdmLoggingHandler())


# =============================================================================
# Base Classes
# =============================================================================
class _BaseWorker(ABC):
    """Abstract base class for worker implementations."""

    @abstractmethod
    def run(self) -> None:
        """Execute the worker loop."""
        pass


class _BaseParallelExecutor(ABC):
    """
    Abstract base class for parallel execution strategies.

    Handles common setup like argument formatting, worker count, and progress bar.
    """

    def __init__(
        self,
        func: Callable,
        n_workers: int | None,
        results_func: Callable | None,
        pbar_colour: str,
        pbar_desc_template: str,
        verbose: bool = True,
        **kwargs,
    ):
        self.func = func
        self.results_func = results_func
        self.n_workers = self._get_worker_count(n_workers)
        self.keywordargs = self._format_args(**kwargs)
        self.interrupt = False
        self.verbose = verbose

        if self.verbose:
            self.pbar = tqdm(
                desc=pbar_desc_template.format(n_workers=self.n_workers),
                total=len(self.keywordargs),
                leave=True,
                position=0,
                colour=pbar_colour,
            )
        else:
            self.pbar = None

        logger.debug(
            f"{self.__class__.__name__} processing [{func.__name__}] "
            f"using [{self.n_workers}] workers..."
        )

    @staticmethod
    def _get_worker_count(n_workers: int | None) -> int:
        """Get the number of workers to use, defaulting to CPU count - 1."""
        if n_workers is None:
            cpu_count = psutil.cpu_count()
            n_workers = max(cpu_count - 1, 1)
            logger.debug(
                f"Auto-detected worker count: {n_workers} (CPU count: {cpu_count})"
            )
        return int(n_workers)

    @staticmethod
    def _format_args(**kwargs) -> list[dict]:
        """Convert keyword arguments into a list of dicts for each task."""
        kwds = []
        arguments = list(kwargs.keys())
        for _, args in enumerate(zip(*kwargs.values(), strict=True)):
            kwds.append({arg: args[arg_idx] for arg_idx, arg in enumerate(arguments)})
        return kwds

    @abstractmethod
    def execute(self) -> tuple[list, bool]:
        """Execute the parallel processing and return (results, interrupted)."""
        pass

    def _apply_results_func(self, value):
        """Apply results_func if provided, otherwise return value as-is."""
        if self.results_func:
            return self.results_func(value)
        return value


# =============================================================================
# Threading Implementation
# =============================================================================
class _ThreadWorker(_BaseWorker):
    """Worker that processes tasks from a queue in a thread."""

    def __init__(
        self,
        func: Callable,
        task_queue: Queue,
        results_queue: Queue,
        stop_event: threading.Event,
        pbar: tqdm,
    ):
        self.func = func
        self.task_queue = task_queue
        self.results_queue = results_queue
        self.stop_event = stop_event
        self.pbar = pbar

    def run(self) -> None:
        """Process tasks until None is received or stop event is set."""
        thread_name = threading.current_thread().name
        logger.debug(f"[{thread_name}] Worker started")
        tasks_processed = 0
        while True:
            item = self.task_queue.get()
            if item is None or self.stop_event.is_set():
                logger.debug(
                    f"[{thread_name}] Worker stopping (processed {tasks_processed} tasks)"
                )
                self.results_queue.put("DONE")
                break
            try:
                idx, kwds = item  # Unpack index and kwargs
                logger.debug(f"[{thread_name}] Processing task {idx}")
                result = self.func(**kwds)
                self.results_queue.put((idx, result))  # Return with index for ordering
                tasks_processed += 1
                if self.pbar:
                    self.pbar.update(1)
            except Exception as e:
                logger.error(f"[{thread_name}] Failed processing task {idx}: {e}")
                raise


class _ThreadedExecutor(_BaseParallelExecutor):
    """Executor that uses threading for parallel execution."""

    def __init__(
        self,
        func: Callable,
        n_workers: int | None,
        results_func: Callable | None,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            func=func,
            n_workers=n_workers,
            results_func=results_func,
            pbar_colour="blue",
            pbar_desc_template="Running code in threads [{n_workers} threads]",
            verbose=verbose,
            **kwargs,
        )
        self.task_queue = Queue()
        self.results_queue = Queue()
        self.stop_event = threading.Event()
        self.threads: list[threading.Thread] = []

    def execute(self) -> tuple[list, bool]:
        """Execute tasks using thread pool."""
        logger.debug(
            f"Starting {self.n_workers} worker threads for {len(self.keywordargs)} tasks"
        )

        # Create and start worker threads
        for _ in range(self.n_workers):
            worker = _ThreadWorker(
                func=self.func,
                task_queue=self.task_queue,
                results_queue=self.results_queue,
                stop_event=self.stop_event,
                pbar=self.pbar,
            )
            thread = threading.Thread(target=worker.run)
            thread.start()
            self.threads.append(thread)

        # Push tasks to queue with index for ordering
        logger.debug(f"Enqueuing {len(self.keywordargs)} tasks")
        for idx, kwds in enumerate(self.keywordargs):
            self.task_queue.put((idx, kwds))

        # Signal workers to stop when done
        logger.debug("Sending stop signals to workers")
        for _ in range(self.n_workers):
            self.task_queue.put(None)

        # Collect results
        results = self._collect_results()

        # Handle interrupt cleanup
        if self.interrupt:
            logger.warning("Caught KeyboardInterrupt, terminating workers...")
            self.stop_event.set()
            self._drain_task_queue()

        # Wait for all threads to finish
        logger.debug("Waiting for all threads to complete")
        for thread in self.threads:
            thread.join()
        logger.debug("All threads completed")

        if self.pbar:
            self.pbar.close()

        if self.interrupt:
            logger.warning("Caught KeyboardInterrupt, Exiting...")
        else:
            logger.debug(
                f"Threaded execution completed: {len([r for r in results if r is not None])} results collected"
            )

        return results, self.interrupt

    def _collect_results(self) -> list:
        """Collect results from worker threads, maintaining order."""
        logger.debug("Starting result collection")
        results = [None] * len(self.keywordargs)
        finished_workers = 0
        results_collected = 0
        try:
            while finished_workers < self.n_workers:
                result = self.results_queue.get()
                if isinstance(result, str) and result == "DONE":
                    finished_workers += 1
                    logger.debug(
                        f"Worker finished ({finished_workers}/{self.n_workers})"
                    )
                else:
                    idx, value = result
                    results[idx] = self._apply_results_func(value)
                    results_collected += 1
        except KeyboardInterrupt:
            logger.warning("Caught KeyboardInterrupt, stopping workers...")
            self.interrupt = True
            # Drain any results already in the queue before returning
            self._drain_results_to(results)
            results_collected = len([r for r in results if r is not None])
        logger.debug(f"Result collection complete: {results_collected} results")
        return results

    def _drain_results_to(self, results: list) -> None:
        """Drain any available results from the queue into the results list."""
        drained = 0
        while not self.results_queue.empty():
            try:
                result = self.results_queue.get_nowait()
                if not (isinstance(result, str) and result == "DONE"):
                    idx, value = result
                    results[idx] = self._apply_results_func(value)
                    drained += 1
            except Exception:
                break
        logger.debug(f"Drained {drained} results from queue")

    def _drain_task_queue(self) -> None:
        """Drain the task queue and push None sentinels to unblock waiting threads."""
        # First drain remaining tasks
        drained_count = 0
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
                drained_count += 1
            except Exception:
                pass
        logger.debug(f"Drained {drained_count} tasks from queue")
        # Push None for each thread to unblock them from task_queue.get()
        logger.debug(f"Sending {self.n_workers} stop sentinels")
        for _ in range(self.n_workers):
            self.task_queue.put(None)


# =============================================================================
# Multiprocessing Implementation
# =============================================================================
class _MultiprocessExecutor(_BaseParallelExecutor):
    """Executor that uses multiprocessing for parallel execution."""

    def __init__(
        self,
        func: Callable,
        n_workers: int | None,
        results_func: Callable | None,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            func=func,
            n_workers=n_workers,
            results_func=results_func,
            pbar_colour="red",
            pbar_desc_template="Running code in parallel [{n_workers} cores]",
            verbose=verbose,
            **kwargs,
        )
        self.pool: mp.Pool | None = None
        self.processes: list = []

    @staticmethod
    def _init_worker() -> None:
        """Initialize worker process to ignore SIGINT."""
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def execute(self) -> tuple[list, bool]:
        """Execute tasks using process pool."""
        logger.debug(
            f"Creating process pool with {self.n_workers} workers for {len(self.keywordargs)} tasks"
        )
        self.pool = mp.Pool(self.n_workers, self._init_worker)
        # Pre-allocate results array to collect partial results on interrupt
        self.results = [None] * len(self.keywordargs)

        def _pbar_callback(_):
            if self.pbar:
                self.pbar.update(1)

        logger.debug("Submitting tasks to process pool")
        self.processes = [
            self.pool.apply_async(self.func, kwds=kwds, callback=_pbar_callback)
            for kwds in self.keywordargs
        ]
        logger.debug(f"Submitted {len(self.processes)} async tasks")

        try:
            self._collect_results()
        except KeyboardInterrupt:
            logger.warning("Caught KeyboardInterrupt, collecting completed results...")
            # Collect any already-finished results before cleanup
            self._collect_ready_results()
            self._cleanup_on_interrupt()
            logger.warning("Caught KeyboardInterrupt, Exiting...")
            self.interrupt = True
        else:
            logger.debug("Closing process pool")
            self.pool.close()
            self.pool.join()
            self.pool = None
            logger.debug(
                f"Multiprocess execution completed: {len([r for r in self.results if r is not None])} results collected"
            )
            if self.pbar:
                self.pbar.close()

        return self.results, self.interrupt

    def _collect_ready_results(self) -> None:
        """Collect results from any processes that have already finished."""
        for proc_idx, process in enumerate(self.processes):
            if process and process.ready():
                try:
                    res = process.get(timeout=0)
                    self.results[proc_idx] = self._apply_results_func(res)
                except Exception:
                    pass  # Process may have failed, leave as None

    def _collect_results(self) -> None:
        """Collect results from worker processes, maintaining order."""
        logger.debug("Starting result collection from processes")
        finished = False
        poll_count = 0
        while not finished:
            ready_count = 0
            for proc_idx, process in enumerate(self.processes):
                if process:
                    if process.ready():
                        res = process.get()
                        self.results[proc_idx] = self._apply_results_func(res)
                        self.processes[proc_idx] = None
                        ready_count += 1
            if ready_count > 0:
                completed = len([r for r in self.results if r is not None])
                logger.debug(
                    f"Collected {ready_count} results (total: {completed}/{len(self.results)})"
                )
            if not [proc for proc in self.processes if proc]:
                finished = True
            else:
                poll_count += 1
                time.sleep(0.5)
        logger.debug(f"Process result collection complete (polled {poll_count} times)")

    def _cleanup_on_interrupt(self) -> None:
        """Clean up resources on keyboard interrupt."""
        logger.debug("Cleaning up after interrupt")
        for idx, _ in enumerate(self.processes):
            self.processes[idx] = None
        self.processes = []
        if self.pool:
            logger.debug("Terminating process pool")
            self.pool.terminate()
            self.pool.join()
            self.pool = None
        if self.pbar:
            self.pbar.close()
        logger.debug("Cleanup complete")


# =============================================================================
# Public API - Facade
# =============================================================================
class ParallelExecutor:
    """
    A unified class for parallel execution using either threads or processes.

    Use `run_threaded` for I/O-bound tasks (network requests, file operations, etc.).
    Use `run_multiprocess` for CPU-bound tasks (heavy computation).

    Both methods share the same interface and return results in the same order as input.

    A simple example:
    -----------------
    import math

    def test_square(number: int, sleep: int) -> int:
        time.sleep(sleep)
        return number**2

    def test_sqrt(number: int) -> float:
        return math.sqrt(number)

    numbers_to_square = range(10)
    sleep = [2] * len(numbers_to_square)

    # Using threads (I/O-bound)
    res, interrupt = ParallelExecutor(test_square).run_threaded(number=numbers_to_square, sleep=sleep)

    # Using processes (CPU-bound)
    res, interrupt = ParallelExecutor(test_square).run_multiprocess(number=numbers_to_square, sleep=sleep)

    # With results function and custom settings
    res_sqrt, interrupt = ParallelExecutor(
        test_square, results_func=test_sqrt, n_workers=4, verbose=False
    ).run_threaded(number=numbers_to_square, sleep=sleep)
    """

    def __init__(
        self,
        func: Callable,
        n_workers: int | None = None,
        results_func: Callable | None = None,
        verbose: bool = True,
    ):
        """
        Initialize the ParallelExecutor with common configuration.

        Parameters:
        -----------
        func : callable
            The function to execute for each set of arguments.
        n_workers : int | None
            Number of workers (threads/processes) to use. Defaults to CPU count - 1.
        results_func : callable | None
            Optional function to process each result in the main thread/process.
        verbose : bool
            Whether to show progress bar. Defaults to True.
        """
        self.func = func
        self.n_workers = n_workers
        self.results_func = results_func
        self.verbose = verbose

    def run_threaded(self, **kwargs) -> tuple[list, bool]:
        """
        Run the function in parallel using threads.

        Best suited for I/O-bound tasks (network requests, file operations, etc.).
        For CPU-bound tasks, use run_multiprocess instead.

        Parameters:
        -----------
        **kwargs
            Keyword arguments where each value is a list/iterable of the same length.

        Returns:
        --------
        tuple[list, bool]
            (results, interrupt) - Results in input order, and whether interrupted.
        """
        executor = _ThreadedExecutor(
            func=self.func,
            n_workers=self.n_workers,
            results_func=self.results_func,
            verbose=self.verbose,
            **kwargs,
        )
        return executor.execute()

    def run_multiprocess(self, **kwargs) -> tuple[list, bool]:
        """
        Run the function in parallel using multiprocessing.

        Best suited for CPU-bound tasks (heavy computation).
        For I/O-bound tasks, use run_threaded instead.

        NOTE: Use if __name__ == "__main__": when calling from a script,
        to avoid recursive spawning of subprocesses on Windows.

        Parameters:
        -----------
        **kwargs
            Keyword arguments where each value is a list/iterable of the same length.

        Returns:
        --------
        tuple[list, bool]
            (results, interrupt) - Results in input order, and whether interrupted.
        """
        executor = _MultiprocessExecutor(
            func=self.func,
            n_workers=self.n_workers,
            results_func=self.results_func,
            verbose=self.verbose,
            **kwargs,
        )
        return executor.execute()
