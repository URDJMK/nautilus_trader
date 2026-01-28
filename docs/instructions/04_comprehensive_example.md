# Chapter 4: The Complete "Out-of-the-Box" Example

**Goal**: A single "Copy-Paste" script that runs a strategy.

This script uses **Test Data** (randomly generated) so you can run it immediately without downloading any files. However, I have added comments showing exactly where to plug in your **real Bybit data**.

```python
import time
from decimal import Decimal
import pandas as pd

from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.model.identifiers import TraderId, InstrumentId, Venue
from nautilus_trader.model.enums import AccountType, BookType, OmsType, OrderSide
from nautilus_trader.model.objects import Money, Currency
from nautilus_trader.model.data import BarType, Bar
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import StrategyConfig
from nautilus_trader.test_kit.providers import TestInstrumentProvider, TestDataProvider
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage

# ==============================================================================
# 1. DEFINE STRATEGY
# ==============================================================================
class EMACrossConfig(StrategyConfig):
    instrument_id: InstrumentId
    bar_type: BarType
    fast_ema: int = 10
    slow_ema: int = 20
    trade_amt: float = 0.01

class EMACrossStrategy(Strategy):
    def __init__(self, config: EMACrossConfig):
        super().__init__(config)
        
        # Indicators
        self.fast_ema = ExponentialMovingAverage(config.fast_ema)
        self.slow_ema = ExponentialMovingAverage(config.slow_ema)

    def on_start(self):
        # Data Subscriptions
        self.subscribe_bars(self.config.bar_type)
        
        # Register Indicators (Auto-Update)
        self.register_indicator_for_bars(self.config.bar_type, self.fast_ema)
        self.register_indicator_for_bars(self.config.bar_type, self.slow_ema)

    def on_bar(self, bar: Bar):
        # Ensure indicators are ready
        if not self.fast_ema.initialized or not self.slow_ema.initialized:
            return

        # Check Logic
        fast = self.fast_ema.value
        slow = self.slow_ema.value
        
        # Log periodically
        # self.log.info(f"Price: {bar.close}, Fast: {fast:.2f}, Slow: {slow:.2f}")

        # Check Position
        position = self.cache.position(self.config.instrument_id)
        is_flat = position is None or position.is_flat
        
        # CROSSOVER LOGIC
        if fast > slow and is_flat:
            # BUY
            order = self.order_factory.market(
                instrument_id=self.config.instrument_id,
                order_side=OrderSide.BUY,
                quantity=self.config.trade_amt
            )
            self.submit_order(order)
            self.log.info(f"BUY SIGNAL @ {bar.close}")
            
        elif fast < slow and not is_flat:
             # SELL (Close Position)
             # We can't just "sell everything" with one command easily in Netting mode,
             # so we sell the exact size of our position.
             qty_to_close = position.quantity
             order = self.order_factory.market(
                instrument_id=self.config.instrument_id,
                order_side=OrderSide.SELL,
                quantity=qty_to_close
             )
             self.submit_order(order)
             self.log.info(f"SELL SIGNAL @ {bar.close}")

# ==============================================================================
# 2. RUN BACKTEST
# ==============================================================================
if __name__ == "__main__":
    # A. Setup Engine
    config = BacktestEngineConfig(trader_id=TraderId("DEMO-BOT"))
    engine = BacktestEngine(config=config)
    
    # B. Setup Venue (Binance)
    # We use L1_MBP because that's good for Tick Data
    BINANCE = Venue("BINANCE")
    engine.add_venue(
        venue=BINANCE,
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        starting_balances=[Money(10_000, Currency.from_str("USDT"))],
        book_type=BookType.L1_MBP
    )
    
    # C. Setup Instrument (ETHUSDT)
    # Use TestInstrumentProvider for ease, or define your own
    ETHUSDT = TestInstrumentProvider.ethusdt_binance()
    engine.add_instrument(ETHUSDT)
    
    # D. Load Data
    # --- REAL DATA (Commented Out) ---
    # from nautilus_trader.persistence.wranglers import TradeTickDataWrangler
    # df = pd.read_parquet("my_bybit_data.parquet") # Load your file
    # wrangler = TradeTickDataWrangler(instrument=ETHUSDT)
    # ticks = wrangler.process(df)
    # engine.add_data(ticks)
    
    # --- TEST DATA (Random) ---
    print("Generating Test Data...")
    provider = TestDataProvider()
    # We generate 1000 random bars just to make the script run
    bars = provider.generate_bars(
        bar_type=BarType.from_str(f"{ETHUSDT.id}-1-MINUTE-LAST-EXTERNAL"),
        days=10
    )
    engine.add_data(bars)
    
    # E. Add Strategy
    strat_config = EMACrossConfig(
        instrument_id=ETHUSDT.id,
        bar_type=BarType.from_str(f"{ETHUSDT.id}-1-MINUTE-LAST-EXTERNAL"),
        trade_amt=0.1
    )
    strategy = EMACrossStrategy(config=strat_config)
    engine.add_strategy(strategy)
    
    # F. Run
    print("Running Backtest...")
    engine.run()
    print("Backtest Complete!")
    
    # G. Report
    print("\n--- Account Balance ---")
    print(engine.trader.generate_account_report(BINANCE))
    
    print("\n--- Generating Tearsheet ---")
    try:
        from nautilus_trader.analysis import create_tearsheet
        create_tearsheet(engine, output_path="demo_results.html")
        print("Success! Open 'demo_results.html'")
    except ImportError:
        print("Please install plotly to see charts: pip install plotly>=6.3.1")
```

## How to use this
1.  Copy the code into a file `run_test.py`.
2.  Run it: `python run_test.py`.
3.  Open `demo_results.html` to see your strategy in action!
