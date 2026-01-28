# my_trading/strategies/__init__.py
"""
Trading Strategies Package.

All custom strategies should be placed in this directory.
"""

from my_trading.strategies.base import BaseStrategy, BaseStrategyConfig
from my_trading.strategies.mean_reversion import MeanReversionStrategy, MeanReversionConfig

__all__ = [
    "BaseStrategy",
    "BaseStrategyConfig",
    "MeanReversionStrategy",
    "MeanReversionConfig",
]
