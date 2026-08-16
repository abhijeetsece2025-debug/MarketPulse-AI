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

    const button =
        document.getElementById("analyzeButton");

    const input =
        document.getElementById("stockSymbol");

    if (button) {

        button.addEventListener(
            "click",
            analyzeStock
        );

    }

    if (input) {

        input.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {

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
                        .forEach(function (b) {

                            b.classList.remove(
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

    const input =
        document.getElementById(
            "stockSymbol"
        );

    if (input) {

        input.value = symbol;

    }

    analyzeStock();

}


// ============================================================
// NORMALIZE SYMBOL
// ============================================================

function normalizeSymbol(symbol) {

    symbol =
        String(symbol || "")
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
// ANALYZE
// ============================================================

async function analyzeStock() {

    const input =
        document.getElementById(
            "stockSymbol"
        );

    const button =
        document.getElementById(
            "analyzeButton"
        );

    if (!input) {

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

        return;

    }

    input.value = symbol;

    hideError();
    showLoading();

    if (button) {

        button.disabled = true;

        button.textContent =
            "Analysing...";

    }


    try {

        console.log(
            "Sending:",
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

                    body: JSON.stringify({
                        symbol: symbol
                    })

                }
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
                "Server error."
            );

        }


        if (!data.success) {

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

        await loadCompanyNews(
            symbol
        );

    }


    catch (error) {

        console.error(
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
        symbol.replace(
            ".NS",
            ""
        )
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
        prices.length
    );


    if (
        predictions.length
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
// HISTORY
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
        data.historical_dates || [];


    let labels = [];
    let values = [];


    for (
        let i = 0;
        i < prices.length;
        i++
    ) {

        const date =
            dates[i] ||
            "";


        if (
            selectedYear !== "all" &&
            !date.includes(
                selectedYear
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

                        data: values,

                        borderWidth: 2,

                        pointRadius: 0,

                        tension: 0.2,

                        fill: false

                    }]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio:
                        false,

                    interaction: {

                        mode: "index",

                        intersect: false

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

function drawPredictionChart(
    data
) {

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

                    labels: labels,

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

async function loadCompanyNews(
    symbol
) {

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
            .replace(
                ".NS",
                ""
            )
            .replace(
                ".BO",
                ""
            );


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
            data.articles || [];


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
        Number.isFinite(
            currentPrice
        ) &&
        Number.isFinite(
            sma20
        ) &&
        Number.isFinite(
            sma50
        )
    ) {

        if (
            currentPrice >
            sma20 &&
            sma20 >
            sma50
        ) {

            trend =
                "Bullish";

        }

        else if (
            currentPrice <
            sma20 &&
            sma20 <
            sma50
        ) {

            trend =
                "Bearish";

        }

    }


    if (
        predictions.length >= 2
    ) {

        const first =
            predictions[0];

        const last =
            predictions[
                predictions.length - 1
            ];

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
// HELPERS
// ============================================================

function getHistoricalPrices(data) {

    return Array.isArray(
        data.historical_prices
    )
        ? data.historical_prices
            .map(Number)
            .filter(
                Number.isFinite
            )
        : [];

}


function getPredictions(data) {

    return Array.isArray(
        data.predictions
    )
        ? data.predictions
            .map(Number)
            .filter(
                Number.isFinite
            )
        : [];

}


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


function formatPrice(
    value
) {

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
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        )
    );

}


function formatPercent(
    value
) {

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


function calculatePercentageChange(
    oldValue,
    newValue
) {

    if (
        !Number.isFinite(
            oldValue
        ) ||
        !Number.isFinite(
            newValue
        ) ||
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


function formatDateLabel(
    value
) {

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


function escapeHtml(
    value
) {

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


function escapeAttribute(
    value
) {

    return escapeHtml(
        value
    );

}


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


function showError(
    message
) {

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


window.selectStock =
    selectStock;

window.analyzeStock =
    analyzeStock;