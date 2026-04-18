# EvenStocks — AI Investment Committee Roadmap

**Owner:** Tarun Tiwari
**Target users:** Indian retail equity investors
**Core idea:** A multi-agent AI "investment committee" that analyzes Indian stocks (fundamentals, technicals, news, sentiment, F&O, macro) and debates live — giving users a transparent, tax-aware, SEBI-aware verdict.
**Inspiration:** TradingAgents (LangGraph multi-agent pattern) — adapted for Indian market.

---

## Re-thought feature list (consolidated from 36 → 18 user stories)

The earlier 36 points mixed UI features, backend agents, data integrations, and analytics together. Reorganized into user-centered stories where each agent/integration is a *technical task* supporting a *user value*.

---

## EPIC A — Core Analysis Engine

The minimum viable "Investment Committee". Everything else builds on this.

### US-A1: One-Click Stock Analysis
**As an** Indian retail investor
**I want** to click an "Analyze with AI Committee" button on any stock page
**So that** I get a thorough multi-angle view without doing manual research on 5 different sites

**Acceptance Criteria:**
- [ ] Button visible on `StockDetailPage` (near price row)
- [ ] Clicking triggers the agent pipeline
- [ ] UI shows loading/progress indicator (which agent is running)
- [ ] Full result returns within ~45s P95
- [ ] Fails gracefully with retry button on error

**Technical Tasks:**
- [ ] FE: Add "Analyze" button + loading state in `StockDetailPage.jsx`
- [ ] BE (Node): `POST /api/analyze/:ticker` → proxies to agents service
- [ ] Agents (Python): `evenstocks-agents/` service with FastAPI + LangGraph
- [ ] Docker: Add `evenstocks-agents` service to `docker-compose.yml`
- [ ] Agents: Read existing Screener data from MySQL

**Priority:** P0  **Phase:** 1  **Effort:** 3 days

---

### US-A2: Live Agent Reasoning Stream
**As an** investor
**I want** to see each agent "think" in real time (not just a final verdict)
**So that** I can trust the analysis — black-box tips don't earn trust

**Acceptance Criteria:**
- [ ] Each agent's output streams token-by-token as it runs
- [ ] Agent avatars shown as a "boardroom" (Fundamentals, Technical, News, Sentiment, Bull, Bear, Risk-3, PM)
- [ ] Active agent highlighted; completed agents show ✓
- [ ] User can expand/collapse each agent's full reasoning

**Technical Tasks:**
- [ ] Agents: FastAPI WebSocket endpoint (or SSE) that streams per-agent tokens
- [ ] BE (Node): WebSocket proxy from frontend → agents service
- [ ] FE: New `InvestmentCommitteePanel.jsx` with agent avatar grid
- [ ] FE: Stream handler hook `useAgentStream(ticker)`
- [ ] CSS: "typing" animation per active agent

**Priority:** P0  **Phase:** 2  **Effort:** 4 days

---

### US-A3: Verdict Card
**As an** investor
**I want** a crisp final verdict card with rating, target price, stop-loss, and time horizon
**So that** I can act without re-reading 10 pages of analysis

**Acceptance Criteria:**
- [ ] Rating: Strong Buy / Accumulate / Hold / Reduce / Sell (Indian convention)
- [ ] Target price + stop-loss + expected time horizon
- [ ] Confidence score (0–100)
- [ ] Key thesis in 3 bullet points
- [ ] Key risks in 3 bullet points

**Technical Tasks:**
- [ ] Agents: `portfolio_manager.py` agent returns structured JSON verdict
- [ ] FE: `VerdictCard.jsx` component with Indian rating badge colors
- [ ] FE: Save verdict to user history (requires US-E1 schema)

**Priority:** P0  **Phase:** 1  **Effort:** 1 day

---

### US-A4: Bull vs Bear Debate Panel
**As an** investor
**I want** to see Bull and Bear researchers argue the thesis
**So that** I see both sides and can form my own view

**Acceptance Criteria:**
- [ ] Two-column layout: Bull (green) vs Bear (red)
- [ ] 2 rounds of debate minimum
- [ ] Each argument references specific data points
- [ ] "Debate Winner" summary at the bottom

**Technical Tasks:**
- [ ] Agents: `bull_researcher.py` + `bear_researcher.py` with debate loop in LangGraph
- [ ] Agents: Research manager that judges debate
- [ ] FE: `DebatePanel.jsx` with alternating bull/bear cards

