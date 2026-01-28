# How to Create Custom Cython Indicators

This guide outlines the process for creating high-performance Cython indicators in the `my_trading` package. Follow these steps to ensure your indicator is correctly compiled, integrated, and tested.

## prerequisites

- Python installed (via Homebrew recommended)
- C Compiler (Xcode Command Line Tools on macOS)
- `cython` and `numpy` installed in your environment
- `uv` for dependency management and running commands

## Step 1: Create the Source `.pyx` File

Create a new file in `my_trading/indicators/` (e.g., `my_indicator.pyx`).
This file contains the implementation logic.

**Key Requirements:**
1.  Inherit from `nautilus_trader.indicators.base.Indicator`.
2.  Declare fields using `cdef` for performance (or `readonly` if you need to access them in Python/Tests).
3.  Implement `handle_bar` (or `handle_quote_tick`, etc.) to process data.

**Example Template:**

```python
# my_trading/indicators/my_indicator.pyx
# distutils: language = c++

from nautilus_trader.core.correctness cimport Condition
from nautilus_trader.indicators.base cimport Indicator
from nautilus_trader.model.data cimport Bar

cdef class MyIndicator(Indicator):
    """
    Description of your indicator.
    """
    # Public Readonly fields (accessible in Python tests)
    cdef readonly int period
    cdef readonly double value

    def __init__(self, int period):
        super().__init__(params=[period])
        self.period = period
        self.value = 0.0

    cpdef void handle_bar(self, Bar bar):
        # Update logic here
        self.update_raw(bar.close.as_double())

    cpdef void update_raw(self, double price):
        self.value = price  # Your calc here
        self._set_initialized(True)
```

## Step 2: Create the Header `.pxd` File (Optional but Recommended)

Create a file with the same name `my_trading/indicators/my_indicator.pxd`.
This allows other Cython modules to access your indicator's internals efficiently.

```python
# my_trading/indicators/my_indicator.pxd
from nautilus_trader.indicators.base cimport Indicator

cdef class MyIndicator(Indicator):
    cdef readonly int period
    cdef readonly double value
    
    cpdef void update_raw(self, double price)
```

> [!CAUTION]
> **Duplicate Declaration Error**
> If you define a field (e.g., `period`, `value`) in the `.pxd` file, **DO NOT** declare it again in the `.pyx` file using `cdef`.
> The `.pxd` acts as the header; redeclaring it in the `.pyx` will cause a compilation error: *"C attributes cannot be added in implementation part of extension type defined in a pxd"*.

## Step 3: Register the Indicator

Add your indicator to `my_trading/indicators/__init__.py` so it can be imported easily.

```python
# my_trading/indicators/__init__.py
try:
    from my_trading.indicators.my_indicator import MyIndicator
except ImportError:
    pass

__all__ = ["MyIndicator"]
```

## Step 4: Compile & Build

We use `setup.py` configured to compile clean artifacts.

### Key `setup.py` Configurations
- **Parallel Compilation**: Uses `if __name__ == "__main__":` to allow `nthreads=4`. **Critical for macOS/multiprocessing**.
- **Clean Artifacts**: Output is directed to `build/` (intermediate files in `build/src`, libraries in `build/lib`).
- **Package Isolation**: `find_packages(include=["my_trading"])` prevents accidental inclusion of the root directory.

### Running the Build
Run via `run_tests_safe.py` (easiest) or manually:

```bash
# Using the helper script (Compiles + Tests)
uv run python my_trading/run_tests_safe.py

# Manual Build (if needed)
uv run python my_trading/setup.py build
```

## Step 5: Testing

Testing compiled extensions requires specific care to avoid importing the "empty" source directory instead of the compiled package.

### Best Practices (Learnings)
1.  **Use `--pyargs`**: Run pytest with `pytest --pyargs my_trading`. This forces pytest to import the package (finding the compiled version in `build/lib`) rather than looking at the local file system.
2.  **Clean `sys.path`**: Ensure the current working directory is **removed** from `sys.path` in your test runner to prevent shadowing the installed/compiled package.
3.  **Partial Data (HMA)**: When implementing complex indicators like HMA (WMA of WMA), ensure your initialization logic handles partial windows correctly (e.g., slicing weights to match available data `weights[-len(data):]`) to avoid shape mismatches during the first few bars.

### Running Tests
Use the safe runner which handles `sys.path` and `--pyargs` for you:

```bash
uv run python my_trading/run_tests_safe.py
```

## Implementation Tips
- **HMA Initialization**: If you have nested indicators dependent on window size (like HMA), use `np.average(..., axis=0)` and carefully match array shapes during the warm-up phase.
- **Debug Prints**: You can use `print()` in Cython, but ensure you access C-array shapes via `shape[0]` (e.g. `arr.shape[0]`) as `shape` alone returns a C-tuple/pointer not directly printable as a Python object in some contexts.

## Summary Checklist
- [ ] Created `.pyx` file (and optional `.pxd`)
- [ ] Added to `__init__.py`
- [ ] **Ran safe runner** (`uv run python my_trading/run_tests_safe.py`)
- [ ] Verified tests passed
