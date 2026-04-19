# EvenStocks — AI-Powered Indian Stock Analysis Platform

EvenStocks is a monorepo for analysing Indian (BSE/NSE) stocks with AI. It scrapes ~5,300 companies from screener.in into a local SQLite store, exposes chat + per-stock detail pages in React, and runs a multi-agent "Investment Committee" that produces a structured Buy / Hold / Sell verdict.

Everything the LLM sees comes from real scraped data — not model training knowledge.

---

## Services

| Service | Stack | Port | Purpose |
|---|---|---|---|
| `evenstocks-react` | React, React Router, Bootstrap | 3000 | Landing page, chatbot, stock detail, admin |
| `evenstocks-backend` | Node / Express | 5000 | Thin proxy between React and Flask / Python services |
| `evenstocks-api` | Flask, MySQL | 5809 | Users, auth, OTP, Razorpay, feedback |
| `evenstocks_chatbot` | FastAPI, WebSocket, Anthropic SDK | 8000 | Chat, stock search, stock detail, autocomplete |
| `evenstocks-agents` | FastAPI, Anthropic SDK | 5810 | Multi-agent Investment Committee + Toolkit |
| `evenstocks-scapping` | Python, requests, BeautifulSoup, Selenium | — | Scrapes screener.in → `stocks.db` |
| `mysql` | MySQL 8 | 3307 | User data |

SQLite (`evenstocks_chatbot/data/stocks.db`) is shared between the chatbot, agents, and scraper via a bind-mount.

---

## Frontend highlights

- **Home / Chat** ([ChatBotPageFinal.jsx](evenstocks-react/src/pages/ChatBotPageFinal.jsx)) — NSE-style live stock ticker above the chat, `@` autocomplete for stock tagging, WebSocket streaming, markdown rendering, collapsible sidebar.
- **Stock Detail** (`/stock/:name`) — company info, financial tables (quarters, P&L, balance sheet, cash flow, ratios, shareholding), Investment Committee and Investment Toolkit panels.
- **Investment Committee** ([InvestmentCommittee.jsx](evenstocks-react/src/components/InvestmentCommittee.jsx)) — live SSE streaming across 4 tabs: **Verdict**, **Debate**, **Risk**, **Analysts**.
- **Investment Toolkit** ([InvestmentToolkit.jsx](evenstocks-react/src/components/InvestmentToolkit.jsx)) — Compare (two tickers side-by-side with autocomplete), Portfolio Health (up to 10 tickers in parallel), Goal Planner (SIP / lumpsum corpus calc), Verdict History.
- **Stock Ticker** ([StockTicker.jsx](evenstocks-react/src/components/StockTicker.jsx)) — curated 30 large-caps, theme-aware, pause button, click-through to stock page.
- Landing, Login/Signup, Admin Dashboard, Checkout, Razorpay, Privacy/Terms.

Theme: brand green `#02634D`, light/dark via `.chatbot-page-final.{light,dark}-theme`.

---

## Multi-agent Investment Committee

Lives in [evenstocks-agents/agents/](evenstocks-agents/agents/). Pipeline streams agent-by-agent to the UI.

1. **Analysts** — Fundamentals, Technical, News (Google News + Yahoo RSS), Sentiment (Reddit: 5 Indian investing subs), Macro India (RBI / CPI / FII / USD-INR / Brent), Concall Summarizer, SEBI red-flag scanner (pledged shares, RoE, CFO-vs-PAT divergence).
2. **Research Debate** — Bull vs Bear Researcher → Research Manager synthesis.
3. **Risk Team** — Aggressive / Conservative / Neutral → Chief Risk Officer.
4. **Portfolio Manager** — Final Buy / Hold / Sell verdict with post-July-2024 Indian tax impact (STCG 20% / LTCG 12.5% above ₹1.25L).

Verdicts are logged to `evenstocks_chatbot/data/verdicts.db` for the History tab.

---

## Scraper

[evenstocks-scapping/scrape_tables.py](evenstocks-scapping/scrape_tables.py) pulls company info + 6 financial tables per stock from screener.in.

**Auto-freshness**: rows older than `STALE_AFTER_DAYS` (default 2) are re-scraped; fresher rows are skipped. Override with `--stale-days N` or `--force`. Every row carries a `last_updated` UTC timestamp.

```bash
docker compose --profile scraping run --rm evenstocks-scapping python scrape_tables.py
docker compose --profile scraping run --rm evenstocks-scapping python scrape_tables.py --force
```

Other scripts: `get_all_stocks_list.py` (refresh the 5,300-row CSV via Selenium), `scrape_stock_fundamental.py` (deeper per-stock scrape), `scrape_pdfs.py` (annual reports / concalls → text).

---

## Databases

**MySQL `evenstocks_db`** (used by `evenstocks-api`)
`users`, `user_feedback`, `contact_info`, `user_billing_history`, `user_queries`.

**SQLite `stocks.db`** (used by chatbot + agents)
`company_info` (one row per stock, + `last_updated`), `financial_tables` (JSON per `stock × table_type`), `pdf_texts` (annual reports, announcements, concalls).

**SQLite `verdicts.db`** — committee verdict history.

---

## Run

### Docker (recommended)

```bash
cp .env.example .env        # fill in ANTHROPIC_API_KEY, SENDER_*, RAZORPAY_*
docker compose up --build
```

Then open <http://localhost:3000>. See [DOCKER.md](DOCKER.md) for details.

### Local dev (4 terminals, from `evenstocksv2/`)

```bash
# 1. Flask user API  (needs MySQL + schema.sql)
cd evenstocks-api && pip install -r requirements.txt && python app.py

# 2. AI chatbot       (needs ANTHROPIC_API_KEY, data/stocks.db)
cd evenstocks_chatbot && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# 3. Agents service   (needs ANTHROPIC_API_KEY, data/stocks.db)
cd evenstocks-agents && pip install -r requirements.txt && uvicorn main:app --reload --port 5810

# 4. Node proxy
cd evenstocks-backend && npm install && node server.js

# 5. Frontend
cd evenstocks-react && npm install && npm start
```

---

## Request flow

```
Auth       : React → Node(5000) → Flask(5809) → MySQL
Chat       : React ⇄ WebSocket → FastAPI(8000) → Claude + SQLite
Stock page : React → FastAPI(8000) /api/stocks/:name → SQLite
Committee  : React ⇄ SSE → FastAPI(5810) → Claude (n agents) → SQLite
Payments   : React → Node(5000) → Flask(5809) → Razorpay
```

---

## Key env vars

```
ANTHROPIC_API_KEY=sk-ant-...
SENDER_EMAIL=...        SENDER_PASSWORD=...
RAZORPAY_KEY_ID=...     RAZORPAY_KEY_SECRET=...
DB_PASSWORD=example
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_CHATBOT_WS_URL=ws://localhost:8000
```

---

## Repo layout

```
evenstocksv2/
├── evenstocks-react/        # React frontend
├── evenstocks-backend/      # Node proxy
├── evenstocks-api/          # Flask user API + MySQL schema
├── evenstocks_chatbot/      # FastAPI chat + stock endpoints + SQLite
├── evenstocks-agents/       # Multi-agent committee + toolkit
├── evenstocks-scapping/     # Screener.in scrapers
├── graphify-out/            # Knowledge graph (architecture reference)
├── docker-compose.yml
├── DOCKER.md
├── CLAUDE.md
└── README.md
```
