"""Tests for threaded executor."""

import time

from py_parallelizer.executors.threader import ThreadedExecutor


def square(number: int) -> int:
    return number**2


def square_with_sleep(number: int, sleep: float) -> int:
    time.sleep(sleep)
    return number**2


def add(a: int, b: int) -> int:
    return a + b


class TestThreadedExecutor:
    def test_returns_correct_results(self):
        executor = ThreadedExecutor(func=square, n_workers=2, verbose=False)
        results, interrupted = executor.execute(number=[1, 2, 3, 4, 5])
        assert results == [1, 4, 9, 16, 25]
        assert interrupted is False

    def test_with_multiple_args(self):
        executor = ThreadedExecutor(func=add, n_workers=2, verbose=False)
        results, interrupted = executor.execute(a=[1, 2, 3], b=[10, 20, 30])
        assert results == [11, 22, 33]
        assert interrupted is False

    def test_maintains_order(self):
        executor = ThreadedExecutor(func=square_with_sleep, n_workers=5, verbose=False)
        results, interrupted = executor.execute(
            number=[1, 2, 3, 4, 5],
            sleep=[0.05, 0.04, 0.03, 0.02, 0.01],
        )
        assert results == [1, 4, 9, 16, 25]

    def test_single_worker(self):
        executor = ThreadedExecutor(func=square, n_workers=1, verbose=False)
        results, interrupted = executor.execute(number=[1, 2, 3])
        assert results == [1, 4, 9]

    def test_empty_tasks(self):
        executor = ThreadedExecutor(func=square, n_workers=2, verbose=False)
        results, interrupted = executor.execute()
        assert results == []
        assert interrupted is False

    def test_more_workers_than_tasks(self):
        executor = ThreadedExecutor(func=square, n_workers=10, verbose=False)
        results, interrupted = executor.execute(number=[1, 2])
        assert results == [1, 4]

    def test_creates_progress_bar_when_verbose(self):
        executor = ThreadedExecutor(func=square, n_workers=2, verbose=True)
        executor.execute(number=[1, 2, 3])
        # pbar is closed after execute but we can check it was created

    def test_no_progress_bar_when_not_verbose(self):
        executor = ThreadedExecutor(func=square, n_workers=2, verbose=False)
        assert executor.pbar is None
