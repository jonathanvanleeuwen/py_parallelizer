"""
py_parallelizer - A simple parallel execution library for Python.

This package provides a unified interface for parallel execution using
either threads (for I/O-bound tasks) or processes (for CPU-bound tasks).
"""

__version__ = "1.0.0"

from py_parallelizer.base import BaseParallelExecutor, BaseWorker
from py_parallelizer.executor import ParallelExecutor
from py_parallelizer.executors.multiprocess import MultiprocessExecutor
from py_parallelizer.executors.threaded import ThreadedExecutor, ThreadWorker
from py_parallelizer.logging_utils import TqdmLoggingHandler, setup_logger

__all__ = [
    "ParallelExecutor",
    "ThreadedExecutor",
    "MultiprocessExecutor",
    "ThreadWorker",
    "BaseWorker",
    "BaseParallelExecutor",
    "TqdmLoggingHandler",
    "setup_logger",
]
