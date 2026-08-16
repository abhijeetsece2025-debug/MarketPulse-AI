import requests

NEWS_API_KEY = "8937aef04b394e098fb89479fc7ecdd7"

NEWS_URL = "https://newsapi.org/v2/everything"


def get_company_news(symbol):

    symbol = str(symbol).strip().upper()

    # Remove NSE/BSE suffix
    company = (
        symbol
        .replace(".NS", "")
        .replace(".BO", "")
    )

    # Map common Indian stocks to company names
    company_names = {

        "RELIANCE": "Reliance Industries",
        "TCS": "Tata Consultancy Services",
        "INFY": "Infosys",
        "HDFCBANK": "HDFC Bank",
        "ICICIBANK": "ICICI Bank",
        "SBIN": "State Bank of India",
        "ITC": "ITC Limited",
        "BHARTIARTL": "Bharti Airtel",
        "MARUTI": "Maruti Suzuki",
        "SUNPHARMA": "Sun Pharmaceutical",
        "AXISBANK": "Axis Bank",
        "KOTAKBANK": "Kotak Mahindra Bank",
        "LT": "Larsen Toubro",
        "ADANIENT": "Adani Enterprises",
        "ADANIPORTS": "Adani Ports",
        "WIPRO": "Wipro",
        "HCLTECH": "HCL Technologies",
        "TATAMOTORS": "Tata Motors",
        "TATASTEEL": "Tata Steel",
        "BAJFINANCE": "Bajaj Finance",
        "ASIANPAINT": "Asian Paints",
        "HINDUNILVR": "Hindustan Unilever",
        "POWERGRID": "Power Grid Corporation",
        "NTPC": "NTPC",
        "ONGC": "ONGC",
        "COALINDIA": "Coal India",
        "DRREDDY": "Dr Reddy",
        "CIPLA": "Cipla",
        "EICHERMOT": "Eicher Motors",
        "HEROMOTOCO": "Hero MotoCorp",
        "M&M": "Mahindra Mahindra",
    }

    company_name = company_names.get(
        company,
        company
    )

    print(
        f"Searching news for: {company_name}"
    )

    params = {

        "q": f'"{company_name}"',

        "language": "en",

        "sortBy": "publishedAt",

        "pageSize": 10,

        "apiKey": NEWS_API_KEY
    }

    try:

        response = requests.get(
            NEWS_URL,
            params=params,
            timeout=15
        )

        print(
            "NewsAPI status:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "NewsAPI error:",
                response.text
            )

            return []

        result = response.json()

        articles = result.get(
            "articles",
            []
        )

        clean_articles = []

        for article in articles:

            title = article.get(
                "title"
            )

            if not title:
                continue

            clean_articles.append({

                "title": title,

                "source": {
                    "name":
                    (
                        article.get(
                            "source",
                            {}
                        ).get(
                            "name"
                        )
                        or
                        "Unknown source"
                    )
                },

                "publishedAt":
                    article.get(
                        "publishedAt",
                        ""
                    ),

                "url":
                    article.get(
                        "url",
                        ""
                    )
            })

        print(
            f"Company news found: {len(clean_articles)}"
        )

        return clean_articles

    except Exception as error:

        print(
            "News request error:",
            repr(error)
        )

        return []