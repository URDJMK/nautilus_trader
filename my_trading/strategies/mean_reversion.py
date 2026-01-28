# my_trading/strategies/mean_reversion.py
"""
Mean Reversion Strategy.

Uses the BUILT-IN SimpleMovingAverage from nautilus_trader.indicators.
"""

from decimal import Decimal

from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.events import OrderFilled
from nautilus_trader.model.identifiers import InstrumentId

# USE THE BUILT-IN INDICATOR!
from nautilus_trader.indicators import SimpleMovingAverage

from my_trading.strategies.base import BaseStrategy, BaseStrategyConfig


class MeanReversionConfig(BaseStrategyConfig):
    """
    Configuration for MeanReversionStrategy.
    """
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal = Decimal("0.1")
    
    # Strategy-specific parameters
    sma_period: int = 20
    entry_deviation: float = 0.01  # Buy when price is 1% below SMA


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy.
    
    Entry Logic:
        - BUY when price is `entry_deviation` percent below SMA
        
    Exit Logic:
        - SELL when price returns to or above SMA
    """

    def __init__(self, config: MeanReversionConfig) -> None:
        super().__init__(config)
        
        # Use the BUILT-IN SimpleMovingAverage indicator
        self.sma = SimpleMovingAverage(period=config.sma_period)

    def _on_start(self) -> None:
        """Custom startup logic."""
        # Subscribe to bar data
        self.subscribe_bars(self.config.bar_type)
        
        # Register indicator for automatic updates
        self.register_indicator_for_bars(self.config.bar_type, self.sma)
        
        self.log.info(f"Using indicator: {self.sma.name}")
        self.log.info(f"Entry deviation: {self.config.entry_deviation * 100:.1f}%")

    def on_bar(self, bar: Bar) -> None:
        """Process a new bar."""
        # Wait for indicator to be initialized
        if not self.sma.initialized:
            return
        
        price = bar.close.as_double()
        sma_value = self.sma.value
        deviation = (price - sma_value) / sma_value
        
        # Entry: Price is significantly below SMA
        if deviation < -self.config.entry_deviation and self.is_flat():
            self.buy_market()
        
        # Exit: Price has reverted to or above SMA
        elif deviation >= 0 and not self.is_flat():
            self.close_position()

    def on_order_filled(self, event: OrderFilled) -> None:
        """Log filled orders."""
        self.log.info(
            f"FILLED: {event.order_side} {event.last_qty} @ {event.last_px}"
        )
