import time
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
import pandas as pd
import argparse
import requests
from config import API_KEY, SECRET_KEY, BASE_URL, DEFAULT_QUANTITY, DEFAULT_SYMBOL, TRADE_LENGTH
from logger import log_status
from strategy import MovingAverageStrategy


class TradingBot:
    def __init__(self):
        # Initialize the Alpaca trade API connection
        self.api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
        self.symbol = DEFAULT_SYMBOL
        self.quantity = DEFAULT_QUANTITY
        self.strategy = MovingAverageStrategy()

        # Status tracking
        self.cash = 0
        self.position = 0
        self.status = 'Idle'  # Tracks the bot's status

    def get_account_status(self):
        # Check the account balance and buying power
        account = self.api.get_account()
        self.cash = float(account.cash)
        log_status(f"Current cash balance: {self.cash}")
        self.position = float(account.buying_power)
        log_status(f"Current buying power: {self.position}")

    def get_historical_data(self):
        # Get Historical data for the stock
        log_status(f"Fetching historical data for {self.symbol}...")
        bars = self.api.get_bars(self.symbol, '1Day', limit=100)  # Get the last 100 days of stock data
        data = pd.DataFrame([{
            'time': bar.t,
            'open': bar.o,
            'high': bar.h,
            'low': bar.l,
            'close': bar.c,  # Extract the 'close' price
            'volume': bar.v
        }for bar in bars])
        return data

    def check_signals_and_trade(self, data):
        # Apply the trading strategy and execute trades based on signals
        log_status(f"Applying strategy to {self}")
        signals = self.strategy.generate_signals(data)

        # Check the most recent position
        latest_position = signals['Position'].iloc[-1]  # Grabs the last signal

        # Buy signal (Position = 1)
        if latest_position == 1:
            log_status(f"Buy signal detected. Placing order for {self.symbol}...")
            self.place_order('buy')

        # Sell signal (Position = -1)
        elif latest_position == -1:
            log_status(f"Sell signal detected. Placing order for {self.symbol}...")
            self.place_order('sell')
        else:
            log_status(f"No buy/sell signal detected. Holding Position.")

    def place_order(self, side):
        # Place an order to buy or sell
        try:
            order = self.api.submit_order(
                symbol=self.symbol,
                qty=self.quantity,
                side=side,
                type='market',
                time_in_force='gtc'  # Good till cancel
            )
            log_status(f"Order Placed: {side} {self.quantity} shares of {self.symbol}")
        except Exception as e:
            log_status(f"Error placing order: {e}")

    def run(self):
        # Main bot loop that checks for signals and trades at intervals
        while True:
            log_status("Starting new cycle...")
            self.get_account_status()  # Check account balance and status
            data = self.get_historical_data()  # Fetch stock data
            self.check_signals_and_trade(data)  # Apply strategy and trade
            log_status(f"Cycle complete. Bot now idling...\n")
            time.sleep(1)  # Sleep for an hour before the next cycle

class BacktestTradingBot:
    def __init__(self, symbol="BTC/USD", cash=500000, quantity=10):
        # Default trading parameters for backtest
        self.symbol = DEFAULT_SYMBOL
        self.quantity = DEFAULT_QUANTITY
        self.cash = cash  # Start with $500,000 cash
        self.position = 0  # No initial stock position
        self.share_price = 0  # Track the price at which shares are bought/sold
        self.strategy = MovingAverageStrategy()  # Assuming you have this strategy class

    def get_historical_data(self):
        """Fetch historical data for backtesting."""
        startDate = str(datetime.today().date() - timedelta(days=TRADE_LENGTH))
        endDate = str(datetime.today().date())
        limit = 1000
        timeframe = '1Day'

        # Use self.symbol for flexibility
        url = f'https://data.alpaca.markets/v1beta3/crypto/us/bars?symbols={self.symbol}&timeframe={timeframe}&start={startDate}&end={endDate}&limit={limit}&sort=asc'
        headers = {"accept": "application/json"}

        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            bars = response.json()
            if 'bars' in bars and self.symbol in bars['bars']:
                bar_data = bars['bars'][self.symbol]

                data = pd.DataFrame([{
                    'time': bar['t'],  # Timestamp
                    'open': bar['o'],  # Open price
                    'high': bar['h'],  # High price
                    'low': bar['l'],  # Low price
                    'close': bar['c'],  # Close price
                    'volume': bar['v']   # Volume traded
                } for bar in bar_data])
                #log_status(data)
                return data
            else:
                print(f"No data found for symbol {self.symbol}.")
                return pd.DataFrame()
        else:
            print(f"Error fetching data: {response.status_code}, {response.text}")
            return pd.DataFrame()

    def run_backtest(self):
        """Simulate 175 days of trading based on the last 50 days of data."""
        data = self.get_historical_data()

        # If no data, stop the backtest
        if data.empty:
            print("No data available for backtest.")
            return

        # Simulate trading for the next 175 days, starting with day 50 for ample market data
        for i in range(50, len(data)):  # Start from day 50 (or TRADE_LENGTH, whichever variable you're using)
            # Select the previous 50 days of data (or however many days are needed for the long SMA)
            window_data = data.iloc[i - 50:i + 1]  # This provides a rolling window of the last 50 days of data
            
            # Generate signals based on the rolling window of data
            signals = self.strategy.generate_signals(window_data)

            # Check the most recent position (buy/sell/hold) based on the latest signals
            latest_position = signals['Position'].iloc[-1]
            
            if latest_position == 1 and self.position == 0:
                # Buy signal: Buy shares if no position is held
                self.buy_shares(data['close'].iloc[i])
                print(f"Day {i - 49}: Bought {self.quantity} shares at ${data['close'].iloc[i]}")

            elif latest_position == -1 and self.position > 0:
                # Sell signal: Sell all shares if a position is held
                self.sell_shares(data['close'].iloc[i])
                print(f"Day {i - 49}: Sold {self.quantity} shares at ${data['close'].iloc[i]}")
            
            else:
                print(f"Day {i - 49}: Held position at ${data['close'].iloc[i]}")

        # Print final cash balance after the backtest
        print(f"Backtest completed. Final cash balance: ${self.cash}")


    def buy_shares(self, price):
        """Simulate buying shares."""
        total_cost = self.quantity * price
        if self.cash >= total_cost:
            self.cash -= total_cost
            self.position += self.quantity
            self.share_price = price

    def sell_shares(self, price):
        """Simulate selling shares."""
        total_sale = self.position * price
        self.cash += total_sale
        self.position = 0  # Reset the position


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Trading Bot')
    parser.add_argument('--mode', choices=['live', 'backtest'], required=True, help="Mode to run the bot in: 'live' for real trading or 'backtest' for backtesting.")

    args = parser.parse_args()

    if args.mode == 'live':
        bot = TradingBot()
        bot.run()
    elif args.mode == 'backtest':
        bot = BacktestTradingBot()
        bot.run_backtest()
