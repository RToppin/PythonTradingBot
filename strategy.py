import pandas as pd
from logger import log_status

class MovingAverageStrategy:
    def __init__(self, short_window=10, long_window=28):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, data):
        """
        A simple moving average strategy that buys when the short moving average (SMA) crosses above the long SMA 
        and sells when it crosses below. It generates buy and sell signals based on a moving average crossover.
        """

        # Ensure we are working with a copy of the data to avoid SettingWithCopyWarning
        data = data.copy()

        # Calculate the moving averages
        data['SMA_short'] = data['close'].rolling(window=self.short_window).mean()
        data['SMA_long'] = data['close'].rolling(window=self.long_window).mean()

        # Initialize 'Signal' column to 0
        data['Signal'] = 0

        # Create a signal: 1 = buy, 0 = hold, based on the moving average crossover
        data.loc[self.short_window:, 'Signal'] = (
            (data.loc[self.short_window:, 'SMA_short'] > data.loc[self.short_window:, 'SMA_long']).astype(int)
        )

        # Calculate the difference in 'Signal' to identify buy/sell positions
        # 1 means a buy signal (crossover up), -1 means a sell signal (crossover down)
        data['Position'] = data['Signal'].diff()

        return data
