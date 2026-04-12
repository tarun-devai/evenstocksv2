# EvenStocks — Architecture & Project Guide

## Overview

EvenStocks is an AI-powered Indian stock market analysis platform. Users can search stocks (BSE/NSE), tag them in a chat interface, and get detailed AI-generated analysis powered by Claude (Anthropic).

The project is a **monorepo** with **5 independent services**:

```
evenstocksv2/
├── evenstocks-react/       # Frontend (React) — port 3000
├── evenstocks-backend/     # Backend proxy (Node.js/Express) — port 5000
├── evenstocks-api/         # User API (Flask/MySQL) — port 5809
├── evenstocks_chatbot/     # AI Service (FastAPI/WebSocket) — port 8000
├── evenstocks-scapping/    # Web scraping scripts (Python)
├── evenstock.md            # This file — architecture guide
└── start.md                # Quick-start instructions
```

---

## Service Details

### 1. evenstocks-react (Frontend)

**Tech:** React, React Router, Bootstrap 5, FontAwesome, Bootstrap Icons, AOS, PureCounter  
**Port:** 3000  
**Theme CSS:** `public/assets/css/main4.css` (iLanding Bootstrap template)  
**Purpose:** All UI — landing page, login/signup, admin dashboard, chatbot, checkout, privacy/terms pages.

**Key files:**
- `src/App.jsx` — Routes: `/`, `/login`, `/signup`, `/admins`, `/chatbot`, `/checkout`, `/privacy`, `/terms`, `/razorpay`
- `src/pages/HomePage.jsx` — Landing page with hero (typewriter animation), about, timeline, features chat widget, testimonials, stats, pricing, FAQ, CTA, contact form
- `src/pages/ChatBotPage.jsx` — AI chatbot UI with WebSocket streaming, `@` stock autocomplete
- `src/pages/AdminDashboard.jsx` — Admin panel with user management, stock analysis, AI chatbot nav
- `src/pages/LoginPage.jsx` / `SignupPage.jsx` — Auth forms
- `src/pages/CheckoutPage.jsx` — Checkout flow
- `src/pages/RazorpayPayment.jsx` — Razorpay payment integration
- `src/pages/PrivacyPage.jsx` / `TermsPage.jsx` — Legal pages
- `src/components/Header.jsx` — Sticky header with logo, nav (smooth scroll), login/signup buttons, user dropdown (when logged in), mobile hamburger menu
- `src/components/Footer.jsx` — 4-column footer with about, quick links, resources, contact info, social links, scroll-to-top button
- `src/components/EntryModal.jsx` — Welcome modal for new users (10 free tokens)
- `src/components/LoginPopup.jsx` — Login/signup popup for unauthenticated actions
- `src/services/api.js` — API client (`apiPost`, `apiGet`) that talks to evenstocks-backend
- `src/context/AuthContext.jsx` — Auth state (cookies: `username`, `user_token`)

**Styles:**
- `public/assets/css/main4.css` — Global theme (colors, header, nav, hero, sections, footer, responsive)
- `src/styles/Header.css` — User dropdown, logo sizing, mobile responsive
- `src/styles/HomePage.css` — Chat widget, timeline, modals, typewriter cursor, hover animations, pricing card effects, hero float animation
- `src/styles/chatbot.css` — Isolated chatbot styles (light theme: white/green, uses `all: initial` to block Bootstrap bleed)
- `src/styles/LoginPage.css` / `SignupPage.css` / `AdminDashboard.css` / `CheckoutPage.css` / `PrivacyTerms.css`

**Logo files** (`public/assets/img/`):
- `logo-horizontal.png` — Green icon + "Even Stocks" text, horizontal (trimmed, for header & footer)
- `logo-icon.png` — Green icon only (for chatbot page)
- `logo-vertical.png` — Green icon + text, stacked
- `logo-horizontal-white.png` — White version (for dark backgrounds)
- `favicon-logo.png` — Green icon (browser tab favicon)

**CSS Color System** (defined in `main4.css`):
```css
--background-color: #ffffff;
--accent-color: #02634D;       /* Brand green */
--heading-color: #2d465e;
--surface-color: #ffffff;
--contrast-color: #ffffff;
--nav-hover-color: #02634D;
```

**Env vars (`.env`):**
```
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_CHATBOT_WS_URL=ws://localhost:8000
```

**Data flow:**
- UI pages → `api.js` → evenstocks-backend (port 5000) → evenstocks-api (port 5809)
- Chatbot page → WebSocket → evenstocks_chatbot (port 8000)

---

### 2. evenstocks-backend (Backend Proxy)

