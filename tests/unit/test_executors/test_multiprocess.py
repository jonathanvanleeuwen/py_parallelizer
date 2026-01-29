"""Tests for multiprocess executor."""

import time

from py_parallelizer.executors.multiprocess import MultiprocessExecutor


# =============================================================================
# Test helper functions (must be at module level for pickling)
# =============================================================================
def square(number: int) -> int:
    """Square a number."""
    return number**2


def square_with_sleep(number: int, sleep: float) -> int:
    """Square a number after sleeping."""
    time.sleep(sleep)
    return number**2


def double(x: int) -> int:
    """Double a number."""
    return x * 2


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


# =============================================================================
# MultiprocessExecutor Tests
# =============================================================================
class TestMultiprocessExecutor:
    """Tests for MultiprocessExecutor class."""

    def test_executor_returns_correct_results(self):
        """Test that executor returns correct results in order."""
        executor = MultiprocessExecutor(
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
        executor = MultiprocessExecutor(
            func=add,
            n_workers=2,
            results_func=None,
            verbose=False,
            a=[1, 2, 3],
            b=[10, 20, 30],
        )

        results, interrupted = executor.execute()

        assert results == [11, 22, 33]
        assert interrupted is False

    def test_executor_with_results_func(self):
        """Test executor applies results_func to each result."""
        executor = MultiprocessExecutor(
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
        executor = MultiprocessExecutor(
            func=square_with_sleep,
            n_workers=4,
            results_func=None,
            verbose=False,
            # Later items finish first due to shorter sleep
            number=[1, 2, 3, 4],
            sleep=[0.1, 0.08, 0.06, 0.04],
        )

        results, interrupted = executor.execute()

        # Results should be in input order despite varying completion times
        assert results == [1, 4, 9, 16]

    def test_executor_with_single_worker(self):
        """Test executor works with single worker."""
        executor = MultiprocessExecutor(
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
        executor = MultiprocessExecutor(
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
        executor = MultiprocessExecutor(
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
        executor = MultiprocessExecutor(
            func=square,
            n_workers=2,
            results_func=None,
            verbose=True,
            number=[1, 2, 3],
        )

        assert executor.pbar is not None
        executor.execute()

    def test_executor_no_progress_bar_when_not_verbose(self):
        """Test that no progress bar is created when verbose=False."""
        executor = MultiprocessExecutor(
            func=square,
            n_workers=2,
            results_func=None,
            verbose=False,
            number=[1, 2, 3],
        )

        assert executor.pbar is None
