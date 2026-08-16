import numpy as np
import pandas as pd


def calculate_indicators(df):

    df = df.copy()

    # ==================================================
    # CLOSE PRICE
    # ==================================================

    if "Close" not in df.columns:

        if "ClsPric" in df.columns:
            df["Close"] = df["ClsPric"]

        else:
            raise ValueError(
                "Close column not found."
            )

    # ==================================================
    # NUMERIC CONVERSION
    # ==================================================

    for column in [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    close = df["Close"]

    # ==================================================
    # SMA
    # ==================================================

    df["SMA_20"] = (
        close
        .rolling(window=20, min_periods=20)
        .mean()
    )

    df["SMA_50"] = (
        close
        .rolling(window=50, min_periods=50)
        .mean()
    )

    # ==================================================
    # EMA
    # ==================================================

    df["EMA_20"] = (
        close
        .ewm(
            span=20,
            adjust=False
        )
        .mean()
    )

    df["EMA_50"] = (
        close
        .ewm(
            span=50,
            adjust=False
        )
        .mean()
    )

    # ==================================================
    # RSI 14
    # ==================================================

    change = close.diff()

    gain = change.clip(
        lower=0
    )

    loss = -change.clip(
        upper=0
    )

    avg_gain = (
        gain
        .rolling(
            window=14,
            min_periods=14
        )
        .mean()
    )

    avg_loss = (
        loss
        .rolling(
            window=14,
            min_periods=14
        )
        .mean()
    )

    rs = (
        avg_gain /
        avg_loss.replace(
            0,
            np.nan
        )
    )

    df["RSI_14"] = (
        100 -
        (
            100 /
            (1 + rs)
        )
    )

    # ==================================================
    # MACD
    # ==================================================

    ema12 = (
        close
        .ewm(
            span=12,
            adjust=False
        )
        .mean()
    )

    ema26 = (
        close
        .ewm(
            span=26,
            adjust=False
        )
        .mean()
    )

    df["MACD"] = (
        ema12 - ema26
    )

    df["MACD_Signal"] = (
        df["MACD"]
        .ewm(
            span=9,
            adjust=False
        )
        .mean()
    )

    df["MACD_Histogram"] = (
        df["MACD"] -
        df["MACD_Signal"]
    )

    # ==================================================
    # VOLATILITY 20
    # ==================================================

    returns = (
        close
        .pct_change()
    )

    df["Volatility_20"] = (
        returns
        .rolling(
            window=20,
            min_periods=20
        )
        .std()
        * np.sqrt(252)
    )

    # ==================================================
    # MOMENTUM 10
    # ==================================================

    df["Momentum_10"] = (
        close.diff(10)
    )

    # ==================================================
    # ATR 14
    # ==================================================

    if (
        "High" in df.columns and
        "Low" in df.columns
    ):

        previous_close = (
            close.shift(1)
        )

        tr1 = (
            df["High"] -
            df["Low"]
        )

        tr2 = (
            df["High"] -
            previous_close
        ).abs()

        tr3 = (
            df["Low"] -
            previous_close
        ).abs()

        true_range = pd.concat(
            [
                tr1,
                tr2,
                tr3
            ],
            axis=1
        ).max(
            axis=1
        )

        df["ATR_14"] = (
            true_range
            .rolling(
                window=14,
                min_periods=14
            )
            .mean()
        )

    else:

        df["ATR_14"] = np.nan

    # ==================================================
    # STOCHASTIC %K
    # ==================================================

    if (
        "High" in df.columns and
        "Low" in df.columns
    ):

        lowest_low = (
            df["Low"]
            .rolling(
                window=14,
                min_periods=14
            )
            .min()
        )

        highest_high = (
            df["High"]
            .rolling(
                window=14,
                min_periods=14
            )
            .max()
        )

        price_range = (
            highest_high -
            lowest_low
        )

        df["Stochastic_K"] = (
            (
                close -
                lowest_low
            )
            /
            price_range.replace(
                0,
                np.nan
            )
        ) * 100

    else:

        df["Stochastic_K"] = np.nan

    # ==================================================
    # RELATIVE VOLUME
    # ==================================================

    if "Volume" in df.columns:

        volume_average = (
            df["Volume"]
            .rolling(
                window=20,
                min_periods=20
            )
            .mean()
        )

        df["Relative_Volume"] = (
            df["Volume"] /
            volume_average.replace(
                0,
                np.nan
            )
        )

    else:

        df["Relative_Volume"] = np.nan

    # ==================================================
    # PRICE RANGE
    # ==================================================

    if (
        "High" in df.columns and
        "Low" in df.columns
    ):

        df["Price_Range"] = (
            df["High"] -
            df["Low"]
        )

        df["Range_Percentage"] = (
            (
                df["High"] -
                df["Low"]
            )
            /
            close.replace(
                0,
                np.nan
            )
        ) * 100

    # ==================================================
    # CLEAN INVALID VALUES
    # ==================================================

    df = df.replace(
        [
            np.inf,
            -np.inf
        ],
        np.nan
    )

    # ==================================================
    # RESET INDEX
    # ==================================================

    df = df.reset_index(
        drop=True
    )

    return df