"""
Custom Indicators Package.

Includes:
- FutureBollingerBands (Cython)
"""

try:
    from my_trading.indicators.future_bollinger_bands import FutureBollingerBands
except ImportError:
    # Fallback or warning if not compiled
    FutureBollingerBands = None
    pass

__all__ = [
    "FutureBollingerBands",
]
