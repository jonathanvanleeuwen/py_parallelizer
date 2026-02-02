"""Tests for results_func functionality in executors."""

import threading
from collections.abc import Callable

import pytest

from py_parallelizer import ParallelExecutor
from py_parallelizer.executors.multiprocess import MultiprocessExecutor
from py_parallelizer.executors.threader import ThreadedExecutor


def square(number: int) -> int:
    return number**2


def add(a: int, b: int) -> int:
    return a + b


def transform_result(result, process_index):
    """Simple results function that adds the process_index to the result."""
    return result + process_index


def transform_result_with_kwargs(result, **kwargs):
    """Results function using kwargs to accept process_index."""
    return result + kwargs.get("process_index", 0)


class TestThreadedExecutorResultsFunc:
    def test_results_func_is_called(self):
        """Test that results_func is called for each result."""
        called_indices = []

        def track_results(result, process_index):
            called_indices.append(process_index)
            return result * 10

        executor = ThreadedExecutor(
            func=square, n_workers=2, verbose=False, results_func=track_results
        )
        results, interrupted = executor.execute(number=[1, 2, 3, 4])

        assert sorted(called_indices) == [0, 1, 2, 3]
        assert results == [10, 40, 90, 160]  # squared then * 10
        assert interrupted is False

    def test_results_func_receives_correct_index(self):
        """Test that process_index matches the original task index."""
        index_result_map = {}

        def capture_index(result, process_index):
            index_result_map[process_index] = result
            return result

        executor = ThreadedExecutor(
            func=square, n_workers=2, verbose=False, results_func=capture_index
        )
        results, _ = executor.execute(number=[5, 6, 7])

        assert index_result_map == {0: 25, 1: 36, 2: 49}
        assert results == [25, 36, 49]

    def test_results_func_with_transform(self):
        """Test that results_func can transform results."""
        executor = ThreadedExecutor(
            func=square, n_workers=2, verbose=False, results_func=transform_result
        )
        results, _ = executor.execute(number=[1, 2, 3])

        # Result is squared + process_index
        # index 0: 1^2 + 0 = 1
        # index 1: 2^2 + 1 = 5
        # index 2: 3^2 + 2 = 11
        assert results == [1, 5, 11]

    def test_results_func_with_kwargs_signature(self):
        """Test that results_func works with **kwargs signature."""
        executor = ThreadedExecutor(
            func=square,
            n_workers=2,
            verbose=False,
            results_func=transform_result_with_kwargs,
        )
        results, _ = executor.execute(number=[1, 2, 3])

        assert results == [1, 5, 11]

    def test_results_func_runs_in_main_thread(self):
        """Test that results_func executes in the main thread."""
        main_thread_id = threading.current_thread().ident
        results_thread_ids = []

        def check_thread(result, process_index):
            results_thread_ids.append(threading.current_thread().ident)
            return result

        executor = ThreadedExecutor(
            func=square, n_workers=4, verbose=False, results_func=check_thread
        )
        executor.execute(number=[1, 2, 3, 4])

        # All results_func calls should happen in the main thread
        assert all(tid == main_thread_id for tid in results_thread_ids)

    def test_no_results_func(self):
        """Test normal operation without results_func."""
        executor = ThreadedExecutor(func=square, n_workers=2, verbose=False)
        results, interrupted = executor.execute(number=[1, 2, 3])

        assert results == [1, 4, 9]
        assert interrupted is False


