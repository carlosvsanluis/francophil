from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import yfinance as yf
from dateutil import parser as dateparser
import requests as http_requests
from datetime import datetime, timedelta
import re

app = Flask(__name__)
CORS(app)

# --- Company Lists ---

CAC40_TICKERS = {
    "MC.PA":    "LVMH",
    "OR.PA":    "L'Oreal",
    "TTE.PA":   "TotalEnergies",
    "SAN.PA":   "Sanofi",
    "AIR.PA":   "Airbus",
    "BNP.PA":   "BNP Paribas",
    "SAF.PA":   "Safran",
    "AI.PA":    "Air Liquide",
    "DSY.PA":   "Dassault Systemes",
    "ENGI.PA":  "Engie",
    "DG.PA":    "Vinci",
    "SGO.PA":   "Saint-Gobain",
    "CAP.PA":   "Capgemini",
    "CS.PA":    "AXA",
    "BN.PA":    "Danone",
    "RI.PA":    "Pernod Ricard",
    "LR.PA":    "Legrand",
    "CA.PA":    "Carrefour",
    "EN.PA":    "Bouygues",
    "STLAP.PA": "Stellantis",
}

PSEI_TICKERS = {
    "SM":    {"name": "SM Investments",   "cmpy_id": "599", "security_id": "520"},
    "BDO":   {"name": "BDO Unibank",     "cmpy_id": "260", "security_id": "468"},
    "ALI":   {"name": "Ayala Land",       "cmpy_id": "180", "security_id": "293"},
    "JFC":   {"name": "Jollibee Foods",   "cmpy_id": "86",  "security_id": "158"},
    "AC":    {"name": "Ayala Corporation","cmpy_id": "57",  "security_id": "180"},
    "MBT":   {"name": "Metrobank",        "cmpy_id": "128", "security_id": "108"},
    "BPI":   {"name": "BPI",              "cmpy_id": "234", "security_id": "101"},
    "TEL":   {"name": "PLDT",             "cmpy_id": "6",   "security_id": "134"},
    "MER":   {"name": "Meralco",          "cmpy_id": "118", "security_id": "137"},
    "SMPH":  {"name": "SM Prime Holdings","cmpy_id": "112", "security_id": "314"},
    "GLO":   {"name": "Globe Telecom",    "cmpy_id": "69",  "security_id": "127"},
    "URC":   {"name": "Universal Robina", "cmpy_id": "124", "security_id": "167"},
    "ICT":   {"name": "ICTSI",            "cmpy_id": "83",  "security_id": "142"},
    "AP":    {"name": "Aboitiz Power",    "cmpy_id": "609", "security_id": "532"},
    "DMC":   {"name": "DMCI Holdings",    "cmpy_id": "188", "security_id": "192"},
    "RLC":   {"name": "Robinsons Land",   "cmpy_id": "195", "security_id": "312"},
    "PGOLD": {"name": "Puregold",         "cmpy_id": "629", "security_id": "567"},
    "CNPF":  {"name": "Century Pacific",  "cmpy_id": "652", "security_id": "597"},
    "CNVRG": {"name": "Converge ICT",     "cmpy_id": "680", "security_id": "656"},
}


# --- Helpers ---

def fetch_yfinance_chart(symbol):
    """Fetch 1-year daily closing prices from Yahoo Finance."""
    data = yf.Ticker(symbol)
    hist = data.history(period="1y", interval="1d")
    hist = hist.dropna(subset=["Close"])

    if hist.empty:
        return None

    labels = [d.strftime("%Y-%m-%d") for d in hist.index]
    prices = [round(float(p), 2) for p in hist["Close"].tolist()]
    return {"ticker": symbol, "labels": labels, "prices": prices}


