"""Base classes for parallel execution strategies."""

from abc import ABC, abstractmethod
from collections.abc import Callable

import psutil
from tqdm import tqdm

from py_parallelizer.logging_utils import setup_logger

logger = setup_logger(__name__)


class BaseWorker(ABC):
    """Abstract base class for worker implementations."""

    @abstractmethod
    def run(self) -> None:
        """Execute the worker loop."""
        pass


class BaseParallelExecutor(ABC):
    """
    Abstract base class for parallel execution strategies.

    Handles common setup like argument formatting, worker count, and progress bar.
    """

    def __init__(
        self,
        func: Callable,
        n_workers: int | None,
        results_func: Callable | None,
        pbar_colour: str,
        pbar_desc_template: str,
        verbose: bool = True,
        **kwargs,
    ):
        self.func = func
        self.results_func = results_func
        self.n_workers = self._get_worker_count(n_workers)
        self.keywordargs = self._format_args(**kwargs)
        self.interrupt = False
        self.verbose = verbose

        if self.verbose:
            self.pbar = tqdm(
                desc=pbar_desc_template.format(n_workers=self.n_workers),
                total=len(self.keywordargs),
                leave=True,
                position=0,
                colour=pbar_colour,
            )
        else:
            self.pbar = None

        logger.debug(f"{self.__class__.__name__} processing [{func.__name__}] using [{self.n_workers}] workers...")

    @staticmethod
    def _get_worker_count(n_workers: int | None) -> int:
        """Get the number of workers to use, defaulting to CPU count - 1."""
        if n_workers is None:
            cpu_count = psutil.cpu_count()
            n_workers = max(cpu_count - 1, 1)
            logger.debug(f"Auto-detected worker count: {n_workers} (CPU count: {cpu_count})")
        return int(n_workers)

    @staticmethod
    def _format_args(**kwargs) -> list[dict]:
        """
        Convert keyword arguments into a list of dicts for each task.

        Parameters
        ----------
        **kwargs
            Keyword arguments where each value is an iterable of the same length.

        Returns
        -------
        list[dict]
            List of dictionaries, one for each task.

        Raises
        ------
        ValueError
            If the iterables have different lengths.
        """
        if not kwargs:
            return []
        kwds = []
        arguments = list(kwargs.keys())
        for _, args in enumerate(zip(*kwargs.values(), strict=True)):
            kwds.append({arg: args[arg_idx] for arg_idx, arg in enumerate(arguments)})
        return kwds

    @abstractmethod
    def execute(self) -> tuple[list, bool]:
        """
        Execute the parallel processing.

        Returns
        -------
        tuple[list, bool]
            (results, interrupted) - Results in input order, and whether interrupted.
        """
        pass

    def _apply_results_func(self, value):
        """Apply results_func if provided, otherwise return value as-is."""
        if self.results_func:
            return self.results_func(value)
        return value
