"""Integration tests for nested parallelism (multiprocess + threading)."""

import time

from py_parallelizer import ParallelExecutor, create_batches, flatten_results


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


# Configuration for nested parallelism
N_THREADS_PER_PROCESS = 3


def process_batch(batch_numbers: list, batch_sleep: list) -> list:
    """
    Process a batch of tasks using threads.

    This function is called by multiprocessing and uses threading internally.
    Must be at module level for multiprocessing pickling.
    """
    results, _ = ParallelExecutor(
        square_with_sleep, n_workers=N_THREADS_PER_PROCESS, verbose=False
    ).run_threaded(number=batch_numbers, sleep=batch_sleep)
    return results


def process_batch_simple(batch_numbers: list) -> list:
    """
    Process a batch of numbers using threads (no sleep).

    Must be at module level for multiprocessing pickling.
    """
    results, _ = ParallelExecutor(square, n_workers=2, verbose=False).run_threaded(
        number=batch_numbers
    )
    return results


class TestNestedParallelism:
    """Tests for nested parallelism (multiprocess outer + threading inner)."""

    def test_nested_execution_produces_correct_results(self):
        """Test that nested parallel execution produces correct results."""
        # Create workload
        all_numbers = list(range(12))
        n_processes = 3

        # Split data into batches
        number_batches = create_batches(all_numbers, n_processes)

        # Run batches across processes (each process uses threads internally)
        batch_results, interrupted = ParallelExecutor(
            process_batch_simple, n_workers=n_processes, verbose=False
        ).run_multiprocess(batch_numbers=number_batches)

        # Flatten results
        results = flatten_results(batch_results)

        # Verify correctness
        expected = [i**2 for i in all_numbers]
        assert sorted(results) == sorted(expected)
        assert interrupted is False

    def test_nested_execution_with_sleep(self):
        """Test nested parallel execution with sleep to verify parallelism."""
        # Create workload: 12 tasks
        all_numbers = list(range(12))
        all_sleep = [0.1] * len(all_numbers)

        n_processes = 4

        # Split data into batches
        number_batches = create_batches(all_numbers, n_processes)
        sleep_batches = create_batches(all_sleep, n_processes)

        # Time the nested execution
        start = time.time()
        batch_results, interrupted = ParallelExecutor(
            process_batch, n_workers=n_processes, verbose=False
        ).run_multiprocess(
            batch_numbers=number_batches,
            batch_sleep=sleep_batches,
        )
        elapsed = time.time() - start

        # Flatten results
        results = flatten_results(batch_results)

        # Verify correctness
        expected = [i**2 for i in all_numbers]
        assert sorted(results) == sorted(expected)
        assert interrupted is False

        # Sequential would take 12 * 0.1 = 1.2 seconds
        # With 4 processes and 3 threads each, should be much faster
        # Each process handles 3 tasks with 3 threads, so roughly 0.1s per process
        # Plus process spawn overhead
        sequential_time = len(all_numbers) * 0.1
        assert elapsed < sequential_time, (
            f"Nested execution took {elapsed:.2f}s, expected < {sequential_time}s"
        )

    def test_nested_with_varying_batch_sizes(self):
        """Test nested execution handles uneven batch sizes correctly."""
        # 10 items split into 3 batches = [4, 3, 3]
        all_numbers = list(range(10))
        n_processes = 3

        number_batches = create_batches(all_numbers, n_processes)

        # Verify batch distribution
        assert len(number_batches) == 3
        batch_sizes = [len(b) for b in number_batches]
        assert sum(batch_sizes) == 10

        # Run nested execution
        batch_results, _ = ParallelExecutor(
            process_batch_simple, n_workers=n_processes, verbose=False
        ).run_multiprocess(batch_numbers=number_batches)

        results = flatten_results(batch_results)

        expected = [i**2 for i in all_numbers]
        assert sorted(results) == sorted(expected)

    def test_nested_with_single_process(self):
        """Test nested execution with single outer process."""
        all_numbers = list(range(6))

        number_batches = create_batches(all_numbers, 1)

        batch_results, _ = ParallelExecutor(
            process_batch_simple, n_workers=1, verbose=False
        ).run_multiprocess(batch_numbers=number_batches)

        results = flatten_results(batch_results)

        expected = [i**2 for i in all_numbers]
        assert results == expected

    def test_nested_with_more_processes_than_items(self):
        """Test nested execution with more processes than data items."""
        all_numbers = [1, 2, 3]
        n_processes = 10  # More than items

        number_batches = create_batches(all_numbers, n_processes)

        # Should create 3 batches (one per item), not 10
        assert len(number_batches) == 3

        batch_results, _ = ParallelExecutor(
            process_batch_simple, n_workers=len(number_batches), verbose=False
        ).run_multiprocess(batch_numbers=number_batches)

        results = flatten_results(batch_results)

        assert results == [1, 4, 9]


class TestNestedParallelismPerformance:
    """Performance tests for nested parallelism."""

    def test_nested_faster_than_sequential(self):
        """Test that nested parallel execution is faster than sequential."""
        n_tasks = 12
        sleep_time = 0.1
        all_numbers = list(range(n_tasks))
        all_sleep = [sleep_time] * n_tasks

        n_processes = 4

        # Split data into batches
        number_batches = create_batches(all_numbers, n_processes)
        sleep_batches = create_batches(all_sleep, n_processes)

        start = time.time()
        batch_results, _ = ParallelExecutor(
            process_batch, n_workers=n_processes, verbose=False
        ).run_multiprocess(
            batch_numbers=number_batches,
            batch_sleep=sleep_batches,
        )
        nested_elapsed = time.time() - start

        nested_results = flatten_results(batch_results)

        # Sequential would be: n_tasks * sleep_time
        sequential_time = n_tasks * sleep_time

        # Verify correctness
        assert sorted(nested_results) == sorted([i**2 for i in all_numbers])

        # Nested should be significantly faster than sequential
        assert nested_elapsed < sequential_time, (
            f"Nested execution ({nested_elapsed:.2f}s) should be faster "
            f"than sequential ({sequential_time}s)"
        )
