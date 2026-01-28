# my_trading/indicators/__init__.py
"""
Custom Indicators Package.

IMPORTANT: Nautilus Trader already has 40+ built-in indicators!
Check `nautilus_trader.indicators` before creating your own.

Built-in indicators include:
    - SimpleMovingAverage, ExponentialMovingAverage, HullMovingAverage
    - RelativeStrengthIndex, Stochastics, MACD
    - BollingerBands, AverageTrueRange, KeltnerChannel
    - OnBalanceVolume, VolumeWeightedAveragePrice
    - And many more!

Example usage:
    from nautilus_trader.indicators import ExponentialMovingAverage, RelativeStrengthIndex
    
    ema = ExponentialMovingAverage(period=20)
    rsi = RelativeStrengthIndex(period=14)

Only create custom indicators here if you need something that doesn't exist.
"""

# Example: If you create a custom indicator, import it here
# from my_trading.indicators.my_custom_indicator import MyCustomIndicator

__all__ = []
