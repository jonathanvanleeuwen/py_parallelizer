"""Executors package for parallel execution strategies."""

from py_parallelizer.executors.multiprocess import MultiprocessExecutor
from py_parallelizer.executors.threaded import ThreadedExecutor

__all__ = ["ThreadedExecutor", "MultiprocessExecutor"]
