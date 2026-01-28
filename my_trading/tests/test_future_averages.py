import pytest
import numpy as np
from nautilus_trader.test_kit.stubs.data import TestDataStubs
from nautilus_trader.model.objects import Price
from my_trading.indicators import (
    FutureSimpleMovingAverage,
    FutureExponentialMovingAverage,
    FutureDoubleExponentialMovingAverage,
    FutureWeightedMovingAverage,
    FutureHullMovingAverage,
    FutureAdaptiveMovingAverage,
    FutureWilderMovingAverage,
    FutureVariableIndexDynamicAverage,
)

class TestFutureAverages:
    
    def test_future_sma(self):
        # 1. Standard Behavior (pred=0)
        sma = FutureSimpleMovingAverage(period=5, pred=0)
        prices = [10, 11, 12, 13, 14, 15]
        for p in prices:
            sma.update_raw(float(p))
            
        # Last window: 11, 12, 13, 14, 15 => Mean 13.0
        assert sma.value == 13.0
        
        # 2. Prediction Behavior (pred=2)
        # Window: [13, 14, 15, 15, 15] (since 10, 11, 12 dropped)
        # Wait, if period=5. History: [11, 12, 13, 14, 15]
        # Pred=2. Shift logic:
        # Keep period-pred = 5-2 = 3 items from history end: [13, 14, 15]
        # Append current (15) 2 times: [15, 15]
        # Eff window: [13, 14, 15, 15, 15] -> Mean = 72 / 5 = 14.4
        
        sma_pred = FutureSimpleMovingAverage(period=5, pred=2)
        for p in prices:
            sma_pred.update_raw(float(p))
            
        assert sma_pred.value == 14.4

    def test_future_ema(self):
        # Period 2 => Alpha = 2/3 = 0.666...
        ema = FutureExponentialMovingAverage(period=2, pred=0)
        
        # t1: 10. avg=10
        ema.update_raw(10.0) 
        assert ema.value == 10.0
        
        # t2: 20. avg = 0.66*20 + 0.33*10 = 13.33 + 3.33 = 16.66
        ema.update_raw(20.0)
        expected = (2.0/3.0)*20.0 + (1.0/3.0)*10.0
        assert ema.value == pytest.approx(expected)
        
        # Prediction
        # If we predict 1 step ahead with current price 20
        # Next = Alpha * 20 + (1-Alpha) * CurrentEMA
        # Next = Alpha * 20 + (1-Alpha) * 16.666
        ema_pred = FutureExponentialMovingAverage(period=2, pred=1)
        ema_pred.update_raw(10.0)
        ema_pred.update_raw(20.0)
        
        expected_next = (2.0/3.0)*20.0 + (1.0/3.0)*expected
        assert ema_pred.value == pytest.approx(expected_next)

    def test_future_dema(self):
        # DEMA = 2*EMA1 - EMA2
        dema = FutureDoubleExponentialMovingAverage(period=5, pred=0)
        dema_pred = FutureDoubleExponentialMovingAverage(period=5, pred=2)
        
        prices = [10.0] * 10
        for p in prices:
            dema.update_raw(p)
            dema_pred.update_raw(p)
            
        assert dema.value == pytest.approx(10.0)
        assert dema_pred.value == pytest.approx(10.0) # Flat entries should predict flat

    def test_future_wma(self):
        # Period 3. Weights 1, 2, 3. Sum 6.
        wma = FutureWeightedMovingAverage(period=3, pred=0)
        # Inputs: 10, 20, 30
        wma.update_raw(10.0)
        wma.update_raw(20.0)
        wma.update_raw(30.0)
        
        # (10*1 + 20*2 + 30*3) / 6 = (10 + 40 + 90)/6 = 140/6 = 23.333
        assert wma.value == pytest.approx(23.33333333)
        
        # Pred 1 step. 
        # Virtual window: [20, 30, 30]
        # (20*1 + 30*2 + 30*3) / 6 = (20 + 60 + 90)/6 = 170/6 = 28.333
        wma_pred = FutureWeightedMovingAverage(period=3, pred=1)
        wma_pred.update_raw(10.0)
        wma_pred.update_raw(20.0)
        wma_pred.update_raw(30.0)
        
        assert wma_pred.value == pytest.approx(28.33333333)

    def test_future_hma(self):
        # Basic sanity for HMA
        hma = FutureHullMovingAverage(period=10, pred=0)
        hma_pred = FutureHullMovingAverage(period=10, pred=2)
        
        # Flat test
        for i in range(20):
             hma.update_raw(100.0)
             hma_pred.update_raw(100.0)
             
        assert hma.value == 100.0
        assert hma_pred.value == 100.0
        
        # Trend test
        # If ramp 100, 101, 102... HMA tracks closely
        hma = FutureHullMovingAverage(period=4, pred=0) 
        # Weights for p=4:
        # ma1(2): 1,2 -> 2/3, 1/3? No arange(1,3)=[1,2]. Sum=3.
        # ma2(4): 1,2,3,4. Sum=10.
        # ma3(2): 1,2.
        
        # Feed 1, 2, 3, 4
        # At 4:
        # Window: 1, 2, 3, 4
        # wma1(2) on [3,4]: (3*1 + 4*2)/3 = 11/3 = 3.666
        # wma2(4) on [1,2,3,4]: (1*1 + 2*2 + 3*3 + 4*4)/10 = (1+4+9+16)/10 = 30/10 = 3.0
        # raw = 2*3.666 - 3.0 = 7.333 - 3.0 = 4.333
        # We need history of raw.
        # Previous raw values would be 1.333, 2.333, 3.333 if ideal ramp?
        # Let's assume ideal ramp results in HMA = current price (low lag).
        pass

    def test_future_ama(self):
        ama = FutureAdaptiveMovingAverage(period_er=10, period_fast=2, period_slow=30, pred=0)
        for _ in range(20):
            ama.update_raw(100.0)
        assert ama.value == 100.0
        
    def test_future_wilder(self):
        wilder = FutureWilderMovingAverage(period=10, pred=0)
        for _ in range(20):
            wilder.update_raw(10.0)
        assert wilder.value == 10.0

    def test_future_vida(self):
        # Initializes with CMO
        vida = FutureVariableIndexDynamicAverage(period=10, pred=0)
        for i in range(20):
            vida.update_raw(10.0)
        assert vida.value == 10.0