class TestMultiprocessExecutorResultsFunc:
    def test_results_func_is_called(self):
        """Test that results_func is called for each result."""
        called_indices = []

        def track_results(result, process_index):
            called_indices.append(process_index)
            return result * 10

        executor = MultiprocessExecutor(
            func=square, n_workers=2, verbose=False, results_func=track_results
        )
        results, interrupted = executor.execute(number=[1, 2, 3, 4])

        assert sorted(called_indices) == [0, 1, 2, 3]
        assert results == [10, 40, 90, 160]
        assert interrupted is False

    def test_results_func_receives_correct_index(self):
        """Test that process_index matches the original task index."""
        index_result_map = {}

        def capture_index(result, process_index):
            index_result_map[process_index] = result
            return result

        executor = MultiprocessExecutor(
            func=square, n_workers=2, verbose=False, results_func=capture_index
        )
        results, _ = executor.execute(number=[5, 6, 7])

        assert index_result_map == {0: 25, 1: 36, 2: 49}
        assert results == [25, 36, 49]

    def test_results_func_with_transform(self):
        """Test that results_func can transform results."""
        executor = MultiprocessExecutor(
            func=square, n_workers=2, verbose=False, results_func=transform_result
        )
        results, _ = executor.execute(number=[1, 2, 3])

        assert results == [1, 5, 11]

    def test_no_results_func(self):
        """Test normal operation without results_func."""
        executor = MultiprocessExecutor(func=square, n_workers=2, verbose=False)
        results, interrupted = executor.execute(number=[1, 2, 3])

        assert results == [1, 4, 9]
        assert interrupted is False


class TestParallelExecutorResultsFunc:
    def test_results_func_with_run_threaded(self):
        """Test that results_func works with run_threaded."""
        executor = ParallelExecutor(
            func=square, n_workers=2, verbose=False, results_func=transform_result
        )
        results, _ = executor.run_threaded(number=[1, 2, 3])

        assert results == [1, 5, 11]

    def test_results_func_with_run_multiprocess(self):
        """Test that results_func works with run_multiprocess."""
        executor = ParallelExecutor(
            func=square, n_workers=2, verbose=False, results_func=transform_result
        )
        results, _ = executor.run_multiprocess(number=[1, 2, 3])

        assert results == [1, 5, 11]

    def test_results_func_stored_in_executor(self):
        """Test that results_func is properly stored."""

        def my_func(r, process_index):
            return r

        executor = ParallelExecutor(func=square, results_func=my_func)
        assert executor.results_func == my_func

    def test_no_results_func_threaded(self):
        """Test normal threaded operation without results_func."""
        results, _ = ParallelExecutor(square, verbose=False).run_threaded(
            number=[1, 2, 3]
        )
        assert results == [1, 4, 9]

    def test_no_results_func_multiprocess(self):
        """Test normal multiprocess operation without results_func."""
        results, _ = ParallelExecutor(square, verbose=False).run_multiprocess(
            number=[1, 2, 3]
        )
        assert results == [1, 4, 9]


class TestResultsFuncThreadSafety:
    """Tests demonstrating thread-safe result handling."""

    def test_sequential_file_write_simulation(self):
        """
        Simulate a use case where results need to be written to a shared resource
        sequentially in the main thread.
        """
        shared_list = []
        write_order = []

        def process_item(x):
            return x * 2

        def write_to_shared(result, process_index):
            # This runs in main thread, so it's safe to modify shared state
            write_order.append(process_index)
            shared_list.append(result)
            return result

        executor = ThreadedExecutor(
            func=process_item, n_workers=4, verbose=False, results_func=write_to_shared
        )
        results, _ = executor.execute(x=[1, 2, 3, 4, 5])

        # All writes happened (order may vary due to task completion order)
        assert sorted(write_order) == [0, 1, 2, 3, 4]
        assert sorted(shared_list) == [2, 4, 6, 8, 10]
        assert results == [2, 4, 6, 8, 10]

    def test_accumulator_pattern(self):
        """Test accumulating results in the main thread."""
        accumulator = {"sum": 0, "count": 0}

        def compute(x):
            return x**2

        def accumulate(result, process_index):
            accumulator["sum"] += result
            accumulator["count"] += 1
            return result

        executor = ThreadedExecutor(
            func=compute, n_workers=2, verbose=False, results_func=accumulate
        )
        results, _ = executor.execute(x=[1, 2, 3, 4])

        assert accumulator["sum"] == 1 + 4 + 9 + 16  # 30
        assert accumulator["count"] == 4
        assert results == [1, 4, 9, 16]
