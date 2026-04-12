Terminal 1 — Flask User API (port 5809)

cd evenstocks-api
pip install -r requirements.txt
python app.py
Requires MySQL running with database set up:


mysql -u root -p < schema.sql
Terminal 2 — AI Chatbot Service (port 8000)

cd evenstocksv2
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
Requires ANTHROPIC_API_KEY in evenstocksv2/.env

Terminal 3 — Node.js Backend Proxy (port 5000)

cd evenstocks-backend
npm install
node server.js
Terminal 4 — React Frontend (port 3000)

cd evenstocks-react
npm install
npm start
Then open http://localhost:3000 in your browser.

