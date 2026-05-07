# FrancoPhil.com — CAC 40 & PSEi Dashboard

A stock market dashboard web app displaying index charts and news for the French (CAC 40) and Philippine (PSEi) stock exchanges.

## Project Structure

```
AI Project/
├── main.py              # Flask backend
├── requirements.txt     # Python dependencies
└── templates/
    └── index.html       # Single-page frontend (HTML + CSS + JS)
```

## Stack

- **Backend**: Python / Flask with Flask-CORS
- **Data**: yfinance (Yahoo Finance API)
- **Frontend**: Vanilla HTML/CSS/JavaScript, Chart.js (CDN)

## Running the App

```bash
pip install -r requirements.txt
python main.py
```

App runs at `http://localhost:5000` with debug mode enabled.

## Backend (`main.py`)

### Ticker Lists

- `CAC40_TICKERS` — 20 French companies with `.PA` suffix (e.g., `MC.PA`, `OR.PA`)
- `PSEI_TICKERS` — 20 Philippine companies with `.PS` suffix (e.g., `SM.PS`, `BDO.PS`)
- `ALL_TICKERS` — Combined list of both

### API Routes

| Route | Description |
|---|---|
| `GET /` | Serves `index.html` |
| `GET /api/chart/<ticker>` | Returns 1-year daily closing prices for `^FCHI` or `^PSEI`. Accepts `FCHI` or `PSEI` as the ticker param. |
| `GET /api/news` | Fetches up to 3 news articles per ticker across all 40 companies. Returns up to 60 articles sorted by most recent first. |

## Frontend (`templates/index.html`)

### Features

- **Live UTC clock** in the header
- **Two index charts** (CAC 40 and PSEi) with:
  - Current price and day-over-day change (green/red)
  - Time range selector: 1M, 3M (default), 6M, 1Y
  - Gradient line charts via Chart.js
- **Market News grid** with:
  - Filter buttons: All News / CAC 40 Only / PSEi Only
  - Color-coded cards (orange for CAC 40, blue for PSEi)
  - Links open in new tab

### Design

- Dark theme with CSS variables (`--bg-primary: #0d1117`, GitHub-style dark)
- Accent colors: orange (`#f7931a`) for CAC 40, cyan (`#00b4d8`) for PSEi
- Responsive grid layout (single column below 900px)

## Dependencies

```
flask==3.0.3
flask-cors==4.0.1
yfinance==0.2.40
```
