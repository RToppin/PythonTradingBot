import requests
import pandas as pd
from datetime import timedelta, datetime

class HistoricalData:
    
    @staticmethod
    def get_historical_data():
        # Define the date range
        startDate = str(datetime.today().date() - timedelta(days=255))
        endDate = str(datetime.today().date())
        limit = 1000
        timeframe = '1Day'
        
        # Construct the URL
        url = f'https://data.alpaca.markets/v1beta3/crypto/us/bars?symbols=BTC%2FUSD&timeframe={timeframe}&start={startDate}&end={endDate}&limit={limit}&sort=asc'
        headers = {"accept": "application/json"}
        
        # Make the GET request
        response = requests.get(url, headers=headers)
        
        # Check if the response status is OK
        if response.status_code == 200:
            # Parse the JSON response
            bars = response.json()
            
            # If the 'bars' field is present, process it
            if 'bars' in bars and 'BTC/USD' in bars['bars']:
                bar_data = bars['bars']['BTC/USD']  # Access the bars data for BTC/USD
                
                # Create a DataFrame from the parsed data
                data = pd.DataFrame([{
                    't': bar['t'],  # Timestamp
                    'o': bar['o'],  # Open price
                    'h': bar['h'],  # High price
                    'l': bar['l'],  # Low price
                    'c': bar['c'],  # Close price
                    'v': bar['v']   # Volume traded
                } for bar in bar_data])
                
                return data  # Return the DataFrame
            else:
                return pd.DataFrame()  # Return an empty DataFrame if no data is found
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return pd.DataFrame()  # Return an empty DataFrame on error
