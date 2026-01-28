from decimal import Decimal
from nautilus_trader.model.enums import OrderSide
from my_trading.utils.calculations import BreakevenCalculator

def main():
    print("=== Breakeven Calculator Demo ===\n")

    # 1. Initialize Calculator
    calc = BreakevenCalculator()

    # 2. Define Scenario: Long Position on BTC/USDT
    entry_price = Decimal("50000.00")  # Entered at $50,000
    qty = Decimal("1.0")               # 1 BTC
    
    # 3. Fees (e.g. Bybit Taker Fee 0.055%, Maker 0.02%)
    # Note: Fees must be Decimals. 0.055% = 0.00055
    maker_fee = Decimal("0.0002")  # 0.02%
    taker_fee = Decimal("0.00055") # 0.055%

    print(f"Scenario: LONG 1 BTC @ ${entry_price}")
    print(f"Fees: Entry Taker ({taker_fee*100}%), Exit Maker ({maker_fee*100}%)")

    # 4. Calculate Breakeven
    # We paid Taker fee on entry, plan to pay Maker fee on exit
    be_price = calc.calculate_breakeven_price(
        entry_price=entry_price,
        side=OrderSide.BUY,
        entry_fee_rate=taker_fee,
        exit_fee_rate=maker_fee
    )

    print(f"\nBreakeven Exit Price: ${be_price:.2f}")
    
    # Validation
    # Entry Cost = 50000 + (50000 * 0.00055) = 50027.5
    # Exit Revenue needed = 50027.5 / (1 - 0.0002) = 50037.506...
    entry_cost = entry_price * (1 + taker_fee)
    exit_revenue = be_price * (1 - maker_fee)
    pnl = exit_revenue - entry_cost
    
    print(f"Verification PnL: {pnl:.10f} (Should be ~0.0)")

    # 5. Scenario: Short Position
    print("\n--------------------------------")
    print("Scenario: SHORT 1 BTC @ $50,000")
    print(f"Fees: Entry Maker ({maker_fee*100}%), Exit Taker ({taker_fee*100}%)")
    
    be_price_short = calc.calculate_breakeven_price(
        entry_price=entry_price,
        side=OrderSide.SELL,
        entry_fee_rate=maker_fee,
        exit_fee_rate=taker_fee
    )
    
    print(f"\nBreakeven Exit Price: ${be_price_short:.2f}")
    
    # Validation Short
    # Entry Revenue = 50000 * (1 - 0.0002) = 49990
    # Exit Cost needed = 49990 / (1 + 0.00055) = 49962.52...
    entry_revenue = entry_price * (1 - maker_fee)
    exit_cost = be_price_short * (1 + taker_fee)
    pnl_short = entry_revenue - exit_cost
    print(f"Verification PnL: {pnl_short:.10f} (Should be ~0.0)")

if __name__ == "__main__":
    main()
