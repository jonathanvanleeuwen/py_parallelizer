"""Tests for utility functions."""

import pytest

from py_parallelizer.utils.input_parsing import (
    create_batch_kwargs,
    create_batches,
    flatten_results,
)


class TestCreateBatches:
    def test_even_split(self):
        result = create_batches([1, 2, 3, 4], 2)
        assert result == [[1, 2], [3, 4]]

    def test_uneven_split(self):
        result = create_batches([1, 2, 3, 4, 5], 2)
        assert result == [[1, 2, 3], [4, 5]]

    def test_more_batches_than_items(self):
        result = create_batches([1, 2, 3], 10)
        assert result == [[1], [2], [3]]

    def test_single_batch(self):
        result = create_batches([1, 2, 3, 4], 1)
        assert result == [[1, 2, 3, 4]]

    def test_empty_data(self):
        result = create_batches([], 3)
        assert result == []

    def test_single_item(self):
        result = create_batches([42], 3)
        assert result == [[42]]

    def test_zero_batches_raises_error(self):
        with pytest.raises(ValueError, match="n_batches must be positive"):
            create_batches([1, 2, 3], 0)

    def test_negative_batches_raises_error(self):
        with pytest.raises(ValueError, match="n_batches must be positive"):
            create_batches([1, 2, 3], -1)

    def test_preserves_order(self):
        result = create_batches([5, 4, 3, 2, 1], 2)
        assert result == [[5, 4, 3], [2, 1]]

    def test_with_strings(self):
        result = create_batches(["a", "b", "c", "d"], 2)
        assert result == [["a", "b"], ["c", "d"]]

    def test_batch_sizes_differ_by_at_most_one(self):
        for total in range(1, 20):
            for n_batches in range(1, total + 1):
                batches = create_batches(list(range(total)), n_batches)
                sizes = [len(b) for b in batches]
                assert max(sizes) - min(sizes) <= 1


class TestFlattenResults:
    def test_simple(self):
        result = flatten_results([[1, 2], [3, 4], [5]])
        assert result == [1, 2, 3, 4, 5]

    def test_with_none(self):
        result = flatten_results([[1, 2], None, [3, 4]])
        assert result == [1, 2, 3, 4]

    def test_empty(self):
        result = flatten_results([])
        assert result == []

    def test_all_none(self):
        result = flatten_results([None, None, None])
        assert result == []

    def test_single_batch(self):
        result = flatten_results([[1, 2, 3]])
        assert result == [1, 2, 3]

    def test_preserves_order(self):
        result = flatten_results([[1, 2], [3], [4, 5, 6]])
        assert result == [1, 2, 3, 4, 5, 6]

    def test_with_empty_batches(self):
        result = flatten_results([[1, 2], [], [3, 4]])
        assert result == [1, 2, 3, 4]


class TestCreateBatchKwargs:
    def test_simple_batch(self):
        result = create_batch_kwargs({"x": [1, 2, 3, 4], "y": [10, 20, 30, 40]}, 2)
        assert result == [
            {"x": [1, 2], "y": [10, 20]},
            {"x": [3, 4], "y": [30, 40]},
        ]

    def test_single_arg(self):
        result = create_batch_kwargs({"numbers": [1, 2, 3, 4]}, 2)
        assert result == [{"numbers": [1, 2]}, {"numbers": [3, 4]}]

    def test_uneven_split(self):
        result = create_batch_kwargs({"x": [1, 2, 3, 4, 5]}, 2)
        assert result == [{"x": [1, 2, 3]}, {"x": [4, 5]}]

    def test_empty_kwargs(self):
        result = create_batch_kwargs({}, 2)
        assert result == []

    def test_empty_values(self):
        result = create_batch_kwargs({"x": []}, 2)
        assert result == []

    def test_preserves_correspondence(self):
        result = create_batch_kwargs(
            {"a": [1, 2, 3, 4], "b": ["w", "x", "y", "z"], "c": [10, 20, 30, 40]}, 2
        )
        assert result == [
            {"a": [1, 2], "b": ["w", "x"], "c": [10, 20]},
            {"a": [3, 4], "b": ["y", "z"], "c": [30, 40]},
        ]

    def test_more_batches_than_items(self):
        result = create_batch_kwargs({"x": [1, 2]}, 5)
        assert result == [{"x": [1]}, {"x": [2]}]
