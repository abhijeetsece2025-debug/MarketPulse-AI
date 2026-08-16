# data_loader.py

import pandas as pd
import os


class DataLoader:
    def __init__(self):
        # Data folder location
        self.data_folder = "data"

        self.nse_file = os.path.join(self.data_folder, "nse_data.csv")
        self.bse_file = os.path.join(self.data_folder, "bse_data.csv")

        self.nse_data = None
        self.bse_data = None


    def load_all_data(self):
        """
        Load NSE and BSE stock data
        """

        # Load NSE data
        if os.path.exists(self.nse_file):
            self.nse_data = pd.read_csv(self.nse_file)
            print("NSE data loaded successfully")
        else:
            print("NSE file not found:", self.nse_file)


        # Load BSE data
        if os.path.exists(self.bse_file):
            self.bse_data = pd.read_csv(self.bse_file)
            print("BSE data loaded successfully")
        else:
            print("BSE file not found:", self.bse_file)


    def get_nse_data(self):
        """
        Return NSE dataframe
        """
        return self.nse_data


    def get_bse_data(self):
        """
        Return BSE dataframe
        """
        return self.bse_data


    def get_stock_data(self, exchange):
        """
        Get data by exchange name
        """

        exchange = exchange.upper()

        if exchange == "NSE":
            return self.nse_data

        elif exchange == "BSE":
            return self.bse_data

        else:
            print("Invalid exchange. Use NSE or BSE")
            return None