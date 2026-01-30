# py_parallelizer

A simple, flexible Python library for parallel execution using threading or multiprocessing.

## Table of Contents

- [py\_parallelizer](#py_parallelizer)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
    - [Option 1: Install from Wheel File (Recommended)](#option-1-install-from-wheel-file-recommended)
    - [Option 2: Install from Source (Clone Repository)](#option-2-install-from-source-clone-repository)
    - [Using uv (recommended)](#using-uv-recommended)
    - [Building a Wheel File](#building-a-wheel-file)
  - [Quick Start](#quick-start)
  - [When to Use What](#when-to-use-what)
  - [Usage Guide](#usage-guide)
    - [Threading (I/O-bound tasks)](#threading-io-bound-tasks)
    - [Multiprocessing (CPU-bound tasks)](#multiprocessing-cpu-bound-tasks)
    - [Multiple Arguments](#multiple-arguments)
    - [Handling Interrupts](#handling-interrupts)
    - [Sequential Parallelism (Threaded then Multiprocess)](#sequential-parallelism-threaded-then-multiprocess)
    - [Nested Parallelism (Threading WITHIN Multiprocessing)](#nested-parallelism-threading-within-multiprocessing)
  - [Batch Utilities](#batch-utilities)
  - [Common Pitfalls](#common-pitfalls)
    - [1. Using multiprocessing for I/O-bound tasks](#1-using-multiprocessing-for-io-bound-tasks)
    - [2. Lambda functions with multiprocessing](#2-lambda-functions-with-multiprocessing)
    - [3. Missing `if __name__ == "__main__":` guard](#3-missing-if-__name__--__main__-guard)
    - [4. Too many workers](#4-too-many-workers)
    - [5. Forgetting that multiprocessing copies data](#5-forgetting-that-multiprocessing-copies-data)
    - [6. Not handling exceptions](#6-not-handling-exceptions)
    - [7. Passing arguments with wrong names](#7-passing-arguments-with-wrong-names)
  - [API Reference](#api-reference)
    - [ThreadedExecutor](#threadedexecutor)
    - [MultiprocessExecutor](#multiprocessexecutor)
    - [ParallelExecutor](#parallelexecutor)
  - [Coverage Report](#coverage-report)

## Features

- **ThreadedExecutor**: Run tasks in parallel using threads (best for I/O-bound tasks)
- **MultiprocessExecutor**: Run tasks in parallel using processes (best for CPU-bound tasks)
- **ParallelExecutor**: Unified API that can switch between threading and multiprocessing
- **Progress bars**: Built-in tqdm progress tracking
- **Graceful interrupts**: Ctrl+C returns partial results instead of crashing
- **Batch utilities**: Helper functions for chunking data

## Installation

This package is not published to PyPI. You can install it by either cloning the repository or downloading the wheel file.

### Option 1: Install from Wheel File (Recommended)

Download the latest wheel file from the [releases](https://github.com/jonathanvanleeuwen/py_parallelizer/releases) or from the `dist/` directory:

```bash
# Install a specific version (include the path to the wheel file)
pip install dist/py_parallelizer-1.0.2-py3-none-any.whl

# Or using uv
uv pip install dist/py_parallelizer-1.0.2-py3-none-any.whl
```

> **Note:** Replace `dist/` with the actual path where you downloaded the wheel file, and update the version number as needed.

### Option 2: Install from Source (Clone Repository)

```bash
# Clone the repository
git clone https://github.com/jonathanvanleeuwen/py_parallelizer.git
cd py_parallelizer

# Install using pip
pip install .

# Or install in editable/development mode
pip install -e ".[dev]"
```

### Using uv (recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager. To use it:

```bash
# Install uv (if not already installed)
pip install uv

# Clone and enter the repository
git clone https://github.com/jonathanvanleeuwen/py_parallelizer.git
cd py_parallelizer

# Create a virtual environment
uv venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix/macOS:
source .venv/bin/activate

# Install the package
uv pip install .

# Or install with dev dependencies
uv pip install -e ".[dev]"
```

### Building a Wheel File

If you want to build a wheel file yourself:

```bash
# Using uv
uv build

# Or using pip/build
pip install build
python -m build

# The wheel will be created in the dist/ directory
```

## Quick Start

```python
from py_parallelizer import ParallelExecutor

def process_item(x, multiplier=2):
    return x * multiplier

# Simple usage - pass the function to the constructor
executor = ParallelExecutor(process_item)
results, interrupted = executor.run_threaded(x=[1, 2, 3, 4, 5])
print(results)  # [2, 4, 6, 8, 10]

# With extra kwargs - ALL arguments must be lists of the same length
results, interrupted = executor.run_threaded(
    x=[1, 2, 3],
    multiplier=[10, 10, 10]
)
print(results)  # [10, 20, 30]
```

**Important:**
- The `execute()` and `run_*` methods return a tuple of `(results, interrupted)` where `interrupted` is a boolean indicating if execution was interrupted (e.g., by Ctrl+C).
- When using `run_multiprocess()`, you **must** wrap your code in `if __name__ == "__main__":` to prevent infinite process spawning. See [Multiprocessing](#multiprocessing-cpu-bound-tasks) section.

## When to Use What

| Scenario | Use | Why |
|----------|-----|-----|
| API calls, file I/O, web scraping | `ThreadedExecutor` or `run_threaded` | I/O-bound; threads release GIL while waiting |
| Heavy computation, data processing | `MultiprocessExecutor` or `run_multiprocess` | CPU-bound; bypasses GIL with separate processes |
| Mixed workloads | Nested parallelism | See example below |

## Usage Guide

### Threading (I/O-bound tasks)

```python
from py_parallelizer import ThreadedExecutor

def fetch_url(url, timeout=30):
    import requests
    return requests.get(url, timeout=timeout).status_code

# Pass the function to the constructor
executor = ThreadedExecutor(func=fetch_url, n_workers=10, verbose=True)
urls = ["https://example.com", "https://google.com", "https://github.com"]

# All arguments must be lists of the same length
results, interrupted = executor.execute(
    url=urls,
    timeout=[10, 10, 10]  # One timeout per URL
)
```

### Multiprocessing (CPU-bound tasks)

**Important:** When using multiprocessing, you must:
1. Use a named function (not a lambda) - functions must be picklable
2. Place your execution code inside `if __name__ == "__main__":` guard

The `if __name__ == "__main__":` guard is required because multiprocessing spawns new processes that re-import your module. Without this guard, the code at the top level would execute in each spawned process, causing infinite recursion and unwanted behavior.

```python
from py_parallelizer import MultiprocessExecutor

def heavy_computation(n):
    return sum(i * i for i in range(n))

# REQUIRED: All multiprocessing code must be inside this guard
if __name__ == "__main__":
    # Pass the function to the constructor
    executor = MultiprocessExecutor(func=heavy_computation, n_workers=4, verbose=True)

    # All arguments must be lists of the same length
    results, interrupted = executor.execute(n=[100000, 200000, 300000])
    print(results)
```

### Multiple Arguments

All arguments to the function must be passed as lists of the same length:

```python
from py_parallelizer import ParallelExecutor

def process(a, b, constant="default"):
    return f"{a}-{b}-{constant}"

# Pass the function to the constructor
executor = ParallelExecutor(process, verbose=False)

# All arguments are lists - each index forms one function call
results, interrupted = executor.run_threaded(
    a=[1, 2, 3],
    b=["x", "y", "z"],
    constant=["shared", "shared", "shared"]  # Must also be a list!
)
# Results: ["1-x-shared", "2-y-shared", "3-z-shared"]
```

### Handling Interrupts

Both executors handle Ctrl+C gracefully and return partial results:

```python
from py_parallelizer import ThreadedExecutor
import time

def slow_task(x):
    time.sleep(1)
    return x * 2

executor = ThreadedExecutor(func=slow_task, n_workers=2)

# If you press Ctrl+C during execution:
# - Workers stop gracefully
# - Already-completed results are returned
# - No crash or traceback spam
results, interrupted = executor.execute(x=list(range(100)))

if interrupted:
    print(f"Execution was interrupted! Got {len([r for r in results if r is not None])} results")
else:
    print(f"Completed all {len(results)} tasks")
```

### Sequential Parallelism (Threaded then Multiprocess)

For workflows where you first gather data (I/O-bound) then process it (CPU-bound), run them sequentially:

```python
from py_parallelizer import ThreadedExecutor, MultiprocessExecutor

def fetch_data(url):
    """I/O-bound: fetch from API"""
    import requests
    return requests.get(url).json()

def process_data(data):
    """CPU-bound: heavy processing"""
    return expensive_computation(data)

if __name__ == "__main__":
    urls = ["https://api.example.com/1", "https://api.example.com/2"]

    # Step 1: Fetch all data in parallel using threads (I/O-bound)
    thread_executor = ThreadedExecutor(func=fetch_data, n_workers=10)
    raw_data, _ = thread_executor.execute(url=urls)

    # Step 2: Process all data in parallel using multiprocessing (CPU-bound)
    process_executor = MultiprocessExecutor(func=process_data, n_workers=4)
    results, _ = process_executor.execute(data=raw_data)
```

### Nested Parallelism (Threading WITHIN Multiprocessing)

For maximum parallelism, run threads **inside** each process. This is useful when each task involves both I/O and CPU work. Use `create_batches` to split work across processes, and each process runs threads internally:

```python
from py_parallelizer import ParallelExecutor, create_batches, flatten_results

def process_item(item, multiplier):
    """Individual item processing (runs in a thread)"""
    # Could include I/O operations here
    return item * multiplier

def process_batch(batch_items: list, batch_multipliers: list) -> list:
    """Process a batch of items using threads (runs in a separate process)"""
    results, _ = ParallelExecutor(
        process_item, n_workers=4, verbose=False
    ).run_threaded(item=batch_items, multiplier=batch_multipliers)
    return results

if __name__ == "__main__":
    # All items to process
    all_items = list(range(100))
    all_multipliers = [2] * len(all_items)
    n_processes = 4

    # Split into batches - one batch per process
    item_batches = create_batches(all_items, n_batches=n_processes)
    multiplier_batches = create_batches(all_multipliers, n_batches=n_processes)

    # Each process receives a batch and spawns threads internally
    batch_results, _ = ParallelExecutor(
        process_batch, n_workers=n_processes, verbose=True
    ).run_multiprocess(
        batch_items=item_batches,
        batch_multipliers=multiplier_batches
    )

    # Flatten the nested results from each process
    final_results = flatten_results(batch_results)
    print(f"Processed {len(final_results)} items")  # 100 items
```

This pattern gives you:
- **n_processes** separate Python processes (bypassing the GIL)
- **n_workers** threads per process for concurrent I/O
- Automatic batching and result flattening

## Batch Utilities

Helper functions for splitting data and combining results:

```python
from py_parallelizer import create_batches, flatten_results, create_batch_kwargs

# Split items into n_batches for distributing across processes
items = list(range(100))
batches = create_batches(items, n_batches=4)  # 4 batches of 25 items each
# [[0-24], [25-49], [50-74], [75-99]]

# Flatten nested results (e.g., after nested parallelism)
nested = [[1, 2], [3, 4], [5, 6]]
flat = flatten_results(nested)  # [1, 2, 3, 4, 5, 6]

# Split multiple kwargs into batches (keeps arguments aligned)
batch_kwargs_list = create_batch_kwargs(
    kwargs={'x': [1, 2, 3, 4], 'y': ['a', 'b', 'c', 'd']},
    n_batches=2
)
# [{'x': [1, 2], 'y': ['a', 'b']}, {'x': [3, 4], 'y': ['c', 'd']}]
```

## Common Pitfalls

### 1. Using multiprocessing for I/O-bound tasks
```python
# ❌ Bad: Multiprocessing has overhead, threads are better for I/O
executor = ParallelExecutor(fetch_url)
results, _ = executor.run_multiprocess(url=urls)

# ✅ Good: Use threads for I/O
executor = ParallelExecutor(fetch_url)
results, _ = executor.run_threaded(url=urls)
```

### 2. Lambda functions with multiprocessing
```python
# ❌ Bad: Lambdas can't be pickled
executor = ParallelExecutor(lambda x: x * 2)
executor.run_multiprocess(x=[1, 2, 3])  # Will fail!

# ✅ Good: Use named functions
def double(x):
    return x * 2
executor = ParallelExecutor(double)
executor.run_multiprocess(x=[1, 2, 3])
```

### 3. Missing `if __name__ == "__main__":` guard
```python
# ❌ Bad: Code outside guard runs in every spawned process
from py_parallelizer import ParallelExecutor

def double(x):
    return x * 2

executor = ParallelExecutor(double)
results, _ = executor.run_multiprocess(x=[1, 2, 3])  # Causes issues!

# ✅ Good: Protect multiprocessing code with the guard
from py_parallelizer import ParallelExecutor

def double(x):
    return x * 2

if __name__ == "__main__":
    executor = ParallelExecutor(double)
    results, _ = executor.run_multiprocess(x=[1, 2, 3])
```

### 4. Too many workers
```python
# ❌ Bad: More processes than CPU cores wastes resources
executor = MultiprocessExecutor(func=my_func, n_workers=100)

# ✅ Good: Match CPU cores for CPU-bound work (or leave as None for auto-detect)
import os
executor = MultiprocessExecutor(func=my_func, n_workers=os.cpu_count())
```

### 5. Forgetting that multiprocessing copies data
```python
# ❌ Bad: Large objects get copied to each process
huge_data = load_huge_dataset()
def process(idx):
    return huge_data[idx]  # huge_data copied to each process!

# ✅ Good: Pass only what's needed
def process(item):
    return transform(item)

if __name__ == "__main__":
    executor = ParallelExecutor(process)
    executor.run_multiprocess(item=huge_data)
```

### 6. Not handling exceptions
```python
# Results may contain None for failed items
# Check your results or add try/except in your worker function
def safe_process(x):
    try:
        return risky_operation(x)
    except Exception as e:
        return {"error": str(e), "item": x}
```

### 7. Passing arguments with wrong names
```python
# ❌ Bad: Using 'items' when function expects 'x'
def double(x):
    return x * 2

executor = ParallelExecutor(double)
results, _ = executor.run_threaded(items=[1, 2, 3])  # Error! 'items' is not a parameter

# ✅ Good: Use the actual parameter name
executor = ParallelExecutor(double)
results, _ = executor.run_threaded(x=[1, 2, 3])  # Correct!
```

## API Reference

### ThreadedExecutor
```python
ThreadedExecutor(func, n_workers=None, verbose=True)
executor.execute(**kwargs) -> tuple[list, bool]
```
- `func`: The function to execute in parallel
- `n_workers`: Number of threads (defaults to CPU count)
- `verbose`: Show progress bar
- `**kwargs`: Each keyword argument must be a list of the same length
- Returns: `(results, interrupted)` tuple

### MultiprocessExecutor
```python
MultiprocessExecutor(func, n_workers=None, verbose=True)
executor.execute(**kwargs) -> tuple[list, bool]
```
- `func`: The function to execute in parallel (must be picklable)
- `n_workers`: Number of processes (defaults to CPU count)
- `verbose`: Show progress bar
- `**kwargs`: Each keyword argument must be a list of the same length
- Returns: `(results, interrupted)` tuple

### ParallelExecutor
```python
ParallelExecutor(func, n_workers=None, verbose=True)
executor.run_threaded(**kwargs) -> tuple[list, bool]
executor.run_multiprocess(**kwargs) -> tuple[list, bool]
```
- `func`: The function to execute in parallel
- `n_workers`: Number of workers (defaults to CPU count)
- `verbose`: Show progress bar
- `**kwargs`: Each keyword argument must be a list of the same length
- Returns: `(results, interrupted)` tuple

## Coverage Report
<!-- Pytest Coverage Comment:Begin -->
<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/README.md"><img alt="Coverage" src="https://img.shields.io/badge/Coverage-95%25-brightgreen.svg" /></a><details><summary>Coverage Report </summary><table><tr><th>File</th><th>Stmts</th><th>Miss</th><th>Cover</th><th>Missing</th></tr><tbody><tr><td colspan="5"><b>src/py_parallelizer/executors</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/base.py">base.py</a></td><td>45</td><td>3</td><td>93%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/base.py#L72">72</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/base.py#L76">76</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/base.py#L80">80</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/multiprocess.py">multiprocess.py</a></td><td>80</td><td>3</td><td>96%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/multiprocess.py#L38">38</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/multiprocess.py#L60-L61">60&ndash;61</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threader.py">threader.py</a></td><td>116</td><td>9</td><td>92%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threader.py#L88-L89">88&ndash;89</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threader.py#L112-L113">112&ndash;113</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threader.py#L147-L151">147&ndash;151</a></td></tr><tr><td colspan="5"><b>src/py_parallelizer/utils</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/utils/logging.py">logging.py</a></td><td>19</td><td>2</td><td>89%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/utils/logging.py#L21-L22">21&ndash;22</a></td></tr><tr><td><b>TOTAL</b></td><td><b>316</b></td><td><b>17</b></td><td><b>95%</b></td><td>&nbsp;</td></tr></tbody></table></details>
<!-- Pytest Coverage Comment:End -->
