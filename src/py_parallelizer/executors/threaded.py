"""Threading-based parallel executor implementation."""

import threading
from collections.abc import Callable
from queue import Queue

from tqdm import tqdm

from py_parallelizer.base import BaseParallelExecutor, BaseWorker
from py_parallelizer.logging_utils import setup_logger

logger = setup_logger(__name__)


class ThreadWorker(BaseWorker):
    """Worker that processes tasks from a queue in a thread."""

    def __init__(
        self,
        func: Callable,
        task_queue: Queue,
        results_queue: Queue,
        stop_event: threading.Event,
        pbar: tqdm | None,
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


class ThreadedExecutor(BaseParallelExecutor):
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
        self.task_queue: Queue = Queue()
        self.results_queue: Queue = Queue()
        self.stop_event = threading.Event()
        self.threads: list[threading.Thread] = []

    def execute(self) -> tuple[list, bool]:
        """Execute tasks using thread pool."""
        logger.debug(
            f"Starting {self.n_workers} worker threads for {len(self.keywordargs)} tasks"
        )

        # Create and start worker threads
        for _ in range(self.n_workers):
            worker = ThreadWorker(
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
