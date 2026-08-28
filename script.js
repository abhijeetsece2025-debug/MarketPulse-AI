// ============================================================
// MARKETPULSE AI - CORRECTED SCRIPT
// ============================================================

let historyChart = null;
let predictionChart = null;
let currentData = null;


// ============================================================
// PAGE LOAD
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("MarketPulse AI JavaScript loaded");

    const analyzeButton =
        document.getElementById("analyzeButton");

    const stockInput =
        document.getElementById("stockSymbol");


    // --------------------------------------------------------
    // ANALYZE BUTTON
    // --------------------------------------------------------

    if (analyzeButton) {

        analyzeButton.addEventListener("click", function (event) {

            event.preventDefault();

            analyzeStock();

        });

    }


    // --------------------------------------------------------
    // ENTER KEY
    // --------------------------------------------------------

    if (stockInput) {

        stockInput.addEventListener("keydown", function (event) {

            if (event.key === "Enter") {

                event.preventDefault();

                analyzeStock();

            }

        });

    }


    // --------------------------------------------------------
    // YEAR BUTTONS
    // --------------------------------------------------------

    document
        .querySelectorAll(".year-button")
        .forEach(function (button) {

            button.addEventListener("click", function () {

                document
                    .querySelectorAll(".year-button")
                    .forEach(function (btn) {

                        btn.classList.remove("active");

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


    console.log("Event listeners ready");

});


// ============================================================
// SELECT QUICK STOCK
// ============================================================

function selectStock(symbol) {

    console.log("Selected stock:", symbol);


    const input =
        document.getElementById("stockSymbol");


    if (!input) {

        console.error(
            "stockSymbol input not found"
        );

        return;

    }


    // Put stock name into input box
    input.value = symbol;


    // Make sure input is visible and focused
    input.focus();


    // Automatically analyse
    analyzeStock();

}


// Make available to HTML onclick=""
window.selectStock = selectStock;


// ============================================================
// NORMALIZE SYMBOL
// ============================================================

function normalizeSymbol(symbol) {

    let value =
        String(symbol || "")
            .trim()
            .toUpperCase();


    if (!value) {

        return "";

    }


    // Already Yahoo Finance format
    if (
        value.includes(".") ||
        value.startsWith("^")
    ) {

        return value;

    }


    // Indian NSE stock
    return value + ".NS";

}


// ============================================================
// ANALYZE STOCK
// ============================================================

async function analyzeStock() {

    const input =
        document.getElementById("stockSymbol");


    const button =
        document.getElementById("analyzeButton");


    if (!input) {

        console.error(
            "Stock input not found"
        );

        return;

    }


    let enteredValue =
        input.value.trim();


    if (!enteredValue) {

        showError(
            "Please enter a stock symbol such as RELIANCE, TCS or INFY."
        );

        return;

    }


    const symbol =
        normalizeSymbol(
            enteredValue
        );


    // Show normalized symbol
    input.value = symbol;


    console.log(
        "Analysing:",
        symbol
    );


    hideError();

    showLoading();


    if (button) {

        button.disabled = true;

        button.textContent =
            "Analysing...";

    }


    try {

        // ----------------------------------------------------
        // CALL BACKEND
        // ----------------------------------------------------

        const response =
            await fetch(
                "/predict",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        symbol: symbol
                    })

                }
            );


        console.log(
            "Response status:",
            response.status
        );


        // ----------------------------------------------------
        // READ RESPONSE
        // ----------------------------------------------------

        const data =
            await response.json();


        console.log(
            "Backend response:",
            data
        );


        if (!response.ok) {

            throw new Error(
                data.error ||
                data.detail ||
                "Server error: " +
                response.status
            );

        }


        if (
            data.success === false
        ) {

            throw new Error(
                data.error ||
                "Stock analysis failed."
            );

        }


        // ----------------------------------------------------
        // SAVE DATA
        // ----------------------------------------------------

        currentData = data;


        // ----------------------------------------------------
        // SHOW DASHBOARD
        // ----------------------------------------------------

        showDashboard();


        // ----------------------------------------------------
        // UPDATE DASHBOARD
        // ----------------------------------------------------

        updateDashboard(data);


        // ----------------------------------------------------
        // HISTORY CHART
        // ----------------------------------------------------

        drawHistoryChart(
            data,
            "all"
        );


        // ----------------------------------------------------
        // PREDICTION CHART
        // ----------------------------------------------------

        drawPredictionChart(
            data
        );


        // ----------------------------------------------------
        // NEWS
        // ----------------------------------------------------

        await loadCompanyNews(
            symbol
        );


        console.log(
            "Analysis completed successfully"
        );

    }


    catch (error) {

        console.error(
            "ANALYSIS ERROR:",
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

            button.textContent =
                "Analyze";

        }

    }

}


// Make available globally
window.analyzeStock = analyzeStock;


// ============================================================
// UPDATE DASHBOARD
// ============================================================

function updateDashboard(data) {

    console.log(
        "Updating dashboard:",
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


    let currentPrice =
        Number(
            data.current_price
        );


    // --------------------------------------------------------
    // STOCK NAME
    // --------------------------------------------------------

    setText(
        "stockName",
        cleanSymbol(symbol)
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
        data.historical_records ??
        prices.length
    );


    // --------------------------------------------------------
    // FORECAST
    // --------------------------------------------------------

    if (
        predictions.length > 0
    ) {

        const finalPrediction =
            predictions[
                predictions.length - 1
            ];


        setText(
            "forecastPrice",
            formatPrice(
                finalPrediction
            )
        );


        const change =
            calculatePercentageChange(
                currentPrice,
                finalPrediction
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


    // --------------------------------------------------------
    // INDICATORS
    // --------------------------------------------------------

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


    // --------------------------------------------------------
    // RISK
    // --------------------------------------------------------

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

        console.error(
            "historyChart canvas not found"
        );

        return;

    }


    const prices =
        getHistoricalPrices(data);


    const dates =
        Array.isArray(
            data.historical_dates
        )
            ? data.historical_dates
            : [];


    if (
        prices.length === 0
    ) {

        console.warn(
            "No historical price data"
        );

        return;

    }


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


    if (
        labels.length === 0
    ) {

        console.warn(
            "No data for selected year"
        );

        return;

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

                    datasets: [

                        {

                            label:
                                "Closing Price",

                            data: values,

                            borderWidth: 2,

                            pointRadius: 0,

                            tension: 0.2,

                            fill: false

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {

                        mode: "index",

                        intersect: false

                    },

                    scales: {

                        x: {

                            ticks: {

                                maxTicksLimit: 12

                            }

                        },

                        y: {

                            beginAtZero: false

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

        console.warn(
            "Prediction chart data unavailable"
        );

        return;

    }


    const historical =
        history.slice(-60);


    const labels = [];


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


    for (
        let i = 0;
        i < predictions.length;
        i++
    ) {

        labels.push(
            "Forecast " +
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
            Math.max(
                historical.length - 1,
                0
            )
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

                    labels: labels,

                    datasets: [

                        {

                            label:
                                "Historical Price",

                            data:
                                historyData,

                            borderWidth: 2,

                            pointRadius: 0,

                            tension: 0.2

                        },

                        {

                            label:
                                "Bayesian Prediction",

                            data:
                                predictionData,

                            borderWidth: 3,

                            borderDash: [
                                6,
                                5
                            ],

                            pointRadius: 3,

                            tension: 0.2

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {

                        mode: "index",

                        intersect: false

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
        cleanSymbol(symbol);


    try {

        const response =
            await fetch(
                "/news/" +
                encodeURIComponent(
                    company
                )
            );


        if (!response.ok) {

            throw new Error(
                "News request failed"
            );

        }


        const data =
            await response.json();


        const articles =
            Array.isArray(
                data.articles
            )
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
                .map(function (article) {

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

                })
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
// RISK ANALYSIS
// ============================================================

function calculateRisk(
    data,
    currentPrice,
    predictions,
    indicators
) {

    let trend =
        "Neutral";


    let confidence =
        "Moderate";


    let risk =
        "Medium";


    const sma20 =
        Number(
            indicators.sma_20
        );


    const sma50 =
        Number(
            indicators.sma_50
        );


    const rsi =
        Number(
            indicators.rsi_14
        );


    // --------------------------------------------------------
    // MARKET DIRECTION
    // --------------------------------------------------------

    if (
        Number.isFinite(currentPrice) &&
        Number.isFinite(sma20) &&
        Number.isFinite(sma50)
    ) {

        if (
            currentPrice > sma20 &&
            sma20 > sma50
        ) {

            trend =
                "Bullish";

        }

        else if (
            currentPrice < sma20 &&
            sma20 < sma50
        ) {

            trend =
                "Bearish";

        }

        else {

            trend =
                "Neutral";

        }

    }


    // --------------------------------------------------------
    // CONFIDENCE
    // --------------------------------------------------------

    if (
        predictions.length >= 2
    ) {

        const first =
            Number(
                predictions[0]
            );


        const last =
            Number(
                predictions[
                    predictions.length - 1
                ]
            );


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


            if (
                movement < 1
            ) {

                confidence =
                    "High";

            }

            else if (
                movement < 3
            ) {

                confidence =
                    "Moderate";

            }

            else {

                confidence =
                    "Lower";

            }

        }

    }


    // --------------------------------------------------------
    // RISK
    // --------------------------------------------------------

    if (
        Number.isFinite(rsi)
    ) {

        if (
            rsi > 70 ||
            rsi < 30
        ) {

            risk =
                "High";

        }

        else if (
            rsi > 60 ||
            rsi < 40
        ) {

            risk =
                "Medium";

        }

        else {

            risk =
                "Lower";

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

    if (
        !Array.isArray(
            data?.historical_prices
        )
    ) {

        return [];

    }


    return data.historical_prices
        .map(Number)
        .filter(Number.isFinite);

}


// ============================================================
// GET PREDICTIONS
// ============================================================

function getPredictions(data) {

    if (
        !Array.isArray(
            data?.predictions
        )
    ) {

        return [];

    }


    return data.predictions
        .map(Number)
        .filter(Number.isFinite);

}


// ============================================================
// SET INDICATOR
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
        Number(value);


    if (
        !Number.isFinite(number)
    ) {

        element.textContent =
            "—";

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
        Number(value);


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
        Number(value);


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
// CALCULATE PERCENTAGE
// ============================================================

function calculatePercentageChange(
    oldValue,
    newValue
) {

    const oldNumber =
        Number(oldValue);


    const newNumber =
        Number(newValue);


    if (
        !Number.isFinite(oldNumber) ||
        !Number.isFinite(newNumber) ||
        oldNumber === 0
    ) {

        return null;

    }


    return (
        (
            (newNumber - oldNumber) /
            oldNumber
        ) * 100
    );

}


// ============================================================
// CLEAN SYMBOL
// ============================================================

function cleanSymbol(symbol) {

    return String(symbol || "")
        .replace(
            ".NS",
            ""
        )
        .replace(
            ".BO",
            ""
        );

}


// ============================================================
// FORMAT DATE
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
// ESCAPE HTML
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


// ============================================================
// ESCAPE ATTRIBUTE
// ============================================================

function escapeAttribute(value) {

    return escapeHtml(value);

}


// ============================================================
// SHOW DASHBOARD
// ============================================================

function showDashboard() {

    const dashboard =
        document.getElementById(
            "dashboard"
        );


    if (dashboard) {

        dashboard.classList.remove(
            "hidden"
        );

    }

}


// ============================================================
// SHOW LOADING
// ============================================================

function showLoading() {

    const loading =
        document.getElementById(
            "loading"
        );


    if (loading) {

        loading.classList.remove(
            "hidden"
        );

    }

}


// ============================================================
// HIDE LOADING
// ============================================================

function hideLoading() {

    const loading =
        document.getElementById(
            "loading"
        );


    if (loading) {

        loading.classList.add(
            "hidden"
        );

    }

}


// ============================================================
// SHOW ERROR
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


// ============================================================
// HIDE ERROR
// ============================================================

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