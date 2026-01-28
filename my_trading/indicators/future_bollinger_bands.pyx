# my_trading/indicators/future_bollinger_bands.pyx
# distutils: language = c++

from collections import deque
import numpy as np
cimport numpy as np
from libc.math cimport sqrt

from nautilus_trader.core.correctness cimport Condition
from nautilus_trader.indicators.base cimport Indicator
from nautilus_trader.model.data cimport QuoteTick
from nautilus_trader.model.data cimport TradeTick
from nautilus_trader.model.data cimport Bar
from nautilus_trader.model.objects cimport Price

cdef class FutureBollingerBands(Indicator):
    """
    Future Bollinger Bands indicator.
    
    Calculates Bollinger Bands with a 'prediction' feature that simulates
    future price action by repeating the latest price.
    
    Parameters
    ----------
    period : int
        Rolling window size.
    k_upper : float
        Standard deviation multiplier for upper band.
    k_lower : float
        Standard deviation multiplier for lower band.
    pred : int
        Number of future bars to predict (repeat current price).
    """
    
    # Fields are declared in .pxd file, so they are not repeated here.
    # Implementation follows.
    
    def __init__(self, int period, double k_upper=2.0, double k_lower=2.0, int pred=0):
        Condition.positive_int(period, "period")
        Condition.not_negative(pred, "pred")
        
        super().__init__(params=[period, k_upper, k_lower, pred])
        
        self.period = period
        self.k_upper = k_upper
        self.k_lower = k_lower
        self.pred = pred
        self._prices = deque(maxlen=period)
        
        self.upper = 0.0
        self.middle = 0.0
        self.lower = 0.0

    cpdef void handle_quote_tick(self, QuoteTick tick):
        cdef double bid = Price.raw_to_f64_c(tick._mem.bid_price.raw)
        cdef double ask = Price.raw_to_f64_c(tick._mem.ask_price.raw)
        cdef double mid = (ask + bid) / 2.0
        self.update_raw(mid)

    cpdef void handle_trade_tick(self, TradeTick tick):
        cdef double price = Price.raw_to_f64_c(tick._mem.price.raw)
        self.update_raw(price)

    cpdef void handle_bar(self, Bar bar):
        self.update_raw(bar.close.as_double())

    cpdef void update_raw(self, double price):
        # 1. Update real history
        self._prices.append(price)
        
        # Check initialization
        if not self.initialized:
            self._set_has_inputs(True)
            if len(self._prices) >= self.period:
                self._set_initialized(True)
            else:
                return

        # 2. Construct Calculation Window
        # We need a window of size `self.period`.
        # Standard: list(self._prices)
        # Prediction: Shift window by `pred`.
        
        # Convert to list to manipulate
        cdef list window = list(self._prices)
        
        if self.pred > 0:
            # If we predict 1 step, we effectively are at t+1.
            # The window should be [t-(N-1)+1 ... t+1]
            # Since t+1 is the *current* real price repeated (as we assume flat future),
            # And we want the window size to remain `period`.
            # We remove the oldest `pred` items and append `current_price` `pred` times.
            
            # NOTE: If we don't have enough history yet to pop (rare if initialized), guard it.
            # But we are initialized (len >= period).
            
            # Drop oldest 'pred' items
            # Append 'price' 'pred' times
            # Optimization: slice the list
            
            # Keep the last (period - pred) items
            keep_count = self.period - self.pred
            if keep_count < 0:
                keep_count = 0  # Should effectively just be all 'price'
            
            window = window[-keep_count:]
            # Append current price
            window.extend([price] * (self.period - len(window)))
           
        # 3. Calculate Stats using Numpy
        cdef np.ndarray[np.double_t, ndim=1] arr = np.array(window, dtype=np.float64)
        cdef double mean = np.mean(arr)
        cdef double std = np.std(arr)
        
        # 4. Set Values
        self.middle = mean
        self.upper = mean + (self.k_upper * std)
        self.lower = mean - (self.k_lower * std)

    cpdef void _reset(self):
        self._prices.clear()
        self.upper = 0.0
        self.middle = 0.0
        self.lower = 0.0
