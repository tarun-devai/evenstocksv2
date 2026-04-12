# Graph Report - .  (2026-04-12)

## Corpus Check
- 128 files · ~298,199 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2424 nodes · 4967 edges · 72 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Bootstrap Vendor JS|Bootstrap Vendor JS]]
- [[_COMMUNITY_Bootstrap UI Components|Bootstrap UI Components]]
- [[_COMMUNITY_Bootstrap Components Alt|Bootstrap Components Alt]]
- [[_COMMUNITY_Bootstrap Components Alt 2|Bootstrap Components Alt 2]]
- [[_COMMUNITY_Bootstrap Swiper Minified|Bootstrap Swiper Minified]]
- [[_COMMUNITY_Bootstrap Alert System|Bootstrap Alert System]]
- [[_COMMUNITY_Bootstrap Utilities|Bootstrap Utilities]]
- [[_COMMUNITY_Bootstrap Modal Overlay|Bootstrap Modal Overlay]]
- [[_COMMUNITY_Swiper Slider Library|Swiper Slider Library]]
- [[_COMMUNITY_GLightbox Gallery|GLightbox Gallery]]
- [[_COMMUNITY_Flask Auth Payment API|Flask Auth Payment API]]
- [[_COMMUNITY_GLightbox Minified|GLightbox Minified]]
- [[_COMMUNITY_Stock Fundamental Scraper|Stock Fundamental Scraper]]
- [[_COMMUNITY_Bootstrap Tabs Variant|Bootstrap Tabs Variant]]
- [[_COMMUNITY_Bootstrap Tabs|Bootstrap Tabs]]
- [[_COMMUNITY_Bootstrap Tabs Alt|Bootstrap Tabs Alt]]
- [[_COMMUNITY_Platform Dependencies|Platform Dependencies]]
- [[_COMMUNITY_PureCounter Animation|PureCounter Animation]]
- [[_COMMUNITY_React API Client|React API Client]]
- [[_COMMUNITY_Stock List Scraper|Stock List Scraper]]
- [[_COMMUNITY_Vendor JS Utilities|Vendor JS Utilities]]
- [[_COMMUNITY_PDF Scraper|PDF Scraper]]
- [[_COMMUNITY_Table Scraper|Table Scraper]]
- [[_COMMUNITY_Chat WebSocket Endpoint|Chat WebSocket Endpoint]]
- [[_COMMUNITY_AOS Animation Library|AOS Animation Library]]
- [[_COMMUNITY_Stock DB Reader|Stock DB Reader]]
- [[_COMMUNITY_Stock DB Context Builder|Stock DB Context Builder]]
- [[_COMMUNITY_AOS Animation Alt|AOS Animation Alt]]
- [[_COMMUNITY_Main App Initializer|Main App Initializer]]
- [[_COMMUNITY_React App Router|React App Router]]
- [[_COMMUNITY_Express Response Utils|Express Response Utils]]
- [[_COMMUNITY_Chatbot UI Component|Chatbot UI Component]]
- [[_COMMUNITY_Express POST Routes|Express POST Routes]]
- [[_COMMUNITY_Email Form Validator|Email Form Validator]]
- [[_COMMUNITY_Auth Context Provider|Auth Context Provider]]
- [[_COMMUNITY_Entry Modal|Entry Modal]]
- [[_COMMUNITY_Footer Component|Footer Component]]
- [[_COMMUNITY_Header Component|Header Component]]
- [[_COMMUNITY_Login Popup|Login Popup]]
- [[_COMMUNITY_Admin Dashboard|Admin Dashboard]]
- [[_COMMUNITY_Checkout Page|Checkout Page]]
- [[_COMMUNITY_Home Page|Home Page]]
- [[_COMMUNITY_Login Page|Login Page]]
- [[_COMMUNITY_Privacy Page|Privacy Page]]
- [[_COMMUNITY_Razorpay Payment Component|Razorpay Payment Component]]
- [[_COMMUNITY_Signup Page|Signup Page]]
- [[_COMMUNITY_Terms Page|Terms Page]]
- [[_COMMUNITY_FastAPI Main Application|FastAPI Main Application]]
- [[_COMMUNITY_Health Check Endpoint|Health Check Endpoint]]
- [[_COMMUNITY_Auth UI Assets|Auth UI Assets]]
- [[_COMMUNITY_Trading Chart Assets|Trading Chart Assets]]
- [[_COMMUNITY_Features Illustration Set|Features Illustration Set]]
- [[_COMMUNITY_Express Server Entry|Express Server Entry]]
- [[_COMMUNITY_Express GET Routes|Express GET Routes]]
- [[_COMMUNITY_Chatbot Config|Chatbot Config]]
- [[_COMMUNITY_API Init Module|API Init Module]]
- [[_COMMUNITY_Chatbot Init Module|Chatbot Init Module]]
- [[_COMMUNITY_iLanding Template|iLanding Template]]
- [[_COMMUNITY_ChatBot Page Doc|ChatBot Page Doc]]
- [[_COMMUNITY_API Client Doc|API Client Doc]]
- [[_COMMUNITY_Auth Context Doc|Auth Context Doc]]
- [[_COMMUNITY_Stock DB Doc|Stock DB Doc]]
- [[_COMMUNITY_Chat Session Doc|Chat Session Doc]]
- [[_COMMUNITY_MySQL Connector Dep|MySQL Connector Dep]]
- [[_COMMUNITY_Bcrypt Dep|Bcrypt Dep]]
- [[_COMMUNITY_Websockets Dep|Websockets Dep]]
- [[_COMMUNITY_HDFC Bank Stock|HDFC Bank Stock]]
- [[_COMMUNITY_ICICI Bank Stock|ICICI Bank Stock]]
- [[_COMMUNITY_Reliance Stock|Reliance Stock]]
- [[_COMMUNITY_TCS Stock|TCS Stock]]
- [[_COMMUNITY_User Referral Asset|User Referral Asset]]
- [[_COMMUNITY_Testimonials Asset|Testimonials Asset]]

