
import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.instruments.base import Instrument

from my_trading.utils.calculations import BreakevenCalculator


class TestBreakevenCalculator(unittest.TestCase):
    def setUp(self):
        # Mock Instrument
        self.mock_instrument = MagicMock(spec=Instrument)
        self.mock_instrument.maker_fee = Decimal("0.0002")  # 0.02%
        self.mock_instrument.taker_fee = Decimal("0.0005")  # 0.05%

    def test_long_breakeven_same_fees(self):
        """Test Long Breakeven with Taker Entry (0.05%) and Taker Exit (0.05%)"""
        entry_price = Decimal("10000")
        
        # Expected: Exit = Entry * (1 + 0.0005) / (1 - 0.0005)
        # Exit = 10000 * 1.0005 / 0.9995 = 10005 / 0.9995 = 10010.0050025
        expected = entry_price * (Decimal(1) + self.mock_instrument.taker_fee) / \
                   (Decimal(1) - self.mock_instrument.taker_fee)
        
        result = BreakevenCalculator.calculate_breakeven_price(
            entry_price=entry_price,
            side=OrderSide.BUY,
            instrument=self.mock_instrument,
            is_maker_entry=False,
            is_maker_exit=False
        )
        
        self.assertAlmostEqual(result, expected)
        self.assertTrue(result > entry_price)

    def test_short_breakeven_mixed_fees(self):
        """Test Short Breakeven with Taker Entry (0.05%) and Maker Exit (0.02%)"""
        entry_price = Decimal("10000")
        
        # Short: Entry - Exit - EntryFee - ExitFee = 0
        # Entry(1 - FeeIn) = Exit(1 + FeeOut)
        # Exit = Entry * (1 - 0.0005) / (1 + 0.0002)
        expected = entry_price * (Decimal(1) - self.mock_instrument.taker_fee) / \
                   (Decimal(1) + self.mock_instrument.maker_fee)
        
        result = BreakevenCalculator.calculate_breakeven_price(
            entry_price=entry_price,
            side=OrderSide.SELL,
            instrument=self.mock_instrument,
            is_maker_entry=False, # Taker
            is_maker_exit=True    # Maker
        )
        
        self.assertAlmostEqual(result, expected)
        self.assertTrue(result < entry_price)

    def test_manual_override(self):
        """Test with manual fee overrides ignoring instrument"""
        entry_price = 100
        manual_fee = 0.001 # 0.1%
        
        # Long: Exit = 100 * 1.001 / 0.999
        expected = Decimal(str(entry_price)) * Decimal("1.001") / Decimal("0.999")
        
        result = BreakevenCalculator.calculate_breakeven_price(
            entry_price=entry_price,
            side=OrderSide.BUY,
            instrument=None, # Should work without instrument if fees provided
            entry_fee_rate=manual_fee,
            exit_fee_rate=manual_fee
        )
        
        self.assertAlmostEqual(result, expected)

    def test_raises_value_error(self):
        """Test error when no instrument or fee rate provided"""
        with self.assertRaises(ValueError):
            BreakevenCalculator.calculate_breakeven_price(
                entry_price=100,
                side=OrderSide.BUY,
                instrument=None
            )

if __name__ == "__main__":
    unittest.main()
