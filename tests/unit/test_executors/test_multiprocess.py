"""Tests for multiprocess executor."""

import time

from py_parallelizer.executors.multiprocess import MultiprocessExecutor


def square(number: int) -> int:
    return number**2


def square_with_sleep(number: int, sleep: float) -> int:
    time.sleep(sleep)
    return number**2


def add(a: int, b: int) -> int:
    return a + b


class TestMultiprocessExecutor:
    def test_returns_correct_results(self):
        executor = MultiprocessExecutor(func=square, n_workers=2, verbose=False)
        results, interrupted = executor.execute(number=[1, 2, 3, 4, 5])
        assert results == [1, 4, 9, 16, 25]
        assert interrupted is False

    def test_with_multiple_args(self):
        executor = MultiprocessExecutor(func=add, n_workers=2, verbose=False)
        results, interrupted = executor.execute(a=[1, 2, 3], b=[10, 20, 30])
        assert results == [11, 22, 33]
        assert interrupted is False

    def test_maintains_order(self):
        executor = MultiprocessExecutor(
            func=square_with_sleep, n_workers=4, verbose=False
        )
        results, interrupted = executor.execute(
            number=[1, 2, 3, 4],
            sleep=[0.1, 0.08, 0.06, 0.04],
        )
        assert results == [1, 4, 9, 16]

    def test_single_worker(self):
        executor = MultiprocessExecutor(func=square, n_workers=1, verbose=False)
        results, interrupted = executor.execute(number=[1, 2, 3])
        assert results == [1, 4, 9]

    def test_empty_tasks(self):
        executor = MultiprocessExecutor(func=square, n_workers=2, verbose=False)
        results, interrupted = executor.execute()
        assert results == []
        assert interrupted is False

    def test_more_workers_than_tasks(self):
        executor = MultiprocessExecutor(func=square, n_workers=10, verbose=False)
        results, interrupted = executor.execute(number=[1, 2])
        assert results == [1, 4]

    def test_no_progress_bar_when_not_verbose(self):
        executor = MultiprocessExecutor(func=square, n_workers=2, verbose=False)
        assert executor.pbar is None
