# Chapter 3: Execution & Backtesting Cycle

**Goal**: Learn how to configure the `BacktestEngine`, assemble your strategy components, and run a complete simulation.

## 1. The Backtest Engine

The `BacktestEngine` is a "Time Machine". It accepts:
1.  **Valid Configuration**: (Trader ID, etc.)
2.  **Venues**: (Virtual Exchanges like "BINANCE")
3.  **Instruments**: (Definitions of what you trade)
4.  **Data**: (The history to replay)
5.  **Strategies**: (Your logic)

It then acts as a conductor, replaying data time-step by time-step and feeding it to your strategies.

---

## 2. Configuration Step-by-Step

### Step 1: Engine Config
```python
from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.model.identifiers import TraderId

config = BacktestEngineConfig(
    trader_id=TraderId("MY-BOT-001"),
    log_level="INFO", # Use "DEBUG" to see every single tick (Warning: Slow/Huge output)
)
```

### Step 2: Instantiating the Engine
```python
from nautilus_trader.backtest.engine import BacktestEngine

engine = BacktestEngine(config=config)
```

### Step 3: Adding a Venue
You must add a "Venue" (Exchange) where orders will go.
*   **BookType**: Crucial! If you use Tick Data, use `L1_MBP` (Level 1 Market By Price).
*   **AccountType**: `CASH` (Spot) or `MARGIN` (Futures).

```python
from nautilus_trader.model.enums import AccountType, BookType, OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money, Currency

# Define a Venue
BINANCE = Venue("BINANCE")

engine.add_venue(
    venue=BINANCE,
    oms_type=OmsType.NETTING,          # NETTING = Futures/Forex (Positions), HEDGING = individual deals
    account_type=AccountType.CASH,     # or MARGIN
    starting_balances=[Money(10_000, Currency.from_str("USDT"))],
    book_type=BookType.L1_MBP,         # Important for Tick Backtests
)
```

### Step 4: Adding an Instrument
The engine needs to know the rules of the symbol (e.g. min quantity, precision).
*   **Option A**: Use built-in test providers (e.g. `TestInstrumentProvider.ethusdt_binance()`).
*   **Option B**: Define your own `CurrencyPair` or `CryptoPerpetual` manual object.

```python
from nautilus_trader.test_kit.providers import TestInstrumentProvider

ETHUSDT = TestInstrumentProvider.ethusdt_binance()
engine.add_instrument(ETHUSDT)
```

### Step 5: Adding Data
(From Chapter 1)
```python
# Assuming 'ticks' is your list of wrangled TradeTicks
engine.add_data(ticks)
```

### Step 6: Adding Strategy
(From Chapter 2)
```python
from my_strategy import MyStrategy, MyStrategyConfig

# Configure your strategy
strat_config = MyStrategyConfig(
    instrument_id=ETHUSDT.id,
    bar_type=...
)

# Create an instance
strategy = MyStrategy(config=strat_config)

# Register with engine
engine.add_strategy(strategy)
```

---

## 3. Running the Simulation

```python
print("Running Backtest...")
engine.run()
print("Done!")
```

The engine will now process every tick in your data list.

---

## 4. Generating Reports & Analytics

After `engine.run()` returns, the memory contains all the results. You must extract them.

### Account Report (Balance over time)
```python
account_report = engine.trader.generate_account_report(BINANCE)
print(account_report)
# Tip: Plot the 'total' column to see equity curve
```

### Fills Report (List of Trades)
```python
fills = engine.trader.generate_fills_report()
# Save to CSV for Excel analysis
fills.to_csv("my_trades.csv")
```

### The "Tearsheet" (Visual Dashboard)
This is the best way to visualize performance.
```python
from nautilus_trader.analysis import create_tearsheet

create_tearsheet(engine, output_path="results.html")
print("Open results.html in your browser")
```

---

## 5. Troubleshooting Common Issues

### "Strategy didn't trade"
1.  **Check Data Date Range**: Did your data actually cover the period?
2.  **Check Logic**: Add `self.log.info("Checking...")` in `on_bar` to ensure it's actually running.
3.  **Check Cash**: Did you start with `USDT` but try to buy `BTC` with `USD`? Currencies must match exactly.
4.  **Check Instruments**: Did you `add_instrument(ETHUSDT)` but try to trade `BTCUSDT`?

### "BarType mismatch"
If you request `1-MINUTE` bars but your data is broken/sparse, bars might not form.
*   **Fix**: Ensure you have enough tick data to form bars.

### "Order Rejected: Insufficient Margin"
*   **Fix**: You are trying to buy more than your `starting_balances`. Decrease your trade quantity in `StrategyConfig`.
