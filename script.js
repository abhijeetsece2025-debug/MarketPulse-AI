// ============================================================
// MARKETPULSE AI
// ============================================================

let historyChart = null;
let predictionChart = null;
let currentData = null;


// ============================================================
// PAGE LOAD
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("MarketPulse AI loaded");

    const button = document.getElementById("analyzeButton");
    const input = document.getElementById("stockSymbol");

    if (button) {
        button.addEventListener("click", analyzeStock);
    }

    if (input) {
        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                analyzeStock();
            }
        });
    }

    document.querySelectorAll(".year-button").forEach(function (button) {

        button.addEventListener("click", function () {

            document.querySelectorAll(".year-button").forEach(function (b) {
                b.classList.remove("active");
            });

            this.classList.add("active");

            if (currentData) {
                drawHistoryChart(
                    currentData,
                    this.dataset.year
                );
            }

        });

    });

});


// ============================================================
// SELECT STOCK
// ============================================================

function selectStock(symbol) {

    const input = document.getElementById("stockSymbol");

    if (input) {
        input.value = symbol;
    }

    analyzeStock();
}


// ============================================================
// NORMALIZE SYMBOL
// ============================================================

function normalizeSymbol(symbol) {

    symbol = String(symbol || "")
        .trim()
        .toUpperCase();

    if (!symbol) {
        return "";
    }

    if (
        !symbol.includes(".") &&
        !symbol.startsWith("^")
    ) {
        symbol += ".NS";
    }

    return symbol;
}


// ============================================================
// ANALYZE STOCK
// ============================================================

async function analyzeStock() {

    const input = document.getElementById("stockSymbol");
    const button = document.getElementById("analyzeButton");

    if (!input) {
        return;
    }

    const symbol = normalizeSymbol(input.value);

    if (!symbol) {

        showError(
            "Please enter a stock symbol."
        );

        return;
    }

    input.value = symbol;

    hideError();
    showLoading();

    if (button) {

        button.disabled = true;
        button.textContent = "Analysing...";

    }

    try {

        console.log("Sending stock:", symbol);

        const response = await fetch(
            "/predict",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    symbol: symbol
                })
            }
        );

        const data = await response.json();

        console.log("FULL API RESPONSE:");
        console.log(data);

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Server error."
            );

        }

        if (
            data.success === false
        ) {

            throw new Error(
                data.error ||
                "Analysis failed."
            );

        }

        currentData = data;

        showDashboard();

        updateDashboard(data);

        drawHistoryChart(
            data,
            "all"
        );

        drawPredictionChart(
            data
        );

        await loadCompanyNews(symbol);

    }

    catch (error) {

        console.error(
            "Analysis error:",
            error
        );

        showError(
            error.message ||
            "Unable to analyse stock."
        );

    }

    finally {

        hideLoading();

        if (button) {

            button.disabled = false;
            button.textContent = "Analyze";

        }

    }

}


// ============================================================
// UPDATE DASHBOARD
// ============================================================

