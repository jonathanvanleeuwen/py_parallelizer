"""Integration tests for ThreadedExecutor."""

import time

from py_parallelizer.executors.threaded import ThreadedExecutor


# =============================================================================
# Test helper functions (must be at module level for pickling)
# =============================================================================
def square_with_sleep(number: int, sleep: float) -> int:
    """Square a number after sleeping."""
    time.sleep(sleep)
    return number**2


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
