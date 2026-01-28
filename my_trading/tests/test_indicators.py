# my_trading/tests/test_indicators.py
"""
Unit tests for custom indicators.

NOTE: Since we're using built-in Nautilus indicators,
this file is a placeholder for when you create custom indicators.
"""

import pytest


class TestPlaceholder:
    """Placeholder tests."""
    
    def test_built_in_indicators_exist(self):
        """Verify we can import built-in indicators."""
        from nautilus_trader.indicators import (
            SimpleMovingAverage,
            ExponentialMovingAverage,
            RelativeStrengthIndex,
            BollingerBands,
            AverageTrueRange,
        )
        
        # Create instances to verify they work
        sma = SimpleMovingAverage(period=20)
        ema = ExponentialMovingAverage(period=20)
        rsi = RelativeStrengthIndex(period=14)
        bb = BollingerBands(period=20)
        atr = AverageTrueRange(period=14)
        
        assert sma.period == 20
        assert ema.period == 20
        assert rsi.period == 14
        assert bb.period == 20
        assert atr.period == 14

    def test_indicator_not_initialized_by_default(self):
        """Verify indicators are not initialized before receiving data."""
        from nautilus_trader.indicators import SimpleMovingAverage
        
        sma = SimpleMovingAverage(period=5)
        
        assert not sma.initialized
        assert not sma.has_inputs
