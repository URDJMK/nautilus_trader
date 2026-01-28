# my_trading/indicators/future_averages.pyx
# distutils: language = c++

from collections import deque
import numpy as np
cimport numpy as np
from libc.math cimport sqrt, pow, abs

from nautilus_trader.core.correctness cimport Condition
from nautilus_trader.indicators.base cimport Indicator
from nautilus_trader.model.data cimport Bar, QuoteTick, TradeTick
from nautilus_trader.model.objects cimport Price
from nautilus_trader.indicators.momentum cimport EfficiencyRatio, ChandeMomentumOscillator

# --------------------------------------------------------------------------------------
# 1. Future SMA
# --------------------------------------------------------------------------------------
cdef class FutureSimpleMovingAverage(Indicator):
    # Fields declared in .pxd

    def __init__(self, int period, int pred=0):
        Condition.positive_int(period, "period")
        Condition.not_negative(pred, "pred")
        super().__init__(params=[period, pred])
        
        self.period = period
        self.pred = pred
        self._inputs = deque(maxlen=period)
        self.value = 0.0

    cpdef void handle_quote_tick(self, QuoteTick tick):
        cdef double bid = Price.raw_to_f64_c(tick._mem.bid_price.raw)
        cdef double ask = Price.raw_to_f64_c(tick._mem.ask_price.raw)
        self.update_raw((ask + bid) / 2.0)

    cpdef void handle_trade_tick(self, TradeTick tick):
        self.update_raw(Price.raw_to_f64_c(tick._mem.price.raw))

    cpdef void handle_bar(self, Bar bar):
        self.update_raw(bar.close.as_double())

    cpdef void update_raw(self, double value):
        # 1. Update State
        self._inputs.append(value)
        if len(self._inputs) == self.period:
            self._set_initialized(True)
        else:
            self._set_has_inputs(True)

        # 2. Calculate
        cdef list window = list(self._inputs)
        
        if self.pred > 0:
            keep_count = self.period - self.pred
            if keep_count < 0:
                keep_count = 0 
            
            if len(window) < self.period:
                window.extend([value] * self.pred)
                if len(window) > self.period:
                     window = window[-self.period:]
            else:
                window = window[-keep_count:]
                window.extend([value] * (self.period - len(window)))

        cdef np.ndarray[np.double_t, ndim=1] arr = np.array(window, dtype=np.float64)
        self.value = np.mean(arr)

# --------------------------------------------------------------------------------------
# 2. Future EMA
# --------------------------------------------------------------------------------------
cdef class FutureExponentialMovingAverage(Indicator):
    # Fields declared in .pxd

    def __init__(self, int period, int pred=0):
        Condition.positive_int(period, "period")
        super().__init__(params=[period, pred])
        
        self.period = period
        self.pred = pred
        self.alpha = 2.0 / (period + 1.0)
        self.value = 0.0
        self._real_value = 0.0

    cpdef void handle_quote_tick(self, QuoteTick tick):
        cdef double bid = Price.raw_to_f64_c(tick._mem.bid_price.raw)
        cdef double ask = Price.raw_to_f64_c(tick._mem.ask_price.raw)
        self.update_raw((ask + bid) / 2.0)

    cpdef void handle_trade_tick(self, TradeTick tick):
        self.update_raw(Price.raw_to_f64_c(tick._mem.price.raw))

    cpdef void handle_bar(self, Bar bar):
        self.update_raw(bar.close.as_double())

    cpdef void update_raw(self, double value):
        if not self.has_inputs:
            self._real_value = value
            self._set_has_inputs(True)
            self._set_initialized(True)
        
        # Real Update
        self._real_value = self.alpha * value + (1.0 - self.alpha) * self._real_value
        
        # Predict
        cdef double proj = self._real_value
        if self.pred > 0:
            for _ in range(self.pred):
                proj = self.alpha * value + (1.0 - self.alpha) * proj
        
        self.value = proj


