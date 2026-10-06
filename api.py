# ============================================================
# MARKETPULSE AI
# COMPLETE FASTAPI BACKEND
# Bayesian Stock Prediction + Technical Indicators + News
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import os
import numpy as np
import pandas as pd

from sklearn.linear_model import BayesianRidge
from sklearn.preprocessing import StandardScaler


# ============================================================
# CREATE APP
# ============================================================

app = FastAPI(
    title="MarketPulse AI",
    version="1.0.0",
    description="Bayesian Stock Prediction and Market Risk Analysis"
)


# ============================================================
# PROJECT DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================================
# STATIC FILES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR),
    name="static"
)


# ============================================================
# PWA ICONS
# ============================================================

ICONS_DIR = os.path.join(
    BASE_DIR,
    "icons"
)

if os.path.exists(ICONS_DIR):

    app.mount(
        "/icons",
        StaticFiles(directory=ICONS_DIR),
        name="icons"
    )

else:

    print(
        "WARNING: icons folder not found:",
        ICONS_DIR
    )


# ============================================================
# PWA MANIFEST
# ============================================================

@app.get("/manifest.json")
async def manifest():

    manifest_file = os.path.join(
        BASE_DIR,
        "manifest.json"
    )

    if not os.path.exists(manifest_file):

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "manifest.json not found."
            }
        )

    return FileResponse(
        manifest_file,
        media_type="application/manifest+json"
    )


# ============================================================
# SERVICE WORKER
# ============================================================

