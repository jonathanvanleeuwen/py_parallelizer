"""Tests for ParallelExecutor public API."""

import time

from py_parallelizer import ParallelExecutor


def square(number: int) -> int:
    return number**2


def square_with_sleep(number: int, sleep: float) -> int:
    time.sleep(sleep)
    return number**2


def add(a: int, b: int) -> int:
    return a + b


class TestParallelExecutorInit:
    def test_init_with_func_only(self):
        executor = ParallelExecutor(square)
        assert executor.func == square
        assert executor.n_workers is None
        assert executor.verbose is True

    def test_init_with_all_params(self):
        executor = ParallelExecutor(func=square, n_workers=4, verbose=False)
        assert executor.func == square
        assert executor.n_workers == 4
        assert executor.verbose is False


class TestRunThreaded:
    def test_basic_execution(self):
        results, interrupted = ParallelExecutor(square, verbose=False).run_threaded(
            number=[1, 2, 3, 4, 5]
        )
        assert results == [1, 4, 9, 16, 25]
        assert interrupted is False

    def test_with_multiple_args(self):
        results, interrupted = ParallelExecutor(add, verbose=False).run_threaded(
            a=[1, 2, 3], b=[10, 20, 30]
        )
        assert results == [11, 22, 33]
        assert interrupted is False

    def test_with_custom_worker_count(self):
        results, interrupted = ParallelExecutor(
            square, n_workers=2, verbose=False
        ).run_threaded(number=[1, 2, 3])
        assert results == [1, 4, 9]

    def test_maintains_order(self):
        results, interrupted = ParallelExecutor(
            square_with_sleep, n_workers=5, verbose=False
        ).run_threaded(
            number=[5, 4, 3, 2, 1],
            sleep=[0.05, 0.04, 0.03, 0.02, 0.01],
        )
        assert results == [25, 16, 9, 4, 1]

    def test_empty_input(self):
        results, interrupted = ParallelExecutor(square, verbose=False).run_threaded()
        assert results == []
        assert interrupted is False


class TestRunMultiprocess:
    def test_basic_execution(self):
        results, interrupted = ParallelExecutor(square, verbose=False).run_multiprocess(
            number=[1, 2, 3, 4, 5]
        )
        assert results == [1, 4, 9, 16, 25]
        assert interrupted is False

    def test_with_multiple_args(self):
        results, interrupted = ParallelExecutor(add, verbose=False).run_multiprocess(
            a=[1, 2, 3], b=[10, 20, 30]
        )
        assert results == [11, 22, 33]
        assert interrupted is False

    def test_with_custom_worker_count(self):
        results, interrupted = ParallelExecutor(
            square, n_workers=2, verbose=False
        ).run_multiprocess(number=[1, 2, 3])
        assert results == [1, 4, 9]

    def test_maintains_order(self):
        results, interrupted = ParallelExecutor(
            square_with_sleep, n_workers=4, verbose=False
        ).run_multiprocess(
            number=[4, 3, 2, 1],
            sleep=[0.1, 0.08, 0.06, 0.04],
        )
        assert results == [16, 9, 4, 1]

    def test_empty_input(self):
        results, interrupted = ParallelExecutor(
            square, verbose=False
        ).run_multiprocess()
        assert results == []
        assert interrupted is False
