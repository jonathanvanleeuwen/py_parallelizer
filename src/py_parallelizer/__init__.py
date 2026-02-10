"""
py_parallelizer - A simple parallel execution library for Python.

This package provides a unified interface for parallel execution using
either threads (for I/O-bound tasks) or processes (for CPU-bound tasks).
"""

__version__ = "1.1.10"

from py_parallelizer.executor import ParallelExecutor
from py_parallelizer.executors.multiprocess import MultiprocessExecutor
from py_parallelizer.executors.threader import ThreadedExecutor
from py_parallelizer.utils.input_parsing import (
    create_batch_kwargs,
    create_batches,
    flatten_results,
)

__all__ = [
    "ParallelExecutor",
    "ThreadedExecutor",
    "MultiprocessExecutor",
    "create_batches",
    "flatten_results",
    "create_batch_kwargs",
]