**Priority:** P1  **Phase:** 2  **Effort:** 3 days

---

### US-A5: 3-Way Risk Panel
**As an** investor
**I want** to see aggressive / conservative / neutral risk views side-by-side
**So that** I know the risk range, not just a single risk score

**Acceptance Criteria:**
- [ ] 3 tabs: Aggressive / Conservative / Neutral
- [ ] Each tab shows that analyst's view
- [ ] Final risk rating synthesizes all three

**Technical Tasks:**
- [ ] Agents: 3 risk debators + synthesis in LangGraph
- [ ] FE: `RiskPanel.jsx` with tab switcher

**Priority:** P1  **Phase:** 2  **Effort:** 2 days

---

## EPIC B — Indian Market Differentiators

These make EvenStocks genuinely useful to Indian investors — TradingAgents has none of this.

### US-B1: Tax-Aware Hold/Sell Guidance
**As an** Indian investor
**I want** tax impact calculated on every Buy/Sell recommendation
**So that** I don't lose gains to STCG (15%) when holding 34 more days saves me ₹X via LTCG (12.5% over ₹1L)

**Acceptance Criteria:**
- [ ] Verdict card shows "Sell now: ₹X STCG tax" vs "Hold N days for LTCG: saves ₹Y"
- [ ] Accounts for ₹1L LTCG exemption per FY
- [ ] Works for both equity + mutual funds
- [ ] User can input their buy price or connect portfolio (later)

**Technical Tasks:**
- [ ] Agents: `tax_engine.py` — STCG/LTCG calculator module
- [ ] Agents: Inject tax context into PM's prompt
- [ ] FE: `TaxImpactBadge.jsx` component
- [ ] DB: `user_holdings` table for buy price/quantity

**Priority:** P0  **Phase:** 4  **Effort:** 3 days

---

### US-B2: SEBI Red Flag Alerts
**As an** investor
**I want** critical SEBI/regulatory red flags prominently flagged
**So that** I avoid companies with insider selling clusters, rising promoter pledge, or FII exits — these predict 60% of Indian stock blow-ups

**Acceptance Criteria:**
- [ ] Red banner at top of stock page if any flag triggers
- [ ] Flags: promoter pledge ↑ >5% QoQ, insider selling cluster (3+ in 30d), FII holding ↓ >2%, rating downgrade, auditor resignation
- [ ] Click flag → detail view with source links
- [ ] Historical flag timeline

**Technical Tasks:**
- [ ] Data: SEBI insider trade disclosure scraper
- [ ] Data: BSE promoter pledge tracker
- [ ] Data: FII/DII holding parser (shareholding pattern XBRL)
- [ ] Agents: `regulatory_analyst.py` that aggregates + ranks flags
- [ ] BE: `GET /api/redflags/:ticker` endpoint
- [ ] FE: `RedFlagBanner.jsx` + detail modal

**Priority:** P0  **Phase:** 3  **Effort:** 5 days

---

### US-B3: F&O Context Panel
**As an** investor (even cash-only)
**I want** to see F&O signals for liquid stocks — OI build-up, PCR, max pain, ban-list status
**So that** I know if smart money is positioned against my trade

**Acceptance Criteria:**
- [ ] Panel shown only for F&O-eligible stocks
- [ ] Current OI, OI change %, PCR, max pain strike
- [ ] F&O ban list warning badge
- [ ] Roll-over % during expiry week

**Technical Tasks:**
- [ ] Data: NSE F&O data scraper (bhavcopy + live OI)
- [ ] Agents: `fno_analyst.py`
- [ ] FE: `FnoPanel.jsx`

**Priority:** P1  **Phase:** 3  **Effort:** 3 days

---

### US-B4: Macro-India Impact Agent
**As an** investor
**I want** the agent to factor in RBI policy, budget, monsoon, election cycle, and sector rotation
**So that** sector bets are timed correctly (e.g., bank stocks before rate cut, FMCG after good monsoon)

**Acceptance Criteria:**
- [ ] Macro panel on every stock with sector-specific signals
- [ ] RBI policy calendar highlighted
- [ ] Election-cycle historical pattern for the sector
- [ ] Monsoon/GST changes mentioned where relevant

**Technical Tasks:**
- [ ] Data: RBI policy calendar + past decisions
- [ ] Data: Historical sector performance by macro event (Claude-generated baseline)
- [ ] Agents: `macro_india_analyst.py`
- [ ] FE: `MacroPanel.jsx`

