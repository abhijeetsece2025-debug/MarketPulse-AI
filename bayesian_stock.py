# ============================================================
# MARKETPULSE AI
# Bayesian Stock Price Prediction Model
# ============================================================

import pymc as pm
import numpy as np


class BayesianStockModel:

    def __init__(self):

        self.model = None
        self.trace = None

        self.price_mean = None
        self.price_std = None

        self.X_mean = None
        self.X_std = None

    # ========================================================
    # TRAIN MODEL
    # ========================================================

    def train(self, X, y):

        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        if len(X) != len(y):
            raise ValueError(
                "X and y must contain the same number of records."
            )

        if len(y) < 30:
            raise ValueError(
                "At least 30 historical records are required."
            )

        # ----------------------------------------------------
        # PRICE NORMALIZATION
        # ----------------------------------------------------

        self.price_mean = float(np.mean(y))
        self.price_std = float(np.std(y))

        if self.price_std == 0:
            self.price_std = 1.0

        y_scaled = (
            y - self.price_mean
        ) / self.price_std

        # ----------------------------------------------------
        # FEATURE NORMALIZATION
        # ----------------------------------------------------

        self.X_mean = np.mean(
            X,
            axis=0
        )

        self.X_std = np.std(
            X,
            axis=0
        )

        self.X_std = np.asarray(
            self.X_std,
            dtype=float
        )

        self.X_std[
            self.X_std == 0
        ] = 1.0

        X_scaled = (
            X - self.X_mean
        ) / self.X_std

        # ----------------------------------------------------
        # BAYESIAN MODEL
        # ----------------------------------------------------

        with pm.Model() as self.model:

            alpha = pm.Normal(
                "alpha",
                mu=0,
                sigma=1
            )

            beta = pm.Normal(
                "beta",
                mu=0,
                sigma=1,
                shape=X_scaled.shape[1]
            )

            sigma = pm.HalfNormal(
                "sigma",
                sigma=1
            )

            mu = (
                alpha
                +
                pm.math.dot(
                    X_scaled,
                    beta
                )
            )

            pm.Normal(
                "price",
                mu=mu,
                sigma=sigma,
                observed=y_scaled
            )

            self.trace = pm.sample(
                draws=500,
                tune=500,
                cores=1,
                chains=2,
                target_accept=0.90,
                random_seed=42,
                progressbar=True
            )

        return self.trace

    # ========================================================
    # INTERNAL POSTERIOR DATA
    # ========================================================

    def _posterior_samples(self):

        if self.trace is None:
            raise RuntimeError(
                "Bayesian model has not been trained."
            )

        posterior = self.trace.posterior

        alpha_samples = (
            posterior["alpha"]
            .values
            .reshape(-1)
        )

        beta_samples = (
            posterior["beta"]
            .values
            .reshape(
                -1,
                len(self.X_mean)
            )
        )

        sigma_samples = (
            posterior["sigma"]
            .values
            .reshape(-1)
        )

        return (
            alpha_samples,
            beta_samples,
            sigma_samples
        )

    # ========================================================
    # PREDICT
    # ========================================================

    def predict(self, X_new):

        result = self.predict_with_uncertainty(
            X_new
        )

        return result["mean"]

    # ========================================================
    # PREDICT WITH BAYESIAN UNCERTAINTY
    # ========================================================

    def predict_with_uncertainty(
        self,
        X_new
    ):

        if self.model is None:
            raise RuntimeError(
                "Model has not been trained."
            )

        if self.trace is None:
            raise RuntimeError(
                "Bayesian trace is not available."
            )

        if self.X_mean is None:
            raise RuntimeError(
                "X normalization values are missing."
            )

        if self.price_mean is None:
            raise RuntimeError(
                "Price normalization values are missing."
            )

        X_new = np.asarray(
            X_new,
            dtype=float
        )

        if X_new.ndim == 1:
            X_new = X_new.reshape(-1, 1)

        # ----------------------------------------------------
        # NORMALIZE FUTURE FEATURES
        # ----------------------------------------------------

        X_scaled = (
            X_new - self.X_mean
        ) / self.X_std

        (
            alpha_samples,
            beta_samples,
            sigma_samples
        ) = self._posterior_samples()

        means = []
        lower = []
        upper = []

        # ----------------------------------------------------
        # PREDICT EACH FUTURE DAY
        # ----------------------------------------------------

        for x in X_scaled:

            mu_samples = (
                alpha_samples
                +
                np.dot(
                    beta_samples,
                    x
                )
            )

            # Convert scaled model output
            # back into real stock price

            price_samples = (
                mu_samples
                *
                self.price_std
                +
                self.price_mean
            )

            # Bayesian predictive noise

            noise = np.random.normal(
                loc=0,
                scale=sigma_samples
            )

            predictive_samples = (
                price_samples
                +
                noise * self.price_std
            )

            means.append(
                float(
                    np.mean(
                        predictive_samples
                    )
                )
            )

            lower.append(
                float(
                    np.percentile(
                        predictive_samples,
                        2.5
                    )
                )
            )

            upper.append(
                float(
                    np.percentile(
                        predictive_samples,
                        97.5
                    )
                )
            )

        return {

            "mean": np.asarray(
                means,
                dtype=float
            ),

            "lower": np.asarray(
                lower,
                dtype=float
            ),

            "upper": np.asarray(
                upper,
                dtype=float
            )
        }