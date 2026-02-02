"""Base classes for parallel execution strategies."""

from abc import ABC, abstractmethod
from collections.abc import Callable

import psutil
from tqdm import tqdm

from py_parallelizer.utils.logging import setup_logger

logger = setup_logger(__name__)


class BaseParallelExecutor(ABC):
    """Abstract base class for parallel execution strategies."""

    def __init__(
        self,
        func: Callable,
        n_workers: int | None,
        pbar_color: str,
        results_func=None,
        verbose: bool = True,
    ) -> None:
        self.func = func
        self.n_workers = psutil.cpu_count() if n_workers is None else n_workers
        self.interrupt = False
        self.verbose = verbose
        self.pbar = None
        self.pbar_color = pbar_color
        self.pbar_desc: str = "Running code concurrently"
        self.results_func = results_func
        self.first_error: Exception | None = None
        logger.debug(
            "%s processing [%s] using [%s] workers...",
            self.__class__.__name__,
            func.__name__,
            self.n_workers,
        )

    @staticmethod
    def _format_args(**kwargs) -> list[dict]:
        """Convert keyword arguments into a list of dicts for each task."""
        if not kwargs:
            return []
        kwds = []
        arguments = list(kwargs.keys())
        for _, args in enumerate(zip(*kwargs.values(), strict=True)):
            kwds.append({arg: args[arg_idx] for arg_idx, arg in enumerate(arguments)})
        return kwds

    def init_pbar(self, total: int) -> None:
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
        """Execute the parallel processing, returns (results, interrupted)."""
        pass

    @abstractmethod
    def _cleanup_on_interrupt(self) -> None:
        pass

    @abstractmethod
    def _cleanup_on_done(self) -> None:
        pass