**Priority:** P2  **Phase:** 4  **Effort:** 4 days

---

## EPIC C — Real-Time Data Feeds

The agents are only as good as their data.

### US-C1: India-Focused News Feed
**As an** investor
**I want** news filtered by stock from Moneycontrol / ET / Livemint / BS
**So that** I don't miss corporate announcements, earnings, or sector news

**Acceptance Criteria:**
- [ ] News tab on stock page with latest 20 items
- [ ] Source attribution + timestamp
- [ ] LLM-generated 1-line summary per item
- [ ] Sentiment tag (positive / negative / neutral)

**Technical Tasks:**
- [ ] Scrapers: Moneycontrol, ET Markets, Livemint, BS RSS/API
- [ ] Worker: Every 15min crawl + summarize
- [ ] DB: `news_articles` table with ticker mapping
- [ ] Agents: `news_analyst.py` reads last 7 days
- [ ] FE: `NewsFeed.jsx` already exists — enhance with sentiment tags

**Priority:** P0  **Phase:** 3  **Effort:** 4 days

---

### US-C2: Social Sentiment Gauge
**As an** investor
**I want** a sentiment gauge combining X/Twitter + Reddit signals
**So that** I see when retail is euphoric (sell signal) or panicking (buy signal)

**Acceptance Criteria:**
- [ ] Needle gauge: Extreme Fear → Neutral → Extreme Greed
- [ ] 24h / 7d / 30d windows
- [ ] Drill down: sample tweets with sentiment scores
- [ ] Volume trend (mention count over time)

**Technical Tasks:**
- [ ] X API v2 streaming filtered by cashtag ($TATAMOTORS etc.)
- [ ] Reddit API for r/IndianStocks, r/IndianStreetBets, r/StocksInvestment
- [ ] Sentiment scoring: Claude Haiku cheap LLM pass
- [ ] DB: `social_mentions` table
- [ ] Agents: `sentiment_analyst.py`
- [ ] FE: `SentimentGauge.jsx` + sample mentions drawer

**Priority:** P0  **Phase:** 3  **Effort:** 5 days

---

### US-C3: BSE/NSE Corporate Announcements
**As an** investor
**I want** official BSE/NSE filings (dividends, bonuses, splits, board meetings, results)
**So that** I react to corporate actions before retail herd does

**Acceptance Criteria:**
- [ ] Announcements tab on stock page
- [ ] Categorized: Dividend / Bonus / Split / Results / Board Meeting / Other
- [ ] PDF links + LLM summary
- [ ] Push notification on material announcements (see US-E3)

**Technical Tasks:**
- [ ] Data: BSE announcements API + NSE corporate actions
- [ ] Worker: hourly crawl
- [ ] DB: `corporate_announcements` table
- [ ] FE: `AnnouncementsPanel.jsx`

**Priority:** P1  **Phase:** 3  **Effort:** 3 days

---

### US-C4: Earnings Call Summarizer
**As an** investor
**I want** 5-bullet summary of the latest quarterly earnings call
**So that** I don't have to listen to 90-minute calls — I get guidance, capex, red flags in 30 seconds

**Acceptance Criteria:**
- [ ] "Latest Concall" card on stock page
- [ ] 5 bullets: Revenue/PAT beat-miss, Guidance, Capex plans, Management tone, Red flags
- [ ] Link to full transcript
- [ ] Historical concall sentiment trend

**Technical Tasks:**
- [ ] Scraper: BSE concall PDFs / YouTube transcripts
- [ ] Agents: `concall_summarizer.py` (Claude Sonnet for reasoning)
- [ ] DB: `concalls` table with summary + transcript URL
- [ ] FE: `ConcallCard.jsx`

**Priority:** P1  **Phase:** 4  **Effort:** 4 days

---

## EPIC D — Portfolio Intelligence

Differentiator — no Indian broker platform does this well.

### US-D1: Portfolio Health Check
**As an** investor with existing holdings
**I want** to upload my portfolio and have the AI committee debate my entire portfolio
**So that** I see concentration risk, sector overlap, beta exposure, and under/over-weight recommendations

**Acceptance Criteria:**
- [ ] Upload CSV (Zerodha/Groww format) or manual entry
- [ ] Portfolio summary: total value, sector %, beta, P/E weighted
- [ ] Top 3 concentration risks
- [ ] Top 3 suggested actions (trim X, add Y, rebalance Z)
- [ ] Tax-aware action suggestions (US-B1 dependency)

