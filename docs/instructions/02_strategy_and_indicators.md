# Chapter 2: Understanding Strategies, Indicators, and Instruments

This chapter provides a deep dive into the core concepts of Nautilus Trader.

---

## Part 1: Core Concepts and Relationships

Before writing any code, you must understand how the main pieces fit together.

### What is an Instrument?
An **Instrument** is a detailed definition of *what you are trading*. It is **not** price data; it describes the *rules* of the product.

Think of it like the rulebook for a game. It tells you:
*   The **name** (e.g., `ETHUSDT`).
*   The **venue** (the exchange, e.g., `BINANCE`).
*   **Price Precision**: How many decimal places a price can have (e.g., `2` means prices like `1800.50`).
*   **Size Precision**: How many decimal places a quantity can have (e.g., `5` means you can trade `0.00001` ETH).
*   **Minimum/Maximum Order Sizes**.
*   **Fees/Commissions**.

**Why is this important?**
When you send an order for `ETHUSDT`, the engine needs to know how to validate your request (e.g., is `0.01` a valid quantity?). The `Instrument` object provides this.

### What is a Strategy?
A **Strategy** is a Python class you write that contains your trading logic. It inherits from `Strategy` (which inherits from `Actor`).

**Key point**: A Strategy is **event-driven**. It doesn't run in a loop asking "what's the price now?". Instead, it *waits* for events:
*   "A new bar just closed" -> `on_bar()` is called.
*   "A trade just happened" -> `on_trade_tick()` is called.
*   "My order was filled" -> `on_order_filled()` is called.

You just implement the handler methods for the events you care about.

### What is an Indicator?
An **Indicator** is a math function that transforms data. For example, an Exponential Moving Average (EMA) takes a series of prices and outputs a smoothed average.

**Key point**: Indicators don't run on their own. They need to be *fed* data.

Nautilus has **two ways** to feed data to an indicator:
1.  **Automatic (Registration)**: You tell the engine "whenever a bar for `ETHUSDT` arrives, update this indicator automatically". This is fast and clean.
2.  **Manual**: You call the indicator's `update_raw()` method yourself in your handler.

---

## Part 2: How They Connect

Here is the flow:

```
        +----------------+
        |  Historical    |
        |    Data        |  (CSVs, Parquet Files)
        +--------+-------+
                 |
                 v
        +----------------+
        |  BacktestEngine|  (Replays Data as Events)
        +--------+-------+
                 |
  EVENTS:        |  (e.g., TradeTick, Bar)
                 v
+----------------+----------------+
|             Strategy             |
|                                  |
|  +----------+    +-----------+  |
|  | Indicator|<---| on_bar()  |  |
|  | (EMA)    |    | handler   |  |
|  +----------+    +-----------+  |
|                                  |
|         (uses Instrument)        |
|               |                  |
|               v                  |
|  +------------------------+      |
|  | self.submit_order(..)|-------> To the Venue (Simulated)
|  +------------------------+      |
+----------------------------------+
```

1.  **Data is loaded** and added to the `BacktestEngine`.
2.  The Engine **replays the data** event-by-event, calling your Strategy's handlers.
3.  Inside your handlers (e.g., `on_bar`), you access your **Indicator** to get a calculated value.
4.  Based on the indicator and price, you decide to trade.
5.  You call `self.submit_order()`, using the **Instrument** to ensure the order is valid.

---

## Part 3: The Strategy Lifecycle

A Strategy goes through specific lifecycle states. You hook into these via methods.

### `__init__(self, config)`
*   Called when the object is created.
*   **DO NOT** access `self.clock`, `self.log`, or `self.cache` here! They are not yet initialized.
*   **Use this for**: Storing config values, initializing your Indicator objects.

```python
def __init__(self, config: MyStrategyConfig):
    super().__init__(config)
    # GOOD: Initialize indicators here
    self.ema = ExponentialMovingAverage(period=config.ema_period)
    
    # BAD: Do NOT call self.clock or self.log here!
    # self.log.info("Hello")  <-- This will crash!
```

### `on_start(self)`
*   Called when the engine starts running.
*   **This is where you do setup**:
    *   Subscribe to data feeds.
    *   Register indicators.
    *   Request historical data.

```python
def on_start(self):
    # 1. Subscribe to bar data (so on_bar gets called)
    self.subscribe_bars(self.config.bar_type)
    
    # 2. Register indicator to receive bar updates automatically
    self.register_indicator_for_bars(self.config.bar_type, self.ema)
```

