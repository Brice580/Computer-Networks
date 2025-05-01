import yfinance as yf
import os

os.makedirs('data', exist_ok=True)

aapl = yf.download('AAPL', start='2010-01-01', end='2024-01-01')

aapl.to_csv('data/AAPL.csv') 