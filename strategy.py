# strategy.py
import pandas as pd

def moving_average_strategy(candles: pd.DataFrame):
    """
    단순 이동평균선 돌파 전략
    candles: DataFrame (열: timestamp, open, high, low, close, volume)
    """
    candles["ma20"] = candles["close"].rolling(20).mean()
    candles["ma50"] = candles["close"].rolling(50).mean()

    if candles["ma20"].iloc[-2] < candles["ma50"].iloc[-2] and candles["ma20"].iloc[-1] > candles["ma50"].iloc[-1]:
        return "LONG"
    elif candles["ma20"].iloc[-2] > candles["ma50"].iloc[-2] and candles["ma20"].iloc[-1] < candles["ma50"].iloc[-1]:
        return "SHORT"
    return "HOLD"
