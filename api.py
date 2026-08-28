# ============================================================
# MARKETPULSE AI - COMPLETE FASTAPI
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import numpy as np
import os


# ============================================================
# CREATE APP
# ============================================================

app = FastAPI(
    title="MarketPulse AI",
    version="1.0.0",
    description="Bayesian Stock Prediction and Market Analysis API"
)


# ============================================================
# PROJECT DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# STATIC FILES
# ============================================================
# Your project has:
#
# index.html
# script.js
# style.css
#
# directly inside the project folder.
#
# Therefore we serve the project folder as /static.
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR),
    name="static"
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
            <html>
                <head>
                    <title>MarketPulse AI</title>
                </head>

                <body>

                    <h1>MarketPulse AI</h1>

                    <h2>index.html not found</h2>

                    <p>
                        Please make sure index.html
                        exists in the project folder.
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
# PREDICT STOCK
# ============================================================

@app.post("/predict")
async def predict(request: Request):

    try:

        # ----------------------------------------------------
        # READ REQUEST
        # ----------------------------------------------------

        body = await request.json()

        print()
        print("==============================")
        print("PREDICTION REQUEST")
        print("==============================")
        print(body)


        # ----------------------------------------------------
        # GET SYMBOL
        # ----------------------------------------------------

        symbol = str(
            body.get("symbol", "")
        ).strip().upper()


        if not symbol:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Stock symbol is required."
                }
            )


        # ----------------------------------------------------
        # CONVERT TO NSE SYMBOL
        # ----------------------------------------------------

        if (
            "." not in symbol
            and not symbol.startswith("^")
        ):

            symbol = symbol + ".NS"


        print(
            "Analysing:",
            symbol
        )


        # ----------------------------------------------------
        # LOAD STOCK DATA
        # ----------------------------------------------------

        from combined_loader import CombinedLoader


        loader = CombinedLoader()


        try:

            data_frame = loader.prepare_stock_data(
                symbol,
                period="5y"
            )

        except TypeError:

            # Compatibility with loaders that
            # don't accept period argument.

            data_frame = loader.prepare_stock_data(
                symbol
            )


        if (
            data_frame is None
            or data_frame.empty
        ):

            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": f"No stock data found for {symbol}."
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
        # FIND CLOSE PRICE
        # ====================================================

        if "ClsPric" in data_frame.columns:

            price_column = "ClsPric"

        elif "Close" in data_frame.columns:

            price_column = "Close"

        else:

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Closing price column not found."
                }
            )


        # ====================================================
        # CLEAN PRICE DATA
        # ====================================================

        clean_data = data_frame.copy()


        clean_data[price_column] = np.asarray(
            clean_data[price_column],
            dtype=float
        )


        clean_data = clean_data.replace(
            [np.inf, -np.inf],
            np.nan
        )


        clean_data = clean_data.dropna(
            subset=[price_column]
        )


        if clean_data.empty:

            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "No valid closing price data found."
                }
            )


        prices = [
            float(value)
            for value in clean_data[price_column].tolist()
        ]


        if len(prices) < 60:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Not enough historical data."
                }
            )


        # ====================================================
        # HISTORICAL DATES
        # ====================================================

        if "TradDt" in clean_data.columns:

            historical_dates = [
                str(value)
                for value in clean_data["TradDt"].tolist()
            ]

        elif "Date" in clean_data.columns:

            historical_dates = [
                str(value)
                for value in clean_data["Date"].tolist()
            ]

        else:

            historical_dates = [
                str(index + 1)
                for index in range(len(prices))
            ]


        # Keep same length

        minimum_length = min(
            len(prices),
            len(historical_dates)
        )


        prices = prices[
            -minimum_length:
        ]


        historical_dates = historical_dates[
            -minimum_length:
        ]


        # ====================================================
        # TECHNICAL INDICATORS
        # ====================================================

        indicators = {}


        try:

            from indicators import calculate_indicators


            indicator_data = clean_data.copy()


            # indicators.py expects Close

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
                            latest.get("RSI_14")
                        ),

                    "sma_20":
                        safe_number(
                            latest.get("SMA_20")
                        ),

                    "sma_50":
                        safe_number(
                            latest.get("SMA_50")
                        ),

                    "ema_20":
                        safe_number(
                            latest.get("EMA_20")
                        ),

                    "ema_50":
                        safe_number(
                            latest.get("EMA_50")
                        ),

                    "macd":
                        safe_number(
                            latest.get("MACD")
                        ),

                    "macd_signal":
                        safe_number(
                            latest.get("MACD_Signal")
                        ),

                    "volatility_20":
                        safe_number(
                            latest.get("Volatility_20")
                        ),

                    "momentum_10":
                        safe_number(
                            latest.get("Momentum_10")
                        ),

                    "atr_14":
                        safe_number(
                            latest.get("ATR_14")
                        ),

                    "stochastic_k":
                        safe_number(
                            latest.get("Stochastic_K")
                        ),

                    "relative_volume":
                        safe_number(
                            latest.get("Relative_Volume")
                        )

                }


        except Exception as error:

            print(
                "Indicator error:",
                repr(error)
            )


        # ====================================================
        # BAYESIAN PREDICTION
        # ====================================================

        predictions = []


        try:

            from bayesian_stock import BayesianStockModel


            # ------------------------------------------------
            # TRAINING DATA
            # ------------------------------------------------

            X = np.arange(
                len(prices),
                dtype=float
            ).reshape(
                -1,
                1
            )


            y = np.asarray(
                prices,
                dtype=float
            )


            # ------------------------------------------------
            # CREATE MODEL
            # ------------------------------------------------

            model = BayesianStockModel()


            # ------------------------------------------------
            # TRAIN
            # ------------------------------------------------

            model.train(
                X,
                y
            )


            # ------------------------------------------------
            # FUTURE DAYS
            # ------------------------------------------------

            future_X = np.arange(
                len(prices),
                len(prices) + 5,
                dtype=float
            ).reshape(
                -1,
                1
            )


            # ------------------------------------------------
            # PREDICT
            # ------------------------------------------------

            prediction_result = model.predict(
                future_X
            )


            prediction_result = np.asarray(
                prediction_result,
                dtype=float
            ).flatten()


            predictions = [

                float(value)

                for value in prediction_result

                if np.isfinite(value)

            ]


            # Make sure exactly 5 predictions exist

            if len(predictions) < 5:

                last_price = float(
                    prices[-1]
                )

                while len(predictions) < 5:

                    predictions.append(
                        last_price
                    )


            predictions = predictions[:5]


        except Exception as error:

            print()
            print("==============================")
            print("Bayesian prediction error")
            print("==============================")
            print(repr(error))
            print("==============================")


            # ------------------------------------------------
            # FALLBACK
            # ------------------------------------------------

            last_price = float(
                prices[-1]
            )


            predictions = [

                last_price,
                last_price,
                last_price,
                last_price,
                last_price

            ]


        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return {

            "success": True,

            "stock": symbol,

            "symbol": symbol,

            "current_price":
                float(prices[-1]),

            "historical_records":
                len(prices),

            "historical_dates":
                historical_dates,

            "historical_prices": [

                float(value)

                for value in prices

            ],

            "predictions":
                predictions,

            "future_labels": [

                "Day 1",
                "Day 2",
                "Day 3",
                "Day 4",
                "Day 5"

            ],

            "indicators":
                indicators

        }


    except Exception as error:

        print()
        print("==============================")
        print("PREDICTION ERROR")
        print("==============================")
        print(repr(error))
        print("==============================")


        return JSONResponse(

            status_code=500,

            content={

                "success": False,

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
            f"Loading news for {symbol}"
        )


        from news import get_company_news


        clean_symbol = (
            symbol
            .replace(".NS", "")
            .replace(".BO", "")
            .upper()
        )


        articles = get_company_news(
            clean_symbol
        )


        if articles is None:

            articles = []


        return {

            "success": True,

            "articles":
                articles

        }


    except Exception as error:

        print(
            "News error:",
            repr(error)
        )


        return JSONResponse(

            status_code=500,

            content={

                "success": False,

                "articles": [],

                "error":
                    str(error)

            }

        )


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
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup():

    print()
    print("==========================================")
    print("       MARKETPULSE AI STARTED")
    print("==========================================")

    print()
    print("Dashboard:")
    print("http://127.0.0.1:8000")

    print()
    print("Health:")
    print("http://127.0.0.1:8000/health")

    print()
    print("Swagger:")
    print("http://127.0.0.1:8000/docs")

    print()
    print("News:")
    print("http://127.0.0.1:8000/news/RELIANCE")

    print("==========================================")
    print()