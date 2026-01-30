"""Utility functions for batching and result processing."""


def create_batches(data: list, n_batches: int) -> list[list]:
    """
    Split data into n roughly equal batches.

    Parameters
    ----------
    data : list
        The data to split into batches.
    n_batches : int
        The number of batches to create.

    Returns
    -------
    list[list]
        A list of batches, where each batch is a list of items.

    Examples
    --------
    >>> create_batches([1, 2, 3, 4, 5], 2)
    [[1, 2, 3], [4, 5]]

    >>> create_batches([1, 2, 3, 4], 4)
    [[1], [2], [3], [4]]

    >>> create_batches([], 3)
    []
    """
    if not data:
        return []

    if n_batches <= 0:
        raise ValueError("n_batches must be positive")

    # Limit batches to data length
    n_batches = min(n_batches, len(data))

    batch_size = len(data) // n_batches
    remainder = len(data) % n_batches
    batches = []
    start = 0

    for i in range(n_batches):
        # Distribute remainder across first batches
        size = batch_size + (1 if i < remainder else 0)
        if size > 0:
            batches.append(data[start : start + size])
            start += size

    return batches


def flatten_results(batch_results: list[list | None]) -> list:
    """
    Flatten a list of batch results into a single list.

    Handles None values gracefully (skips them).

    Parameters
    ----------
    batch_results : list[list | None]
        A list of batch results, where each batch is a list or None.

    Returns
    -------
    list
        A flattened list of all results.

    Examples
    --------
    >>> flatten_results([[1, 2], [3, 4], [5]])
    [1, 2, 3, 4, 5]

    >>> flatten_results([[1, 2], None, [3, 4]])
    [1, 2, 3, 4]

    >>> flatten_results([])
    []
    """
    flat = []
    for batch in batch_results:
        if batch is not None:
            flat.extend(batch)
    return flat


def create_batch_kwargs(
    kwargs: dict[str, list], n_batches: int
) -> list[dict[str, list]]:
    """
    Split keyword arguments into batches for parallel processing.

    Each kwarg value should be a list of the same length. This function
    splits them into n_batches, preserving the correspondence between arguments.

    Parameters
    ----------
    kwargs : dict[str, list]
        Keyword arguments where each value is a list of the same length.
    n_batches : int
        The number of batches to create.

    Returns
    -------
    list[dict[str, list]]
        A list of batch dictionaries, each with the same keys but batched values.

    Examples
    --------
    >>> create_batch_kwargs({'x': [1, 2, 3, 4], 'y': [10, 20, 30, 40]}, 2)
    [{'x': [1, 2], 'y': [10, 20]}, {'x': [3, 4], 'y': [30, 40]}]
    """
    if not kwargs:
        return []

    # Get length from first value
    first_key = next(iter(kwargs))
    total_items = len(kwargs[first_key])

    if total_items == 0:
        return []

    # Create index batches
    indices = list(range(total_items))
    index_batches = create_batches(indices, n_batches)

    # Create kwarg batches using the index batches
    batch_kwargs_list = []
    for index_batch in index_batches:
        batch_dict = {
            key: [values[i] for i in index_batch] for key, values in kwargs.items()
        }
        batch_kwargs_list.append(batch_dict)

    return batch_kwargs_list
