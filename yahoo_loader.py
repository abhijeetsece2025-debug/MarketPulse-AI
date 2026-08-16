# yahoo_loader.py

import yfinance as yf
import pandas as pd


class YahooLoader:

    def get_stock_data(self, symbol, period="5y"):

        ticker = yf.Ticker(symbol)

        data = ticker.history(
            period=period,
            interval="1d"
        )

        data = data.reset_index()

        return data