**Technical Tasks:**
- [ ] FE: Upload UI + holdings table
- [ ] DB: `portfolios` + `portfolio_holdings` tables
- [ ] Agents: `portfolio_health_agent.py` — runs analysis pipeline on each holding + aggregates
- [ ] BE: `POST /api/portfolio/analyze`
- [ ] FE: `PortfolioHealthPage.jsx`

**Priority:** P1  **Phase:** 4  **Effort:** 6 days

---

### US-D2: Compare 2 Stocks
**As an** investor torn between 2 stocks
**I want** to run the same analysis pipeline on both and see verdicts side-by-side
**So that** I pick the better one with apples-to-apples comparison

**Acceptance Criteria:**
- [ ] Compare page with 2 stock pickers
- [ ] Side-by-side verdict cards
- [ ] Delta highlighting (which metric is better)
- [ ] Final "Winner" summary

**Technical Tasks:**
- [ ] FE: `ComparePage.jsx` with 2-column layout
- [ ] BE: parallel agent runs for 2 tickers
- [ ] Caching: reuse recent analyses if <24h old

**Priority:** P2  **Phase:** 5  **Effort:** 3 days

---

### US-D3: Goal-Based Investing Planner
**As an** investor
**I want** to enter a financial goal ("₹50L in 7 years")
**So that** the AI recommends an asset allocation and stock mix

**Acceptance Criteria:**
- [ ] Goal input: target amount, time horizon, risk tolerance, monthly SIP capacity
- [ ] Output: allocation breakdown (equity/debt/gold), suggested large-cap/mid-cap/small-cap split
- [ ] Suggested specific stocks or funds
- [ ] Monthly SIP schedule

**Technical Tasks:**
- [ ] Agents: `goal_planner.py`
- [ ] FE: `GoalPlannerPage.jsx` (multi-step form)
- [ ] DB: `user_goals` table

**Priority:** P2  **Phase:** 5  **Effort:** 5 days

---

## EPIC E — Learning & Retention

Make the product sticky — users come back.

### US-E1: Analysis History & Accuracy Tracking
**As an** investor
**I want** to see past AI verdicts and their hit-rate
**So that** I know if I should trust this AI — and the AI learns from past mistakes

**Acceptance Criteria:**
- [ ] Profile page tab: "My Analyses" — timeline of past verdicts
- [ ] Each verdict shows: date, ticker, recommendation, current status (win/loss/open)
- [ ] Overall accuracy % over last 30/90/365 days
- [ ] Public "AI Track Record" page (anonymized)

**Technical Tasks:**
- [ ] DB: `analyses` table with full verdict JSON + outcome
- [ ] Worker: daily job to mark verdicts as win/loss based on price movement vs target
- [ ] Agents: Memory layer feeds past mistakes into new analyses (TradingAgents `memory.get_memories` pattern)
- [ ] FE: `AnalysisHistoryPage.jsx`

**Priority:** P1  **Phase:** 5  **Effort:** 4 days

---

### US-E2: Backtest Mode
**As an** investor
**I want** to see what the AI would have said 6 months ago
**So that** I can verify it's not hindsight-biased

**Acceptance Criteria:**
- [ ] Backtest page: pick ticker + date
- [ ] AI runs analysis using only data available up to that date
- [ ] Shows recommendation vs actual price performance since

**Technical Tasks:**
- [ ] Data: historical data snapshots with "as-of" dates
- [ ] Agents: accept `as_of_date` parameter, filter data accordingly
- [ ] FE: `BacktestPage.jsx`

**Priority:** P2  **Phase:** 5  **Effort:** 5 days

---

### US-E3: Event-Driven Push Alerts
**As an** investor
**I want** push notifications when something material happens to my watchlist stocks
**So that** I act before the market prices it in

**Acceptance Criteria:**
- [ ] Alert types: earnings released, insider trade, credit rating change, SEBI red flag triggered, price breakout, 52wk high/low
- [ ] User can toggle alert types in settings
- [ ] Alerts include mini AI analysis ("this is bullish because X")

**Technical Tasks:**
- [ ] Worker: event detector (poll corporate actions, SEBI filings, price thresholds)
- [ ] Notification service: web push (VAPID) + email fallback
- [ ] DB: `alerts`, `alert_subscriptions` tables
- [ ] FE: Alert settings page + in-app notification center