## God Nodes (most connected - your core abstractions)
1. `Tooltip` - 38 edges
2. `cs` - 38 edges
3. `Tooltip` - 38 edges
4. `Tooltip` - 38 edges
5. `Tooltip` - 38 edges
6. `Ni` - 38 edges
7. `On` - 33 edges
8. `Carousel` - 28 edges
9. `xt` - 28 edges
10. `Carousel` - 28 edges

## Surprising Connections (you probably didn't know these)
- `chat.py — WebSocket endpoint with stock autocomplete + DB-powered analysis` --uses--> `ChatSession`  [INFERRED]
  evenstocks_chatbot\app\api\chat.py → evenstocks_chatbot\app\session.py
- `stock_chat.py — WebSocket endpoint for stock analysis chatbot` --uses--> `ChatSession`  [INFERRED]
  evenstocks_chatbot\app\api\stock_chat.py → evenstocks_chatbot\app\session.py
- `evenstocks-api Flask MySQL API` --implements--> `Flask dependency`  [EXTRACTED]
  README.md → evenstocks-api/requirements.txt
- `evenstocks_chatbot FastAPI AI Service` --implements--> `FastAPI dependency`  [EXTRACTED]
  README.md → evenstocks_chatbot/requirements.txt
- `evenstocks_chatbot FastAPI AI Service` --implements--> `anthropic SDK dependency`  [EXTRACTED]
  README.md → evenstocks_chatbot/requirements.txt

## Hyperedges (group relationships)
- **User Auth Flow React-Node-Flask-MySQL** — readme_evenstocks_react, readme_evenstocks_backend, readme_evenstocks_api, readme_mysql_db [EXTRACTED 1.00]
- **AI Chatbot Flow React-WebSocket-FastAPI-Claude** — readme_evenstocks_react, readme_evenstocks_chatbot, readme_anthropic_claude_api, readme_sqlite_db [EXTRACTED 1.00]
- **Razorpay Payment Flow** — readme_evenstocks_react, readme_evenstocks_backend, readme_evenstocks_api, readme_razorpay [EXTRACTED 1.00]
- **Stock Data Scraping Pipeline** — readme_screener_in, readme_evenstocks_scraping, readme_sqlite_db [EXTRACTED 1.00]
- **Featured Indian Stock Companies** — brand_hdfc_bank, brand_icici_bank, brand_reliance, brand_tcs [INFERRED 0.85]

## Communities

### Community 0 - "Bootstrap Vendor JS"
Cohesion: 0.01
Nodes (65): _(), a(), Ae(), ao, b(), be(), Bt, c() (+57 more)

### Community 1 - "Bootstrap UI Components"
Cohesion: 0.01
Nodes (50): addHandler(), Alert, allowedAttribute(), Backdrop, BaseComponent, bootstrapDelegationHandler(), bootstrapHandler(), Button (+42 more)

### Community 2 - "Bootstrap Components Alt"
Cohesion: 0.01
Nodes (50): addHandler(), Alert, allowedAttribute(), Backdrop, BaseComponent, bootstrapDelegationHandler(), bootstrapHandler(), Button (+42 more)

