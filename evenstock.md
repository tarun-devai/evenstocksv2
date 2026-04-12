# EvenStocks — Architecture & Project Guide

## Overview

EvenStocks is an AI-powered Indian stock market analysis platform. Users can search stocks (BSE/NSE), tag them in a chat interface, and get detailed AI-generated analysis powered by Claude (Anthropic).

The project is split into **4 independent services**:

```
public_html/
├── evenstocks-react/     # Frontend (React) — port 3000
├── evenstocks-backend/   # Backend proxy (Node.js/Express) — port 5000
├── evenstocks-api/       # User API (Flask/MySQL) — port 5809
└── evenstocksv2/         # AI Service (FastAPI/WebSocket) — port 8000
```

---

## Service Details

### 1. evenstocks-react (Frontend)

**Tech:** React, React Router, Bootstrap, FontAwesome, AOS  
**Port:** 3000  
**Purpose:** All UI — landing page, login/signup, admin dashboard, chatbot, checkout, privacy/terms pages.

**Key files:**
- `src/App.jsx` — Routes: `/`, `/login`, `/signup`, `/admins`, `/chatbot`, `/checkout`, `/privacy`, `/terms`, `/razorpay`
- `src/pages/ChatBotPage.jsx` — AI chatbot UI with WebSocket streaming, `@` stock autocomplete
- `src/pages/HomePage.jsx` — Landing page
- `src/pages/AdminDashboard.jsx` — Admin panel with user management, stock analysis, AI chatbot nav
- `src/pages/LoginPage.jsx` / `SignupPage.jsx` — Auth forms
- `src/services/api.js` — API client (`apiPost`, `apiGet`) that talks to evenstocks-backend
- `src/context/AuthContext.jsx` — Auth state (cookies: `username`, `user_token`)
- `src/styles/chatbot.css` — Isolated chatbot styles (uses `all: initial` to block Bootstrap bleed)

**Env vars (`.env`):**
```
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_CHATBOT_WS_URL=ws://localhost:8000
```

**Data flow:**
- UI pages → `api.js` → evenstocks-backend (port 5000) → evenstocks-api (port 5809)
- Chatbot page → WebSocket → evenstocksv2 (port 8000)

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
- `schema.sql` — MySQL database schema (`evenstocks_db`):
  - `users` — User accounts, auth tokens, subscription plans
  - `user_feedback` — User feedback entries
  - `contact_info` — Contact form submissions
  - `user_billing_history` — Payment history
  - `user_queries` — Query/response logs

**Env vars (`.env`):**
```
SENDER_EMAIL=...
SENDER_PASSWORD=...
DB_PASSWORD=...
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
```

---

### 4. evenstocksv2 (AI Service)

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
- `data/stocks.db` — SQLite database with scraped stock data (company_info, financial_tables, pdf_texts)
- `scapping/` — Web scraping scripts:
  - `get_all_stocks_list.py` — Fetch stock list from screener.in
  - `scrape_tables.py` — Scrape company info + financial tables into SQLite
  - `scrape_stock_fundamental.py` — Scrape full stock data + PDF documents
  - `scrape_pdfs.py` — PDF text extraction

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

### 1. Start evenstocks-api (Flask — port 5809)
```bash
cd evenstocks-api
pip install -r requirements.txt
python app.py
```
Requires: MySQL running with `evenstocks_db` (see `schema.sql`)

### 2. Start evenstocksv2 (AI — port 8000)
```bash
cd evenstocksv2
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Requires: `ANTHROPIC_API_KEY` in `.env`, `data/stocks.db` populated via scraping scripts

### 3. Start evenstocks-backend (Node.js — port 5000)
```bash
cd evenstocks-backend
npm install
node server.js
```

### 4. Start evenstocks-react (React — port 3000)
```bash
cd evenstocks-react
npm install
npm start
```

---

## Database

### MySQL (`evenstocks_db`) — used by evenstocks-api
- `users` — Accounts, auth, subscriptions
- `user_feedback` — Feedback entries
- `contact_info` — Contact form data
- `user_billing_history` — Payment records
- `user_queries` — Query logs

### SQLite (`data/stocks.db`) — used by evenstocksv2
- `company_info` — Stock metrics (market cap, PE, ROCE, ROE, etc.)
- `financial_tables` — Quarterly results, P&L, balance sheet, cash flow, ratios, shareholding (JSON)
- `pdf_texts` — Extracted text from annual reports, announcements, concalls

Populated by running scraping scripts in `evenstocksv2/scapping/`.

---

## Key Technical Notes

- **CSS Isolation:** The chatbot page (`/chatbot`) uses `all: initial` and `position: fixed` in its CSS to fully isolate from Bootstrap/global styles imported in `index.js`.
- **Auth:** Cookie-based (`username`, `user_token`). ProtectedRoute in React redirects to `/login`. The `/chatbot` route is NOT protected (accessible without login).
- **WebSocket Streaming:** Claude responses stream token-by-token via `stream_start` → `stream_delta` → `stream_end`.
- **Stock Autocomplete:** Type `@` in chatbot input to trigger autocomplete. Searches SQLite via WebSocket `autocomplete` action.
- **Markdown Rendering:** Custom `renderMarkdown()` function converts AI responses to HTML (headings, bold, italic, lists, code blocks).