# --------------------------------------------------------------------------------------
# 3. Future DEMA (Double EMA)
# --------------------------------------------------------------------------------------
cdef class FutureDoubleExponentialMovingAverage(Indicator):
    # Fields declared in .pxd

    def __init__(self, int period, int pred=0):
        Condition.positive_int(period, "period")
        super().__init__(params=[period, pred])
        
        self.period = period
        self.pred = pred
        self.alpha = 2.0 / (period + 1.0)
        
        self.value = 0.0
        self._ema1_real = 0.0
        self._ema2_real = 0.0

    cpdef void handle_quote_tick(self, QuoteTick tick):
        cdef double bid = Price.raw_to_f64_c(tick._mem.bid_price.raw)
        cdef double ask = Price.raw_to_f64_c(tick._mem.ask_price.raw)
        self.update_raw((ask + bid) / 2.0)

    cpdef void handle_trade_tick(self, TradeTick tick):
        self.update_raw(Price.raw_to_f64_c(tick._mem.price.raw))

    cpdef void handle_bar(self, Bar bar):
        self.update_raw(bar.close.as_double())

    cpdef void update_raw(self, double value):
        if not self.has_inputs:
            self._ema1_real = value
            self._ema2_real = value
            self._set_has_inputs(True)
            self._set_initialized(True)

        # Real Update
        self._ema1_real = self.alpha * value + (1.0 - self.alpha) * self._ema1_real
        self._ema2_real = self.alpha * self._ema1_real + (1.0 - self.alpha) * self._ema2_real
        
        # Predict
        cdef double e1 = self._ema1_real
        cdef double e2 = self._ema2_real
        
        if self.pred > 0:
            for _ in range(self.pred):
                e1 = self.alpha * value + (1.0 - self.alpha) * e1
                e2 = self.alpha * e1 + (1.0 - self.alpha) * e2
        
        self.value = 2.0 * e1 - e2

# --------------------------------------------------------------------------------------
# 4. Future WMA
# --------------------------------------------------------------------------------------
cdef class FutureWeightedMovingAverage(Indicator):
    # Fields declared in .pxd
    
    def __init__(self, int period, int pred=0):
        Condition.positive_int(period, "period")
        super().__init__(params=[period, pred])
        
        self.period = period
        self.pred = pred
        self._inputs = deque(maxlen=period)
        
        self.weights = np.arange(1, period + 1, dtype=np.float64)
        cdef double w_sum = self.weights.sum()
        self.weights /= w_sum # Normalize
        
        self.value = 0.0

    cpdef void handle_quote_tick(self, QuoteTick tick):
        cdef double bid = Price.raw_to_f64_c(tick._mem.bid_price.raw)
        cdef double ask = Price.raw_to_f64_c(tick._mem.ask_price.raw)
        self.update_raw((ask + bid) / 2.0)

    cpdef void handle_trade_tick(self, TradeTick tick):
        self.update_raw(Price.raw_to_f64_c(tick._mem.price.raw))

    cpdef void handle_bar(self, Bar bar):
        self.update_raw(bar.close.as_double())

    cpdef void update_raw(self, double value):
        # 1. Update
        self._inputs.append(value)
        if len(self._inputs) == self.period:
            self._set_initialized(True)
        else:
            self._set_has_inputs(True)
            
        # 2. Window Construction
        cdef list window = list(self._inputs)
        
        if self.pred > 0:
            keep_count = self.period - self.pred
            if keep_count < 0: keep_count = 0
            
            if len(window) < self.period:
                 window.extend([value] * self.pred)
                 if len(window) > self.period:
                     window = window[-self.period:]
            else:
                window = window[-keep_count:]
                window.extend([value] * (self.period - len(window)))
        
        # 3. Calculate
        cdef np.ndarray data = np.array(window, dtype=np.float64)
        if len(data) == self.period:
            self.value = np.average(data, weights=self.weights)
        else:
            self.value = np.average(data, weights=self.weights[-len(data):])


