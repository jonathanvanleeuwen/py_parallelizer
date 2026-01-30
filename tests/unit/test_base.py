"""Tests for base classes."""

import pytest

from py_parallelizer.executors.base import BaseParallelExecutor


class TestBaseParallelExecutor:
    def test_is_abstract(self):
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseParallelExecutor(
                func=lambda x: x,
                n_workers=2,
                pbar_color="blue",
                verbose=False,
            )


class TestFormatArgs:
    def test_empty_kwargs(self):
        result = BaseParallelExecutor._format_args()
        assert result == []

    def test_single_argument(self):
        result = BaseParallelExecutor._format_args(x=[1, 2, 3])
        assert result == [{"x": 1}, {"x": 2}, {"x": 3}]

    def test_multiple_arguments(self):
        result = BaseParallelExecutor._format_args(x=[1, 2, 3], y=["a", "b", "c"])
        expected = [{"x": 1, "y": "a"}, {"x": 2, "y": "b"}, {"x": 3, "y": "c"}]
        assert result == expected

    def test_with_range(self):
        result = BaseParallelExecutor._format_args(x=range(3), y=[10, 20, 30])
        expected = [{"x": 0, "y": 10}, {"x": 1, "y": 20}, {"x": 2, "y": 30}]
        assert result == expected

    def test_mismatched_lengths_raises_error(self):
        with pytest.raises(ValueError):
            BaseParallelExecutor._format_args(x=[1, 2, 3], y=[1, 2])

    def test_preserves_types(self):
        result = BaseParallelExecutor._format_args(
            number=[1, 2],
            name=["alice", "bob"],
            data=[{"key": "value"}, [1, 2, 3]],
        )
        assert result[0]["data"] == {"key": "value"}
        assert result[1]["data"] == [1, 2, 3]


class TestConcreteExecutor:
    @pytest.fixture
    def concrete_executor_class(self):
        class ConcreteExecutor(BaseParallelExecutor):
            def execute(self, **kwargs) -> tuple[list, bool]:
                return [], False

            def _cleanup_on_interrupt(self) -> None:
                pass

            def _cleanup_on_done(self) -> None:
                pass

        return ConcreteExecutor

    def test_initialization(self, concrete_executor_class):
        executor = concrete_executor_class(
            func=lambda x: x * 2,
            n_workers=4,
            pbar_color="green",
            verbose=False,
        )
        assert executor.n_workers == 4
        assert executor.interrupt is False
        assert executor.pbar is None

    def test_verbose_creates_pbar(self, concrete_executor_class):
        executor = concrete_executor_class(
            func=lambda x: x,
            n_workers=2,
            pbar_color="blue",
            verbose=True,
        )
        executor.init_pbar(total=5)
        assert executor.pbar is not None
        executor.pbar.close()
