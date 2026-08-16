# =============================================================
# prediction.py
# Bayesian Stock Prediction Runner
# =============================================================

from yahoo_loader import YahooLoader
from bayesian_stock import BayesianStockModel
from indicators import prepare_features
from stock_chart import plot_prediction



def run_prediction(stock):

    print("=" * 60)
    print("       BAYESIAN STOCK PREDICTION")
    print("=" * 60)


    # -----------------------------
    # Load Data
    # -----------------------------

    print("\nLoading Data...")


    loader = YahooLoader()


    df = loader.get_stock_data(
        stock,
        period="5y"
    )


    if df.empty:
        print("No stock data found")
        return


    print("Data Loaded Successfully")


    print("\nData Shape:")
    print(df.shape)


    print("\nLatest Data:")
    print(df.tail())



    # -----------------------------
    # Prepare Indicators
    # -----------------------------

    print("\nPreparing Indicators...")


    X, y, final_df = prepare_features(df)


    if X.empty:

        print(
            "Feature data is empty"
        )

        return



    print("\nFeature Shape:")
    print(X.shape)



    # -----------------------------
    # Train Bayesian Model
    # -----------------------------

    print("\nTraining Bayesian Model...")


    model = BayesianStockModel()


    # IMPORTANT: send X and y
    model.train(
        X,
        y
    )


    print("\nModel Training Completed")



    # -----------------------------
    # Prediction
    # -----------------------------


    latest_features = (
        X.iloc[-1]
        .values
    )


    prediction = model.predict(
        latest_features
    )



    print("\n================================")
    print(" NEXT DAY PRICE PREDICTION ")
    print("================================")


    print(
        f"{stock} Predicted Price : ₹{prediction:.2f}"
    )



    # -----------------------------
    # Graph
    # -----------------------------


    history = (
        df["Close"]
        .tail(100)
        .values
    )


    plot_prediction(
        history,
        [prediction]
    )





# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":


    stock = input(
        "\nEnter Yahoo Symbol (Example: ITC.NS): "
    ).strip().upper()


    run_prediction(stock)