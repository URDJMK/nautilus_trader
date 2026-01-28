# my_trading/strategies/base.py
"""
Base Strategy Class.

All custom strategies should inherit from this base class.
This provides common functionality and a consistent interface.
"""

from abc import abstractmethod
from decimal import Decimal

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.trading.strategy import Strategy


class BaseStrategyConfig(StrategyConfig):
    """
    Base configuration for all custom strategies.
    
    Add common config parameters here that all strategies should have.
    """
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal = Decimal("0.01")


class BaseStrategy(Strategy):
    """
    Abstract base class for all custom strategies.
    
    Provides:
    - Common initialization logic
    - Convenience methods for order submission
    - Standardized logging patterns
    """

    def __init__(self, config: BaseStrategyConfig) -> None:
        super().__init__(config)
        self.instrument: Instrument | None = None

    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------

    def on_start(self) -> None:
        """
        Base on_start that fetches the instrument.
        
        Subclasses should call super().on_start() first.
        """
        self.instrument = self.cache.instrument(self.config.instrument_id)
        
        if self.instrument is None:
            self.log.error(f"Instrument not found: {self.config.instrument_id}")
            self.stop()
            return
        
        self.log.info(f"Strategy started for {self.instrument.id}")
        self._on_start()

    @abstractmethod
    def _on_start(self) -> None:
        """
        Override this in subclasses for custom startup logic.
        
        Called after base initialization is complete.
        """
        raise NotImplementedError

    def on_stop(self) -> None:
        """Base on_stop with logging."""
        self.log.info("Strategy stopped")
        self._on_stop()

    def _on_stop(self) -> None:
        """Override in subclasses for custom cleanup."""
        pass

    # -------------------------------------------------------------------------
    # Position Helpers
    # -------------------------------------------------------------------------

    def is_flat(self) -> bool:
        """Return True if we have no open position."""
        position = self.cache.position(self.config.instrument_id)
        return position is None or position.is_flat

    def position_quantity(self) -> Decimal:
        """Return the current position quantity (0 if flat)."""
        position = self.cache.position(self.config.instrument_id)
        if position is None or position.is_flat:
            return Decimal(0)
        return Decimal(str(position.quantity))

    # -------------------------------------------------------------------------
    # Order Helpers
    # -------------------------------------------------------------------------

    def buy_market(self, quantity: Decimal | None = None) -> None:
        """Submit a market buy order."""
        qty = quantity or self.config.trade_size
        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(qty),
        )
        self.submit_order(order)
        self.log.info(f"BUY MARKET: {qty}")

    def sell_market(self, quantity: Decimal | None = None) -> None:
        """Submit a market sell order."""
        qty = quantity or self.config.trade_size
        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(qty),
        )
        self.submit_order(order)
        self.log.info(f"SELL MARKET: {qty}")

    def close_position(self) -> None:
        """Close any open position."""
        position = self.cache.position(self.config.instrument_id)
        if position is None or position.is_flat:
            return
        
        # Sell if long, buy if short
        if position.is_long:
            self.sell_market(Decimal(str(position.quantity)))
        else:
            self.buy_market(Decimal(str(position.quantity)))
