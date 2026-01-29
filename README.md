# py_parallelizer

A simple, flexible Python library for parallel execution using threading or multiprocessing.

## Features

- **ThreadedExecutor**: Run tasks in parallel using threads (best for I/O-bound tasks)
- **MultiprocessExecutor**: Run tasks in parallel using processes (best for CPU-bound tasks)
- **ParallelExecutor**: Unified API that can switch between threading and multiprocessing
- **Progress bars**: Built-in tqdm progress tracking
- **Graceful interrupts**: Ctrl+C returns partial results instead of crashing
- **Batch utilities**: Helper functions for chunking data

## Installation

```bash
pip install py_parallelizer
```

Or for development:
```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from py_parallelizer import ParallelExecutor

def process_item(x, multiplier=2):
    return x * multiplier

# Simple usage
executor = ParallelExecutor()
results = executor.run_threaded(process_item, items=[1, 2, 3, 4, 5])
print(results)  # [2, 4, 6, 8, 10]

# With extra kwargs
results = executor.run_threaded(
    process_item,
    items=[1, 2, 3],
    multiplier=10
)
print(results)  # [10, 20, 30]
```

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

executor = ThreadedExecutor(n_workers=10, show_progress=True)
urls = ["https://example.com", "https://google.com", "https://github.com"]
results = executor.execute(fetch_url, items=urls, timeout=10)
```

### Multiprocessing (CPU-bound tasks)

```python
from py_parallelizer import MultiprocessExecutor

def heavy_computation(n):
    return sum(i * i for i in range(n))

executor = MultiprocessExecutor(n_workers=4, show_progress=True)
results = executor.execute(heavy_computation, items=[100000, 200000, 300000])
```

### Multiple Arguments

For functions requiring multiple varying arguments, use `create_batch_kwargs`:

```python
from py_parallelizer import ParallelExecutor
from py_parallelizer.utils import create_batch_kwargs

def process(a, b, constant="default"):
    return f"{a}-{b}-{constant}"

# Create list of kwargs dicts
batch_kwargs = create_batch_kwargs(
    a=[1, 2, 3],
    b=["x", "y", "z"]
)
# Result: [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}, {"a": 3, "b": "z"}]

executor = ParallelExecutor()
results = executor.run_threaded(
    process,
    items=batch_kwargs,  # Pass kwargs dicts as items
    constant="shared"    # This applies to all calls
)
```

### Handling Interrupts

Both executors handle Ctrl+C gracefully and return partial results:

```python
from py_parallelizer import ThreadedExecutor
import time

def slow_task(x):
    time.sleep(1)
    return x * 2

executor = ThreadedExecutor(n_workers=2)

# If you press Ctrl+C during execution:
# - Workers stop gracefully
# - Already-completed results are returned
# - No crash or traceback spam
results = executor.execute(slow_task, items=range(100))
print(f"Got {len(results)} results before interrupt")
```

### Nested Parallelism (Threading + Multiprocessing)

For complex workloads, combine both: use threading for I/O and multiprocessing for CPU work:

```python
from py_parallelizer import ThreadedExecutor, MultiprocessExecutor

def fetch_data(url):
    """I/O-bound: fetch from API"""
    import requests
    return requests.get(url).json()

def process_data(data):
    """CPU-bound: heavy processing"""
    return expensive_computation(data)

# Step 1: Fetch data in parallel (I/O-bound -> threads)
thread_executor = ThreadedExecutor(n_workers=10)
raw_data = thread_executor.execute(fetch_data, items=urls)

# Step 2: Process data in parallel (CPU-bound -> multiprocessing)
process_executor = MultiprocessExecutor(n_workers=4)
results = process_executor.execute(process_data, items=raw_data)
```

## Batch Utilities

```python
from py_parallelizer.utils import create_batches, flatten_results, create_batch_kwargs

# Split items into chunks
items = list(range(100))
batches = create_batches(items, batch_size=10)  # 10 batches of 10 items

# Flatten nested results
nested = [[1, 2], [3, 4], [5, 6]]
flat = flatten_results(nested)  # [1, 2, 3, 4, 5, 6]

