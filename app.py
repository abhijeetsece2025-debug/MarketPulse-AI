import numpy as np

from combined_loader import CombinedLoader
from bayesian_stock import BayesianStockModel
from stock_chart import plot_prediction


def main():

    # Select stock
    symbol = input("Enter stock symbol (Example: RELIANCE.NS): ").strip().upper()

    try:
        # Load data
        loader = CombinedLoader()
        data = loader.prepare_stock_data(symbol)

        if data.empty:
            print("No data found.")
            return

        print("\nData loaded successfully")
        print(data.head())

        # Features (day index)
        X = np.arange(len(data)).reshape(-1, 1)

        # Target (closing price)
        y = data["ClsPric"]

        # Train Bayesian model
        model = BayesianStockModel()

        print("\nTraining Bayesian model...")
        model.train(X, y)

        # Future days to predict
        future_days = np.arange(len(data), len(data) + 5).reshape(-1, 1)

        # Prediction
        prediction = model.predict(future_days)

        print("\nNext 5 Predicted Prices:")
        print(prediction)

        # Plot graph
        history = data["ClsPric"].values

        plot_prediction(
            history,
            prediction
        )

    except Exception as e:
        print("\nError:", e)


if __name__ == "__main__":
    main()