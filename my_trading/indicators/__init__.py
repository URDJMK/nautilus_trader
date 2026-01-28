"""
Custom Indicators Package.

Includes:
- FutureBollingerBands (Cython)
- FutureSimpleMovingAverage
- FutureExponentialMovingAverage
- FutureDoubleExponentialMovingAverage
- FutureWeightedMovingAverage
- FutureHullMovingAverage
- FutureAdaptiveMovingAverage
- FutureWilderMovingAverage
- FutureVariableIndexDynamicAverage
"""

try:
    from my_trading.indicators.future_bollinger_bands import FutureBollingerBands
    from my_trading.indicators.future_averages import (
        FutureSimpleMovingAverage,
        FutureExponentialMovingAverage,
        FutureDoubleExponentialMovingAverage,
        FutureWeightedMovingAverage,
        FutureHullMovingAverage,
        FutureAdaptiveMovingAverage,
        FutureWilderMovingAverage,
        FutureVariableIndexDynamicAverage,
    )
except ImportError:
    # Fallback or warning if not compiled
    FutureBollingerBands = None
    FutureSimpleMovingAverage = None
    FutureExponentialMovingAverage = None
    FutureDoubleExponentialMovingAverage = None
    FutureWeightedMovingAverage = None
    FutureHullMovingAverage = None
    FutureAdaptiveMovingAverage = None
    FutureWilderMovingAverage = None
    FutureVariableIndexDynamicAverage = None
    pass

__all__ = [
    "FutureBollingerBands",
    "FutureSimpleMovingAverage",
    "FutureExponentialMovingAverage",
    "FutureDoubleExponentialMovingAverage",
    "FutureWeightedMovingAverage",
    "FutureHullMovingAverage",
    "FutureAdaptiveMovingAverage",
    "FutureWilderMovingAverage",
    "FutureVariableIndexDynamicAverage",
]
