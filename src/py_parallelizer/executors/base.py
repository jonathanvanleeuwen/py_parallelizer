"""Base classes for parallel execution strategies."""

from abc import ABC, abstractmethod
from collections.abc import Callable

import psutil
from tqdm import tqdm

from py_parallelizer.utils.logging import setup_logger

logger = setup_logger(__name__)


class BaseParallelExecutor(ABC):
    """
    Abstract base class for parallel execution strategies.

    Handles common setup like argument formatting, worker count, and progress bar.
    """

    def __init__(
        self,
        func: Callable,
        n_workers: int | None,
        pbar_color: str,
        verbose: bool = True,
    ) -> None:
        self.func = func
        self.n_workers = psutil.cpu_count() if n_workers is None else n_workers
        self.interrupt = False
        self.verbose = verbose
        self.pbar = None
        self.pbar_color = pbar_color
        self.pbar_desc: str = "Running code concurrently"
        logger.debug(f"{self.__class__.__name__} processing [{func.__name__}] using [{self.n_workers}] workers...")

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

    def init_pbar(self, total: int) -> None:
        """Initialize the progress bar if verbose."""
        if self.verbose:
            self.pbar = tqdm(
                desc=self.pbar_desc,
                total=total,
                leave=True,
                position=0,
                colour=self.pbar_color,
            )

    def pbar_update(self) -> None:
        if self.pbar:
            self.pbar.update()
            self.pbar.refresh()

    def pbar_close(self) -> None:
        if self.pbar:
            self.pbar.close()

    @abstractmethod
    def execute(self, **kwargs) -> tuple[list, bool]:
        """
        Execute the parallel processing.

        Parameters
        ----------
        **kwargs
            Keyword arguments where each value is an iterable of the same length.

        Returns
        -------
        tuple[list, bool]
            (results, interrupted) - Results in input order, and whether interrupted.
        """
        pass

    @abstractmethod
    def _cleanup_on_interrupt(self) -> None:
        """Clean up resources on interrupt."""
        pass

    @abstractmethod
    def _cleanup_on_done(self) -> None:
        """Clean up resources when done."""
        pass
