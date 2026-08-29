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

    console.log("MarketPulse AI JavaScript loaded.");

    const button =
        document.getElementById("analyzeButton");

    const input =
        document.getElementById("stockSymbol");


    if (button) {

        button.addEventListener(
            "click",
            function () {

                analyzeStock();

            }
        );

    }


    if (input) {

        input.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {

                    event.preventDefault();

                    analyzeStock();

                }

            }
        );

    }


    document
        .querySelectorAll(".year-button")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    document
                        .querySelectorAll(".year-button")
                        .forEach(function (item) {

                            item.classList.remove(
                                "active"
                            );

                        });


                    this.classList.add(
                        "active"
                    );


                    if (currentData) {

                        drawHistoryChart(
                            currentData,
                            this.dataset.year
                        );

                    }

                }
            );

        });

});


// ============================================================
// SELECT STOCK
// ============================================================

function selectStock(symbol) {

    console.log(
        "Selected stock:",
        symbol
    );


    const input =
        document.getElementById(
            "stockSymbol"
        );


    if (!input) {

        console.error(
            "stockSymbol input not found."
        );

        return;

    }


    input.value =
        symbol;


    input.focus();

}


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


    if (
        value.startsWith("^")
    ) {

        return value;

    }


    if (
        !value.includes(".")
    ) {

        value += ".NS";

    }


    return value;

}


// ============================================================
// ANALYZE STOCK
// ============================================================

async function analyzeStock() {

    console.log(
        "Analyze button clicked."
    );


    const input =
        document.getElementById(
            "stockSymbol"
        );


    const button =
        document.getElementById(
            "analyzeButton"
        );


    if (!input) {

        showError(
            "Stock input field was not found."
        );

        return;

    }


    const symbol =
        normalizeSymbol(
            input.value
        );


    if (!symbol) {

        showError(
            "Please enter a stock symbol."
        );

        input.focus();

        return;

    }


    input.value =
        symbol;


    hideError();

    showLoading();


    if (button) {

        button.disabled =
            true;

        button.textContent =
            "Analysing...";

    }


    try {

        console.log(
            "Sending request:",
            symbol
        );


        const response =
            await fetch(
                "/predict",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            symbol: symbol
                        })

                }
            );


        console.log(
            "HTTP status:",
            response.status
        );


        const data =
            await response.json();


        console.log(
            "API response:",
            data
        );


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Server returned an error."
            );

        }


        if (!data.success) {

            throw new Error(
                data.error ||
                "Stock analysis failed."
            );

        }


        currentData =
            data;


        showDashboard();


        updateDashboard(
            data
        );


        drawHistoryChart(
            data,
            "all"
        );


        drawPredictionChart(
            data
        );


        loadCompanyNews(
            symbol
        );


        document
            .getElementById("dashboard")
            ?.scrollIntoView({
                behavior: "smooth"
            });


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

            button.disabled =
                false;

            button.textContent =
                "Analyze";

        }

    }

}


// ============================================================
// UPDATE DASHBOARD
// ============================================================

function updateDashboard(data) {

    const symbol =
        data.stock ||
        data.symbol ||
        "Unknown";


    const prices =
        getHistoricalPrices(
            data
        );


    const predictions =
        getPredictions(
            data
        );


    const currentPrice =
        Number(
            data.current_price
        );


    setText(
        "stockName",
        symbol
            .replace(".NS", "")
            .replace(".BO", "")
    );


    setText(
        "currentPrice",
        formatPrice(
            currentPrice
        )
    );


    setText(
        "historicalRecords",
        data.historical_records ||
        prices.length ||
        "—"
    );


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
            formatPercent(
                change
            )
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
        getHistoricalPrices(
            data
        );


    const dates =
        Array.isArray(
            data.historical_dates
        )
            ? data.historical_dates
            : [];


    if (
        prices.length === 0
    ) {

        return;

    }


    const labels = [];
    const values = [];


    for (
        let i = 0;
        i < prices.length;
        i++
    ) {

        const date =
            dates[i] || "";


        if (
            selectedYear !== "all" &&
            !String(date).startsWith(
                String(selectedYear)
            )
        ) {

            continue;

        }


        labels.push(
            formatDateLabel(
                date
            )
        );


        values.push(
            prices[i]
        );

    }


    if (
        labels.length === 0
    ) {

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

                    labels:
                        labels,

                    datasets: [

                        {

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
        getHistoricalPrices(
            data
        );


    const predictions =
        getPredictions(
            data
        );


    if (
        history.length === 0 ||
        predictions.length === 0
    ) {

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
        cleanSymbol(
            symbol
        );


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
                "News request failed."
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
// RISK
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

    }


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
// DATA HELPERS
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
        .filter(
            Number.isFinite
        );

}


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
        .filter(
            Number.isFinite
        );

}


// ============================================================
// INDICATOR
// ============================================================

function setIndicator(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );


    if (!element) {

        return;

    }


    const number =
        Number(value);


    if (
        !Number.isFinite(
            number
        )
    ) {

        element.textContent =
            "—";

        return;

    }


    element.textContent =
        number.toFixed(2);

}


// ============================================================
// TEXT
// ============================================================

function setText(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );


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
        !Number.isFinite(
            number
        )
    ) {

        return "—";

    }


    return (
        "₹" +
        number.toLocaleString(
            "en-IN",
            {

                minimumFractionDigits:
                    2,

                maximumFractionDigits:
                    2

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
        !Number.isFinite(
            number
        )
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
// PERCENTAGE CHANGE
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
        )
        .toUpperCase();

}


// ============================================================
// DATE
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

            day:
                "2-digit",

            month:
                "short",

            year:
                "numeric"

        }
    );

}


// ============================================================
// HTML ESCAPING
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

    return escapeHtml(
        value
    );

}


// ============================================================
// DASHBOARD
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
// LOADING
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
            String(message);

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