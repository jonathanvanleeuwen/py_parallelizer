"""Integration tests for ThreadedExecutor."""

import time

from py_parallelizer.executors.threader import ThreadedExecutor


def square_with_sleep(number: int, sleep: float) -> int:
    time.sleep(sleep)
    return number**2


class TestThreadedExecutorIntegration:
    def test_concurrent_execution_is_faster(self):
        n_tasks = 5
        sleep_time = 0.1

        executor = ThreadedExecutor(
            func=square_with_sleep, n_workers=n_tasks, verbose=False
        )

        start = time.time()
        results, _ = executor.execute(
            number=list(range(n_tasks)), sleep=[sleep_time] * n_tasks
        )
        elapsed = time.time() - start

        sequential_time = n_tasks * sleep_time
        assert elapsed < sequential_time * 0.6
        assert results == [i**2 for i in range(n_tasks)]