@app.get("/service-worker.js")
async def service_worker():

    service_worker_file = os.path.join(
        BASE_DIR,
        "service-worker.js"
    )

    if not os.path.exists(service_worker_file):

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "service-worker.js not found."
            }
        )

    return FileResponse(
        service_worker_file,
        media_type="application/javascript"
    )


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home():

    index_file = os.path.join(
        BASE_DIR,
        "index.html"
    )

    if not os.path.exists(index_file):

        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>MarketPulse AI</title>
            </head>

            <body>

                <h1>MarketPulse AI</h1>

                <h2>index.html not found</h2>

                <p>
                    Please make sure index.html exists
                    in the project folder.
                </p>

            </body>
            </html>
            """,
            status_code=500
        )

    return FileResponse(
        index_file,
        media_type="text/html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():

    return {
        "success": True,
        "status": "ok",
        "message": "MarketPulse AI API is running"
    }


# ============================================================
# REQUEST MODEL
# ============================================================

class PredictionRequest(BaseModel):

    symbol: str


# ============================================================
# NORMALIZE STOCK SYMBOL
# ============================================================

def normalize_symbol(symbol):

    symbol = str(
        symbol or ""
    ).strip().upper()

    if not symbol:

        return ""

    if (
        "." not in symbol
        and not symbol.startswith("^")
    ):

        symbol += ".NS"

    return symbol


# ============================================================
# SAFE NUMBER
# ============================================================

def safe_number(value):

    try:

        if value is None:

            return None

        number = float(value)

        if not np.isfinite(number):

            return None

        return number

    except Exception:

        return None


# ============================================================
# FIND OHLC COLUMN
# ============================================================

def find_column(data_frame, possible_names):

    for column in possible_names:

        if column in data_frame.columns:

            return column

    return None


# ============================================================
# PREDICT STOCK
# ============================================================

@app.post("/predict")
async def predict(
    request_data: PredictionRequest
):

    print()
    print("==========================================")
    print("          PREDICTION REQUEST")
    print("==========================================")


    try:

        # ====================================================
        # READ REQUEST
        # ====================================================

        body = request_data.model_dump()

        print(
            "Request:",
            body
        )


        # ====================================================
        # GET SYMBOL
        # ====================================================

        symbol = normalize_symbol(
            body.get(
                "symbol",
                ""
            )
        )


        if not symbol:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error":
                        "Please enter a stock symbol."
                }
            )


        print(
            "Analysing stock:",
            symbol
        )


        # ====================================================
        # LOAD STOCK DATA
        # ====================================================

        try:

            from combined_loader import CombinedLoader

            loader = CombinedLoader()


            try:

                data_frame = (
                    loader.prepare_stock_data(
                        symbol,
                        period="5y"
                    )
                )

            except TypeError:

                data_frame = (
                    loader.prepare_stock_data(
                        symbol
                    )
                )


        except Exception as error:

            print(
                "DATA LOADING ERROR:",
                repr(error)
            )

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error":
                        "Unable to load stock data: "
                        + str(error)
                }
            )


        # ====================================================
        # CHECK DATA
        # ====================================================

        if (
            data_frame is None
            or data_frame.empty
        ):

            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error":
                        f"No stock data found for {symbol}."
                }
            )


        print(
            "Historical records:",
            len(data_frame)
        )

        print(
            "Columns:",
            list(data_frame.columns)
        )


        # ====================================================
        # FIND PRICE COLUMN
        # ====================================================

        if "ClsPric" in data_frame.columns:

            price_column = "ClsPric"

        elif "Close" in data_frame.columns:

            price_column = "Close"

        elif "Adj Close" in data_frame.columns:

            price_column = "Adj Close"

        else:

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error":
                        "Closing price column not found."
                }
            )


        # ====================================================
        # CLEAN DATA
        # ====================================================

        clean_data = data_frame.copy()


        clean_data[price_column] = pd.to_numeric(
            clean_data[price_column],
            errors="coerce"
        )


        clean_data = clean_data.replace(
            [np.inf, -np.inf],
            np.nan
        )


        clean_data = clean_data.dropna(
            subset=[
                price_column
            ]
        )


        if clean_data.empty:

            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error":
                        "No valid closing price data found."
                }
            )


        # ====================================================
        # HISTORICAL PRICES
        # ====================================================

        prices = []

        for value in clean_data[price_column].tolist():

            try:

                number = float(value)

                if np.isfinite(number):

                    prices.append(number)

            except Exception:

                continue


        if len(prices) < 60:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error":
                        "Not enough historical data. "
                        "At least 60 records are required."
                }
            )


        # ====================================================
        # HISTORICAL DATES
        # ====================================================

        if "TradDt" in clean_data.columns:

            historical_dates = [

                str(value)

                for value in
                clean_data["TradDt"].tolist()

            ]

        elif "Date" in clean_data.columns:

            historical_dates = [

                str(value)

                for value in
                clean_data["Date"].tolist()

            ]

        else:

            historical_dates = [

                str(index + 1)

                for index in
                range(len(prices))

            ]


        # ====================================================
        # REAL OHLC DATA FOR CANDLESTICK CHART
        # ====================================================

        print()
        print("------------------------------------------")
        print("Preparing OHLC candlestick data...")
        print("------------------------------------------")


        # ----------------------------------------------------
        # Find Open column
        # ----------------------------------------------------

        open_column = find_column(
            clean_data,
            [
                "Open",
                "OpnPric",
                "open",
                "OPEN"
            ]
        )


        # ----------------------------------------------------
        # Find High column
        # ----------------------------------------------------

        high_column = find_column(
            clean_data,
            [
                "High",
                "HghPric",
                "HghPrice",
                "high",
                "HIGH"
            ]
        )


        # ----------------------------------------------------
        # Find Low column
        # ----------------------------------------------------

        low_column = find_column(
            clean_data,
            [
                "Low",
                "LwPric",
                "LwPrice",
                "low",
                "LOW"
            ]
        )


        # ----------------------------------------------------
        # Close column
        # ----------------------------------------------------

        close_column = price_column


        historical_ohlc = []


        if (
            open_column is not None
            and high_column is not None
            and low_column is not None
        ):

            print(
                "Open column:",
                open_column
            )

            print(
                "High column:",
                high_column
            )

            print(
                "Low column:",
                low_column
            )

            print(
                "Close column:",
                close_column
            )


            # ------------------------------------------------
            # Convert OHLC values to numeric
            # ------------------------------------------------

            clean_data[open_column] = pd.to_numeric(
                clean_data[open_column],
                errors="coerce"
            )

            clean_data[high_column] = pd.to_numeric(
                clean_data[high_column],
                errors="coerce"
            )

            clean_data[low_column] = pd.to_numeric(
                clean_data[low_column],
                errors="coerce"
            )

            clean_data[close_column] = pd.to_numeric(
                clean_data[close_column],
                errors="coerce"
            )


            # ------------------------------------------------
            # Create OHLC records
            # ------------------------------------------------

            for index, row in clean_data.iterrows():

                open_price = safe_number(
                    row.get(open_column)
                )

                high_price = safe_number(
                    row.get(high_column)
                )

                low_price = safe_number(
                    row.get(low_column)
                )

                close_price = safe_number(
                    row.get(close_column)
                )


                # ------------------------------------------------
                # Date
                # ------------------------------------------------

                if "TradDt" in clean_data.columns:

                    date_value = row.get(
                        "TradDt"
                    )

                elif "Date" in clean_data.columns:

                    date_value = row.get(
                        "Date"
                    )

                else:

                    date_value = index


                # ------------------------------------------------
                # Only add valid candles
                # ------------------------------------------------

                if (
                    open_price is not None
                    and high_price is not None
                    and low_price is not None
                    and close_price is not None
                ):

                    historical_ohlc.append({

                        "date":
                            str(date_value),

                        "open":
                            open_price,

                        "high":
                            high_price,

                        "low":
                            low_price,

                        "close":
                            close_price

                    })


        else:

            print(
                "WARNING: Complete OHLC columns were not found."
            )

            print(
                "Candlestick data will be empty."
            )


        print(
            "Candlestick records:",
            len(historical_ohlc)
        )


        # ====================================================
        # KEEP EQUAL LENGTHS
        # ====================================================

        minimum_length = min(
            len(prices),
            len(historical_dates)
        )


        prices = prices[
            -minimum_length:
        ]


        historical_dates = (
            historical_dates[
                -minimum_length:
            ]
        )


        # ====================================================
        # CURRENT PRICE
        # ====================================================

        current_price = float(
            prices[-1]
        )


        print(
            "Current price:",
            current_price
        )


        # ====================================================
        # TECHNICAL INDICATORS
        # ====================================================

        indicators = {}


        try:

            from indicators import calculate_indicators


            indicator_data = (
                clean_data.copy()
            )


            # ------------------------------------------------
            # indicators.py expects Close
            # ------------------------------------------------

            if "ClsPric" in indicator_data.columns:

                indicator_data["Close"] = (
                    indicator_data["ClsPric"]
                )


            result = calculate_indicators(
                indicator_data
            )


            if (
                result is not None
                and not result.empty
            ):

                latest = result.iloc[-1]


                indicators = {

                    "rsi_14":
                        safe_number(
                            latest.get(
                                "RSI_14"
                            )
                        ),

                    "sma_20":
                        safe_number(
                            latest.get(
                                "SMA_20"
                            )
                        ),

                    "sma_50":
                        safe_number(
                            latest.get(
                                "SMA_50"
                            )
                        ),

                    "ema_20":
                        safe_number(
                            latest.get(
                                "EMA_20"
                            )
                        ),

                    "ema_50":
                        safe_number(
                            latest.get(
                                "EMA_50"
                            )
                        ),

                    "macd":
                        safe_number(
                            latest.get(
                                "MACD"
                            )
                        ),

                    "macd_signal":
                        safe_number(
                            latest.get(
                                "MACD_Signal"
                            )
                        ),

                    "volatility_20":
                        safe_number(
                            latest.get(
                                "Volatility_20"
                            )
                        ),

                    "momentum_10":
                        safe_number(
                            latest.get(
                                "Momentum_10"
                            )
                        ),

                    "atr_14":
                        safe_number(
                            latest.get(
                                "ATR_14"
                            )
                        ),

                    "stochastic_k":
                        safe_number(
                            latest.get(
                                "Stochastic_K"
                            )
                        ),

                    "relative_volume":
                        safe_number(
                            latest.get(
                                "Relative_Volume"
                            )
                        )

                }


        except Exception as error:

            print(
                "INDICATOR ERROR:",
                repr(error)
            )

            indicators = {}


        # ====================================================
        # BAYESIAN REGRESSION
        # ====================================================

        print()
        print("------------------------------------------")
        print("Starting Bayesian Regression...")
        print("------------------------------------------")


        try:

            # ------------------------------------------------
            # USE RECENT DATA
            # ------------------------------------------------

            training_size = min(
                len(prices),
                250
            )


            training_prices = np.asarray(
                prices[
                    -training_size:
                ],
                dtype=float
            )


            # ------------------------------------------------
            # TIME FEATURE
            # ------------------------------------------------

            X = np.arange(
                training_size,
                dtype=float
            ).reshape(
                -1,
                1
            )


            y = training_prices


            # ------------------------------------------------
            # SCALE X
            # ------------------------------------------------

            scaler = StandardScaler()


            X_scaled = (
                scaler.fit_transform(
                    X
                )
            )


            # ------------------------------------------------
            # BAYESIAN RIDGE MODEL
            # ------------------------------------------------

            bayesian_model = BayesianRidge(

                max_iter=300,

                tol=1e-6,

                alpha_1=1e-6,

                alpha_2=1e-6,

                lambda_1=1e-6,

                lambda_2=1e-6

            )


            # ------------------------------------------------
            # TRAIN
            # ------------------------------------------------

            bayesian_model.fit(
                X_scaled,
                y
            )


            # ------------------------------------------------
            # FUTURE DAYS
            # ------------------------------------------------

            future_X = np.arange(
                training_size,
                training_size + 5,
                dtype=float
            ).reshape(
                -1,
                1
            )


            future_X_scaled = (
                scaler.transform(
                    future_X
                )
            )


            # ------------------------------------------------
            # PREDICTION
            # ------------------------------------------------

            prediction_result = (
                bayesian_model.predict(
                    future_X_scaled
                )
            )


            prediction_result = np.asarray(
                prediction_result,
                dtype=float
            ).flatten()


            # ------------------------------------------------
            # VALIDATE
            # ------------------------------------------------

            predictions = [

                float(value)

                for value in
                prediction_result

                if np.isfinite(value)

            ]


            if len(predictions) != 5:

                raise ValueError(
                    "Bayesian Regression did not "
                    "produce exactly 5 predictions."
                )


            # ------------------------------------------------
            # POSITIVE PRICE CHECK
            # ------------------------------------------------

            if any(
                value <= 0
                for value in predictions
            ):

                raise ValueError(
                    "Bayesian Regression produced "
                    "an invalid stock price."
                )


            print(
                "Bayesian Regression successful."
            )


            print(
                "Predictions:",
                predictions
            )


        except Exception as error:

            print()
            print("------------------------------------------")
            print("BAYESIAN REGRESSION ERROR")
            print("------------------------------------------")

            print(
                repr(error)
            )

            print("------------------------------------------")


            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error":
                        "Bayesian Regression failed: "
                        + str(error)
                }
            )


        # ====================================================
        # FORECAST CHANGE
        # ====================================================

        final_prediction = float(
            predictions[-1]
        )


        if current_price != 0:

            forecast_change = (

                (
                    final_prediction -
                    current_price
                )
                /
                current_price

            ) * 100

        else:

            forecast_change = 0.0


        # ====================================================
        # FUTURE LABELS
        # ====================================================

        future_labels = [

            "Day 1",
            "Day 2",
            "Day 3",
            "Day 4",
            "Day 5"

        ]


        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        response = {

            "success":
                True,

            "stock":
                symbol,

            "symbol":
                symbol,

            "current_price":
                current_price,

            "forecast_price":
                final_prediction,

            "forecast_change":
                float(
                    forecast_change
                ),

            "historical_records":
                len(prices),

            "historical_dates":
                historical_dates,

            "historical_prices": [

                float(value)

                for value in prices

            ],

            # =================================================
            # NEW:
            # REAL OHLC DATA FOR CANDLESTICK CHART
            # =================================================

            "historical_ohlc":
                historical_ohlc,

            "predictions": [

                float(value)

                for value in predictions

            ],

            "future_labels":
                future_labels,

            "indicators":
                indicators

        }


        print()
        print("==========================================")
        print("Prediction completed successfully.")
        print("Stock:", symbol)
        print("Current:", current_price)
        print("Forecast:", predictions)
        print(
            "Forecast Change:",
            round(
                forecast_change,
                2
            ),
            "%"
        )

        print(
            "OHLC records:",
            len(historical_ohlc)
        )

        print("==========================================")


        return response


    except Exception as error:

        print()
        print("==========================================")
        print("PREDICTION ERROR")
        print("==========================================")

        print(
            repr(error)
        )

        print("==========================================")


        return JSONResponse(

            status_code=500,

            content={

                "success":
                    False,

                "error":
                    str(error)

            }

        )


# ============================================================
# COMPANY NEWS
# ============================================================

@app.get("/news/{symbol}")
async def company_news(symbol: str):

    try:

        print(
            "Loading news for:",
            symbol
        )


        from news import get_company_news


        clean_symbol = (
            str(symbol)
            .replace(
                ".NS",
                ""
            )
            .replace(
                ".BO",
                ""
            )
            .upper()
        )


        articles = (
            get_company_news(
                clean_symbol
            )
        )


        if articles is None:

            articles = []


        return {

            "success":
                True,

            "articles":
                articles

        }


    except Exception as error:

        print(
            "NEWS ERROR:",
            repr(error)
        )


        return JSONResponse(

            status_code=500,

            content={

                "success":
                    False,

                "articles":
                    [],

                "error":
                    str(error)

            }

        )


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup():

    print()
    print("==========================================")
    print("          MARKETPULSE AI STARTED")
    print("==========================================")

    print()

    print(
        "Dashboard:"
    )

    print(
        "http://127.0.0.1:8000"
    )

    print()

    print(
        "Health:"
    )

    print(
        "http://127.0.0.1:8000/health"
    )

    print()

    print(
        "Service Worker:"
    )

    print(
        "http://127.0.0.1:8000/service-worker.js"
    )

    print()

    print(
        "Manifest:"
    )

    print(
        "http://127.0.0.1:8000/manifest.json"
    )

    print()

    print(
        "App Icon:"
    )

    print(
        "http://127.0.0.1:8000/icons/launchericon-192x192.png"
    )

    print()

    print(
        "Swagger:"
    )

    print(
        "http://127.0.0.1:8000/docs"
    )

    print()

    print(
        "News:"
    )

    print(
        "http://127.0.0.1:8000/news/RELIANCE"
    )

    print()

    print("==========================================")
    print()