# Create kwargs for zipped arguments
kwargs_list = create_batch_kwargs(x=[1, 2, 3], y=["a", "b", "c"])
# [{"x": 1, "y": "a"}, {"x": 2, "y": "b"}, {"x": 3, "y": "c"}]
```

## Common Pitfalls

### 1. Using multiprocessing for I/O-bound tasks
```python
# ❌ Bad: Multiprocessing has overhead, threads are better for I/O
results = executor.run_multiprocess(fetch_url, items=urls)

# ✅ Good: Use threads for I/O
results = executor.run_threaded(fetch_url, items=urls)
```

### 2. Lambda functions with multiprocessing
```python
# ❌ Bad: Lambdas can't be pickled
executor.run_multiprocess(lambda x: x * 2, items=[1, 2, 3])

# ✅ Good: Use named functions
def double(x):
    return x * 2
executor.run_multiprocess(double, items=[1, 2, 3])
```

### 3. Too many workers
```python
# ❌ Bad: More processes than CPU cores wastes resources
executor = MultiprocessExecutor(n_workers=100)

# ✅ Good: Match CPU cores for CPU-bound work
import os
executor = MultiprocessExecutor(n_workers=os.cpu_count())
```

### 4. Forgetting that multiprocessing copies data
```python
# ❌ Bad: Large objects get copied to each process
huge_data = load_huge_dataset()
def process(idx):
    return huge_data[idx]  # huge_data copied to each process!

# ✅ Good: Pass only what's needed
def process(item):
    return transform(item)
executor.run_multiprocess(process, items=huge_data)
```

### 5. Not handling exceptions
```python
# Results may contain None for failed items
# Check your results or add try/except in your worker function
def safe_process(x):
    try:
        return risky_operation(x)
    except Exception as e:
        return {"error": str(e), "item": x}
```

## API Reference

### ThreadedExecutor
```python
ThreadedExecutor(n_workers=4, show_progress=True, progress_desc="Processing")
executor.execute(func, items, **kwargs) -> list
```

### MultiprocessExecutor
```python
MultiprocessExecutor(n_workers=4, show_progress=True, progress_desc="Processing")
executor.execute(func, items, **kwargs) -> list
```

### ParallelExecutor
```python
ParallelExecutor(n_workers=4, show_progress=True, progress_desc="Processing")
executor.run_threaded(func, items, **kwargs) -> list
executor.run_multiprocess(func, items, **kwargs) -> list
```

## Coverage Report
<!-- Pytest Coverage Comment:Begin -->
<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/README.md"><img alt="Coverage" src="https://img.shields.io/badge/Coverage-80%25-green.svg" /></a><details><summary>Coverage Report </summary><table><tr><th>File</th><th>Stmts</th><th>Miss</th><th>Cover</th><th>Missing</th></tr><tbody><tr><td colspan="5"><b>src/py_parallelizer</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/base.py">base.py</a></td><td>45</td><td>2</td><td>96%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/base.py#L20">20</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/base.py#L111">111</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/logging_utils.py">logging_utils.py</a></td><td>19</td><td>2</td><td>89%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/logging_utils.py#L26-L27">26&ndash;27</a></td></tr><tr><td colspan="5"><b>src/py_parallelizer/executors</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/multiprocess.py">multiprocess.py</a></td><td>84</td><td>26</td><td>69%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/multiprocess.py#L41">41</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/multiprocess.py#L65-L71">65&ndash;71</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/multiprocess.py#L88-L94">88&ndash;94</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/multiprocess.py#L124-L135">124&ndash;135</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threaded.py">threaded.py</a></td><td>115</td><td>34</td><td>70%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threaded.py#L53-L55">53&ndash;55</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threaded.py#L117-L119">117&ndash;119</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threaded.py#L131">131</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threaded.py#L157-L162">157&ndash;162</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threaded.py#L168-L178">168&ndash;178</a>, <a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/executors/threaded.py#L183-L194">183&ndash;194</a></td></tr><tr><td><b>TOTAL</b></td><td><b>325</b></td><td><b>64</b></td><td><b>80%</b></td><td>&nbsp;</td></tr></tbody></table></details>
<!-- Pytest Coverage Comment:End -->
