"""Multiprocessing-based parallel executor implementation."""

import multiprocessing as mp
import signal
import time
from collections.abc import Callable
from typing import Literal

from py_parallelizer.executors.base import BaseParallelExecutor
from py_parallelizer.utils.logging import setup_logger

logger = setup_logger(__name__)


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
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def execute(self, **kwargs) -> tuple[list, bool]:
        keywordargs = self._format_args(**kwargs)
        total_jobs = len(keywordargs)
        self.init_pbar(total=total_jobs)
        logger.debug(
            "Creating process pool with %s workers for %s jobs",
            self.n_workers,
            total_jobs,
        )

        self.processes = []
        self.results = [None] * total_jobs
        logger.debug("Submitting tasks to process pool")
        self.processes = [
            self.pool.apply_async(self.func, kwds=kwds) for kwds in keywordargs
        ]
        logger.debug("Submitted %s tasks", len(self.processes))
        try:
            self._collect_results()
        except KeyboardInterrupt:
            self._cleanup_on_interrupt()
        else:
            self._cleanup_on_done()
        self.pbar_close()
        logger.debug(
            "Multiprocess execution done: %s results collected",
            len([r for r in self.results if r is not None]),
        )
        return self.results, self.interrupt

    def _collect_ready_results(self) -> None:
        for proc_idx, process in enumerate(self.processes):
            if process and process.ready():
                try:
                    self.results[proc_idx] = process.get(timeout=0)
                    self.processes[proc_idx] = None
                    self.pbar_update()
                except Exception:
                    pass

    def _collect_results(self) -> None:
        logger.debug("Starting result collection from processes")
        finished = False
        while not finished:
            self._collect_ready_results()
            if all(proc is None for proc in self.processes):
                finished = True
            else:
                time.sleep(0.3)
        logger.debug("Process result collection complete")

    def _cleanup_on_interrupt(self) -> None:
        logger.warning("Caught KeyboardInterrupt, collecting completed results...")
        self._collect_ready_results()
        self.interrupt = True
        for idx, _ in enumerate(self.processes):
            self.processes[idx] = None
        self.processes = []
        self._clean_pool(how="terminate")
        logger.warning("Caught KeyboardInterrupt, Exiting...")

    def _cleanup_on_done(self) -> None:
        self._clean_pool(how="close")
        logger.debug("Cleanup on done complete")

    def _clean_pool(self, how: Literal["close", "terminate"]) -> None:
        if self.pool:
            if how == "terminate":
                logger.debug("Terminating process pool")
                self.pool.terminate()
            else:
                logger.debug("Closing process pool")
                self.pool.close()
            self.pool.join()
            self.pool = None
