"""Integration tests for nested parallelism (multiprocess + threading)."""

import time

from py_parallelizer import ParallelExecutor, create_batches, flatten_results


def square(number: int) -> int:
    return number**2


def square_with_sleep(number: int, sleep: float) -> int:
    time.sleep(sleep)
    return number**2


N_THREADS_PER_PROCESS = 3


def process_batch(batch_numbers: list, batch_sleep: list) -> list:
    results, _ = ParallelExecutor(
        square_with_sleep, n_workers=N_THREADS_PER_PROCESS, verbose=False
    ).run_threaded(number=batch_numbers, sleep=batch_sleep)
    return results


def process_batch_simple(batch_numbers: list) -> list:
    results, _ = ParallelExecutor(square, n_workers=2, verbose=False).run_threaded(
        number=batch_numbers
    )
    return results


class TestNestedParallelism:
    def test_produces_correct_results(self):
        all_numbers = list(range(12))
        n_processes = 3

        number_batches = create_batches(all_numbers, n_processes)

        batch_results, interrupted = ParallelExecutor(
            process_batch_simple, n_workers=n_processes, verbose=False
        ).run_multiprocess(batch_numbers=number_batches)

        results = flatten_results(batch_results)

        expected = [i**2 for i in all_numbers]
        assert sorted(results) == sorted(expected)
        assert interrupted is False

    def test_with_sleep(self):
        all_numbers = list(range(12))
        all_sleep = [0.1] * len(all_numbers)
        n_processes = 4

        number_batches = create_batches(all_numbers, n_processes)
        sleep_batches = create_batches(all_sleep, n_processes)

        start = time.time()
        batch_results, interrupted = ParallelExecutor(
            process_batch, n_workers=n_processes, verbose=False
        ).run_multiprocess(batch_numbers=number_batches, batch_sleep=sleep_batches)
        elapsed = time.time() - start

        results = flatten_results(batch_results)

        expected = [i**2 for i in all_numbers]
        assert sorted(results) == sorted(expected)
        assert interrupted is False

        sequential_time = len(all_numbers) * 0.1
        assert elapsed < sequential_time

    def test_varying_batch_sizes(self):
        all_numbers = list(range(10))
        n_processes = 3

        number_batches = create_batches(all_numbers, n_processes)

        assert len(number_batches) == 3
        assert sum(len(b) for b in number_batches) == 10

        batch_results, _ = ParallelExecutor(
            process_batch_simple, n_workers=n_processes, verbose=False
        ).run_multiprocess(batch_numbers=number_batches)

        results = flatten_results(batch_results)

        expected = [i**2 for i in all_numbers]
        assert sorted(results) == sorted(expected)

    def test_single_process(self):
        all_numbers = list(range(6))
        number_batches = create_batches(all_numbers, 1)

        batch_results, _ = ParallelExecutor(
            process_batch_simple, n_workers=1, verbose=False
        ).run_multiprocess(batch_numbers=number_batches)

        results = flatten_results(batch_results)
        expected = [i**2 for i in all_numbers]
        assert results == expected

    def test_more_processes_than_items(self):
        all_numbers = [1, 2, 3]
        n_processes = 10

        number_batches = create_batches(all_numbers, n_processes)
        assert len(number_batches) == 3

        batch_results, _ = ParallelExecutor(
            process_batch_simple, n_workers=len(number_batches), verbose=False
        ).run_multiprocess(batch_numbers=number_batches)

        results = flatten_results(batch_results)
        assert results == [1, 4, 9]


class TestNestedParallelismPerformance:
    def test_nested_faster_than_sequential(self):
        n_tasks = 12
        sleep_time = 0.1
        all_numbers = list(range(n_tasks))
        all_sleep = [sleep_time] * n_tasks
        n_processes = 4

        number_batches = create_batches(all_numbers, n_processes)
        sleep_batches = create_batches(all_sleep, n_processes)

        start = time.time()
        batch_results, _ = ParallelExecutor(
            process_batch, n_workers=n_processes, verbose=False
        ).run_multiprocess(batch_numbers=number_batches, batch_sleep=sleep_batches)
        nested_elapsed = time.time() - start

        nested_results = flatten_results(batch_results)

        sequential_time = n_tasks * sleep_time

        assert sorted(nested_results) == sorted([i**2 for i in all_numbers])
        assert nested_elapsed < sequential_time
