"""Tests for threaded executor."""

import threading
import time
from queue import Queue

import pytest

from py_parallelizer.executors.threaded import ThreadedExecutor, ThreadWorker


# =============================================================================
# Test helper functions (must be at module level for pickling)
# =============================================================================
def square(number: int) -> int:
    """Square a number."""
    return number ** 2


def square_with_sleep(number: int, sleep: float) -> int:
    """Square a number after sleeping."""
    time.sleep(sleep)
    return number ** 2


def double(x: int) -> int:
    """Double a number."""
    return x * 2


def failing_func(x: int) -> int:
    """Function that always raises an exception."""
    raise ValueError("Intentional test failure")


# =============================================================================
# ThreadWorker Tests
# =============================================================================
class TestThreadWorker:
    """Tests for ThreadWorker class."""

    def test_worker_processes_task(self):
        """Test that worker correctly processes a task."""
        task_queue = Queue()
        results_queue = Queue()
        stop_event = threading.Event()

        worker = ThreadWorker(
            func=square,
            task_queue=task_queue,
            results_queue=results_queue,
            stop_event=stop_event,
            pbar=None,
        )

        # Add a task and stop signal
        task_queue.put((0, {"number": 5}))
        task_queue.put(None)

        # Run worker in thread
        thread = threading.Thread(target=worker.run)
        thread.start()
        thread.join(timeout=5)

        # Check results
        result = results_queue.get()
        assert result == (0, 25)

        # Check DONE signal
        done = results_queue.get()
        assert done == "DONE"

    def test_worker_stops_on_none(self):
        """Test that worker stops when receiving None."""
        task_queue = Queue()
        results_queue = Queue()
        stop_event = threading.Event()

        worker = ThreadWorker(
            func=square,
            task_queue=task_queue,
            results_queue=results_queue,
            stop_event=stop_event,
            pbar=None,
        )

        task_queue.put(None)

        thread = threading.Thread(target=worker.run)
        thread.start()
        thread.join(timeout=2)

        assert not thread.is_alive()
        assert results_queue.get() == "DONE"

    def test_worker_stops_on_stop_event(self):
        """Test that worker stops when stop event is set."""
        task_queue = Queue()
        results_queue = Queue()
        stop_event = threading.Event()

        worker = ThreadWorker(
            func=lambda: time.sleep(10),  # Long running task
            task_queue=task_queue,
            results_queue=results_queue,
            stop_event=stop_event,
            pbar=None,
        )

        # Set stop event before adding task
        stop_event.set()
        task_queue.put((0, {}))

        thread = threading.Thread(target=worker.run)
        thread.start()
        thread.join(timeout=2)

        assert not thread.is_alive()

    def test_worker_processes_multiple_tasks(self):
        """Test that worker processes multiple tasks in order."""
        task_queue = Queue()
        results_queue = Queue()
        stop_event = threading.Event()

        worker = ThreadWorker(
            func=square,
            task_queue=task_queue,
            results_queue=results_queue,
            stop_event=stop_event,
            pbar=None,
        )

        # Add multiple tasks
        for i in range(5):
            task_queue.put((i, {"number": i}))
        task_queue.put(None)

        thread = threading.Thread(target=worker.run)
        thread.start()
        thread.join(timeout=5)

        # Collect results
        results = []
        while not results_queue.empty():
            item = results_queue.get()
            if item != "DONE":
                results.append(item)

        assert len(results) == 5
        # Results should have correct values (order may vary due to dict)
        result_values = {r[1] for r in results}
        assert result_values == {0, 1, 4, 9, 16}


