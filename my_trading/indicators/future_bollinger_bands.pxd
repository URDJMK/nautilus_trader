from nautilus_trader.indicators.base cimport Indicator

cdef class FutureBollingerBands(Indicator):
    cdef public double upper
    cdef public double middle
    cdef public double lower
    
    cdef readonly int period
    cdef readonly double k_upper
    cdef readonly double k_lower
    cdef readonly int pred
    
    cdef object _prices
    
    cpdef void update_raw(self, double price)
    cpdef void _reset(self)