**Tech:** Node.js, Express, Axios, cookie-parser  
**Port:** 5000  
**Purpose:** Proxy layer between React frontend and Flask API. Handles cookies, forwards requests.

**Key files:**
- `server.js` — Express server with CORS, cookie parsing
- `routes/post.js` — POST `/api/post` with `key` parameter routing:
  - `login` — Forward to Flask `/api/login`, set cookies
  - `signup` — Forward to Flask `/api/add_user`
  - `sendotp` / `otp_validate` / `resendotp` / `resendotps` — OTP flows
  - `pwd` — Password reset
  - `contact` — Contact form
  - `checkUserName` / `checkUserEmail` / `checkUserNumber` — Validation
  - `create_order` / `verify_payment` — Razorpay payment flow
  - `userinfo` — Get user info (reads cookies)
  - `hit_url` / `analyze` — Stock analysis via analyze service (port 5808)
  - `get_user_feedback` — User feedback
- `routes/get.js` — GET `/api/get?method=` routing:
  - `all_signedup_users` — List all users

**Env vars (`.env`):**
```
PORT=5000
EXTERNAL_API_BASE=http://localhost:5809/api
ANALYZE_API_BASE=http://localhost:5808
```

---

### 3. evenstocks-api (User API)

**Tech:** Flask, MySQL, bcrypt, Razorpay SDK  
**Port:** 5809  
**Purpose:** Core user management API. Direct MySQL access. Handles auth, OTP, payments, user data.

**Key files:**
- `app.py` — Flask app with all endpoints:
  - `/api/login` — Authenticate user (bcrypt)
  - `/api/add_user` — Register new user
  - `/api/send_otp` / `/api/verify_otp` / `/api/resend_otp` — Email OTP
  - `/api/forgot_password` — Password reset
  - `/api/get_user_info` — User profile
  - `/api/all_signedup_users` — Admin user list
  - `/api/check_any` — Check username/email/mobile uniqueness
  - `/api/save_contact_info` — Contact form submissions
  - `/api/create_order` / `/api/verify_payment` — Razorpay integration
  - `/api/set_plan` — Subscription plan management
  - `/api/get_user_feedback` — Feedback retrieval
- `schema.sql` — MySQL database schema (`evenstocks_db`)

**Env vars (`.env`):**
```
SENDER_EMAIL=...
SENDER_PASSWORD=...
DB_PASSWORD=...
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
```

---

### 4. evenstocks_chatbot (AI Service)

**Tech:** FastAPI, WebSocket, Anthropic Claude API, SQLite  
**Port:** 8000  
**Purpose:** AI chatbot backend. Handles WebSocket chat, stock autocomplete, Claude streaming responses.

**Key files:**
- `main.py` — FastAPI app entry point, mounts routers
- `app/config.py` — Config: `ANTHROPIC_API_KEY`, `MODEL` (claude-sonnet-4-20250514), `MAX_TOKENS` (2048)
- `app/session.py` — `ChatSession` class (in-memory message history per connection, cancel support)
- `app/stock_db.py` — SQLite stock database access:
  - `search_stocks()` — Fuzzy search by name (for autocomplete)
  - `get_company_info()` — Full company info row
  - `get_financial_tables()` — Quarterly, P&L, balance sheet, cash flow, ratios, shareholding
  - `get_pdf_texts()` — Annual reports, announcements, concalls
  - `build_stock_context()` — Assembles full text context for Claude from all stock data
- `app/api/chat.py` — WebSocket `/ws/chat`:
  - `message` — Chat with optional stock tags; builds context from DB, streams Claude response
  - `autocomplete` — Stock name search from SQLite
  - `stop` — Cancel generation
  - `clear` — Reset conversation
- `app/api/stock_chat.py` — WebSocket `/ws/stock-chat`:
  - `analyze` — Full stock analysis report
  - `search` — Stock search
  - `message` — Follow-up questions
- `app/api/health.py` — `GET /health`
- `data/stocks.db` — SQLite database with scraped stock data

**Env vars (`.env`):**
```
ANTHROPIC_API_KEY=sk-ant-...
HOST=0.0.0.0
PORT=8000
MODEL=claude-sonnet-4-20250514
MAX_TOKENS=2048
```

**WebSocket protocol (`/ws/chat`):**
```
Client → Server:
  { action: "message", content: "...", stocks: ["Stock_Name"] }
  { action: "autocomplete", query: "Tata" }
  { action: "stop" }
  { action: "clear" }

Server → Client:
  { type: "stream_start" }
  { type: "stream_delta", content: "chunk..." }
  { type: "stream_end", usage: { input_tokens, output_tokens } }
  { type: "autocomplete", results: [...] }
  { type: "cleared" }
  { type: "error", message: "..." }
```

