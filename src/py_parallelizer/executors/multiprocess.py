"""Multiprocessing-based parallel executor implementation."""

import multiprocessing as mp
import signal
import time
from collections.abc import Callable
from typing import Literal

from py_parallelizer.executors.base import BaseParallelExecutor
from py_parallelizer.utils.logging import setup_logger

logger = setup_logger(__name__)
# logger.setLevel("DEBUG")


class MultiprocessExecutor(BaseParallelExecutor):
    """Executor that uses multiprocessing for parallel execution."""

    def __init__(
        self,
        func: Callable,
        n_workers: int | None = None,
        verbose: bool = True,
        pbar_color: str = "red",
    ) -> None:
        super().__init__(
            func=func,
            n_workers=n_workers,
            pbar_color=pbar_color,
            verbose=verbose,
        )
        self.pool: mp.Pool = mp.Pool(self.n_workers, self._init_worker)
        self.processes: list = []
        self.results: list = []
        self.pbar_desc = f"Running code in parallel [{self.n_workers} workers]"

    @staticmethod
    def _init_worker() -> None:
        """Initialize worker process to ignore SIGINT."""
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def execute(self, **kwargs) -> tuple[list, bool]:
        """Execute tasks using process pool."""
        keywordargs = self._format_args(**kwargs)
        total_jobs = len(keywordargs)
        self.init_pbar(total=total_jobs)
        logger.debug(f"Creating process pool with {self.n_workers} workers for {total_jobs} jobs")

        # Pre-allocate results array to collect partial results on interrupt
        self.processes = []
        self.results = [None] * total_jobs
        logger.debug("Submitting tasks to process pool")
        self.processes = [self.pool.apply_async(self.func, kwds=kwds) for kwds in keywordargs]
        logger.debug(f"Submitted {len(self.processes)} tasks")
        try:
            self._collect_results()
        except KeyboardInterrupt:
            self._cleanup_on_interrupt()
        else:
            self._cleanup_on_done()
        self.pbar_close()
        logger.debug(
            f"Multiprocess execution done: "
            f"{len([result for result in self.results if result is not None])} results collected"
        )
        return self.results, self.interrupt

    def _collect_ready_results(self) -> None:
        """Collect results from any processes that have already finished."""
        for proc_idx, process in enumerate(self.processes):
            if process and process.ready():
                try:
                    self.results[proc_idx] = process.get(timeout=0)
                    self.processes[proc_idx] = None
                    self.pbar_update()
                except Exception:
                    pass  # Process may have failed, leave as None

    def _collect_results(self) -> None:
        """Collect results from worker processes, maintaining order."""
        logger.debug("Starting result collection from processes")
        finished = False
        while not finished:
            self._collect_ready_results()
            if all(proc is None for proc in self.processes):
                finished = True
            else:
                time.sleep(0.3)
        logger.debug(f"Process result collection complete")

    def _cleanup_on_interrupt(self) -> None:
        """Clean up resources on keyboard interrupt."""
        logger.warning("Caught KeyboardInterrupt, collecting completed results...")
        self._collect_ready_results()
        self.interrupt = True
        for idx, _ in enumerate(self.processes):
            self.processes[idx] = None
        self.processes = []
        self._clean_pool(how="terminate")
        logger.warning("Caught KeyboardInterrupt, Exiting...")

    def _cleanup_on_done(self) -> None:
        """Clean up resources when done."""
        self._clean_pool(how="close")
        logger.debug("Cleanup on done complete")

    def _clean_pool(self, how: Literal["close", "terminate"]) -> None:
        """Clean up the process pool."""
        if self.pool:
            if how == "terminate":
                logger.debug("Terminating process pool")
                self.pool.terminate()
            else:
                logger.debug("Closing process pool")
                self.pool.close()
            self.pool.join()
            self.pool = None