# =============================================================================
# ThreadedExecutor Tests
# =============================================================================
class TestThreadedExecutor:
    """Tests for ThreadedExecutor class."""

    def test_executor_returns_correct_results(self):
        """Test that executor returns correct results in order."""
        executor = ThreadedExecutor(
            func=square,
            n_workers=2,
            results_func=None,
            verbose=False,
            number=[1, 2, 3, 4, 5],
        )

        results, interrupted = executor.execute()

        assert results == [1, 4, 9, 16, 25]
        assert interrupted is False

    def test_executor_with_multiple_args(self):
        """Test executor with multiple arguments."""
        executor = ThreadedExecutor(
            func=square_with_sleep,
            n_workers=3,
            results_func=None,
            verbose=False,
            number=[1, 2, 3],
            sleep=[0.01, 0.01, 0.01],
        )

        results, interrupted = executor.execute()

        assert results == [1, 4, 9]
        assert interrupted is False

    def test_executor_with_results_func(self):
        """Test executor applies results_func to each result."""
        executor = ThreadedExecutor(
            func=square,
            n_workers=2,
            results_func=double,
            verbose=False,
            number=[1, 2, 3],
        )

        results, interrupted = executor.execute()

        # square then double: 1->1->2, 2->4->8, 3->9->18
        assert results == [2, 8, 18]
        assert interrupted is False

    def test_executor_maintains_order(self):
        """Test that results are returned in input order."""
        executor = ThreadedExecutor(
            func=square_with_sleep,
            n_workers=5,
            results_func=None,
            verbose=False,
            # Later items finish first due to shorter sleep
            number=[1, 2, 3, 4, 5],
            sleep=[0.05, 0.04, 0.03, 0.02, 0.01],
        )

        results, interrupted = executor.execute()

        # Results should be in input order despite varying completion times
        assert results == [1, 4, 9, 16, 25]

    def test_executor_with_single_worker(self):
        """Test executor works with single worker."""
        executor = ThreadedExecutor(
            func=square,
            n_workers=1,
            results_func=None,
            verbose=False,
            number=[1, 2, 3],
        )

        results, interrupted = executor.execute()

        assert results == [1, 4, 9]

    def test_executor_with_empty_tasks(self):
        """Test executor handles empty task list."""
        executor = ThreadedExecutor(
            func=square,
            n_workers=2,
            results_func=None,
            verbose=False,
        )

        results, interrupted = executor.execute()

        assert results == []
        assert interrupted is False

    def test_executor_with_more_workers_than_tasks(self):
        """Test executor with more workers than tasks."""
        executor = ThreadedExecutor(
            func=square,
            n_workers=10,
            results_func=None,
            verbose=False,
            number=[1, 2],
        )

        results, interrupted = executor.execute()

        assert results == [1, 4]

    def test_executor_creates_progress_bar_when_verbose(self):
        """Test that progress bar is created when verbose=True."""
        executor = ThreadedExecutor(
            func=square,
            n_workers=2,
            results_func=None,
            verbose=True,
            number=[1, 2, 3],
        )

        assert executor.pbar is not None
        executor.execute()
        # pbar should be closed after execute
        assert executor.pbar.n == 3  # All tasks completed

    def test_executor_no_progress_bar_when_not_verbose(self):
        """Test that no progress bar is created when verbose=False."""
        executor = ThreadedExecutor(
            func=square,
            n_workers=2,
            results_func=None,
            verbose=False,
            number=[1, 2, 3],
        )

        assert executor.pbar is None


class TestThreadedExecutorIntegration:
    """Integration tests for ThreadedExecutor."""

    def test_concurrent_execution_is_faster(self):
        """Test that parallel execution is faster than sequential."""
        n_tasks = 5
        sleep_time = 0.1

        executor = ThreadedExecutor(
            func=square_with_sleep,
            n_workers=n_tasks,
            results_func=None,
            verbose=False,
            number=list(range(n_tasks)),
            sleep=[sleep_time] * n_tasks,
        )

        start = time.time()
        results, _ = executor.execute()
        elapsed = time.time() - start

        # Sequential would take n_tasks * sleep_time
        # Parallel should be much faster (close to sleep_time)
        sequential_time = n_tasks * sleep_time
        assert elapsed < sequential_time * 0.6  # Allow some margin
        assert results == [i**2 for i in range(n_tasks)]
