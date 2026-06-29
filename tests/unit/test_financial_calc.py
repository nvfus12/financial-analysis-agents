import pytest
import pandas as pd
from src.domain.services.financial_calc import calculate_pe, calculate_roe, calculate_rsi, calculate_macd

def test_calculate_pe():
    assert calculate_pe(100.0, 5.0) == 20.0
    assert calculate_pe(100.0, 0.0) is None
    assert calculate_pe(100.0, -2.5) is None

def test_calculate_roe():
    assert calculate_roe(25.0, 100.0) == 25.0
    assert calculate_roe(10.0, 0.0) is None
    assert calculate_roe(10.0, -50.0) is None

def test_calculate_rsi():
    # Prices strictly increasing -> RSI should be high
    prices = pd.Series([10 + i for i in range(20)])
    rsi = calculate_rsi(prices, period=14)
    
    assert len(rsi) == len(prices)
    assert rsi.iloc[-1] > 90.0
    
    # Prices strictly decreasing -> RSI should be low
    prices_dec = pd.Series([100 - i for i in range(20)])
    rsi_dec = calculate_rsi(prices_dec, period=14)
    assert rsi_dec.iloc[-1] < 10.0

def test_calculate_macd():
    prices = pd.Series([100 + i for i in range(35)])
    macd, sig, hist = calculate_macd(prices)
    
    assert len(macd) == len(prices)
    assert len(sig) == len(prices)
    assert len(hist) == len(prices)
    
    # Simple mathematical assertions: hist = macd - sig (with a tolerance of 0.02 due to independent float rounding)
    assert hist.iloc[-1] == pytest.approx(macd.iloc[-1] - sig.iloc[-1], abs=0.02)