### Community 3 - "Bootstrap Components Alt 2"
Cohesion: 0.01
Nodes (49): addHandler(), Alert, allowedAttribute(), Backdrop, BaseComponent, bootstrapDelegationHandler(), bootstrapHandler(), Button (+41 more)

### Community 4 - "Bootstrap Swiper Minified"
Cohesion: 0.01
Nodes (37): a(), Ai, at, b(), bi(), c(), d(), e() (+29 more)

### Community 5 - "Bootstrap Alert System"
Cohesion: 0.02
Nodes (25): Alert, BaseComponent, Button, Carousel, Collapse, contains(), Dropdown, effect$1() (+17 more)

### Community 6 - "Bootstrap Utilities"
Cohesion: 0.06
Nodes (83): addHandler(), allowedAttribute(), applyStyles(), areValidElements(), arrow(), bootstrapDelegationHandler(), bootstrapHandler(), computeAutoPlacement() (+75 more)

### Community 7 - "Bootstrap Modal Overlay"
Cohesion: 0.04
Nodes (12): Backdrop, Config, execute(), executeAfterTransition(), getElement(), getTransitionDurationFromElement(), isElement$1(), parseSelector() (+4 more)

### Community 8 - "Swiper Slider Library"
Cohesion: 0.07
Nodes (38): _(), a(), b(), c(), ce(), d(), de(), emit() (+30 more)

### Community 9 - "GLightbox Gallery"
Cohesion: 0.08
Nodes (56): addClass(), addEvent(), animateElement(), _classCallCheck(), closest(), _createClass(), createHTML(), createIframe() (+48 more)

### Community 10 - "Flask Auth Payment API"
Cohesion: 0.12
Nodes (36): add_user(), all_signedup_users(), api_create_order(), api_verify_payment(), check_any(), cleanup_unverified(), create_razorpay_order(), deduct_request() (+28 more)

### Community 11 - "GLightbox Minified"
Cohesion: 0.28
Nodes (25): _(), a(), b(), c(), d(), e(), f(), g() (+17 more)

### Community 12 - "Stock Fundamental Scraper"
Cohesion: 0.12
Nodes (23): add_pdf_texts(), clean_name(), create_session(), download_documents(), download_file(), extract_company_info(), extract_pdf_text(), extract_tables() (+15 more)

### Community 13 - "Bootstrap Tabs Variant"
Cohesion: 0.24
Nodes (1): Ks

### Community 14 - "Bootstrap Tabs"
Cohesion: 0.24
Nodes (1): Tab

### Community 15 - "Bootstrap Tabs Alt"
Cohesion: 0.24
Nodes (1): ms

### Community 16 - "Platform Dependencies"
Cohesion: 0.15
Nodes (17): Flask dependency, anthropic SDK dependency, FastAPI dependency, Anthropic Claude API, app/api/chat.py WebSocket handler, evenstocks-api Flask MySQL API, evenstocks-backend Node.js Proxy, evenstocks_chatbot FastAPI AI Service (+9 more)

### Community 17 - "PureCounter Animation"
Cohesion: 0.3
Nodes (14): a(), c(), d(), f(), i(), l(), n(), o() (+6 more)

### Community 18 - "React API Client"
Cohesion: 0.25
Nodes (14): apiGet(), apiPost(), checkUserEmail(), checkUserName(), checkUserNumber(), createOrder(), getAllSignedUpUsers(), loginUser() (+6 more)

### Community 19 - "Stock List Scraper"
Cohesion: 0.23
Nodes (11): already_logged_in(), ensure_logged_in(), fetch_page(), fill_login_form(), parse_stocks(), screener_scraper.py ───────────────────────────────────────────────────────────, Navigate to login URL.     - If already redirected to feed/home → already logge, True if the current page shows a logged-in session (no login form present). (+3 more)

### Community 20 - "Vendor JS Utilities"
Cohesion: 0.36
Nodes (9): b(), D(), e(), g(), H(), m(), p(), v() (+1 more)

### Community 21 - "PDF Scraper"
Cohesion: 0.29
Nodes (11): clean_name(), create_session(), download_file(), extract_pdf_text(), find_document_links(), init_db(), main(), pdfs_exist() (+3 more)

### Community 22 - "Table Scraper"
Cohesion: 0.3
Nodes (11): clean_name(), create_session(), extract_company_info(), extract_tables(), init_db(), main(), _parse_html_table(), process_company() (+3 more)

### Community 23 - "Chat WebSocket Endpoint"
Cohesion: 0.18
Nodes (3): chat.py — WebSocket endpoint with stock autocomplete + DB-powered analysis, ChatSession, stock_chat.py — WebSocket endpoint for stock analysis chatbot

