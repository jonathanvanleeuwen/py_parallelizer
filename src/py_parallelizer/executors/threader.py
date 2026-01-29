"""Threading-based parallel executor implementation."""

import threading
from collections.abc import Callable
from queue import Queue

from py_parallelizer.executors.base import BaseParallelExecutor
from py_parallelizer.utils.logging import setup_logger

logger = setup_logger(__name__)


class ThreadedExecutor(BaseParallelExecutor):
    """Executor that uses threading for parallel execution."""

    def __init__(
        self,
        func: Callable,
        n_workers: int | None = None,
        verbose: bool = True,
        pbar_color: str = "blue",
    ) -> None:
        super().__init__(
            func=func,
            n_workers=n_workers,
            pbar_color=pbar_color,
            verbose=verbose,
        )
        self.task_queue: Queue = Queue()
        self.results_queue: Queue = Queue()
        self.stop_event = threading.Event()
        self.threads: list[threading.Thread] = []
        self.results: list = []
        self.pbar_desc = f"Running code in threads [{self.n_workers} workers]"

    def _worker(self) -> None:
        """Worker function that processes tasks from the queue."""
        thread_name = threading.current_thread().name
        logger.debug(f"[{thread_name}] Worker started")
        while True:
            item = self.task_queue.get()
            if item is None or self.stop_event.is_set():
                logger.debug(f"[{thread_name}] Worker stopping")
                self.results_queue.put("DONE")
                break
            try:
                idx, kwds = item
                logger.debug(f"[{thread_name}] Processing task {idx}")
                result = self.func(**kwds)
                self.results_queue.put((idx, result))
            except Exception as e:
                logger.error(f"[{thread_name}] Failed processing task {idx}: {e}")
                self.results_queue.put((idx, None))

    def execute(self, **kwargs) -> tuple[list, bool]:
        """Execute tasks using thread pool."""
        keywordargs = self._format_args(**kwargs)
        total_jobs = len(keywordargs)
        self.init_pbar(total=total_jobs)
        logger.debug(f"Starting {self.n_workers} worker threads for {total_jobs} jobs")

        # Pre-allocate results array to collect partial results on interrupt
        self.threads = []
        self.results = [None] * total_jobs

        # Create and start worker threads
        for _ in range(self.n_workers):
            thread = threading.Thread(target=self._worker)
            thread.start()
            self.threads.append(thread)

        # Push tasks to queue with index for ordering
        logger.debug(f"Enqueuing {total_jobs} tasks")
        for idx, kwds in enumerate(keywordargs):
            self.task_queue.put((idx, kwds))

        # Signal workers to stop when done
        logger.debug("Sending stop signals to workers")
        # The reason we send n = n_workers None sentinels is to ensure that
        # all threads can exit once the tasks are done.
        # This ensures that each thread will eventually get a None to break its loop.
        for _ in range(self.n_workers):
            self.task_queue.put(None)

        try:
            self._collect_results()
        except KeyboardInterrupt:
            self._cleanup_on_interrupt()
        else:
            self._cleanup_on_done()
        self.pbar_close()
        logger.debug(
            f"Threaded execution done: "
            f"{len([result for result in self.results if result is not None])} results collected"
        )
        return self.results, self.interrupt

    def _collect_ready_results(self) -> None:
        """Collect any available results from the queue."""
        while not self.results_queue.empty():
            try:
                result = self.results_queue.get_nowait()
                if not (isinstance(result, str) and result == "DONE"):
                    idx, value = result
                    self.results[idx] = value
                    self.pbar_update()
            except Exception:
                break

    def _collect_results(self) -> None:
        """Collect results from worker threads, maintaining order."""
        logger.debug("Starting result collection")
        finished_workers = 0
        while finished_workers < self.n_workers:
            result = self.results_queue.get()
            if isinstance(result, str) and result == "DONE":
                finished_workers += 1
                logger.debug(f"Worker finished ({finished_workers}/{self.n_workers})")
            else:
                idx, value = result
                self.results[idx] = value
                self.pbar_update()
        logger.debug("Result collection complete")

    def _cleanup_on_interrupt(self) -> None:
        """Clean up resources on keyboard interrupt."""
        logger.warning("Caught KeyboardInterrupt, collecting completed results...")
        self._collect_ready_results()
        self.interrupt = True
        self.stop_event.set()
        self._drain_task_queue()
        self._wait_for_threads()
        logger.warning("Caught KeyboardInterrupt, Exiting...")

    def _cleanup_on_done(self) -> None:
        """Clean up resources when done."""
        self._wait_for_threads()
        logger.debug("Cleanup on done complete")

    def _drain_task_queue(self) -> None:
        """Drain the task queue and push None sentinels to unblock waiting threads."""
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

    def _wait_for_threads(self) -> None:
        logger.debug("Waiting for all threads to complete")
        for thread in self.threads:
            thread.join()
        self.threads = []