**Priority:** P2  **Phase:** 5  **Effort:** 6 days

---

## Phase roadmap

| Phase | Duration | User stories | Outcome |
|---|---|---|---|
| **Phase 1 — Foundation** | 2 weeks | US-A1, US-A3 (partial) | Click "Analyze" → get a one-shot verdict from 4 analysts + PM (no debate, no streaming yet). Docker-integrated. |
| **Phase 2 — Live Committee** | 2 weeks | US-A2, US-A3 (full), US-A4, US-A5 | Streaming UI + Bull/Bear debate + 3-way risk panel |
| **Phase 3 — Real Data** | 3 weeks | US-B2, US-B3, US-C1, US-C2, US-C3 | News, sentiment, BSE/NSE, SEBI flags wired in (replaces placeholders) |
| **Phase 4 — Indian Edge** | 2 weeks | US-B1, US-B4, US-C4 | Tax engine, macro agent, concall summarizer |
| **Phase 5 — Stickiness** | 3 weeks | US-D1, US-D2, US-D3, US-E1, US-E2, US-E3 | Portfolio Health Check, compare, goal planner, history, backtest, alerts |

**Total: ~12 weeks** for full vision. Phase 1 alone is shippable and demonstrates the core value.

---

## Architecture decisions

### New service: `evenstocks-agents/`
- **Language:** Python 3.11
- **Framework:** FastAPI (HTTP + WebSocket)
- **Orchestration:** LangGraph (same as TradingAgents)
- **LLM:** Anthropic Claude — Sonnet 4.6 for reasoning, Haiku 4.5 for sentiment/summary
- **Memory:** Simple JSON-on-disk initially; move to vector DB (Chroma) in Phase 5
- **Caching:** Redis for agent result caching (24h TTL)

### Data layer reuse
- **Screener data:** reuse existing MySQL tables from `evenstocks-scapping`
- **Real-time price:** new Python worker, cache in Redis
- **Scrapers:** new workers in `evenstocks-agents/data_workers/`

### Frontend
- **No new framework** — keep React + existing CSS patterns
- **New pages:** `InvestmentCommittee` view embedded in `StockDetailPage`
- **Streaming:** WebSocket hook pattern (consistent with existing chatbot)

### Docker
- Add `evenstocks-agents` service to `docker-compose.yml`
- Expose port 5810 (next free port after 5809)
- Depend on mysql + redis (new)

---

## Phase 1 — Detailed breakdown (starting now)

### Scaffolding
- [x] Create `AGENT_ROADMAP.md` (this file)
- [ ] Create `evenstocks-agents/` directory
- [ ] `requirements.txt` with fastapi, langgraph, langchain-anthropic, uvicorn, mysql-connector
- [ ] `Dockerfile`
- [ ] `main.py` — FastAPI entrypoint with `/health` + `/analyze/:ticker`
- [ ] `config.py` — settings loader
- [ ] `README.md` — service docs

### Agents (Phase 1 — stubs first, then real logic)
- [ ] `agents/base.py` — BaseAgent abstract class
- [ ] `agents/fundamentals_analyst.py` — reads Screener MySQL data
- [ ] `agents/technical_analyst.py` — reads price table (stub if no price data yet)
- [ ] `agents/news_analyst.py` — stub (real impl in Phase 3)
- [ ] `agents/sentiment_analyst.py` — stub (real impl in Phase 3)
- [ ] `agents/portfolio_manager.py` — synthesizes above into verdict
- [ ] `graph/orchestrator.py` — LangGraph pipeline

### Integration
- [ ] Update `docker-compose.yml` with agents service
- [ ] `evenstocks-backend` (Node): add `/api/analyze/:ticker` proxy route
- [ ] React: add "Analyze with AI Committee" button on `StockDetailPage`
- [ ] React: `VerdictCard.jsx` component showing final verdict
- [ ] Basic loading state (progress indicator)

### Quality gates
- [ ] Pipeline runs locally via `docker-compose up`
- [ ] Returns a verdict for at least 3 test tickers (TATAMOTORS, RELIANCE, INFY)
- [ ] Error handling: missing ticker → 404, LLM error → 503 with retry hint

---

## Out of scope (explicit)

- Automated order execution (broker integration) — not legal without SEBI RIA license
- Intraday day-trading signals — product is for medium/long-term investors
- Crypto, commodities, forex — equity only
- US stocks — India-first focus
- Options strategies builder — too complex for v1
