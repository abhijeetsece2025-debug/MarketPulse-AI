# ============================================================
# MARKETPULSE AI - COMPLETE FASTAPI
# Works with files directly in the project root
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    FileResponse,
)
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path
import numpy as np


# ============================================================
# PROJECT DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INDEX_FILE = BASE_DIR / "index.html"
CSS_FILE = BASE_DIR / "style.css"
JS_FILE = BASE_DIR / "script.js"


# ============================================================
# CREATE FASTAPI APP
# ============================================================

app = FastAPI(
    title="MarketPulse AI",
    description="Bayesian AI Stock Prediction and Market Analysis",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
# HOME PAGE
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home():

    try:

        if not INDEX_FILE.exists():

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
                        Please make sure index.html is
                        in the same folder as api.py.
                    </p>

                </body>
                </html>
                """,
                status_code=500
            )

        return FileResponse(
            INDEX_FILE,
            media_type="text/html"
        )

    except Exception as error:

        print("HOME PAGE ERROR:", repr(error))

        return HTMLResponse(
            content=f"""
            <html>
            <head>
                <title>MarketPulse AI</title>
            </head>

            <body>

                <h1>MarketPulse AI</h1>

                <h2>Homepage Error</h2>

                <pre>{str(error)}</pre>

            </body>
            </html>
            """,
            status_code=500
        )


# ============================================================
# CSS
# ============================================================

@app.get("/style.css")
async def style_css():

    if not CSS_FILE.exists():

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "style.css not found"
            }
        )

    return FileResponse(
        CSS_FILE,
        media_type="text/css"
    )


# ============================================================
# JAVASCRIPT
# ============================================================

@app.get("/script.js")
async def script_js():

    if not JS_FILE.exists():

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "script.js not found"
            }
        )

    return FileResponse(
        JS_FILE,
        media_type="application/javascript"
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
# PROJECT STATUS
# ============================================================

@app.get("/status")
async def project_status():

    return {

        "success": True,

        "project": "MarketPulse AI",

        "files": {

            "index.html":
                INDEX_FILE.exists(),

            "style.css":
                CSS_FILE.exists(),

            "script.js":
                JS_FILE.exists(),

        }

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

        print("")
        print("==========================================")
        print("PREDICTION REQUEST")
        print("==========================================")
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

                    "error":
                        "Stock symbol is required."

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

        print("Analysing:", symbol)

        # ----------------------------------------------------
        # LOAD STOCK DATA
        # ----------------------------------------------------

        try:

            from combined_loader import CombinedLoader

            loader = CombinedLoader()

            data_frame = loader.prepare_stock_data(
                symbol,
                period="5y"
            )

        except TypeError:

            # Compatibility if your loader
            # doesn't accept period

            loader = CombinedLoader()

            data_frame = loader.prepare_stock_data(
                symbol
            )

        # ----------------------------------------------------
        # CHECK DATA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # FIND CLOSE PRICE
        # ----------------------------------------------------

        if "ClsPric" in data_frame.columns:

            price_column = "ClsPric"

        elif "Close" in data_frame.columns:

            price_column = "Close"

        else:

            return JSONResponse(

                status_code=500,

                content={

                    "success": False,

                    "error":
                        "Closing price column not found."

                }

            )

        # ----------------------------------------------------
        # CLEAN PRICES
        # ----------------------------------------------------

        price_series = (

            data_frame[price_column]

            .astype(float)

            .replace(
                [np.inf, -np.inf],
                np.nan
            )

        )

        valid_mask = price_series.notna()

        prices = (
            price_series[valid_mask]
            .tolist()
        )

        if len(prices) < 60:

            return JSONResponse(

                status_code=400,

                content={

                    "success": False,

                    "error":
                        "Not enough historical data."

                }

            )

        # ----------------------------------------------------
        # HISTORICAL DATES
        # ----------------------------------------------------

        if "TradDt" in data_frame.columns:

            dates_series = data_frame.loc[
                valid_mask,
                "TradDt"
            ]

            historical_dates = [

                str(value)

                for value in dates_series

            ]

        elif "Date" in data_frame.columns:

            dates_series = data_frame.loc[
                valid_mask,
                "Date"
            ]

            historical_dates = [

                str(value)

                for value in dates_series

            ]

        else:

            historical_dates = [

                str(index + 1)

                for index in range(len(prices))

            ]

        # ----------------------------------------------------
        # MAKE LENGTHS IDENTICAL
        # ----------------------------------------------------

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

            indicator_data = data_frame.copy()

            # ------------------------------------------------
            # Make Close column available
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
                "Indicator error:",
                repr(error)
            )

        # ====================================================
        # BAYESIAN PREDICTION
        # ====================================================

        predictions = []

        try:

            from bayesian_stock import (
                BayesianStockModel
            )

            # ------------------------------------------------
            # X = time/day index
            # ------------------------------------------------

            X = np.arange(
                len(prices),
                dtype=float
            ).reshape(
                -1,
                1
            )

            # ------------------------------------------------
            # Y = closing prices
            # ------------------------------------------------

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

            # ------------------------------------------------
            # CLEAN PREDICTIONS
            # ------------------------------------------------

            predictions = [

                float(value)

                for value in prediction_result

                if np.isfinite(value)

            ]

            # ------------------------------------------------
            # Make sure exactly 5 predictions
            # ------------------------------------------------

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

            print("")
            print("BAYESIAN PREDICTION ERROR")
            print(repr(error))
            print("")

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

        response = {

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

        print("")
        print("Prediction completed successfully.")
        print("Current price:", prices[-1])
        print("Predictions:", predictions)
        print("==========================================")
        print("")

        return response

    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as error:

        print("")
        print("==========================================")
        print("PREDICTION ERROR")
        print("==========================================")
        print(repr(error))
        print("==========================================")
        print("")

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

        # ----------------------------------------------------
        # Clean symbol
        # ----------------------------------------------------

        clean_symbol = (

            symbol

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

        # ----------------------------------------------------
        # Get news
        # ----------------------------------------------------

        articles = get_company_news(
            clean_symbol
        )

        if articles is None:

            articles = []

        return {

            "success": True,

            "symbol":
                clean_symbol,

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
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup():

    print("")
    print("==========================================")
    print("        MARKETPULSE AI STARTED")
    print("==========================================")
    print("")
    print("Project directory:")
    print(BASE_DIR)
    print("")
    print("Website:")
    print("http://127.0.0.1:8000")
    print("")
    print("Health:")
    print("http://127.0.0.1:8000/health")
    print("")
    print("Status:")
    print("http://127.0.0.1:8000/status")
    print("")
    print("News:")
    print("http://127.0.0.1:8000/news/RELIANCE")
    print("")
    print("CSS:")
    print("http://127.0.0.1:8000/style.css")
    print("")
    print("JavaScript:")
    print("http://127.0.0.1:8000/script.js")
    print("")
    print("==========================================")
    print("")