# py_parallelizer - AI Coding Agent Instructions

---
## 📋 Generic Code Standards (Reusable Across All Projects)


### Code Quality Principles

**DRY (Don't Repeat Yourself)**
- No duplicate code - extract common logic into reusable functions/classes
- If you copy-paste code, you're doing it wrong
- Shared utilities belong in `utils/` or helper modules

**CLEAN Code**
- **C**lear: Code intent is obvious from reading it
- **L**ogical: Functions do one thing, follow single responsibility principle
- **E**asy to understand: Junior developers should be able to review it
- **A**ccessible: Avoid clever tricks; prefer explicit over implicit
- **N**ecessary: Every line serves a purpose; no dead code

**Production-Grade Simplicity**
- Code must be production-ready (robust, tested, maintainable)
- Use the simplest solution that solves the problem completely
- Complexity is a last resort, not a goal
- **Target audience**: Code should be readable by junior software developers/data scientists

### Comments & Documentation Philosophy

**No Commented-Out Code**
- Never commit commented code blocks - use version control instead
- Delete unused code; git history preserves it if needed

**Docstrings: Only When Necessary**
- If code requires a docstring to be understood, it's probably too complex
- Refactor for clarity first, document as a last resort
- When used, docstrings explain **WHY**, not **HOW**
- Good function/variable names eliminate most documentation needs

**Comment Guidelines**
- Explain business logic rationale, not implementation mechanics
- Document non-obvious constraints or requirements
- If a comment explains what code does, rewrite the code to be self-explanatory
- Example:
  ```python
  # ❌ BAD: Explains what (obvious from code)
  # Loop through users and add to list
  for user in users:
      result.append(user)

  # ✅ GOOD: Explains why (non-obvious business rule)
  # Multiprocessing requires pickle serialization; lambdas cannot be pickled
  def square(x):
      return x ** 2
  ```

### Code Organization Standards

**Function Design**
- Functions should do **one thing** and do it well
- If a function has "and" in its description, it likely does too much
- Keep functions short (aim for <20 lines when possible)

**Import Management**
- Keep `__init__.py` files minimal - only version info and essential public API
- Prefer explicit imports: `from module.submodule import specific_function`
- Avoid importing from `__init__.py` in application code
- Long import statements are fine; they show dependencies clearly

**Separation of Concerns**
- Each module/class has a single, well-defined responsibility
- Business logic separated from I/O, API layers, and presentation
- Configuration separated from implementation

**Readability First**
- Variable names should be descriptive: `user_count` not `uc`
- Consistent naming conventions throughout the project
- Code is read 10x more than written - optimize for reading

### Development Tooling Standards

**Python Version**
- Follow Python syntax for the version specified in `pyproject.toml` (currently >=3.11)
- Backwards compatibility is NOT required - use modern Python features

**Package & Environment Management**
- Use `uv` for all virtual environment operations
- Always create venvs with: `uv venv .venv`
- Install dependencies with: `uv pip install -e ".[dev]"`

**Code Quality Tools**
- **ruff**: Primary linter and formatter (replaces black, isort, flake8)
  - Format code: `ruff format .`
  - Check code: `ruff check .`
  - Fix issues: `ruff check --fix .`
- Follow ruff's formatting style (no manual formatting needed)

**Testing**
- **pytest**: Only testing framework to use
- Always run tests in the `.venv` environment
- Execute with: `pytest` (picks up config from pyproject.toml)
- Coverage reports generated in `reports/htmlcov/`

### Meta-Instruction
**Keep these instructions updated** based on chat interactions when patterns emerge or decisions are made that should guide future development.

---

## Library Architecture

**Execution Models**
- **ThreadedExecutor**: For I/O-bound tasks (API calls, file operations, database queries)
- **MultiprocessExecutor**: For CPU-bound tasks (data processing, calculations, image manipulation)
- **ParallelExecutor**: Unified interface that switches between threading/multiprocessing

**Core Design Principle**
- Simple, flexible API: `run()` method accepts function + iterable of arguments
- Built-in progress bars via tqdm
- Graceful Ctrl+C handling returns partial results instead of crashing
- Thread-safe result collection via `results_function` callback

## Critical Usage Rules

**MUST use `if __name__ == "__main__":` with multiprocessing**
```python
from py_parallelizer import MultiprocessExecutor

def cpu_task(x):
    return x ** 2

if __name__ == "__main__":  # REQUIRED - prevents infinite process spawning
    executor = MultiprocessExecutor(max_workers=4)
    results = executor.run(cpu_task, range(100))
```
**Why**: Multiprocessing spawns new processes that re-import the module. Without the guard, code executes in each spawned process causing infinite recursion.

**Threading does NOT need `if __name__` guard**
```python
from py_parallelizer import ThreadedExecutor

executor = ThreadedExecutor(max_workers=10)
results = executor.run(io_task, urls)  # No guard needed
```

**Lambda functions CANNOT be used with multiprocessing**
```python
# ❌ WRONG - will fail with pickle error
executor = MultiprocessExecutor()
results = executor.run(lambda x: x**2, range(10))

# ✅ CORRECT - use named function
def square(x):
    return x ** 2

if __name__ == "__main__":
    results = executor.run(square, range(10))
```
**Why**: Multiprocessing uses pickle serialization; lambdas cannot be pickled.

## Common Patterns

**Multiple Arguments**
```python
# List of tuples - each tuple unpacked as function arguments
inputs = [(1, 2), (3, 4), (5, 6)]
executor.run(add_numbers, inputs)  # Calls add_numbers(1, 2), add_numbers(3, 4), etc.

# Dictionary unpacking - use create_batch_kwargs helper
from py_parallelizer import create_batch_kwargs
kwargs_list = create_batch_kwargs(
    [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
)
executor.run(add_numbers, kwargs_list)
```

**Thread-Safe Result Processing** (e.g., progress tracking, database writes)
```python
def process_result(result):
    # Called immediately when each task completes (thread-safe)
    db.save(result)

executor = ThreadedExecutor()
executor.run(task_func, inputs, results_function=process_result)
```

**Nested Parallelism** (Threading WITHIN Multiprocessing)
```python
from py_parallelizer import MultiprocessExecutor, ThreadedExecutor

def process_batch_with_io(batch):
    # Each process runs its own threaded executor for I/O
    thread_executor = ThreadedExecutor(max_workers=5)
    return thread_executor.run(fetch_url, batch)

if __name__ == "__main__":
    batches = create_batches(all_urls, batch_size=10)
    executor = MultiprocessExecutor(max_workers=4)
    results = executor.run(process_batch_with_io, batches)
    flat_results = flatten_results(results)
```

## Choosing Threading vs Multiprocessing

**Use ThreadedExecutor when:**
- Waiting on I/O (network requests, file reads, database queries)
- Tasks spend time blocked (sleep, waiting for external resources)
- Need to share state between tasks (objects, database connections)

**Use MultiprocessExecutor when:**
- CPU-intensive calculations (data processing, image manipulation)
- Tasks involve number crunching, transformations, computations
- Python GIL is the bottleneck (pure Python math operations)

**Avoid MultiprocessExecutor when:**
- Tasks involve I/O (will be slower due to process overhead)
- Using too many workers (rule of thumb: `os.cpu_count()` for CPU-bound)
- Data copying overhead exceeds computation time (large data structures)

## Development Workflow

**Setup**
```bash
uv venv .venv                    # Create virtual environment with uv
uv pip install -e ".[dev]"      # Install package and dev dependencies
pre-commit install              # Install pre-commit hooks
pre-commit run --all-files      # Run hooks on all files
```

**Code Quality**
```bash
ruff format .                   # Format all code
ruff check .                    # Check for issues
ruff check --fix .              # Auto-fix issues
```

**Testing**
```bash
pytest                          # Run all tests with coverage (reports/htmlcov/)
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest -v                       # Verbose output
```

**Distribution**
- Private GitHub repository - installation requires Personal Access Token
- See README.md "Installation" section for token setup
- Wheel files published to GitHub Releases

## Code Conventions

**Module Structure**
```
src/py_parallelizer/
├── executor.py              # ParallelExecutor (unified interface)
├── executors/
│   ├── threader.py          # ThreadedExecutor
│   └── multiprocess.py      # MultiprocessExecutor
└── utils/
    └── input_parsing.py     # create_batches, flatten_results, etc.
```

**Public API** (exported in `__init__.py`)
- `ParallelExecutor`, `ThreadedExecutor`, `MultiprocessExecutor`
- `create_batches`, `flatten_results`, `create_batch_kwargs`

**Testing Patterns**
- Integration tests demonstrate real-world usage patterns
- Unit tests verify individual component behavior
- Coverage target: >90% (see reports/htmlcov/)

## Common Pitfalls

- **Missing `if __name__` guard with multiprocessing** → infinite spawning
- **Lambda with multiprocessing** → PicklingError
- **Too many workers** → overhead exceeds benefit (use `os.cpu_count()`)
- **Multiprocessing for I/O** → slower than threading due to process overhead
- **Not handling exceptions** → failed tasks return None by default
- **Large data with multiprocessing** → copying overhead can negate parallelism benefits
