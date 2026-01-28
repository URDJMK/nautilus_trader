from nautilus_trader.indicators.base cimport Indicator
from nautilus_trader.indicators.momentum cimport EfficiencyRatio
from nautilus_trader.indicators.momentum cimport ChandeMomentumOscillator
cimport numpy as np

cdef class FutureSimpleMovingAverage(Indicator):
    cdef readonly int period
    cdef readonly int pred
    cdef readonly double value
    
    cdef object _inputs
    
    cpdef void update_raw(self, double value)

cdef class FutureExponentialMovingAverage(Indicator):
    cdef readonly int period
    cdef readonly int pred
    cdef readonly double value
    cdef readonly double alpha
    cdef double _real_value
    
    cpdef void update_raw(self, double value)

cdef class FutureDoubleExponentialMovingAverage(Indicator):
    cdef readonly int period
    cdef readonly int pred
    cdef readonly double value
    
    cdef double _ema1_real
    cdef double _ema2_real
    cdef double alpha
    
    cpdef void update_raw(self, double value)

cdef class FutureWeightedMovingAverage(Indicator):
    cdef readonly int period
    cdef readonly int pred
    cdef readonly double value
    cdef object weights
    cdef object _inputs
    
    cpdef void update_raw(self, double value)

cdef class FutureHullMovingAverage(Indicator):
    cdef readonly int period
    cdef readonly int pred
    cdef readonly double value
    
    cdef object _prices_deque
    cdef object _raw_deque
    
    cdef np.ndarray _w1
    cdef np.ndarray _w2
    cdef np.ndarray _w3
    
    cdef np.ndarray _get_weights(self, int size)
    cpdef void update_raw(self, double value)

cdef class FutureWilderMovingAverage(Indicator):
    cdef readonly int period
    cdef readonly int pred
    cdef readonly double value
    cdef readonly double alpha
    cdef double _real_value
    
    cpdef void update_raw(self, double value)

cdef class FutureAdaptiveMovingAverage(Indicator):
    cdef readonly int period_er
    cdef readonly int period_alpha_fast
    cdef readonly int period_alpha_slow
    cdef readonly int pred
    cdef readonly double value
    
    cdef readonly double alpha_fast
    cdef readonly double alpha_slow
    cdef readonly double alpha_diff
    
    cdef EfficiencyRatio _er_real
    cdef double _real_value
    
    cpdef void update_raw(self, double value)

cdef class FutureVariableIndexDynamicAverage(Indicator):
    cdef readonly int period
    cdef readonly int pred
    cdef readonly double value
    
    cdef ChandeMomentumOscillator cmo
    cdef double cmo_pct
    cdef double alpha
    cdef double _real_value
    
    cpdef void update_raw(self, double value)