### Community 24 - "AOS Animation Library"
Cohesion: 0.27
Nodes (5): check(), containsAOSNode(), getMutationObserver(), isSupported(), ready()

### Community 25 - "Stock DB Reader"
Cohesion: 0.47
Nodes (9): get_conn(), list_stocks(), main(), read_stocks_db.py ─────────────────────────────────────────────────────────────, run_sql(), show_pdfs(), show_stock(), show_table() (+1 more)

### Community 26 - "Stock DB Context Builder"
Cohesion: 0.27
Nodes (8): build_stock_context(), get_company_info(), get_financial_tables(), get_pdf_texts(), stock_db.py — Search and fetch stock data from stocks.db, Fuzzy search stocks by name. Returns list of {stock_name, url, market_cap}., Build a full text context block for Claude from all stock data., search_stocks()

### Community 27 - "AOS Animation Alt"
Cohesion: 0.31
Nodes (5): check(), containsAOSNode(), getMutationObserver(), isSupported(), ready()

### Community 28 - "Main App Initializer"
Cohesion: 0.29
Nodes (0): 

### Community 29 - "React App Router"
Cohesion: 0.4
Nodes (0): 

### Community 30 - "Express Response Utils"
Cohesion: 0.83
Nodes (3): jsonResponse(), sendError(), sendSuccess()

### Community 31 - "Chatbot UI Component"
Cohesion: 0.67
Nodes (2): esc(), renderMarkdown()

### Community 32 - "Express POST Routes"
Cohesion: 0.67
Nodes (0): 

### Community 33 - "Email Form Validator"
Cohesion: 0.67
Nodes (0): 

### Community 34 - "Auth Context Provider"
Cohesion: 0.67
Nodes (0): 

### Community 35 - "Entry Modal"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Footer Component"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Header Component"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Login Popup"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Admin Dashboard"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Checkout Page"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Home Page"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Login Page"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Privacy Page"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Razorpay Payment Component"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Signup Page"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Terms Page"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "FastAPI Main Application"
Cohesion: 1.0
Nodes (1): EvenStocks AI — FastAPI + WebSocket + Anthropic Streaming =====================

### Community 48 - "Health Check Endpoint"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Auth UI Assets"
Cohesion: 1.0
Nodes (2): Mobile Login UI Illustration, Signup Onboarding Illustration

### Community 50 - "Trading Chart Assets"
Cohesion: 1.0
Nodes (2): Stock Chart Trading Analysis Photo, Investment Returns Comparison Chart

### Community 51 - "Features Illustration Set"
Cohesion: 1.0
Nodes (2): Features Illustration Analytics Dashboard, Features Illustration Customer Support

### Community 52 - "Express Server Entry"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Express GET Routes"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Chatbot Config"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "API Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Chatbot Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "iLanding Template"
Cohesion: 1.0
Nodes (1): iLanding Bootstrap Template

### Community 58 - "ChatBot Page Doc"
Cohesion: 1.0
Nodes (1): ChatBotPage.jsx AI Chatbot UI

### Community 59 - "API Client Doc"
Cohesion: 1.0
Nodes (1): api.js React API Client

### Community 60 - "Auth Context Doc"
Cohesion: 1.0
Nodes (1): AuthContext.jsx Cookie-based Auth

### Community 61 - "Stock DB Doc"
Cohesion: 1.0
Nodes (1): app/stock_db.py SQLite Helpers

### Community 62 - "Chat Session Doc"
Cohesion: 1.0
Nodes (1): ChatSession In-memory Message History

### Community 63 - "MySQL Connector Dep"
Cohesion: 1.0
Nodes (1): mysql-connector-python dependency

### Community 64 - "Bcrypt Dep"
Cohesion: 1.0
Nodes (1): bcrypt dependency

### Community 65 - "Websockets Dep"
Cohesion: 1.0
Nodes (1): websockets dependency

### Community 66 - "HDFC Bank Stock"
Cohesion: 1.0
Nodes (1): HDFC Bank Featured Stock

### Community 67 - "ICICI Bank Stock"
Cohesion: 1.0
Nodes (1): ICICI Bank Featured Stock

### Community 68 - "Reliance Stock"
Cohesion: 1.0
Nodes (1): Reliance Industries Featured Stock

### Community 69 - "TCS Stock"
Cohesion: 1.0
Nodes (1): Tata Consultancy Services Featured Stock

### Community 70 - "User Referral Asset"
Cohesion: 1.0
Nodes (1): Features Illustration User Referral

### Community 71 - "Testimonials Asset"
Cohesion: 1.0
Nodes (1): Testimonials Section UI Component

