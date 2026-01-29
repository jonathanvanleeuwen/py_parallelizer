"""Multiprocessing-based parallel executor implementation."""

import multiprocessing as mp
import signal
import time
from collections.abc import Callable

from py_parallelizer.base import BaseParallelExecutor
from py_parallelizer.logging_utils import setup_logger

logger = setup_logger(__name__)


class MultiprocessExecutor(BaseParallelExecutor):
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
        self.results: list = []

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
                f"Multiprocess execution completed: "
                f"{len([r for r in self.results if r is not None])} results collected"
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