function updateDashboard(data) {

    console.log(
        "Updating dashboard with:",
        data
    );

    const symbol =
        data.stock ||
        data.symbol ||
        "Unknown";

    const prices =
        getHistoricalPrices(data);

    const predictions =
        getPredictions(data);

    const currentPrice =
        getNumber(
            data.current_price ||
            data.currentPrice ||
            data.latest_price ||
            data.last_price
        );


    // --------------------------------------------------------
    // STOCK NAME
    // --------------------------------------------------------

    setText(
        "stockName",
        symbol
            .replace(".NS", "")
            .replace(".BO", "")
    );


    // --------------------------------------------------------
    // CURRENT PRICE
    // --------------------------------------------------------

    setText(
        "currentPrice",
        formatPrice(currentPrice)
    );


    // --------------------------------------------------------
    // HISTORICAL RECORDS
    // --------------------------------------------------------

    setText(
        "historicalRecords",
        data.historical_records ||
        data.historicalRecords ||
        prices.length ||
        "—"
    );


    // --------------------------------------------------------
    // FORECAST
    // --------------------------------------------------------

    if (predictions.length > 0) {

        console.log(
            "Predictions:",
            predictions
        );


        // Use the LAST predicted price
        const finalPrediction =
            predictions[
                predictions.length - 1
            ];


        console.log(
            "Current price:",
            currentPrice
        );

        console.log(
            "Final prediction:",
            finalPrediction
        );


        // Forecast price
        setText(
            "forecastPrice",
            formatPrice(
                finalPrediction
            )
        );


        // ----------------------------------------------------
        // CALCULATE FORECAST CHANGE
        // ----------------------------------------------------

        let change = null;


        // First check whether backend already supplied
        // forecast percentage.
        if (
            data.forecast_change !== undefined &&
            data.forecast_change !== null
        ) {

            change =
                getNumber(
                    data.forecast_change
                );

        }

        else if (
            data.forecastChange !== undefined &&
            data.forecastChange !== null
        ) {

            change =
                getNumber(
                    data.forecastChange
                );

        }

        else {

            // Calculate from current price and prediction
            change =
                calculatePercentageChange(
                    currentPrice,
                    finalPrediction
                );

        }


        console.log(
            "Forecast change:",
            change
        );


        setText(
            "forecastChange",
            formatPercent(change)
        );

    }

    else {

        setText(
            "forecastPrice",
            "—"
        );

        setText(
            "forecastChange",
            "—"
        );

    }


    // ========================================================
    // INDICATORS
    // ========================================================

    const indicators =
        data.indicators || {};


    setIndicator(
        "rsi",
        indicators.rsi_14
    );

    setIndicator(
        "sma20",
        indicators.sma_20
    );

    setIndicator(
        "sma50",
        indicators.sma_50
    );

    setIndicator(
        "ema20",
        indicators.ema_20
    );

    setIndicator(
        "ema50",
        indicators.ema_50
    );

    setIndicator(
        "macd",
        indicators.macd
    );

    setIndicator(
        "macdSignal",
        indicators.macd_signal
    );

    setIndicator(
        "volatility",
        indicators.volatility_20
    );

    setIndicator(
        "momentum",
        indicators.momentum_10
    );

    setIndicator(
        "atr",
        indicators.atr_14
    );

    setIndicator(
        "stochastic",
        indicators.stochastic_k
    );

    setIndicator(
        "relativeVolume",
        indicators.relative_volume
    );


    // ========================================================
    // RISK
    // ========================================================

    calculateRisk(
        data,
        currentPrice,
        predictions,
        indicators
    );

}


// ============================================================
// HISTORY CHART
// ============================================================

function drawHistoryChart(
    data,
    selectedYear
) {

    const canvas =
        document.getElementById(
            "historyChart"
        );

    if (!canvas) {
        return;
    }


    const prices =
        getHistoricalPrices(data);

    const dates =
        Array.isArray(data.historical_dates)
            ? data.historical_dates
            : [];


    let labels = [];
    let values = [];


    for (
        let i = 0;
        i < prices.length;
        i++
    ) {

        const date =
            dates[i] || "";


        if (
            selectedYear !== "all" &&
            date &&
            !String(date).includes(
                String(selectedYear)
            )
        ) {

            continue;

        }


        labels.push(
            formatDateLabel(date)
        );

        values.push(
            prices[i]
        );

    }


    if (historyChart) {
        historyChart.destroy();
    }


    historyChart =
        new Chart(
            canvas.getContext("2d"),
            {

                type: "line",

                data: {

                    labels: labels,

                    datasets: [{

                        label:
                            "Closing Price",

                        data:
                            values,

                        borderWidth:
                            2,

                        pointRadius:
                            0,

                        tension:
                            0.2,

                        fill:
                            false

                    }]

                },

                options: {

                    responsive:
                        true,

                    maintainAspectRatio:
                        false,

                    interaction: {

                        mode:
                            "index",

                        intersect:
                            false

                    },

                    scales: {

                        x: {

                            ticks: {

                                maxTicksLimit:
                                    12

                            }

                        },

                        y: {

                            beginAtZero:
                                false

                        }

                    }

                }

            }
        );

}


// ============================================================
// PREDICTION CHART
// ============================================================

function drawPredictionChart(data) {

    const canvas =
        document.getElementById(
            "predictionChart"
        );

    if (!canvas) {
        return;
    }


    const history =
        getHistoricalPrices(data);

    const predictions =
        getPredictions(data);


    if (
        history.length === 0 ||
        predictions.length === 0
    ) {

        console.log(
            "Not enough data for prediction chart."
        );

        return;

    }


    const historical =
        history.slice(-60);


    const labels = [];


    // Historical labels
    for (
        let i = 0;
        i < historical.length;
        i++
    ) {

        labels.push(
            "History " +
            (i + 1)
        );

    }


    // Prediction labels
    for (
        let i = 0;
        i < predictions.length;
        i++
    ) {

        labels.push(
            "Day " +
            (i + 1)
        );

    }


    const historyData = [

        ...historical,

        ...Array(
            predictions.length
        ).fill(null)

    ];


    const predictionData = [

        ...Array(
            historical.length - 1
        ).fill(null),

        historical[
            historical.length - 1
        ],

        ...predictions

    ];


    if (predictionChart) {
        predictionChart.destroy();
    }


    predictionChart =
        new Chart(
            canvas.getContext("2d"),
            {

                type: "line",

                data: {

                    labels:
                        labels,

                    datasets: [

                        {

                            label:
                                "Historical Price",

                            data:
                                historyData,

                            borderWidth:
                                2,

                            pointRadius:
                                0,

                            tension:
                                0.2

                        },

                        {

                            label:
                                "Bayesian Prediction",

                            data:
                                predictionData,

                            borderWidth:
                                3,

                            borderDash:
                                [6, 5],

                            pointRadius:
                                3,

                            tension:
                                0.2

                        }

                    ]

                },

                options: {

                    responsive:
                        true,

                    maintainAspectRatio:
                        false,

                    interaction: {

                        mode:
                            "index",

                        intersect:
                            false

                    }

                }

            }
        );

}


