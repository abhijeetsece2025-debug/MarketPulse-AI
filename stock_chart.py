# =============================================================
# stock_chart.py
# Bayesian Stock Prediction Graph
# =============================================================

import matplotlib.pyplot as plt
import numpy as np



def plot_prediction(history, prediction):

    """
    Plot historical stock price and Bayesian prediction.

    history:
        Historical closing prices

    prediction:
        Future predicted prices
    """


    # Convert to numpy arrays

    history = np.array(history)

    prediction = np.array(prediction)



    # Show only recent history for better view

    display_days = 200


    if len(history) > display_days:

        history_plot = history[-display_days:]

        start_day = len(history) - display_days

    else:

        history_plot = history

        start_day = 0



    # X axis

    historical_days = np.arange(
        start_day,
        len(history)
    )


    future_days = np.arange(

        len(history),

        len(history) + len(prediction)

    )



    # Create graph

    plt.figure(
        figsize=(12,6)
    )



    # Historical price

    plt.plot(

        historical_days,

        history_plot,

        label="Historical Price"

    )



    # Prediction

    plt.plot(

        future_days,

        prediction,

        marker="o",

        label="Bayesian Prediction"

    )



    plt.xlabel(
        "Trading Days"
    )


    plt.ylabel(
        "Stock Price (₹)"
    )


    plt.title(
        "Bayesian Stock Price Prediction"
    )


    plt.legend()


    plt.grid(True)



    # Show graph

    plt.show()