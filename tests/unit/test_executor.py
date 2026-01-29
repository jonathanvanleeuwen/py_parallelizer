"""Tests for ParallelExecutor public API."""

import math
import time

from py_parallelizer import ParallelExecutor


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


def sqrt(number: int) -> float:
    """Calculate square root."""
    return math.sqrt(number)


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


# =============================================================================
# ParallelExecutor Initialization Tests
# =============================================================================
class TestParallelExecutorInit:
    """Tests for ParallelExecutor initialization."""

    def test_init_with_func_only(self):
        """Test initialization with just a function."""
        executor = ParallelExecutor(square)

        assert executor.func == square
        assert executor.n_workers is None
        assert executor.results_func is None
        assert executor.verbose is True

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        executor = ParallelExecutor(
            func=square,
            n_workers=4,
            results_func=sqrt,
            verbose=False,
        )

        assert executor.func == square
        assert executor.n_workers == 4
        assert executor.results_func == sqrt
        assert executor.verbose is False


# =============================================================================
# run_threaded Tests
# =============================================================================
class TestRunThreaded:
    """Tests for run_threaded method."""

    def test_basic_execution(self):
        """Test basic threaded execution."""
        results, interrupted = ParallelExecutor(square).run_threaded(
            number=[1, 2, 3, 4, 5]
        )

        assert results == [1, 4, 9, 16, 25]
        assert interrupted is False

    def test_with_multiple_args(self):
        """Test threaded execution with multiple arguments."""
        results, interrupted = ParallelExecutor(add, verbose=False).run_threaded(
            a=[1, 2, 3],
            b=[10, 20, 30],
        )

        assert results == [11, 22, 33]
        assert interrupted is False

    def test_with_results_func(self):
        """Test threaded execution with results function."""
        results, interrupted = ParallelExecutor(
            square, results_func=sqrt, verbose=False
        ).run_threaded(number=[1, 2, 3, 4])

        # square then sqrt: 1->1->1, 2->4->2, 3->9->3, 4->16->4
        assert results == [1.0, 2.0, 3.0, 4.0]
        assert interrupted is False

    def test_with_custom_worker_count(self):
        """Test threaded execution with custom worker count."""
        results, interrupted = ParallelExecutor(
            square, n_workers=2, verbose=False
        ).run_threaded(number=[1, 2, 3])

        assert results == [1, 4, 9]

    def test_maintains_order(self):
        """Test that results maintain input order."""
        results, interrupted = ParallelExecutor(
            square_with_sleep, n_workers=5, verbose=False
        ).run_threaded(
            number=[5, 4, 3, 2, 1],
            sleep=[0.05, 0.04, 0.03, 0.02, 0.01],
        )

        assert results == [25, 16, 9, 4, 1]

    def test_empty_input(self):
        """Test threaded execution with empty input."""
        results, interrupted = ParallelExecutor(square, verbose=False).run_threaded()

        assert results == []
        assert interrupted is False


# =============================================================================
# run_multiprocess Tests
# =============================================================================
class TestRunMultiprocess:
    """Tests for run_multiprocess method."""

    def test_basic_execution(self):
        """Test basic multiprocess execution."""
        results, interrupted = ParallelExecutor(square, verbose=False).run_multiprocess(
            number=[1, 2, 3, 4, 5]
        )

        assert results == [1, 4, 9, 16, 25]
        assert interrupted is False

    def test_with_multiple_args(self):
        """Test multiprocess execution with multiple arguments."""
        results, interrupted = ParallelExecutor(add, verbose=False).run_multiprocess(
            a=[1, 2, 3],
            b=[10, 20, 30],
        )

        assert results == [11, 22, 33]
        assert interrupted is False

    def test_with_results_func(self):
        """Test multiprocess execution with results function."""
        results, interrupted = ParallelExecutor(
            square, results_func=sqrt, verbose=False
        ).run_multiprocess(number=[1, 2, 3, 4])

        # square then sqrt: 1->1->1, 2->4->2, 3->9->3, 4->16->4
        assert results == [1.0, 2.0, 3.0, 4.0]
        assert interrupted is False

    def test_with_custom_worker_count(self):
        """Test multiprocess execution with custom worker count."""
        results, interrupted = ParallelExecutor(
            square, n_workers=2, verbose=False
        ).run_multiprocess(number=[1, 2, 3])

        assert results == [1, 4, 9]

    def test_maintains_order(self):
        """Test that results maintain input order."""
        results, interrupted = ParallelExecutor(
            square_with_sleep, n_workers=4, verbose=False
        ).run_multiprocess(
            number=[4, 3, 2, 1],
            sleep=[0.1, 0.08, 0.06, 0.04],
        )

        assert results == [16, 9, 4, 1]

    def test_empty_input(self):
        """Test multiprocess execution with empty input."""
        results, interrupted = ParallelExecutor(
            square, verbose=False
        ).run_multiprocess()

        assert results == []
        assert interrupted is False
