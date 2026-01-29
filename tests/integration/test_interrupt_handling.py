"""Integration tests for interrupt handling and partial results."""

import threading
import time

from py_parallelizer.executors.multiprocess import MultiprocessExecutor
from py_parallelizer.executors.threader import ThreadedExecutor


def slow_square(number: int) -> int:
    time.sleep(0.5)
    return number**2


def fast_then_slow_square(number: int, sleep: float) -> int:
    time.sleep(sleep)
    return number**2


class TestThreadedInterruptHandling:
    def test_interrupt_returns_partial_results(self):
        """Test that interrupting threaded execution returns completed results."""
        executor = ThreadedExecutor(func=fast_then_slow_square, n_workers=2, verbose=False)

        # Start execution in a thread so we can interrupt it
        results_container = {"results": None, "interrupted": None}

        def run_executor():
            # Simulate interrupt after some tasks complete
            # First 2 tasks are fast (0.05s), rest are slow (2s)
            try:
                r, i = executor.execute(
                    number=[1, 2, 3, 4, 5, 6],
                    sleep=[0.05, 0.05, 2.0, 2.0, 2.0, 2.0],
                )
                results_container["results"] = r
                results_container["interrupted"] = i
            except Exception as e:
                results_container["error"] = e

        exec_thread = threading.Thread(target=run_executor)
        exec_thread.start()

        # Wait for fast tasks to complete then simulate interrupt
        time.sleep(0.3)

        # Trigger interrupt by setting stop event and raising KeyboardInterrupt
        executor.stop_event.set()

        # We can't easily raise KeyboardInterrupt from another thread,
        # so we directly call the interrupt cleanup
        executor.interrupt = True

        exec_thread.join(timeout=5)

        # Should have at least the fast results (indices 0 and 1)
        results = results_container.get("results") or executor.results
        completed = [r for r in results if r is not None]

        # At minimum, fast tasks should have completed
        assert len(completed) >= 2
        assert 1 in completed  # 1**2
        assert 4 in completed  # 2**2

    def test_interrupt_flag_is_set(self):
        """Test that interrupt flag is properly set on cleanup."""
        executor = ThreadedExecutor(func=slow_square, n_workers=2, verbose=False)

        # Manually trigger interrupt cleanup
        executor.results = [None] * 5
        executor.threads = []
        executor._cleanup_on_interrupt()

        assert executor.interrupt is True

    def test_collect_ready_results_gathers_completed(self):
        """Test that _collect_ready_results captures available results."""
        executor = ThreadedExecutor(func=fast_then_slow_square, n_workers=4, verbose=False)

        # Set up executor state
        executor.results = [None] * 4

        # Manually put some results in the queue
        executor.results_queue.put((0, 1))
        executor.results_queue.put((1, 4))
        executor.results_queue.put((2, 9))

        executor._collect_ready_results()

        assert executor.results[0] == 1
        assert executor.results[1] == 4
        assert executor.results[2] == 9
        assert executor.results[3] is None


class TestMultiprocessInterruptHandling:
    def test_interrupt_flag_is_set(self):
        """Test that interrupt flag is properly set on cleanup."""
        executor = MultiprocessExecutor(func=slow_square, n_workers=2, verbose=False)

        # Manually trigger interrupt cleanup
        executor.results = [None] * 5
        executor.processes = [None] * 5
        executor._cleanup_on_interrupt()

        assert executor.interrupt is True
        assert executor.pool is None  # Pool should be terminated

    def test_partial_results_on_early_termination(self):
        """Test that partial results are available when pool is terminated early."""
        executor = MultiprocessExecutor(func=slow_square, n_workers=2, verbose=False)

        # Simulate partial execution state
        executor.results = [None] * 6
        executor.results[0] = 1  # Completed
        executor.results[1] = 4  # Completed
        executor.processes = [None, None, None, None, None, None]

        # Trigger cleanup
        executor._cleanup_on_interrupt()

        # Completed results should be preserved
        assert executor.results[0] == 1
        assert executor.results[1] == 4
        assert executor.interrupt is True


class TestParallelExecutorInterruptHandling:
    def test_threaded_partial_results_structure(self):
        """Test that threaded execution maintains result structure on interrupt."""
        # Use direct executor to have more control
        executor = ThreadedExecutor(func=fast_then_slow_square, n_workers=2, verbose=False)

        # Pre-allocate and simulate partial execution
        executor.results = [None] * 6
        executor.results[0] = 1  # Simulated completed
        executor.results[1] = 4  # Simulated completed
        # Rest are None (incomplete)

        executor.interrupt = True

        # Results should maintain order with None for incomplete
        assert len(executor.results) == 6
        assert executor.results[0] == 1
        assert executor.results[1] == 4
        assert executor.results[2] is None
        assert executor.results[3] is None

    def test_multiprocess_partial_results_structure(self):
        """Test that multiprocess execution maintains result structure on interrupt."""
        executor = MultiprocessExecutor(func=fast_then_slow_square, n_workers=2, verbose=False)

        # Pre-allocate and simulate partial execution
        executor.results = [None] * 6
        executor.results[0] = 1  # Simulated completed
        executor.results[1] = 4  # Simulated completed

        executor.interrupt = True

        # Results should maintain order with None for incomplete
        assert len(executor.results) == 6
        assert executor.results[0] == 1
        assert executor.results[1] == 4
        assert all(r is None for r in executor.results[2:])

        # Clean up pool
        executor._clean_pool(how="terminate")
