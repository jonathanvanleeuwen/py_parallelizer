"""Tests for base classes."""

import pytest

from py_parallelizer.base import BaseParallelExecutor, BaseWorker


class TestBaseWorker:
    """Tests for BaseWorker abstract class."""

    def test_base_worker_is_abstract(self):
        """Test that BaseWorker cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseWorker()

    def test_base_worker_subclass_must_implement_run(self):
        """Test that subclass without run() implementation raises error."""

        class IncompleteWorker(BaseWorker):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteWorker()

    def test_base_worker_subclass_with_run_can_be_instantiated(self):
        """Test that subclass with run() implementation can be instantiated."""

        class CompleteWorker(BaseWorker):
            def run(self) -> None:
                pass

        worker = CompleteWorker()
        assert worker is not None


class TestBaseParallelExecutor:
    """Tests for BaseParallelExecutor class."""

    def test_base_parallel_executor_is_abstract(self):
        """Test that BaseParallelExecutor cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseParallelExecutor(
                func=lambda x: x,
                n_workers=2,
                results_func=None,
                pbar_colour="blue",
                pbar_desc_template="Test",
                verbose=False,
            )


class TestGetWorkerCount:
    """Tests for _get_worker_count static method."""

    def test_get_worker_count_returns_specified_count(self):
        """Test that specified worker count is returned."""
        assert BaseParallelExecutor._get_worker_count(4) == 4
        assert BaseParallelExecutor._get_worker_count(1) == 1
        assert BaseParallelExecutor._get_worker_count(100) == 100

    def test_get_worker_count_auto_detects_when_none(self):
        """Test that worker count is auto-detected when None."""
        count = BaseParallelExecutor._get_worker_count(None)
        assert count >= 1
        assert isinstance(count, int)

    def test_get_worker_count_converts_float_to_int(self):
        """Test that float values are converted to int."""
        assert BaseParallelExecutor._get_worker_count(4.5) == 4
        assert isinstance(BaseParallelExecutor._get_worker_count(4.5), int)


class TestFormatArgs:
    """Tests for _format_args static method."""

    def test_format_args_empty_kwargs(self):
        """Test that empty kwargs returns empty list."""
        result = BaseParallelExecutor._format_args()
        assert result == []

    def test_format_args_single_argument(self):
        """Test formatting with single argument."""
        result = BaseParallelExecutor._format_args(x=[1, 2, 3])
        assert result == [{"x": 1}, {"x": 2}, {"x": 3}]

    def test_format_args_multiple_arguments(self):
        """Test formatting with multiple arguments."""
        result = BaseParallelExecutor._format_args(
            x=[1, 2, 3],
            y=["a", "b", "c"],
        )
        expected = [
            {"x": 1, "y": "a"},
            {"x": 2, "y": "b"},
            {"x": 3, "y": "c"},
        ]
        assert result == expected

    def test_format_args_with_range(self):
        """Test formatting with range objects."""
        result = BaseParallelExecutor._format_args(
            x=range(3),
            y=[10, 20, 30],
        )
        expected = [
            {"x": 0, "y": 10},
            {"x": 1, "y": 20},
            {"x": 2, "y": 30},
        ]
        assert result == expected

    def test_format_args_mismatched_lengths_raises_error(self):
        """Test that mismatched argument lengths raise ValueError."""
        with pytest.raises(ValueError):
            BaseParallelExecutor._format_args(
                x=[1, 2, 3],
                y=[1, 2],  # Different length
            )

    def test_format_args_preserves_types(self):
        """Test that argument types are preserved."""
        result = BaseParallelExecutor._format_args(
            number=[1, 2],
            name=["alice", "bob"],
            data=[{"key": "value"}, [1, 2, 3]],
        )
        assert result[0]["data"] == {"key": "value"}
        assert result[1]["data"] == [1, 2, 3]


class TestConcreteExecutor:
    """Tests for concrete executor implementation."""

    @pytest.fixture
    def concrete_executor_class(self):
        """Create a concrete executor class for testing."""

        class ConcreteExecutor(BaseParallelExecutor):
            def execute(self) -> tuple[list, bool]:
                return [], False

        return ConcreteExecutor

    def test_executor_initialization(self, concrete_executor_class):
        """Test executor initialization with various parameters."""
        executor = concrete_executor_class(
            func=lambda x: x * 2,
            n_workers=4,
            results_func=None,
            pbar_colour="green",
            pbar_desc_template="Testing [{n_workers}]",
            verbose=False,
            x=[1, 2, 3],
        )

        assert executor.n_workers == 4
        assert len(executor.keywordargs) == 3
        assert executor.interrupt is False
        assert executor.pbar is None  # verbose=False

    def test_executor_with_verbose_creates_pbar(self, concrete_executor_class):
        """Test that verbose=True creates progress bar."""
        executor = concrete_executor_class(
            func=lambda x: x,
            n_workers=2,
            results_func=None,
            pbar_colour="blue",
            pbar_desc_template="Test [{n_workers}]",
            verbose=True,
            x=[1, 2],
        )

        assert executor.pbar is not None
        executor.pbar.close()  # Clean up

    def test_apply_results_func_with_none(self, concrete_executor_class):
        """Test _apply_results_func returns value when no results_func."""
        executor = concrete_executor_class(
            func=lambda x: x,
            n_workers=1,
            results_func=None,
            pbar_colour="blue",
            pbar_desc_template="Test",
            verbose=False,
        )

        result = executor._apply_results_func(42)
        assert result == 42

    def test_apply_results_func_with_function(self, concrete_executor_class):
        """Test _apply_results_func applies the function."""
        executor = concrete_executor_class(
            func=lambda x: x,
            n_workers=1,
            results_func=lambda x: x * 2,
            pbar_colour="blue",
            pbar_desc_template="Test",
            verbose=False,
        )

        result = executor._apply_results_func(21)
        assert result == 42
