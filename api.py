# ============================================================
# MARKETPULSE AI - FASTAPI BACKEND
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import os
import numpy as np


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

    if not os.path.isfile(index_file):

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
                <p>Please check your project files.</p>
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

        print("\n========================================")
        print("PREDICTION REQUEST")
        print("========================================")

        # ----------------------------------------------------
        # READ JSON
        # ----------------------------------------------------

        try:

            body = await request.json()

        except Exception:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Invalid JSON request."
                }
            )


        print("Request:", body)


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
                    "error": "Please enter a stock symbol."
                }
            )


        # ----------------------------------------------------
        # CONVERT TO NSE
        # ----------------------------------------------------

        if (
            "." not in symbol
            and not symbol.startswith("^")
        ):

            symbol = symbol + ".NS"


        print("Stock:", symbol)


        # ====================================================
        # LOAD STOCK DATA
        # ====================================================

        try:

            from combined_loader import CombinedLoader

            loader = CombinedLoader()

            try:

                data = loader.prepare_stock_data(
                    symbol,
                    period="5y"
                )

            except TypeError:

                data = loader.prepare_stock_data(
                    symbol
                )


        except Exception as error:

            print("DATA LOADING ERROR:")
            print(repr(error))

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": (
                        "Unable to load stock data: "
                        + str(error)
                    )
                }
            )


        # ----------------------------------------------------
        # CHECK DATA
        # ----------------------------------------------------

        if data is None:

            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": f"No data found for {symbol}."
                }
            )


        if data.empty:

            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": f"No stock data found for {symbol}."
                }
            )


        print("Records loaded:", len(data))
        print("Columns:", list(data.columns))


        # ====================================================
        # FIND PRICE COLUMN
        # ====================================================

        if "ClsPric" in data.columns:

            price_column = "ClsPric"

        elif "Close" in data.columns:

            price_column = "Close"

        elif "close" in data.columns:

            price_column = "close"

        else:

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": (
                        "Closing price column was not found. "
                        f"Available columns: {list(data.columns)}"
                    )
                }
            )


        # ====================================================
        # CLEAN DATA
        # ====================================================

        clean_data = data.copy()


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
                    "error": "No valid stock prices found."
                }
            )


        # ====================================================
        # HISTORICAL PRICES
        # ====================================================

        prices = [
            float(x)
            for x in clean_data[price_column].tolist()
            if np.isfinite(float(x))
        ]


        if len(prices) < 30:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": (
                        "Not enough historical data "
                        "to analyse this stock."
                    )
                }
            )


        current_price = float(prices[-1])


        print("Current price:", current_price)


        # ====================================================
        # HISTORICAL DATES
        # ====================================================

        if "TradDt" in clean_data.columns:

            dates = clean_data["TradDt"].tolist()

        elif "Date" in clean_data.columns:

            dates = clean_data["Date"].tolist()

        else:

            dates = list(
                range(
                    1,
                    len(prices) + 1
                )
            )


        historical_dates = [
            str(x)
            for x in dates
        ]


        # Keep lengths equal

        length = min(
            len(prices),
            len(historical_dates)
        )


        prices = prices[-length:]
        historical_dates = historical_dates[-length:]


        # ====================================================
        # TECHNICAL INDICATORS
        # ====================================================

        indicators = {}


        try:

            from indicators import calculate_indicators

            indicator_data = clean_data.copy()


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

            print("INDICATOR ERROR:")
            print(repr(error))


        # ====================================================
        # BAYESIAN PREDICTION
        # ====================================================

        predictions = []


        try:

            print("\nStarting Bayesian model...")


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
            # TRAIN MODEL
            # ------------------------------------------------

            print("Training Bayesian model...")

            model.train(
                X,
                y
            )


            print("Bayesian model trained.")


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

            print("Generating predictions...")


            result = model.predict(
                future_X
            )


            result = np.asarray(
                result,
                dtype=float
            ).flatten()


            predictions = [

                float(x)

                for x in result

                if np.isfinite(x)

            ]


            # ------------------------------------------------
            # ENSURE 5 VALUES
            # ------------------------------------------------

            if len(predictions) == 0:

                raise ValueError(
                    "Bayesian model returned no predictions."
                )


            while len(predictions) < 5:

                predictions.append(
                    predictions[-1]
                )


            predictions = predictions[:5]


            # ------------------------------------------------
            # SANITY CHECK
            # ------------------------------------------------

            predictions = [

                max(
                    0.01,
                    float(x)
                )

                for x in predictions

            ]


            print(
                "Predictions:",
                predictions
            )


        except Exception as error:

            print("\n========================================")
            print("BAYESIAN PREDICTION ERROR")
            print("========================================")
            print(repr(error))
            print("========================================")


            # ------------------------------------------------
            # SAFE FALLBACK
            # ------------------------------------------------

            predictions = [

                current_price,
                current_price,
                current_price,
                current_price,
                current_price

            ]


        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        response = {

            "success": True,

            "stock": symbol,

            "symbol": symbol,

            "current_price":
                current_price,

            "historical_records":
                len(prices),

            "historical_dates":
                historical_dates,

            "historical_prices":
                prices,

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


        print("\nPrediction completed successfully.")

        print(
            "Final predictions:",
            predictions
        )

        print("========================================\n")


        return response


    except Exception as error:

        print("\n========================================")
        print("PREDICTION API ERROR")
        print("========================================")
        print(repr(error))
        print("========================================")


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

        clean_symbol = (
            str(symbol)
            .replace(".NS", "")
            .replace(".BO", "")
            .upper()
            .strip()
        )


        print(
            "Loading news:",
            clean_symbol
        )


        from news import get_company_news


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
            "NEWS ERROR:",
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
    print("          MARKETPULSE AI")
    print("==========================================")
    print("API started successfully")
    print()
    print("Dashboard:")
    print("http://127.0.0.1:8000")
    print()
    print("Health:")
    print("http://127.0.0.1:8000/health")
    print()
    print("Swagger:")
    print("http://127.0.0.1:8000/docs")
    print("==========================================")