// ============================================================
// NEWS
// ============================================================

async function loadCompanyNews(symbol) {

    const container =
        document.getElementById(
            "newsContainer"
        );

    if (!container) {
        return;
    }


    container.innerHTML =
        "<p>Loading latest news...</p>";


    const company =
        symbol
            .replace(".NS", "")
            .replace(".BO", "");


    try {

        const response =
            await fetch(
                "/news/" +
                encodeURIComponent(
                    company
                )
            );


        const data =
            await response.json();


        const articles =
            Array.isArray(data.articles)
                ? data.articles
                : [];


        if (
            articles.length === 0
        ) {

            container.innerHTML =
                "<p>No recent news found.</p>";

            return;

        }


        container.innerHTML =
            articles
                .slice(0, 8)
                .map(
                    function (article) {

                        const title =
                            escapeHtml(
                                article.title ||
                                "Untitled"
                            );

                        const source =
                            escapeHtml(
                                article.source?.name ||
                                "Unknown source"
                            );

                        const url =
                            escapeAttribute(
                                article.url ||
                                "#"
                            );


                        return `

                            <article class="news-item">

                                <h3>

                                    <a
                                        href="${url}"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >

                                        ${title}

                                    </a>

                                </h3>

                                <div class="news-meta">

                                    ${source}

                                </div>

                            </article>

                        `;

                    }
                )
                .join("");

    }

    catch (error) {

        console.error(
            "News error:",
            error
        );

        container.innerHTML =
            "<p>News unavailable.</p>";

    }

}


// ============================================================
// RISK
// ============================================================

function calculateRisk(
    data,
    currentPrice,
    predictions,
    indicators
) {

    let trend = "Neutral";
    let confidence = "Moderate";
    let risk = "Medium";


    const sma20 =
        getNumber(
            indicators.sma_20
        );

    const sma50 =
        getNumber(
            indicators.sma_50
        );

    const rsi =
        getNumber(
            indicators.rsi_14
        );


    // ========================================================
    // MARKET TREND
    // ========================================================

    if (
        Number.isFinite(currentPrice) &&
        Number.isFinite(sma20) &&
        Number.isFinite(sma50)
    ) {

        if (
            currentPrice > sma20 &&
            sma20 > sma50
        ) {

            trend = "Bullish";

        }

        else if (
            currentPrice < sma20 &&
            sma20 < sma50
        ) {

            trend = "Bearish";

        }

    }


    // ========================================================
    // PREDICTION CONFIDENCE
    // ========================================================

    if (
        predictions.length >= 2
    ) {

        const first =
            predictions[0];

        const last =
            predictions[
                predictions.length - 1
            ];


        if (
            Number.isFinite(first) &&
            Number.isFinite(last) &&
            first !== 0
        ) {

            const movement =
                Math.abs(
                    (
                        (last - first) /
                        first
                    ) * 100
                );


            if (movement < 1) {

                confidence = "High";

            }

            else if (movement < 3) {

                confidence = "Moderate";

            }

            else {

                confidence = "Lower";

            }

        }

    }


    // ========================================================
    // RISK LEVEL
    // ========================================================

    if (
        Number.isFinite(rsi)
    ) {

        if (
            rsi > 70 ||
            rsi < 30
        ) {

            risk = "High";

        }

        else if (
            rsi > 60 ||
            rsi < 40
        ) {

            risk = "Medium";

        }

        else {

            risk = "Lower";

        }

    }


    setText(
        "marketDirection",
        trend
    );

    setText(
        "riskMomentum",
        confidence
    );

    setText(
        "riskLevel",
        risk
    );

}


// ============================================================
// GET HISTORICAL PRICES
// ============================================================

