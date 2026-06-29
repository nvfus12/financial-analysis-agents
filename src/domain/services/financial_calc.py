import pandas as pd
from typing import Tuple, Optional

def calculate_pe(price: float, eps: float) -> Optional[float]:
    """Calculates the Price-to-Earnings (P/E) ratio."""
    if not eps or eps <= 0:
        return None
    return round(price / eps, 2)

def calculate_roe(net_income: float, equity: float) -> Optional[float]:
    """Calculates the Return on Equity (ROE) as a percentage (e.g. 15.5 for 15.5%)."""
    if not equity or equity <= 0:
        return None
    return round((net_income / equity) * 100, 2)

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculates the Relative Strength Index (RSI) for a series of close prices.
    Returns a pandas Series of the same length containing RSI values (0-100).
    """
    if len(prices) < period:
        return pd.Series(index=prices.index, data=50.0)  # Return neutral default if data too short
        
    delta = prices.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    # Calculate Exponential Moving Averages (EMA)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    
    # Avoid division by zero
    rs = ema_up / ema_down.replace(0, 1e-9)
    
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def calculate_macd(
    prices: pd.Series, 
    fast_period: int = 12, 
    slow_period: int = 26, 
    signal_period: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculates the Moving Average Convergence Divergence (MACD).
    Returns a tuple of (macd_line, signal_line, macd_histogram).
    """
    if len(prices) < slow_period:
        default = pd.Series(index=prices.index, data=0.0)
        return default, default, default

    # Calculate EMAs
    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    
    return round(macd_line, 2), round(signal_line, 2), round(macd_histogram, 2)
