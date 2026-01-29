"""Integration tests for MultiprocessExecutor."""

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


class TestMultiprocessExecutorIntegration:
    """Integration tests for MultiprocessExecutor."""

    def test_concurrent_execution_is_faster(self):
        """Test that parallel execution is faster than sequential."""
        n_tasks = 4
        sleep_time = 0.5  # Longer sleep to make parallelism benefit more apparent

        executor = MultiprocessExecutor(
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
        # Process spawn overhead is significant, but should still be faster than sequential
        sequential_time = n_tasks * sleep_time
        assert elapsed < sequential_time
        assert results == [i**2 for i in range(n_tasks)]

    def test_pool_cleanup_after_execution(self):
        """Test that process pool is cleaned up after execution."""
        executor = MultiprocessExecutor(
            func=square,
            n_workers=2,
            results_func=None,
            verbose=False,
            number=[1, 2, 3],
        )

        executor.execute()

        # Pool should be None after successful execution
        assert executor.pool is None