def fetch_pse_disclosures(ticker, company_name, cmpy_id):
    """Fetch latest disclosures from PSE Edge for a company."""
    url = "https://edge.pse.com.ph/companyDisclosures/search.ax"
    headers = {
        "Referer": "https://edge.pse.com.ph/companyPage/disclosures_702.do",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    resp = http_requests.post(
        url,
        data={"keyword": cmpy_id, "dateSortType": "DESC"},
        headers=headers,
        timeout=15,
    )
    html = resp.text

    items = []
    for edge_no, raw_title in re.findall(
        r"openPopup\('([^']+)'\)[^>]*>([^<]+)</a>", html
    ):
        title = raw_title.strip()
        items.append({"edge_no": edge_no, "title": title})

    # Match dates separately (same order as rows)
    dates = re.findall(r'<td class="alignC">([A-Z][a-z]{2} \d{2}, \d{4} \d{2}:\d{2} [AP]M)</td>', html)

    results = []
    for i, item in enumerate(items[:3]):
        if i < len(dates):
            dt = datetime.strptime(dates[i], "%b %d, %Y %I:%M %p")
            pub_time = int(dt.timestamp())
            published = dt.strftime("%Y-%m-%d %H:%M")
        else:
            pub_time = 0
            published = "N/A"

        results.append({
            "title": item["title"],
            "link": f"https://edge.pse.com.ph/openDiscViewer.do?edge_no={item['edge_no']}",
            "publisher": f"PSE Edge — {company_name} ({ticker})",
            "published": published,
            "timestamp": pub_time,
            "ticker": ticker,
            "exchange": "PSEi",
        })

    return results


def fetch_pse_chart(ticker, cmpy_id, security_id):
    """Fetch 1-year daily closing prices from PSE Edge."""
    url = "https://edge.pse.com.ph/common/DisclosureCht.ax"
    headers = {
        "Referer": "https://edge.pse.com.ph/companyPage/stockData.do",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    end = datetime.now()
    start = end - timedelta(days=365)
    payload = {
        "cmpy_id": cmpy_id,
        "security_id": security_id,
        "startDate": start.strftime("%m-%d-%Y"),
        "endDate": end.strftime("%m-%d-%Y"),
    }
    resp = http_requests.post(url, json=payload, headers=headers, timeout=15)
    data = resp.json()
    records = data.get("chartData", [])

    if not records:
        return None

    labels = []
    prices = []
    for r in records:
        dt = datetime.strptime(r["CHART_DATE"], "%b %d, %Y %H:%M:%S")
        labels.append(dt.strftime("%Y-%m-%d"))
        prices.append(round(float(r["CLOSE"]), 2))

    return {"ticker": ticker, "labels": labels, "prices": prices}


# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chart")
def get_chart_data():
    """Return 1-year daily closing prices for an index or company."""
    ticker = request.args.get("ticker", "")
    index_map = {"FCHI": "^FCHI", "PSEI": "PSEI.PS"}

    try:
        if ticker.upper() in index_map:
            result = fetch_yfinance_chart(index_map[ticker.upper()])
        elif ticker in CAC40_TICKERS:
            result = fetch_yfinance_chart(ticker)
        elif ticker in PSEI_TICKERS:
            info = PSEI_TICKERS[ticker]
            result = fetch_pse_chart(ticker, info["cmpy_id"], info["security_id"])
        else:
            return jsonify({"error": "Invalid ticker."}), 400

        if result is None:
            return jsonify({"error": "No data returned."}), 404

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/news")
def get_news():
    """Fetch news: yfinance for CAC 40, PSE Edge disclosures for PSEi.
    Returns up to 60 articles sorted by most recent first."""
    news_items = []

    # CAC 40 news from yfinance
    for ticker_symbol in CAC40_TICKERS:
        try:
            ticker = yf.Ticker(ticker_symbol)
            raw_news = ticker.news

            for item in raw_news[:3]:
                content = item.get("content", {})
                pub_date = content.get("pubDate", "")
                if pub_date:
                    dt = dateparser.parse(pub_date)
                    pub_time = int(dt.timestamp())
                    published = dt.strftime("%Y-%m-%d %H:%M UTC")
                else:
                    pub_time = 0
                    published = "N/A"

                canonical = content.get("canonicalUrl") or {}
                link = canonical.get("url") or content.get("previewUrl", "#")
                provider = content.get("provider") or {}

                news_items.append({
                    "title": content.get("title", "No Title"),
                    "link": link,
                    "publisher": provider.get("displayName", "Unknown"),
                    "published": published,
                    "timestamp": pub_time,
                    "ticker": ticker_symbol,
                    "exchange": "CAC 40",
                })
        except Exception:
            continue

    # PSEi disclosures from PSE Edge
    for ticker_symbol, info in PSEI_TICKERS.items():
        try:
            disclosures = fetch_pse_disclosures(
                ticker_symbol, info["name"], info["cmpy_id"]
            )
            news_items.extend(disclosures)
        except Exception:
            continue

    news_items.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify({"news": news_items[:60]})


@app.route("/api/companies")
def get_companies():
    """Return ticker-to-name mappings for both exchanges."""
    return jsonify({
        "cac40": CAC40_TICKERS,
        "psei": {t: info["name"] for t, info in PSEI_TICKERS.items()},
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
