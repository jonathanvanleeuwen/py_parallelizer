"""Tests for utility functions."""

import pytest

from py_parallelizer.utils import create_batch_kwargs, create_batches, flatten_results


class TestCreateBatches:
    """Tests for create_batches function."""

    def test_even_split(self):
        """Test splitting data evenly."""
        result = create_batches([1, 2, 3, 4], 2)
        assert result == [[1, 2], [3, 4]]

    def test_uneven_split(self):
        """Test splitting data unevenly (remainder distributed)."""
        result = create_batches([1, 2, 3, 4, 5], 2)
        # Remainder goes to first batches
        assert result == [[1, 2, 3], [4, 5]]

    def test_more_batches_than_items(self):
        """Test creating more batches than items."""
        result = create_batches([1, 2, 3], 10)
        # Should create 3 batches (one per item)
        assert result == [[1], [2], [3]]

    def test_single_batch(self):
        """Test creating a single batch."""
        result = create_batches([1, 2, 3, 4], 1)
        assert result == [[1, 2, 3, 4]]

    def test_empty_data(self):
        """Test with empty data."""
        result = create_batches([], 3)
        assert result == []

    def test_single_item(self):
        """Test with single item."""
        result = create_batches([42], 3)
        assert result == [[42]]

    def test_zero_batches_raises_error(self):
        """Test that zero batches raises ValueError."""
        with pytest.raises(ValueError, match="n_batches must be positive"):
            create_batches([1, 2, 3], 0)

    def test_negative_batches_raises_error(self):
        """Test that negative batches raises ValueError."""
        with pytest.raises(ValueError, match="n_batches must be positive"):
            create_batches([1, 2, 3], -1)

    def test_preserves_order(self):
        """Test that order is preserved within batches."""
        result = create_batches([5, 4, 3, 2, 1], 2)
        assert result == [[5, 4, 3], [2, 1]]

    def test_with_strings(self):
        """Test with string data."""
        result = create_batches(["a", "b", "c", "d"], 2)
        assert result == [["a", "b"], ["c", "d"]]

    def test_batch_sizes_differ_by_at_most_one(self):
        """Test that batch sizes are balanced (differ by at most 1)."""
        for total in range(1, 20):
            for n_batches in range(1, total + 1):
                batches = create_batches(list(range(total)), n_batches)
                sizes = [len(b) for b in batches]
                assert max(sizes) - min(sizes) <= 1


class TestFlattenResults:
    """Tests for flatten_results function."""

    def test_flatten_simple(self):
        """Test flattening simple lists."""
        result = flatten_results([[1, 2], [3, 4], [5]])
        assert result == [1, 2, 3, 4, 5]

    def test_flatten_with_none(self):
        """Test flattening with None values (skipped)."""
        result = flatten_results([[1, 2], None, [3, 4]])
        assert result == [1, 2, 3, 4]

    def test_flatten_empty(self):
        """Test flattening empty list."""
        result = flatten_results([])
        assert result == []

    def test_flatten_all_none(self):
        """Test flattening all None values."""
        result = flatten_results([None, None, None])
        assert result == []

    def test_flatten_single_batch(self):
        """Test flattening single batch."""
        result = flatten_results([[1, 2, 3]])
        assert result == [1, 2, 3]

    def test_flatten_preserves_order(self):
        """Test that order is preserved."""
        result = flatten_results([[1, 2], [3], [4, 5, 6]])
        assert result == [1, 2, 3, 4, 5, 6]

    def test_flatten_with_empty_batches(self):
        """Test flattening with empty batches."""
        result = flatten_results([[1, 2], [], [3, 4]])
        assert result == [1, 2, 3, 4]


class TestCreateBatchKwargs:
    """Tests for create_batch_kwargs function."""

    def test_simple_batch(self):
        """Test creating simple batched kwargs."""
        result = create_batch_kwargs({"x": [1, 2, 3, 4], "y": [10, 20, 30, 40]}, 2)
        assert result == [
            {"x": [1, 2], "y": [10, 20]},
            {"x": [3, 4], "y": [30, 40]},
        ]

    def test_single_arg(self):
        """Test with single argument."""
        result = create_batch_kwargs({"numbers": [1, 2, 3, 4]}, 2)
        assert result == [
            {"numbers": [1, 2]},
            {"numbers": [3, 4]},
        ]

    def test_uneven_split(self):
        """Test with uneven split."""
        result = create_batch_kwargs({"x": [1, 2, 3, 4, 5]}, 2)
        assert result == [
            {"x": [1, 2, 3]},
            {"x": [4, 5]},
        ]

    def test_empty_kwargs(self):
        """Test with empty kwargs."""
        result = create_batch_kwargs({}, 2)
        assert result == []

    def test_empty_values(self):
        """Test with empty value lists."""
        result = create_batch_kwargs({"x": []}, 2)
        assert result == []

    def test_preserves_correspondence(self):
        """Test that argument correspondence is preserved."""
        result = create_batch_kwargs(
            {"a": [1, 2, 3, 4], "b": ["w", "x", "y", "z"], "c": [10, 20, 30, 40]},
            2,
        )
        assert result == [
            {"a": [1, 2], "b": ["w", "x"], "c": [10, 20]},
            {"a": [3, 4], "b": ["y", "z"], "c": [30, 40]},
        ]

    def test_more_batches_than_items(self):
        """Test with more batches than items."""
        result = create_batch_kwargs({"x": [1, 2]}, 5)
        assert result == [{"x": [1]}, {"x": [2]}]