### `on_bar(self, bar: Bar)` / `on_trade_tick(self, tick: TradeTick)` / etc.
*   These are your **data handlers**.
*   Called every time a relevant data event arrives.

```python
def on_bar(self, bar: Bar):
    # Check if indicator has enough data to be meaningful
    if not self.ema.initialized:
        return
    
    # Access indicator value
    ema_value = self.ema.value
    
    # Your logic
    if bar.close.as_double() > ema_value:
        self.buy_market()
```

### `on_stop(self)`
*   Called when the strategy is stopped.
*   **Use this for**: Cleanup tasks, canceling orders.

---

## Part 4: Indicators In Detail

### Creating an Indicator
You create an indicator instance in `__init__`:
```python
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage

class MyStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        self.ema_fast = ExponentialMovingAverage(period=10)
        self.ema_slow = ExponentialMovingAverage(period=30)
```

### Registering an Indicator (The Key Step!)
An indicator object doesn't *do* anything until you **register** it. Registration tells Nautilus:
> "Every time a bar of type `{bar_type}` arrives, automatically update this indicator."

```python
def on_start(self):
    self.register_indicator_for_bars(self.config.bar_type, self.ema_fast)
    self.register_indicator_for_bars(self.config.bar_type, self.ema_slow)
```

### Checking if Initialized
An EMA with `period=20` needs 20 data points before its value is meaningful. Before that, it's "warming up".

```python
def on_bar(self, bar: Bar):
    if not self.ema_fast.initialized:
        self.log.info("EMA still warming up...")
        return
```

### Accessing the Value
Once initialized, get the value with `.value`:
```python
current_ema = self.ema_fast.value
```

---

## Part 5: Instruments In Detail

### Where do Instruments come from?
There are two main ways:

1.  **Test Providers** (for quick demos):
    ```python
    from nautilus_trader.test_kit.providers import TestInstrumentProvider
    
    ETHUSDT = TestInstrumentProvider.ethusdt_binance()
    engine.add_instrument(ETHUSDT)
    ```

2.  **Define Manually** (for full control):
    ```python
    from nautilus_trader.model.instruments import CurrencyPair
    from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
    from nautilus_trader.model.objects import Price, Quantity
    from nautilus_trader.model.currencies import USDT, ETH
    
    ETHUSDT = CurrencyPair(
        instrument_id=InstrumentId(Symbol("ETHUSDT"), Venue("BINANCE")),
        raw_symbol=Symbol("ETHUSDT"),
        base_currency=ETH,
        quote_currency=USDT,
        price_precision=2,   # e.g., 1850.50
        size_precision=5,    # e.g., 0.00001
        price_increment=Price.from_str("0.01"),
        size_increment=Quantity.from_str("0.00001"),
        maker_fee=Decimal("0.0002"), # 0.02%
        taker_fee=Decimal("0.0004"), # 0.04%
        min_quantity=Quantity.from_str("0.001"),
        max_quantity=Quantity.from_str("10000"),
        margin_init=Decimal("0"),
        margin_maint=Decimal("0"),
        ts_event=0,
        ts_init=0,
    )
    ```

### How does Strategy use Instrument?
The Strategy gets the Instrument definition from the `cache`:

```python
def on_start(self):
    self.instrument = self.cache.instrument(self.config.instrument_id)
    
    if self.instrument is None:
        self.log.error("Instrument not found! Did you add it to the engine?")
        self.stop()
        return
```

You then use the instrument to create properly formatted quantities and prices:
```python
# Make a quantity that respects the instrument's size precision
qty = self.instrument.make_qty(0.1)

# Make a price that respects the instrument's price precision
price = self.instrument.make_price(1850.50)
```

---

## Part 6: Order Submission

### The Order Factory
Every strategy has an `order_factory`. Use it to create order objects.

```python
from nautilus_trader.model.enums import OrderSide

def buy_market(self):
    order = self.order_factory.market(
        instrument_id=self.config.instrument_id,
        order_side=OrderSide.BUY,
        quantity=self.instrument.make_qty(0.1),
    )
    self.submit_order(order)
```

### Order Events
After you submit an order, you don't know if it worked. You find out via event handlers:

*   `on_order_submitted(event)`: The order was sent.
*   `on_order_accepted(event)`: The exchange accepted it.
*   `on_order_rejected(event)`: The exchange rejected it (e.g., insufficient funds).
*   `on_order_filled(event)`: A trade occurred!

```python
def on_order_filled(self, event: OrderFilled):
    self.log.info(f"Order filled: {event.last_qty} @ {event.last_px}")
```