## Knowledge Gaps
- **54 isolated node(s):** `EvenStocks User API — Flask + MySQL Run: python app.py (serves on port 5809) S`, `Generate a random numeric OTP of given length.`, `Stores contact info (Name, email, Subject, Message) openly (no user check).`, `Returns all verified and non-deleted users for Excel export.`, `screener_scraper.py ───────────────────────────────────────────────────────────` (+49 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Entry Modal`** (2 nodes): `EntryModal()`, `EntryModal.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Footer Component`** (2 nodes): `Footer.jsx`, `Footer()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Header Component`** (2 nodes): `Header.jsx`, `Header()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Login Popup`** (2 nodes): `LoginPopup.jsx`, `LoginPopup()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Admin Dashboard`** (2 nodes): `AdminDashboard()`, `AdminDashboard.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Checkout Page`** (2 nodes): `CheckoutPage()`, `CheckoutPage.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Home Page`** (2 nodes): `HomePage.jsx`, `HomePage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Login Page`** (2 nodes): `LoginPage.jsx`, `LoginPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Privacy Page`** (2 nodes): `PrivacyPage.jsx`, `PrivacyPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Razorpay Payment Component`** (2 nodes): `RazorpayPayment.jsx`, `RazorpayPayment()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Signup Page`** (2 nodes): `SignupPage.jsx`, `SignupPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Terms Page`** (2 nodes): `TermsPage.jsx`, `TermsPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `FastAPI Main Application`** (2 nodes): `main.py`, `EvenStocks AI — FastAPI + WebSocket + Anthropic Streaming =====================`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Health Check Endpoint`** (2 nodes): `health.py`, `health()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Auth UI Assets`** (2 nodes): `Mobile Login UI Illustration`, `Signup Onboarding Illustration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Trading Chart Assets`** (2 nodes): `Stock Chart Trading Analysis Photo`, `Investment Returns Comparison Chart`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Features Illustration Set`** (2 nodes): `Features Illustration Analytics Dashboard`, `Features Illustration Customer Support`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Express Server Entry`** (1 nodes): `server.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Express GET Routes`** (1 nodes): `get.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Chatbot Config`** (1 nodes): `config.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Chatbot Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `iLanding Template`** (1 nodes): `iLanding Bootstrap Template`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `ChatBot Page Doc`** (1 nodes): `ChatBotPage.jsx AI Chatbot UI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API Client Doc`** (1 nodes): `api.js React API Client`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Auth Context Doc`** (1 nodes): `AuthContext.jsx Cookie-based Auth`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Stock DB Doc`** (1 nodes): `app/stock_db.py SQLite Helpers`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Chat Session Doc`** (1 nodes): `ChatSession In-memory Message History`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `MySQL Connector Dep`** (1 nodes): `mysql-connector-python dependency`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Bcrypt Dep`** (1 nodes): `bcrypt dependency`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Websockets Dep`** (1 nodes): `websockets dependency`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `HDFC Bank Stock`** (1 nodes): `HDFC Bank Featured Stock`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `ICICI Bank Stock`** (1 nodes): `ICICI Bank Featured Stock`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Reliance Stock`** (1 nodes): `Reliance Industries Featured Stock`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `TCS Stock`** (1 nodes): `Tata Consultancy Services Featured Stock`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `User Referral Asset`** (1 nodes): `Features Illustration User Referral`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Testimonials Asset`** (1 nodes): `Testimonials Section UI Component`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Tooltip` connect `Bootstrap Alert System` to `Bootstrap Utilities`, `Bootstrap Modal Overlay`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **What connects `EvenStocks User API — Flask + MySQL Run: python app.py (serves on port 5809) S`, `Generate a random numeric OTP of given length.`, `Stores contact info (Name, email, Subject, Message) openly (no user check).` to the rest of the system?**
  _54 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Bootstrap Vendor JS` be split into smaller, more focused modules?**
  _Cohesion score 0.01 - nodes in this community are weakly interconnected._
- **Should `Bootstrap UI Components` be split into smaller, more focused modules?**
  _Cohesion score 0.01 - nodes in this community are weakly interconnected._
- **Should `Bootstrap Components Alt` be split into smaller, more focused modules?**
  _Cohesion score 0.01 - nodes in this community are weakly interconnected._
- **Should `Bootstrap Components Alt 2` be split into smaller, more focused modules?**
  _Cohesion score 0.01 - nodes in this community are weakly interconnected._
- **Should `Bootstrap Swiper Minified` be split into smaller, more focused modules?**
  _Cohesion score 0.01 - nodes in this community are weakly interconnected._