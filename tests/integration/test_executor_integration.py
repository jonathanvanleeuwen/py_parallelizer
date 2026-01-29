"""Integration tests for ParallelExecutor."""

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


class TestParallelExecutorIntegration:
    """Integration tests for ParallelExecutor."""

    def test_threaded_is_faster_than_sequential(self):
        """Test that threaded execution is faster than sequential."""
        n_tasks = 5
        sleep_time = 0.1

        start = time.time()
        results, _ = ParallelExecutor(
            square_with_sleep, n_workers=n_tasks, verbose=False
        ).run_threaded(
            number=list(range(n_tasks)),
            sleep=[sleep_time] * n_tasks,
        )
        elapsed = time.time() - start

        sequential_time = n_tasks * sleep_time
        assert elapsed < sequential_time * 0.6
        assert len(results) == n_tasks

    def test_multiprocess_is_faster_than_sequential(self):
        """Test that multiprocess execution is faster than sequential."""
        n_tasks = 4
        sleep_time = 0.5  # Longer sleep to make parallelism benefit more apparent

        start = time.time()
        results, _ = ParallelExecutor(
            square_with_sleep, n_workers=n_tasks, verbose=False
        ).run_multiprocess(
            number=list(range(n_tasks)),
            sleep=[sleep_time] * n_tasks,
        )
        elapsed = time.time() - start

        sequential_time = n_tasks * sleep_time
        # Process spawn overhead is significant, but should still be faster than sequential
        assert elapsed < sequential_time
        assert len(results) == n_tasks

    def test_reuse_executor_instance(self):
        """Test that executor instance can be reused."""
        executor = ParallelExecutor(square, n_workers=2, verbose=False)

        results1, _ = executor.run_threaded(number=[1, 2, 3])
        results2, _ = executor.run_threaded(number=[4, 5, 6])

        assert results1 == [1, 4, 9]
        assert results2 == [16, 25, 36]

    def test_same_results_threaded_and_multiprocess(self):
        """Test that threaded and multiprocess give same results."""
        executor = ParallelExecutor(square, n_workers=2, verbose=False)
        numbers = [1, 2, 3, 4, 5]

        threaded_results, _ = executor.run_threaded(number=numbers)
        multiprocess_results, _ = executor.run_multiprocess(number=numbers)

        assert threaded_results == multiprocess_results