---

### 5. evenstocks-scapping (Web Scraping)

**Tech:** Python, BeautifulSoup, requests, SQLite  
**Purpose:** Scrape stock data from screener.in and populate `evenstocks_chatbot/data/stocks.db`.

**Key files:**
- `get_all_stocks_list.py` — Fetch stock list from screener.in
- `scrape_tables.py` — Scrape company info + financial tables into SQLite
- `scrape_stock_fundamental.py` — Scrape full stock data + PDF documents
- `scrape_pdfs.py` — PDF text extraction

---

## Request Flow

### User Auth (Login/Signup/OTP)
```
React (3000) → api.js → Node.js backend (5000) → Flask API (5809) → MySQL
```

### AI Chatbot
```
React (3000) → WebSocket → FastAPI (8000) → Claude API (Anthropic)
                                           → SQLite (stock data)
```

### Stock Analysis (via Admin Dashboard)
```
React (3000) → api.js → Node.js backend (5000) → Analyze service (5808)
```

### Razorpay Payments
```
React (3000) → api.js → Node.js backend (5000) → Flask API (5809) → Razorpay API
```

---

## How to Run (Development)

Open 4 terminals from the `evenstocksv2/` directory:

### Terminal 1 — Flask User API (port 5809)
```bash
cd evenstocks-api
pip install -r requirements.txt
python app.py
```
Requires: MySQL running with `evenstocks_db` (run `mysql -u root -p < schema.sql`)

### Terminal 2 — AI Chatbot Service (port 8000)
```bash
cd evenstocks_chatbot
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Requires: `ANTHROPIC_API_KEY` in `.env`, `data/stocks.db` populated via scraping scripts

### Terminal 3 — Node.js Backend Proxy (port 5000)
```bash
cd evenstocks-backend
npm install
node server.js
```

### Terminal 4 — React Frontend (port 3000)
```bash
cd evenstocks-react
npm install
npm start
```

Then open http://localhost:3000 in your browser.

---

## Database

### MySQL (`evenstocks_db`) — used by evenstocks-api
- `users` — Accounts, auth, subscriptions
- `user_feedback` — Feedback entries
- `contact_info` — Contact form data
- `user_billing_history` — Payment records
- `user_queries` — Query logs

### SQLite (`data/stocks.db`) — used by evenstocks_chatbot
- `company_info` — Stock metrics (market cap, PE, ROCE, ROE, etc.)
- `financial_tables` — Quarterly results, P&L, balance sheet, cash flow, ratios, shareholding (JSON)
- `pdf_texts` — Extracted text from annual reports, announcements, concalls

Populated by running scraping scripts in `evenstocks-scapping/`.

---

## Key Technical Notes

- **Monorepo Structure:** All services live under `evenstocksv2/`. The `.git` repo is at the `evenstocksv2/` level.
- **CSS Theme:** The homepage uses the iLanding Bootstrap template (`main4.css`) with brand color `#02634D`. The chatbot page uses isolated CSS (`all: initial`) with a matching light theme (white/green).
- **Logo Images:** All logo PNGs have been trimmed of whitespace for proper display. The header uses `logo-horizontal.png` (green icon + text on transparent bg, visible on white header bar).
- **Header:** White pill-shaped bar (`border-radius: 50px`) with sticky positioning. Adds `scrolled` class on scroll. Smooth-scroll navigation for anchor links. Mobile hamburger menu for small screens.
- **Footer:** 4-column layout — company info with social links, quick links, resources, contact info. Scroll-to-top button appears after scrolling 300px.
- **Homepage Interactivity:** Typewriter animation on hero headline (cycles: "Smarter Decisions", "Better Returns", "Real-Time Insights", "Confident Investing"), AOS scroll animations, hover effects on pricing/features/testimonials/stats, floating hero image, pulsing CTA button, interactive timeline with intersection observer.
- **Auth:** Cookie-based (`username`, `user_token`). ProtectedRoute in React redirects to `/login`. The `/chatbot` route is NOT protected (accessible without login).
- **WebSocket Streaming:** Claude responses stream token-by-token via `stream_start` → `stream_delta` → `stream_end`.
- **Stock Autocomplete:** Type `@` in chatbot input to trigger autocomplete. Searches SQLite via WebSocket `autocomplete` action.
- **Markdown Rendering:** Custom `renderMarkdown()` function converts AI responses to HTML (headings, bold, italic, lists, code blocks).
- **Pricing Plans:** Free (10 tokens, ₹0), Pluse Pack (15 tokens, ₹249), Edge Pack (30 tokens, ₹549, most popular), Prime Pack (60 tokens, ₹1149). Payments via Razorpay.
