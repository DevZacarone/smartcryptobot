
import numpy as np
import pandas as pd

def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    avg_gain = avg_gain.combine_first(gain.ewm(alpha=1/period, adjust=False).mean())
    avg_loss = avg_loss.combine_first(loss.ewm(alpha=1/period, adjust=False).mean())
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val.fillna(method="bfill")

def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def bollinger(series: pd.Series, period: int = 20, std: float = 2.0):
    ma = series.rolling(period).mean()
    sd = series.rolling(period).std(ddof=0)
    upper = ma + std * sd
    lower = ma - std * sd
    width = (upper - lower) / ma
    return ma, upper, lower, width
