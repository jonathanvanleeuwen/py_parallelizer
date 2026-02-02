# py_parallelizer

A simple, flexible Python library for parallel execution using threading or multiprocessing.

## Table of Contents

- [py\_parallelizer](#py_parallelizer)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
    - [Option 1: Install from Private GitHub Release (Recommended)](#option-1-install-from-private-github-release-recommended)
      - [Step 1: Create a Personal Access Token (one-time setup)](#step-1-create-a-personal-access-token-one-time-setup)
      - [Step 2: Install the package](#step-2-install-the-package)
      - [Using uv (faster alternative to pip)](#using-uv-faster-alternative-to-pip)
    - [Option 2: Install from Wheel File in Repository](#option-2-install-from-wheel-file-in-repository)
    - [Option 3: Install from Source (Clone Repository)](#option-3-install-from-source-clone-repository)
    - [Option 4: Add to requirements.txt or pyproject.toml](#option-4-add-to-requirementstxt-or-pyprojecttoml)
    - [Building a Wheel File Locally](#building-a-wheel-file-locally)
  - [Quick Start](#quick-start)
  - [When to Use What](#when-to-use-what)
  - [Usage Guide](#usage-guide)
    - [Threading (I/O-bound tasks)](#threading-io-bound-tasks)
    - [Multiprocessing (CPU-bound tasks)](#multiprocessing-cpu-bound-tasks)
    - [Multiple Arguments](#multiple-arguments)
    - [Handling Interrupts](#handling-interrupts)
    - [Results Function (Thread-Safe Result Handling)](#results-function-thread-safe-result-handling)
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

This package is distributed privately via GitHub. Only users with access to the repository can install it. You can install it directly with pip if you have been added as a collaborator.

### Option 1: Install from Private GitHub Release (Recommended)

Since this is a private repository, you need to authenticate with a GitHub Personal Access Token (PAT).

#### Step 1: Create a Personal Access Token (one-time setup)

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Give it a descriptive name (e.g., `py_parallelizer-install`)
4. Select the **`repo`** scope (required for private repositories)
5. Click **"Generate token"**
6. **Copy the token immediately** - you won't be able to see it again!

#### Step 2: Install the package

**Option A: Install directly with the token in the URL**

```bash
# Replace YOUR_TOKEN with your actual token and VERSION with the desired version (e.g., v1.1.0)
pip install "git+https://YOUR_TOKEN@github.com/jonathanvanleeuwen/py_parallelizer.git@VERSION"

# Example with a specific version:
pip install "git+https://YOUR_TOKEN@github.com/jonathanvanleeuwen/py_parallelizer.git@v1.1.0"

# Install the latest version (main branch):
pip install "git+https://YOUR_TOKEN@github.com/jonathanvanleeuwen/py_parallelizer.git"
```

**Option B: Configure git credentials (more secure, recommended)**

This method doesn't expose your token in command history:

```bash
# Store credentials in git (one-time setup)
git config --global credential.helper store

# Then install normally - git will prompt for credentials once
pip install "git+https://github.com/jonathanvanleeuwen/py_parallelizer.git@v1.1.0"
# When prompted: username = your GitHub username, password = your PAT
```

**Option C: Using environment variable (good for CI/CD)**

```bash
# Set your token as an environment variable
# On Windows (PowerShell):
$env:GH_TOKEN = "your_token_here"
pip install "git+https://$env:GH_TOKEN@github.com/jonathanvanleeuwen/py_parallelizer.git@v1.1.0"

# On Linux/macOS:
export GH_TOKEN="your_token_here"
pip install "git+https://${GH_TOKEN}@github.com/jonathanvanleeuwen/py_parallelizer.git@v1.1.0"
```

#### Using uv (faster alternative to pip)

```bash
# Using uv with token in URL
uv pip install "git+https://YOUR_TOKEN@github.com/jonathanvanleeuwen/py_parallelizer.git@v1.1.0"

# Or using environment variable
uv pip install "git+https://${GH_TOKEN}@github.com/jonathanvanleeuwen/py_parallelizer.git@v1.1.0"
```

### Option 2: Install from Wheel File in Repository

The latest wheel files are also committed to the `dist/` directory in the repository. After cloning:

```bash
# Clone the repository first
git clone https://github.com/jonathanvanleeuwen/py_parallelizer.git

# Install the wheel file directly
pip install py_parallelizer/dist/py_parallelizer-1.1.0-py3-none-any.whl

# Or using uv
uv pip install py_parallelizer/dist/py_parallelizer-1.1.0-py3-none-any.whl
```

> **Note:** Replace the version number with the actual version in the `dist/` directory.

### Option 3: Install from Source (Clone Repository)

```bash
# Clone the repository (requires git credentials or SSH key)
git clone https://github.com/jonathanvanleeuwen/py_parallelizer.git
cd py_parallelizer

# Install using pip
pip install .

# Or install in editable/development mode
pip install -e ".[dev]"
```

### Option 4: Add to requirements.txt or pyproject.toml

**In requirements.txt:**

```txt
# Using git+https (requires GH_TOKEN environment variable to be set)
py_parallelizer @ git+https://github.com/jonathanvanleeuwen/py_parallelizer.git@v1.1.0
```

**In pyproject.toml (for projects using PEP 621):**

```toml
[project]
dependencies = [
    "py_parallelizer @ git+https://github.com/jonathanvanleeuwen/py_parallelizer.git@v1.1.0",
]
```

> **Note:** When installing from requirements.txt with a private repo, ensure your git credentials are configured (see Option 1, Step 2, Option B above).

### Building a Wheel File Locally

If you want to build a wheel file yourself:

```bash
# Clone the repo first
git clone https://github.com/jonathanvanleeuwen/py_parallelizer.git
cd py_parallelizer

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

### Results Function (Thread-Safe Result Handling)

When processing results that need thread-safe handling (e.g., writing to a single file, updating a shared database), use the `results_func` parameter. This function runs in the **main thread/process** and is called sequentially for each completed result, making it safe to perform operations that aren't thread/process-safe.

```python
from py_parallelizer import ThreadedExecutor

def process_image(image_path):
    """Process an image (runs in parallel threads)"""
    # Heavy computation here
    return {"path": image_path, "processed": True}

def save_result(result, process_index):
    """
    Handle result in main thread (thread-safe).

    Args:
        result: The return value from the worker function
        process_index: The index of this task in the original input list

    Returns:
        The (optionally transformed) result to store
    """
    # Safe to write to a shared file here - runs sequentially in main thread
    with open("results.txt", "a") as f:
        f.write(f"{process_index}: {result}\n")
    return result

executor = ThreadedExecutor(
    func=process_image,
    n_workers=4,
    results_func=save_result  # Called in main thread for each result
)
results, _ = executor.execute(image_path=["img1.jpg", "img2.jpg", "img3.jpg"])
```

**Key points:**
- `results_func` receives two arguments: `result` (the return value) and `process_index` (the task's index)
- It runs in the main thread/process, so it's safe to modify shared state
- The return value of `results_func` is what gets stored in the results list
- You can use `**kwargs` in your function signature: `def my_func(result, **kwargs)`

**Use cases:**
- Writing results to a single file (not thread-safe on Windows)
- Updating a database connection
- Accumulating statistics
- Progress logging with task indices

```python
# Accumulator pattern - safe because results_func runs in main thread
accumulator = {"total": 0, "count": 0}

def accumulate(result, process_index):
    accumulator["total"] += result
    accumulator["count"] += 1
    return result

executor = ThreadedExecutor(func=compute, n_workers=4, results_func=accumulate)
results, _ = executor.execute(x=[1, 2, 3, 4, 5])
print(f"Sum: {accumulator['total']}, Count: {accumulator['count']}")
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
executor = ThreadedExecutor(func, n_workers=None, verbose=True, results_func=None)
executor.execute(**kwargs) -> tuple[list, bool]
```
- `func`: The function to execute in parallel
- `n_workers`: Number of threads (defaults to CPU count)
- `verbose`: Show progress bar
- `results_func`: Optional callback function called in main thread for each result. Receives `(result, process_index)` and returns the (optionally transformed) result to store
- `**kwargs`: Each keyword argument must be a list of the same length
- Returns: `(results, interrupted)` tuple

### MultiprocessExecutor
```python
executor = MultiprocessExecutor(func, n_workers=None, verbose=True, results_func=None)
executor.execute(**kwargs) -> tuple[list, bool]
```
- `func`: The function to execute in parallel (must be picklable)
- `n_workers`: Number of processes (defaults to CPU count)
- `verbose`: Show progress bar
- `results_func`: Optional callback function called in main process for each result. Receives `(result, process_index)` and returns the (optionally transformed) result to store
- `**kwargs`: Each keyword argument must be a list of the same length
- Returns: `(results, interrupted)` tuple

### ParallelExecutor
```python
executor = ParallelExecutor(func, n_workers=None, verbose=True, results_func=None)
executor.run_threaded(**kwargs) -> tuple[list, bool]
executor.run_multiprocess(**kwargs) -> tuple[list, bool]
```
- `func`: The function to execute in parallel
- `n_workers`: Number of workers (defaults to CPU count)
- `verbose`: Show progress bar
- `results_func`: Optional callback function called in main thread/process for each result. Receives `(result, process_index)` and returns the (optionally transformed) result to store
- `**kwargs`: Each keyword argument must be a list of the same length
- Returns: `(results, interrupted)` tuple

## Coverage Report
<!-- Pytest Coverage Comment:Begin -->
<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/README.md"><img alt="Coverage" src="https://img.shields.io/badge/Coverage-94%25-brightgreen.svg" /></a><details><summary>Coverage Report </summary><table><tr><th>File</th><th>Stmts</th><th>Miss</th><th>Cover</th><th>Missing</th></tr><tbody><tr><td colspan="5"><b>src/py_parallelizer/executors</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/base.py">base.py</a></td><td>46</td><td>3</td><td>93%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/base.py#L74">74</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/base.py#L78">78</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/base.py#L82">82</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/multiprocess.py">multiprocess.py</a></td><td>83</td><td>3</td><td>96%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/multiprocess.py#L40">40</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/multiprocess.py#L62-L63">62&ndash;63</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threader.py">threader.py</a></td><td>120</td><td>10</td><td>92%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threader.py#L90-L91">90&ndash;91</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threader.py#L113">113</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threader.py#L116-L117">116&ndash;117</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threader.py#L153-L157">153&ndash;157</a></td></tr><tr><td colspan="5"><b>src/py_parallelizer/utils</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/utils/logging.py">logging.py</a></td><td>19</td><td>2</td><td>89%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/utils/logging.py#L21-L22">21&ndash;22</a></td></tr><tr><td><b>TOTAL</b></td><td><b>325</b></td><td><b>18</b></td><td><b>94%</b></td><td>&nbsp;</td></tr></tbody></table></details>
<!-- Pytest Coverage Comment:End -->
