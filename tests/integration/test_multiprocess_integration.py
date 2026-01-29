"""Integration tests for MultiprocessExecutor."""

import time

from py_parallelizer.executors.multiprocess import MultiprocessExecutor


def square(number: int) -> int:
    return number**2


def square_with_sleep(number: int, sleep: float) -> int:
    time.sleep(sleep)
    return number**2


class TestMultiprocessExecutorIntegration:
    def test_concurrent_execution_is_faster(self):
        n_tasks = 4
        sleep_time = 0.5

        executor = MultiprocessExecutor(
            func=square_with_sleep, n_workers=n_tasks, verbose=False
        )

        start = time.time()
        results, _ = executor.execute(
            number=list(range(n_tasks)), sleep=[sleep_time] * n_tasks
        )
        elapsed = time.time() - start

        sequential_time = n_tasks * sleep_time
        assert elapsed < sequential_time
        assert results == [i**2 for i in range(n_tasks)]

    def test_pool_cleanup_after_execution(self):
        executor = MultiprocessExecutor(func=square, n_workers=2, verbose=False)
        executor.execute(number=[1, 2, 3])
        assert executor.pool is None