# --------------------------------------------------------------------------------------
# 5. Future HMA
# --------------------------------------------------------------------------------------
cdef class FutureHullMovingAverage(Indicator):
    # Fields declared in .pxd

    def __init__(self, int period, int pred=0):
        Condition.positive_int(period, "period")
        super().__init__(params=[period, pred])
        
        self.period = period
        self.pred = pred
        self._prices_deque = deque(maxlen=period)
        
        cdef int p_half = int(period / 2)
        cdef int p_sqrt = int(sqrt(period))
        self._raw_deque = deque(maxlen=p_sqrt)
        
        self._w1 = self._get_weights(p_half)
        self._w2 = self._get_weights(period)
        self._w3 = self._get_weights(p_sqrt)
        
        self.value = 0.0

    cdef np.ndarray _get_weights(self, int size):
        cdef np.ndarray w = np.arange(1, size + 1, dtype=np.float64)
        return w / w.sum()

    cpdef void handle_quote_tick(self, QuoteTick tick):
        cdef double bid = Price.raw_to_f64_c(tick._mem.bid_price.raw)
        cdef double ask = Price.raw_to_f64_c(tick._mem.ask_price.raw)
        self.update_raw((ask + bid) / 2.0)

    cpdef void handle_trade_tick(self, TradeTick tick):
        self.update_raw(Price.raw_to_f64_c(tick._mem.price.raw))

    cpdef void handle_bar(self, Bar bar):
        self.update_raw(bar.close.as_double())

    cpdef void update_raw(self, double value):
        self._prices_deque.append(value)
        if len(self._prices_deque) == self.period:
            self._set_initialized(True)
        else:
            self._set_has_inputs(True)
        
        cdef int p_half = int(self.period / 2)
        cdef int p_sqrt = len(self._w3)
        
        # Real Calculation (no pred)
        cdef np.ndarray prices_arr = np.array(self._prices_deque, dtype=np.float64)
        cdef double w1_real
        cdef double w2_real
        
        # WMA 1 (n/2)
        cdef np.ndarray p1 = prices_arr[-p_half:]
        if len(p1) == p_half:
             w1_real = np.average(p1, weights=self._w1, axis=0)
        else:
             w1_real = np.average(p1, weights=self._w1[-len(p1):], axis=0)
             
        # WMA 2 (n)
        if len(prices_arr) == self.period:
             w2_real = np.average(prices_arr, weights=self._w2, axis=0)
        else:
             w2_real = np.average(prices_arr, weights=self._w2[-len(prices_arr):], axis=0)

        cdef double raw_real = 2.0 * w1_real - w2_real
        
        self._raw_deque.append(raw_real)
        
        # Future Calculation
        cdef list raw_window = list(self._raw_deque)
        
        if self.pred > 0:
            sim_prices = list(self._prices_deque)
            for _ in range(self.pred):
                sim_prices.append(value)
                if len(sim_prices) > self.period:
                    sim_prices.pop(0)
                
                sim_arr = np.array(sim_prices, dtype=np.float64)
                
                if len(sim_arr) == self.period:
                     s_w1 = np.average(sim_arr[-p_half:], weights=self._w1, axis=0)
                     s_w2 = np.average(sim_arr, weights=self._w2, axis=0)
                     s_raw = 2.0 * s_w1 - s_w2
                     
                     raw_window.append(s_raw)
                     if len(raw_window) > p_sqrt:
                         raw_window.pop(0)

        cdef np.ndarray raw_arr = np.array(raw_window, dtype=np.float64)
        if len(raw_arr) == p_sqrt:
            self.value = np.average(raw_arr, weights=self._w3, axis=0)
        else:
            self.value = np.average(raw_arr, weights=self._w3[-len(raw_arr):], axis=0)


# --------------------------------------------------------------------------------------
# 6. Future AMA (KAMA)
# --------------------------------------------------------------------------------------
cdef class FutureAdaptiveMovingAverage(Indicator):
    # Fields declared in .pxd

    def __init__(self, int period_er=10, int period_fast=2, int period_slow=30, int pred=0):
        super().__init__(params=[period_er, period_fast, period_slow, pred])
        
        self.period_er = period_er
        self.period_alpha_fast = period_fast
        self.period_alpha_slow = period_slow
        self.pred = pred
        
        self.alpha_fast = 2.0 / (float(period_fast) + 1.0)
        self.alpha_slow = 2.0 / (float(period_slow) + 1.0)
        self.alpha_diff = self.alpha_fast - self.alpha_slow
        
        self._er_real = EfficiencyRatio(period_er)
        self._real_value = 0.0
        self.value = 0.0

    cpdef void handle_quote_tick(self, QuoteTick tick):
        cdef double bid = Price.raw_to_f64_c(tick._mem.bid_price.raw)
        cdef double ask = Price.raw_to_f64_c(tick._mem.ask_price.raw)
        self.update_raw((ask + bid) / 2.0)

    cpdef void handle_trade_tick(self, TradeTick tick):
        self.update_raw(Price.raw_to_f64_c(tick._mem.price.raw))

    cpdef void handle_bar(self, Bar bar):
        self.update_raw(bar.close.as_double())

    cpdef void update_raw(self, double value):
        if not self.has_inputs:
            self._real_value = value
            self._set_has_inputs(True)
        
        # 1. Update Real
        self._er_real.update_raw(value)
        if self._er_real.initialized:
            self._set_initialized(True)
            
        cdef double sc = pow(self._er_real.value * self.alpha_diff + self.alpha_slow, 2)
        self._real_value = self._real_value + sc * (value - self._real_value)

        # 2. Predict
        cdef double proj = self._real_value
        
        if self.pred > 0:
            for _ in range(self.pred):
                 proj = proj + sc * (value - proj)
        
        self.value = proj

