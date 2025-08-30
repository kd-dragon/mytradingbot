# backtest.py
import pandas as pd
from strategy import moving_average_strategy

def run_backtest(candles: pd.DataFrame):
    signals = []
    for i in range(50, len(candles)):
        signal = moving_average_strategy(candles.iloc[:i])
        signals.append(signal)
    return signals
