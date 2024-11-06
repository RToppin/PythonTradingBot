import logging

# Basic Logging functionality
logging.basicConfig(filename='trading_bot_log', level=logging.INFO, format= '%(asctime)s - %(message)s')

def log_status(message):
    print(message) # Output to console
    logging.info(message) # Save to log file