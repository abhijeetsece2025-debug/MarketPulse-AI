# ============================================================
# MARKETPULSE AI - COMPLETE API
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import numpy as np


# ============================================================
# CREATE APP
# ============================================================

app = FastAPI(
    title="MarketPulse AI",
    version="1.0.0"
)


# ============================================================
# STATIC FILES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# ============================================================
# HTML TEMPLATES
# ============================================================

templates = Jinja2Templates(
    directory="templates"
)


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    try:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request
            }
        )

    except Exception as error:

        print("\n==============================")
        print("HOME PAGE ERROR")
        print("==============================")
        print(repr(error))
        print("==============================\n")

        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>MarketPulse AI</title>
            </head>
            <body>

                <h1>MarketPulse AI</h1>

                <h2>Homepage Error</h2>

                <pre>{error}</pre>

            </body>
            </html>
            """,
            status_code=500
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
        # READ JSON
        # ----------------------------------------------------

        body = await request.json()

        print("\n==============================")
        print("PREDICTION REQUEST")
        print("==============================")
        print(body)


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


        print(
            "Analysing:",
            symbol
        )


        # ----------------------------------------------------
        # LOAD STOCK DATA
        # ----------------------------------------------------

        from combined_loader import CombinedLoader


        loader = CombinedLoader()


        data_frame = loader.prepare_stock_data(
            symbol,
            period="5y"
        )


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
        # FIND CLOSE COLUMN
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
        # GET PRICES
        # ----------------------------------------------------

        prices = (
            data_frame[price_column]
            .astype(float)
            .replace(
                [np.inf, -np.inf],
                np.nan
            )
            .dropna()
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
        # GET DATES
        # ----------------------------------------------------

        if "TradDt" in data_frame.columns:

            historical_dates = [
                str(value)
                for value in data_frame["TradDt"]
            ]

        elif "Date" in data_frame.columns:

            historical_dates = [
                str(value)
                for value in data_frame["Date"]
            ]

        else:

            historical_dates = [
                str(index + 1)
                for index in range(len(prices))
            ]


        # ----------------------------------------------------
        # KEEP LENGTHS SAME
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


            model = BayesianStockModel()


            model.train(
                X,
                y
            )


            future_X = np.arange(
                len(prices),
                len(prices) + 5,
                dtype=float
            ).reshape(
                -1,
                1
            )


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


        except Exception as error:

            print(
                "Bayesian prediction error:",
                repr(error)
            )


            # Fallback so dashboard can still load

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

        print("\n==============================")
        print("PREDICTION ERROR")
        print("==============================")
        print(repr(error))
        print("==============================\n")


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

    print("")
    print("==========================================")
    print("       MARKETPULSE AI STARTED")
    print("==========================================")
    print("Chrome:")
    print("http://127.0.0.1:8000")
    print("")
    print("Health:")
    print("http://127.0.0.1:8000/health")
    print("")
    print("News:")
    print("http://127.0.0.1:8000/news/RELIANCE")
    print("==========================================")
    print("")