function getHistoricalPrices(data) {

    const values =
        data.historical_prices ||
        data.historicalPrices ||
        data.history ||
        [];


    if (!Array.isArray(values)) {
        return [];
    }


    return values
        .map(function (value) {

            return getNumber(value);

        })
        .filter(function (value) {

            return Number.isFinite(value);

        });

}


// ============================================================
// GET PREDICTIONS
// ============================================================

function getPredictions(data) {

    const values =
        data.predictions ||
        data.predicted_prices ||
        data.predictedPrices ||
        data.forecast ||
        data.forecast_prices ||
        [];


    if (!Array.isArray(values)) {
        return [];
    }


    return values
        .map(function (value) {

            // Handle normal numbers
            if (
                typeof value === "number"
            ) {

                return value;

            }


            // Handle numeric strings
            if (
                typeof value === "string"
            ) {

                return Number(value);

            }


            // Handle objects returned by API
            if (
                typeof value === "object" &&
                value !== null
            ) {

                return getNumber(
                    value.price ||
                    value.prediction ||
                    value.predicted_price ||
                    value.value
                );

            }


            return NaN;

        })
        .filter(function (value) {

            return Number.isFinite(value);

        });

}


// ============================================================
// NUMBER HELPER
// ============================================================

function getNumber(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return NaN;

    }


    const number =
        Number(value);


    return Number.isFinite(number)
        ? number
        : NaN;

}


// ============================================================
// INDICATOR
// ============================================================

function setIndicator(
    id,
    value
) {

    const element =
        document.getElementById(id);

    if (!element) {
        return;
    }


    const number =
        getNumber(value);


    if (
        !Number.isFinite(number)
    ) {

        element.textContent = "—";

        return;

    }


    element.textContent =
        number.toFixed(2);

}


// ============================================================
// SET TEXT
// ============================================================

function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);

    if (element) {

        element.textContent =
            value;

    }

}


// ============================================================
// FORMAT PRICE
// ============================================================

function formatPrice(value) {

    const number =
        getNumber(value);


    if (
        !Number.isFinite(number)
    ) {

        return "—";

    }


    return (
        "₹" +
        number.toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        )
    );

}


// ============================================================
// FORMAT PERCENT
// ============================================================

function formatPercent(value) {

    const number =
        getNumber(value);


    if (
        !Number.isFinite(number)
    ) {

        return "—";

    }


    return (
        (number >= 0 ? "+" : "") +
        number.toFixed(2) +
        "%"
    );

}


// ============================================================
// CALCULATE PERCENTAGE CHANGE
// ============================================================

function calculatePercentageChange(
    oldValue,
    newValue
) {

    oldValue =
        getNumber(oldValue);

    newValue =
        getNumber(newValue);


    if (
        !Number.isFinite(oldValue) ||
        !Number.isFinite(newValue) ||
        oldValue === 0
    ) {

        return null;

    }


    return (
        (
            (newValue - oldValue) /
            oldValue
        ) * 100
    );

}


// ============================================================
// DATE FORMAT
// ============================================================

function formatDateLabel(value) {

    if (!value) {
        return "";
    }


    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(value);

    }


    return date.toLocaleDateString(
        "en-IN",
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    );

}


// ============================================================
// HTML SECURITY
// ============================================================

function escapeHtml(value) {

    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}


function escapeAttribute(value) {

    return escapeHtml(value);

}


// ============================================================
// SHOW DASHBOARD
// ============================================================

function showDashboard() {

    const element =
        document.getElementById(
            "dashboard"
        );

    if (element) {

        element.classList.remove(
            "hidden"
        );

    }

}


// ============================================================
// LOADING
// ============================================================

function showLoading() {

    const element =
        document.getElementById(
            "loading"
        );

    if (element) {

        element.classList.remove(
            "hidden"
        );

    }

}


function hideLoading() {

    const element =
        document.getElementById(
            "loading"
        );

    if (element) {

        element.classList.add(
            "hidden"
        );

    }

}


// ============================================================
// ERROR
// ============================================================

function showError(message) {

    const box =
        document.getElementById(
            "errorBox"
        );

    const messageElement =
        document.getElementById(
            "errorMessage"
        );


    if (messageElement) {

        messageElement.textContent =
            message;

    }


    if (box) {

        box.classList.remove(
            "hidden"
        );

    }

}


function hideError() {

    const box =
        document.getElementById(
            "errorBox"
        );

    if (box) {

        box.classList.add(
            "hidden"
        );

    }

}


// ============================================================
// GLOBAL FUNCTIONS
// ============================================================

window.selectStock =
    selectStock;

window.analyzeStock =
    analyzeStock;