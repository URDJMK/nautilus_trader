# How to Create Custom Cython Indicators

This guide outlines the process for creating high-performance Cython indicators in the `my_trading` package. Follow these steps to ensure your indicator is correctly compiled, integrated, and tested.

## prerequisites

- Python installed (via Homebrew recommended)
- C Compiler (Xcode Command Line Tools on macOS)
- `cython` and `numpy` installed in your environment

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

## Step 2.5: Implement Tick Handlers (Critical for Real-Time)

To ensure your indicator updates **intra-bar** (on every price tick), you must implement these callback methods in your `.pyx` file:

```python
from nautilus_trader.model.data cimport QuoteTick, TradeTick
from nautilus_trader.model.objects cimport Price

    cpdef void handle_quote_tick(self, QuoteTick tick):
        cdef double bid = Price.raw_to_f64_c(tick._mem.bid_price.raw)
        cdef double ask = Price.raw_to_f64_c(tick._mem.ask_price.raw)
        cdef double mid = (ask + bid) / 2.0
        self.update_raw(mid)

    cpdef void handle_trade_tick(self, TradeTick tick):
        cdef double price = Price.raw_to_f64_c(tick._mem.price.raw)
        self.update_raw(price)
```
**Warning**: Ensure you keep specific imports like `Bar` if you use them! Don't accidentally remove imports when adding new ones.

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

## Step 4: Compile

You **MUST** compile the code for Python to see the changes. We have configured `setup.py` to automatically find your new `.pyx` file.

Run this command from the project root (`nautilus_trader/`):

```bash
# If using uv/venv, ensure you activate it first
source .venv/bin/activate

python my_trading/setup.py build_ext --inplace
```

*   **Success**: You will see compilation output and a `.so` file generated in the indicators folder.
*   **Failure**: Check the error message. Common issues include syntax errors in `.pyx` or missing imports.

## Step 5: Test Your Indicator

Create a test file in `my_trading/tests/` (e.g., `test_my_indicator.py`) to verify behavior.

**Example Test:**
```python
from my_trading.indicators import MyIndicator
from nautilus_trader.test_kit.stubs.data import TestDataStubs
import pytest

class TestMyIndicator:
    def test_initialization(self):
        ind = MyIndicator(period=10)
        assert ind.period == 10
        assert not ind.initialized

    def test_calculation(self):
        ind = MyIndicator(period=10)
        # Feed data
        ind.update_raw(100.0)
        assert ind.value == 100.0
```

Run the tests:
```bash
pytest my_trading/tests/test_my_indicator.py
```

## Summary Checklist
- [ ] Created `.pyx` file
- [ ] (Optional) Created `.pxd` file
- [ ] Added to `__init__.py`
- [ ] **Ran compilation command** (`python setup.py build_ext --inplace`)
- [ ] Wrote and ran tests
