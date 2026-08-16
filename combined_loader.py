import yfinance as yf
import pandas as pd


class CombinedLoader:

    def prepare_stock_data(self, symbol, period="5y"):

        print(f"Downloading {symbol} data for {period}...")

        try:

            ticker = yf.Ticker(symbol)

            df = ticker.history(
                period=period,
                interval="1d",
                auto_adjust=False
            )

            if df is None or df.empty:

                print(f"No data found for {symbol}")

                return pd.DataFrame()

            # Convert index to column
            df = df.reset_index()

            # --------------------------------------------------
            # REQUIRED COLUMNS
            # --------------------------------------------------

            required_columns = [
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]

            available_columns = [
                column
                for column in required_columns
                if column in df.columns
            ]

            df = df[available_columns].copy()

            # --------------------------------------------------
            # RENAME COLUMNS
            # --------------------------------------------------

            df = df.rename(
                columns={
                    "Date": "TradDt",
                    "Close": "ClsPric"
                }
            )

            # --------------------------------------------------
            # NUMERIC CONVERSION
            # --------------------------------------------------

            numeric_columns = [
                "Open",
                "High",
                "Low",
                "ClsPric",
                "Volume"
            ]

            for column in numeric_columns:

                if column in df.columns:

                    df[column] = pd.to_numeric(
                        df[column],
                        errors="coerce"
                    )

            # --------------------------------------------------
            # REMOVE INVALID PRICE ROWS
            # --------------------------------------------------

            df = df.dropna(
                subset=["ClsPric"]
            )

            # --------------------------------------------------
            # RESET INDEX
            # --------------------------------------------------

            df = df.reset_index(
                drop=True
            )

            # --------------------------------------------------
            # DISPLAY INFORMATION
            # --------------------------------------------------

            print(
                f"Downloaded {len(df)} records for {symbol}"
            )

            print(
                "Columns:",
                list(df.columns)
            )

            return df

        except Exception as error:

            print(
                "CombinedLoader error:",
                repr(error)
            )

            return pd.DataFrame()