# --------------------------------------------------------------------------------------
# 7. Future Wilder
# --------------------------------------------------------------------------------------
cdef class FutureWilderMovingAverage(Indicator):
    # Fields declared in .pxd

    def __init__(self, int period, int pred=0):
        Condition.positive_int(period, "period")
        super().__init__(params=[period, pred])
        
        self.period = period
        self.pred = pred
        self.alpha = 1.0 / period
        self.value = 0.0
        self._real_value = 0.0

    cpdef void handle_quote_tick(self, QuoteTick tick):
        cdef double bid = Price.raw_to_f64_c(tick._mem.bid_price.raw)
        cdef double ask = Price.raw_to_f64_c(tick._mem.ask_price.raw)
        self.update_raw((ask + bid) / 2.0)

    cpdef void handle_trade_tick(self, TradeTick tick):
        self.update_raw(Price.raw_to_f64_c(tick._mem.price.raw))

    cpdef void handle_bar(self, Bar bar):
        self.update_raw(bar.close.as_double())

    cpdef void update_raw(self, double value):
        if not self.has_inputs:
            self._real_value = value
            self._set_has_inputs(True)
            self._set_initialized(True)
        
        # Real
        self._real_value = self.alpha * value + (1.0 - self.alpha) * self._real_value
        
        # Predict
        cdef double proj = self._real_value
        if self.pred > 0:
            for _ in range(self.pred):
                proj = self.alpha * value + (1.0 - self.alpha) * proj
        
        self.value = proj


# --------------------------------------------------------------------------------------
# 8. Future VIDA
# --------------------------------------------------------------------------------------
cdef class FutureVariableIndexDynamicAverage(Indicator):
    # Fields declared in .pxd

    def __init__(self, int period, int pred=0):
        super().__init__(params=[period, pred])
        self.period = period
        self.pred = pred
        self.cmo = ChandeMomentumOscillator(period)
        self.alpha = 2.0 / (period + 1.0)
        self._real_value = 0.0
        self.value = 0.0

    cpdef void handle_quote_tick(self, QuoteTick tick):
        cdef double bid = Price.raw_to_f64_c(tick._mem.bid_price.raw)
        cdef double ask = Price.raw_to_f64_c(tick._mem.ask_price.raw)
        self.update_raw((ask + bid) / 2.0)

    cpdef void handle_trade_tick(self, TradeTick tick):
        self.update_raw(Price.raw_to_f64_c(tick._mem.price.raw))

    cpdef void handle_bar(self, Bar bar):
        self.update_raw(bar.close.as_double())

    cpdef void update_raw(self, double value):
        if not self.has_inputs:
            self._real_value = value
            self._set_has_inputs(True)
        
        self.cmo.update_raw(value)
        if self.cmo.initialized:
            self._set_initialized(True)
            
        cdef double cmo_pct = abs(self.cmo.value / 100.0)
        
        # Real update
        if self.initialized:
            self._real_value = self.alpha * cmo_pct * value + (1.0 - self.alpha * cmo_pct) * self._real_value
        else:
            self._real_value = value # fallback
            
        # Predict
        cdef double proj = self._real_value
        if self.pred > 0:
            for _ in range(self.pred):
                 proj = self.alpha * cmo_pct * value + (1.0 - self.alpha * cmo_pct) * proj
        
        self.value = proj
