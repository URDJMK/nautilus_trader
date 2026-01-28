# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2024 Nautech Systems Pty Ltd. All rights reserved.
# -------------------------------------------------------------------------------------------------

from decimal import Decimal
from typing import Optional

from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.instruments.base import Instrument


class BreakevenCalculator:
    """
    Utilities for calculating breakeven prices and PnL considering fees.
    
    This class supports scalable calculations for multiple exchanges by relying on:
    1. Instrument properties (maker_fee, taker_fee) which vary per instrument/exchange.
    2. Optional manual fee overrides for custom scenarios.
    
    The breakeven formula used is derived to ensure Net PnL is zero:
    
    Net PnL = (Exit Value - Entry Value) - (Entry Fee + Exit Fee)
    
    For percentage based fees:
       Entry Fee = Entry Price * Quantity * Fee Rate
       Exit Fee = Exit Price * Quantity * Fee Rate
       
       Long Breakeven:  Exit = Entry * (1 + EntryFeeRate) / (1 - ExitFeeRate)
       Short Breakeven: Exit = Entry * (1 - EntryFeeRate) / (1 + ExitFeeRate)
    """

    @staticmethod
    def calculate_breakeven_price(
        entry_price: Decimal | float,
        side: OrderSide,
        instrument: Optional[Instrument] = None,
        is_maker_entry: bool = False,
        is_maker_exit: bool = False,
        entry_fee_rate: Optional[Decimal | float] = None,
        exit_fee_rate: Optional[Decimal | float] = None,
    ) -> Decimal:
        """
        Calculate the exit price required to break even (Net PnL = 0).

        Parameters
        ----------
        entry_price : Decimal | float
            The average entry price of the position.
        side : OrderSide
            The side of the ENTRY order (BUY for Long, SELL for Short).
        instrument : Instrument, optional
            The instrument to retrieve default fee rates from.
        is_maker_entry : bool, default False
            If the entry was a maker order (used to select fee rate from instrument).
        is_maker_exit : bool, default False
            If the planned exit is a maker order (used to select fee rate from instrument).
        entry_fee_rate : Decimal | float, optional
            Manual override for entry fee rate (e.g. 0.001 for 0.1%). 
            If provided, ignores instrument/is_maker_entry.
        exit_fee_rate : Decimal | float, optional
            Manual override for exit fee rate.
            If provided, ignores instrument/is_maker_exit.

        Returns
        -------
        Decimal
            The price at which the trade breaks even.
        
        Raises
        ------
        ValueError
            If neither instrument nor fee rates are provided.
        """
        entry_price_dec = Decimal(str(entry_price))
        
        # Determine Fee Rates
        fee_in = BreakevenCalculator._resolve_fee_rate(
            instrument, entry_fee_rate, is_maker_entry
        )
        fee_out = BreakevenCalculator._resolve_fee_rate(
            instrument, exit_fee_rate, is_maker_exit
        )

        # Calculate Breakeven
        if side == OrderSide.BUY:
            # Long: (Exit - Entry) - (Entry * FeeIn) - (Exit * FeeOut) = 0
            # Exit * (1 - FeeOut) = Entry * (1 + FeeIn)
            # Exit = Entry * (1 + FeeIn) / (1 - FeeOut)
            if fee_out >= 1:
                raise ValueError("Exit fee rate cannot be >= 100% for long breakeven.")
            return entry_price_dec * (1 + fee_in) / (1 - fee_out)
            
        else: # OrderSide.SELL
            # Short: (Entry - Exit) - (Entry * FeeIn) - (Exit * FeeOut) = 0
            # Entry * (1 - FeeIn) = Exit * (1 + FeeOut)
            # Exit = Entry * (1 - FeeIn) / (1 + FeeOut)
            return entry_price_dec * (1 - fee_in) / (1 + fee_out)

    @staticmethod
    def _resolve_fee_rate(
        instrument: Optional[Instrument], 
        override_rate: Optional[Decimal | float], 
        is_maker: bool
    ) -> Decimal:
        if override_rate is not None:
            return Decimal(str(override_rate))
        
        if instrument is None:
            raise ValueError("Must provide either `instrument` or explicit fee rates.")
            
        if is_maker:
            return instrument.maker_fee
        else:
            return instrument.taker_fee
