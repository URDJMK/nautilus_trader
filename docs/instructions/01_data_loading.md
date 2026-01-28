# Chapter 1: Data Loading & Management

**Goal**: Learn how to acquire, clean, and load historical tick data from Bybit for Nautilus Trader using the `BacktestEngine`.

## 1. Introduction to Data in Nautilus

Nautilus Trader is an **Event-Driven** system. This means it replays history event-by-event (tick-by-tick) rather than just looking at a simple list of closing prices.

To get the most accurate backtest results, you should use **Trade Ticks** (actual transactions) or **Order Book Deltas** (market depth updates). While you *can* use OHLC Bars, they provide the lowest resolution and simulation quality.

In this chapter, we focus on **Bybit Trade Tick Data**, which is free, high-quality, and easy to access.

---

## 2. Acquiring Bybit Public Data

Bybit hosts a public repository of historical data at [public.bybit.com](https://public.bybit.com/trading/).

### Structure
The data is organized by **Symbol** and then by **Date**.
- **URL Pattern**: `https://public.bybit.com/trading/{SYMBOL}/{SYMBOL}{YYYY-MM-DD}.csv.gz`
- **Example**: `https://public.bybit.com/trading/ETHUSDT/ETHUSDT2023-11-01.csv.gz`

### Files
The files are **GZipped CSVs**. You do not need to unzip them manually; Python can read them directly.

### Download Script (Python)
Here is a robust script to download data for a specific range.

```python
import requests
import os
import pandas as pd

def download_bybit_data(symbol: str, start_date: str, end_date: str, download_dir: str = "data"):
    """
    Downloads daily compressed CSVs from Bybit public data.
    """
    os.makedirs(download_dir, exist_ok=True)
    dates = pd.date_range(start=start_date, end=end_date)
    
    for date in dates:
        date_str = date.strftime("%Y-%m-%d")
        filename = f"{symbol}{date_str}.csv.gz"
        url = f"https://public.bybit.com/trading/{symbol}/{filename}"
        
        output_path = os.path.join(download_dir, filename)
        
        if os.path.exists(output_path):
            print(f"Skipping {filename} (already exists)")
            continue

        print(f"Downloading {url} ...")
        response = requests.get(url)
        
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Saved to {output_path}")
        else:
            print(f"Failed to download {url} (Status: {response.status_code})")

# Example Usage:
# download_bybit_data("ETHUSDT", "2023-10-01", "2023-10-05")
```

---

## 3. The Nautilus Data Wrangler

Nautilus cannot simply "read any CSV". It uses strict internal objects (Rust structs) for performance. To bridge the gap between your CSV and Nautilus, we use a **Data Wrangler**.

For trade ticks, we use the `TradeTickDataWrangler`.

### What the Wrangler Expects
The `TradeTickDataWrangler.process()` method accepts a **Pandas DataFrame** with a specific index and column structure:

1.  **Index**: Must be named `timestamp` and contain `datetime64[ns, UTC]` values.
2.  **Column `price`**: Float64 (The price of the trade).
3.  **Column `quantity`**: Float64 (The size of the trade).
4.  **Column `side`** (Optional but Recommended): String (`"BUY"` or `"SELL"`) or `aggressor_side`.
5.  **Column `trade_id`** (Optional): String (Unique ID).

### Bybit CSV Format
A raw Bybit CSV usually has these columns:
`timestamp`, `symbol`, `side`, `size`, `price`, `tickDirection`, `trdMatchID`, `crossSeq`, `id`

We must **Map** (rename) these to what Nautilus wants.

---

## 4. Processing the Data (The ETL Pipeline)

Here is a thorough function to load and process Bybit data into a format Nautilus accepts.

### Step-by-Step Code

```python
from nautilus_trader.persistence.wranglers import TradeTickDataWrangler
from nautilus_trader.model.instruments import Instrument
import pandas as pd

def load_and_wrangle_bybit(filepath: str, instrument: Instrument):
    print(f"Loading {filepath}...")
    
    # 1. Read CSV (Handle GZIP automatically)
    df = pd.read_csv(filepath, compression="gzip")
    
    # 2. Rename columns
    # Bybit -> Nautilus Mapping
    df = df.rename(columns={
        "timestamp": "timestamp", # Often in seconds float
        "size": "quantity",       # "size" -> "quantity"
        "price": "price",         # "price" -> "price" (same)
        "side": "side",           # "side" -> "side" (same)
        "trdMatchID": "trade_id"  # "trdMatchID" -> "trade_id"
    })
    
    # 3. Process Timestamps
    # Bybit public timestamps are often Floats representing Seconds (e.g. 167888.1235)
    # We must convert to Datetime UTC.
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    
    # Set as Index
    df.set_index("timestamp", inplace=True)
    
    # 4. Filter and Sort
    # We only need the relevant columns
    df = df[["price", "quantity", "side", "trade_id"]]
    
    # CRITICAL: Data MUST be sorted by time or the Engine will crash/error
    df.sort_index(inplace=True)
    
    # 5. Type Enforcement (Optional but safe)
    df["side"] = df["side"].str.upper() # Ensure "Buy"/"Sell" are uppercase
    
    # 6. Wrangle
    # The wrangler uses the Instrument definition to check decimal precision
    wrangler = TradeTickDataWrangler(instrument=instrument)
    ticks = wrangler.process(df)
    
    return ticks
```

---

## 5. Merging Multiple Days

You usually want to backtest over weeks or months. DO NOT add data to the engine loop-by-loop. It is more efficient to combine your DataFrames first.

```python
import pandas as pd

def load_multiple_files(filenames, instrument):
    all_dfs = []
    
    for f in filenames:
        df = pd.read_csv(f, compression="gzip")
        # ... perform the renaming/cleaning here ...
        all_dfs.append(df)
        
    # Combine into one giant DataFrame
    full_df = pd.concat(all_dfs)
    
    # Sort ONCE at the end
    full_df["timestamp"] = pd.to_datetime(full_df["timestamp"], unit="s", utc=True)
    full_df.set_index("timestamp", inplace=True)
    full_df.sort_index(inplace=True)
    
    # Wrangle ONCE
    wrangler = TradeTickDataWrangler(instrument)
    ticks = wrangler.process(full_df)
    
    return ticks
```

---

## 6. Common Pitfalls & Errors

### 1. `ValueError: Data is not sorted`
**Cause**: The CSV was concatenated in the wrong order, or the raw data had out-of-order ticks (rare but happens).
**Fix**: Always call `df.sort_index(inplace=True)` before wrangling.

### 2. `Decimal Precision Error` regarding Instrument
**Cause**: Your `Instrument` definition (e.g. ETHUSDT) says `price_precision=2`, but your CSV has prices like `1800.12345`.
**Fix**: Ensure your `Instrument` matches the data real-world specs. The wrangler will typically handle rounding, but if it's way off, check your instrument provider.

### 3. `MemoryError`
**Cause**: Loading 1 year of Tick Data into RAM is massive.
**Fix**: 
    1. Filter the DataFrame (`df = df[columns]`) to drop unused columns like `crossSeq` immediately.
    2. Convert types (`float32` instead of `float64` if precision allows, though Nautilus prefers `float64`/`double`).
    3. Use **Parquet** format.

---

## 7. Advanced: Using Parquet for Speed

CSVs are slow to read. After you download and clean your data once, save it as `.parquet`.

```python
# Save processed dataframe
df.to_parquet("ETHUSDT_2023_CLEAN.parquet")

# Load instantly next time
df = pd.read_parquet("ETHUSDT_2023_CLEAN.parquet")
```

This reduces load times from minutes to seconds.
