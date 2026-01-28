#!/usr/bin/env python3
# my_trading/scripts/run_backtest.py
"""
Backtest Runner Script.

Usage:
    python -m my_trading.scripts.run_backtest
    
Or from project root:
    python my_trading/scripts/run_backtest.py
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add project root to path if running directly
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.enums import AccountType, BookType, OmsType
from nautilus_trader.model.objects import Money, Currency
from nautilus_trader.model.data import BarType
from nautilus_trader.test_kit.providers import TestInstrumentProvider, TestDataProvider

from my_trading.strategies import MeanReversionStrategy, MeanReversionConfig


def main():
    """Run the backtest."""
    print("=" * 60)
    print("NAUTILUS TRADER BACKTEST")
    print("=" * 60)

    # =========================================================================
    # 1. CREATE ENGINE
    # =========================================================================
    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id=TraderId("BACKTEST-001"),
            log_level="INFO",
        )
    )

    # =========================================================================
    # 2. SETUP VENUE
    # =========================================================================
    BINANCE = Venue("BINANCE")
    engine.add_venue(
        venue=BINANCE,
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        starting_balances=[Money(10_000, Currency.from_str("USDT"))],
        book_type=BookType.L1_MBP,
    )

    # =========================================================================
    # 3. SETUP INSTRUMENT
    # =========================================================================
    instrument = TestInstrumentProvider.ethusdt_binance()
    engine.add_instrument(instrument)
    
    bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")

    # =========================================================================
    # 4. LOAD DATA
    # =========================================================================
    # Using test data. Replace with real data for production.
    print(f"\nLoading test data for {instrument.id}...")
    provider = TestDataProvider()
    bars = provider.generate_bars(bar_type=bar_type, days=30)
    engine.add_data(bars)
    print(f"Loaded {len(bars)} bars")

    # =========================================================================
    # 5. CONFIGURE STRATEGY
    # =========================================================================
    config = MeanReversionConfig(
        instrument_id=instrument.id,
        bar_type=bar_type,
        trade_size=Decimal("0.1"),
        sma_period=20,
        entry_deviation=0.01,
    )
    strategy = MeanReversionStrategy(config=config)
    engine.add_strategy(strategy)

    # =========================================================================
    # 6. RUN BACKTEST
    # =========================================================================
    print("\nRunning backtest...")
    engine.run()
    print("Backtest complete!\n")

    # =========================================================================
    # 7. RESULTS
    # =========================================================================
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    # Account Report
    account_report = engine.trader.generate_account_report(BINANCE)
    print("\n--- Account Balance ---")
    print(account_report.to_string())
    
    # Fills Report
    fills = engine.trader.generate_fills_report()
    print(f"\n--- Trades: {len(fills)} ---")
    if len(fills) > 0:
        print(fills[["instrument_id", "order_side", "last_qty", "last_px"]].head(10))

    # Generate Tearsheet
    print("\n--- Generating Tearsheet ---")
    try:
        from nautilus_trader.analysis import create_tearsheet
        output_path = PROJECT_ROOT / "my_trading" / "backtest_results.html"
        create_tearsheet(engine, output_path=str(output_path))
        print(f"Tearsheet saved to: {output_path}")
    except ImportError:
        print("Install plotly for charts: pip install plotly>=6.3.1")


if __name__ == "__main__":
    main()
