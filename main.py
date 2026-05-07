from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import yfinance as yf
from dateutil import parser as dateparser

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
    "SVTMF": "SM Investments",
    "BDOUY": "BDO Unibank",
    "AYAAY": "Ayala Land",
    "JBFCY": "Jollibee Foods",
    "AYALY": "Ayala Corporation",
    "MTPOY": "Metrobank",
    "BPHLY": "BPI",
    "PHI":   "PLDT",
    "MAEOY": "Meralco",
    "SPHXF": "SM Prime Holdings",
    "GTMEY": "Globe Telecom",
    "UVRBY": "Universal Robina",
    "ICTEY": "ICTSI",
    "ABZPY": "Aboitiz Power",
    "DMCHY": "DMCI Holdings",
    "RBLAY": "Robinsons Land",
    "PRGLY": "Puregold",
}

ALL_TICKERS = list(CAC40_TICKERS.keys()) + list(PSEI_TICKERS.keys())


# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chart")
def get_chart_data():
    """Return 1-year daily closing prices for an index or company."""
    ticker = request.args.get("ticker", "")
    index_map = {"FCHI": "^FCHI", "PSEI": "PSEI.PS"}
    if ticker.upper() in index_map:
        symbol = index_map[ticker.upper()]
    elif ticker in CAC40_TICKERS or ticker in PSEI_TICKERS:
        symbol = ticker
    else:
        return jsonify({"error": "Invalid ticker."}), 400

    try:
        data = yf.Ticker(symbol)
        hist = data.history(period="1y", interval="1d")

        hist = hist.dropna(subset=["Close"])

        if hist.empty:
            return jsonify({"error": "No data returned from Yahoo Finance."}), 404

        labels = [d.strftime("%Y-%m-%d") for d in hist.index]
        prices = [round(float(p), 2) for p in hist["Close"].tolist()]

        return jsonify({
            "ticker": symbol,
            "labels": labels,
            "prices": prices,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/news")
def get_news():
    """Fetch up to 3 news items per company across CAC 40 + PSEi tickers.
    Returns up to 60 articles sorted by most recent first."""
    news_items = []

    for ticker_symbol in ALL_TICKERS:
        try:
            ticker = yf.Ticker(ticker_symbol)
            raw_news = ticker.news

            exchange = "CAC 40" if ticker_symbol in CAC40_TICKERS else "PSEi"

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
                    "exchange": exchange,
                })
        except Exception:
            continue  # skip tickers that fail silently

    news_items.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify({"news": news_items[:60]})


@app.route("/api/companies")
def get_companies():
    """Return ticker-to-name mappings for both exchanges."""
    return jsonify({
        "cac40": CAC40_TICKERS,
        "psei": PSEI_TICKERS,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
