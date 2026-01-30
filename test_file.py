from py_parallelizer import ParallelExecutor

def process_item(x, multiplier=2):
    return x * multiplier


# Simple usage
executor = ParallelExecutor(process_item)
results, interrupted = executor.run_threaded(x=[1, 2, 3, 4, 5])
print(results)  # [2, 4, 6, 8, 10]

# With extra kwargs
results, interrupted = executor.run_threaded(
    x=[1, 2, 3],
    multiplier=[10, 10, 10]
)
print(results)  # [10, 20, 30]


# Parallel execution using multiprocessing requires the function to be picklable
# And requires the `if __name__ == "__main__":` guard
# Having the code like this triggers the threading for each proceess as well, as each process will
# re-import the module and execute the code at the top level.
# This is unwanted behavior, so you should have all executing code inside the main guard
if __name__ == "__main__":

    # With extra kwargs
    results, interrupted = executor.run_multiprocess(
        x=[1, 2, 3],
        multiplier=[10, 10, 10]
    )
    print(results)  # [10, 20, 30]


# I need you to help me with the following tasks:

## Add uv instructions
Install uv
create venv using uv
uv venv .venv
uv pip install -r pyproject.toml
uv pip install -e .
How to build a wheel file using uv
How to install from a wheel file using uv

## Fix code examples in readme
the init of the class requires the function. The execture method takes the kwargs
Also, all arguments must be a list of the same length with the required input for the function
so the code example should be like above.
Add explicit instructions about the `if __name__ == "__main__":` guard when using multiprocessing


The multiple argumensts ection is incorret
Multiple Arguments
For functions requiring multiple varying arguments, use create_batch_kwargs:
The natch fnuction is used when combing parallel and thraedfing executors.

Please check the tests and understand how to call the code for the examples in the readme




## bug fixes:
[Thread-10 (_worker)] Failed processing task 0: process_item() got an unexpected keyword argument 'items'
invalid input arguments should raise an error because 'items' is not a valid argument for process_item