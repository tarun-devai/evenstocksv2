import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/FloatingChat.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5809';
const WS_URL = process.env.REACT_APP_CHATBOT_WS_URL || 'ws://localhost:8001';

/* ── helpers ── */
function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function renderMarkdown(text) {
  let h = esc(text);
  h = h.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  h = h.replace(/`([^`]+)`/g, '<code>$1</code>');
  h = h.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  h = h.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  h = h.replace(/\*(.+?)\*/g, '<em>$1</em>');
  h = h.replace(/^- (.+)$/gm, '<li>$1</li>');
  h = h.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
  h = h.replace(/\n\n/g, '<br>');
  h = h.replace(/\n/g, '<br>');
  h = h.replace(/<br><\/ul>/g, '</ul>');
  h = h.replace(/<ul><br>/g, '<ul>');
  return h;
}

/* ── Stock fun facts & tips rotated for engagement ── */
const STOCK_FACTS = [
  "The BSE Sensex was launched in 1986 with a base value of 100. Today it trades above 70,000!",
  "India's stock market is the 4th largest in the world by market capitalization.",
  "Warren Buffett's first stock purchase was at age 11 — he bought 3 shares of Cities Service Preferred at $38 each.",
  "The term 'bull market' comes from the way a bull attacks — thrusting its horns upward.",
  "Nifty 50 has given an average annual return of ~12% over the last 20 years.",
  "SIP (Systematic Investment Plan) in India started gaining popularity only after 2010.",
  "The longest bull run in Indian markets lasted from 2003 to 2008 — Sensex went from 3,000 to 21,000!",
  "Over 13 crore demat accounts are active in India — that's roughly 10% of the population investing.",
];

const STOCK_TIPS = [
  "Start with index funds if you're new — they track Nifty/Sensex and diversify risk automatically.",
  "Never invest money you'll need in the next 2-3 years. Stock markets reward patience.",
  "A company's P/E ratio tells you how much investors are willing to pay per rupee of earnings.",
  "Diversification is key — don't put more than 10-15% of your portfolio in a single stock.",
  "SIPs beat lump-sum investing 70% of the time due to rupee cost averaging.",
  "Always check a company's debt-to-equity ratio before investing. Below 1 is generally healthy.",
];

/* ── CRM conversation stages ── */
const STAGE = {
  WELCOME: 'welcome',
  ASK_NAME: 'ask_name',
  ASK_INTEREST: 'ask_interest',
  ASK_EXPERIENCE: 'ask_experience',
  ASK_EMAIL: 'ask_email',
  FREE_CHAT: 'free_chat',
};

/* ── Lead data key ── */
const LEAD_KEY = 'fc_lead_data';

function getStoredLead() {
  try {
    return JSON.parse(localStorage.getItem(LEAD_KEY)) || {};
  } catch { return {}; }
}

function storeLead(data) {
  const existing = getStoredLead();
  const merged = { ...existing, ...data, updatedAt: new Date().toISOString() };
  localStorage.setItem(LEAD_KEY, JSON.stringify(merged));
  return merged;
}

/* ── Push lead to backend (fire-and-forget) ── */
function pushLeadToBackend(lead) {
  if (!lead.name && !lead.email) return;
  const interests = [lead.interest, lead.experience].filter(Boolean).join(', ');
  fetch(`${API_URL}/api/save_contact_info`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: lead.name || 'Chatbot Visitor',
      email: lead.email || '',
      subject: 'Chatbot Lead',
      message: `Interest: ${interests || 'N/A'} | Source: FloatingChat`,
    }),
  }).catch(() => {});
}

const FloatingChat = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [connected, setConnected] = useState(false);
  const [unread, setUnread] = useState(0);
  const [stage, setStage] = useState(STAGE.WELCOME);
  const [lead, setLead] = useState(getStoredLead);
  const [typing, setTyping] = useState(false);
  const [quickActions, setQuickActions] = useState([]);
  const [factIndex, setFactIndex] = useState(() => Math.floor(Math.random() * STOCK_FACTS.length));

  const wsRef = useRef(null);
  const msgEndRef = useRef(null);
  const inputRef = useRef(null);
  const streamBufRef = useRef('');
  const initRef = useRef(false);

  const scrollToBottom = useCallback(() => {
    msgEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => inputRef.current.focus(), 250);
    }
  }, [open]);

  /* ── Add a bot message with a typing delay for realism ── */
  const botSay = useCallback((content, actions = [], delay = 600) => {
    setTyping(true);
    setTimeout(() => {
      setMessages((prev) => [...prev, { role: 'assistant', content }]);
      setQuickActions(actions);
      setTyping(false);
      if (!open) setUnread((u) => u + 1);
    }, delay);
  }, [open]);

  /* ── Initialize conversation on first open ── */
  useEffect(() => {
    if (!open || initRef.current) return;
    initRef.current = true;

    const stored = getStoredLead();
    if (stored.name) {
      // Returning visitor
      setStage(stored.email ? STAGE.FREE_CHAT : STAGE.ASK_EMAIL);
      botSay(
        `Welcome back, **${stored.name}**! Great to see you again. Here's a stock fact for you:\n\n*"${STOCK_FACTS[factIndex]}"*\n\nWhat can I help you with today?`,
        stored.email
          ? [
              { label: 'Stock tip of the day', value: '__tip' },
              { label: 'Analyze a stock', value: '__analyze' },
              { label: 'Market overview', value: '__market' },
              { label: 'How EvenStocks works', value: '__how' },
            ]
          : [
              { label: 'Stock tip of the day', value: '__tip' },
              { label: 'How EvenStocks works', value: '__how' },
            ],
        400,
      );
    } else {
      // New visitor
      setStage(STAGE.ASK_NAME);
      botSay(
        "Hey there! I'm **EvenStocks AI** — your smart stock market companion.\n\nI can share market insights, stock tips, and help you explore the world of investing.\n\nWhat's your name? I'd love to get to know you!",
        [],
        500,
      );
    }
  }, [open, botSay, factIndex]);

  /* ── WebSocket for AI chat (lazy connect in free_chat stage) ── */
  useEffect(() => {
    if (!open || stage !== STAGE.FREE_CHAT) return;
    if (wsRef.current && wsRef.current.readyState === 1) return;

    const ws = new WebSocket(`${WS_URL}/ws/chat`);
    ws.onopen = () => { setConnected(true); wsRef.current = ws; };
    ws.onclose = () => { setConnected(false); wsRef.current = null; };
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'stream_start') {
        setStreaming(true);
        streamBufRef.current = '';
        setMessages((prev) => [...prev, { role: 'assistant', content: '', streaming: true }]);
        return;
      }
      if (data.type === 'stream_delta') {
        streamBufRef.current += data.content;
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === 'assistant' && last.streaming) {
            updated[updated.length - 1] = { ...last, content: streamBufRef.current };
          }
          return updated;
        });
        return;
      }
      if (data.type === 'stream_end') {
        setStreaming(false);
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === 'assistant') {
            updated[updated.length - 1] = { ...last, streaming: false };
          }
          return updated;
        });
        setQuickActions([
          { label: 'Tell me more', value: 'Tell me more about this' },
          { label: 'Another stock tip', value: '__tip' },
          { label: 'Analyze a stock', value: '__analyze' },
        ]);
        return;
      }
      if (data.type === 'error') {
        setStreaming(false);
        setMessages((prev) => [...prev, { role: 'assistant', content: data.message || 'Oops, something went wrong. Try again!' }]);
      }
    };

    return () => { ws.close(); wsRef.current = null; };
  }, [open, stage]);

  /* ── Next stock fact ── */
  const nextFact = useCallback(() => {
    const idx = (factIndex + 1) % STOCK_FACTS.length;
    setFactIndex(idx);
    return STOCK_FACTS[idx];
  }, [factIndex]);

  /* ── Handle CRM flow ── */
  const handleCrmResponse = useCallback((text) => {
    const lower = text.toLowerCase().trim();

    switch (stage) {
      case STAGE.ASK_NAME: {
        const name = text.trim().split(/\s+/).map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
        const updated = storeLead({ name });
        setLead(updated);
        setStage(STAGE.ASK_INTEREST);
        botSay(
          `Nice to meet you, **${name}**! \n\nTo give you the best experience, what interests you most about the stock market?`,
          [
            { label: 'Long-term investing', value: 'Long-term investing' },
            { label: 'Short-term trading', value: 'Short-term trading' },
            { label: 'Mutual funds & SIPs', value: 'Mutual funds & SIPs' },
            { label: 'IPOs & new listings', value: 'IPOs & new listings' },
            { label: 'Just learning', value: 'Just learning about stocks' },
          ],
        );
        return true;
      }

      case STAGE.ASK_INTEREST: {
        const updated = storeLead({ interest: text.trim() });
        setLead(updated);
        setStage(STAGE.ASK_EXPERIENCE);
        botSay(
          `Great choice! **${text.trim()}** is ${lower.includes('learn') ? 'a wonderful way to start' : 'a popular strategy among Indian investors'}.\n\nHere's a quick fact: *"${nextFact()}"*\n\nHow would you describe your investing experience?`,
          [
            { label: "I'm a beginner", value: 'Beginner' },
            { label: 'Intermediate', value: 'Intermediate' },
            { label: 'Advanced investor', value: 'Advanced' },
            { label: 'Professional trader', value: 'Professional' },
          ],
        );
        return true;
      }

      case STAGE.ASK_EXPERIENCE: {
        const updated = storeLead({ experience: text.trim() });
        setLead(updated);
        setStage(STAGE.ASK_EMAIL);

        const tipIdx = Math.floor(Math.random() * STOCK_TIPS.length);
        const personalTip = text.toLowerCase().includes('beginner')
          ? STOCK_TIPS[0]
          : text.toLowerCase().includes('professional')
            ? STOCK_TIPS[5]
            : STOCK_TIPS[tipIdx];

        botSay(
          `Got it — **${text.trim()}** level! Here's a tip just for you:\n\n*"${personalTip}"*\n\nI'd love to send you personalized stock insights and market alerts. What's your email? (or type "skip" to continue)`,
          [
            { label: 'Skip for now', value: 'skip' },
          ],
        );
        return true;
      }

      case STAGE.ASK_EMAIL: {
        if (lower === 'skip' || lower === 'no' || lower === 'not now' || lower === 'later') {
          setStage(STAGE.FREE_CHAT);
          pushLeadToBackend(getStoredLead());
          botSay(
            "No worries at all! You can always share it later.\n\nYou're all set! Ask me anything about stocks, markets, or investing. I'm here to help!",
            [
              { label: 'Stock tip of the day', value: '__tip' },
              { label: 'Analyze a stock', value: '__analyze' },
              { label: 'Market overview', value: '__market' },
              { label: 'Fun stock fact', value: '__fact' },
            ],
          );
          return true;
        }

        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (emailRegex.test(text.trim())) {
          const updated = storeLead({ email: text.trim() });
          setLead(updated);
          setStage(STAGE.FREE_CHAT);
          pushLeadToBackend(updated);
          botSay(
            `Awesome, thanks **${updated.name || ''}**! I'll keep you posted with the best insights.\n\nNow let's dive in! What would you like to explore?`,
            [
              { label: 'Stock tip of the day', value: '__tip' },
              { label: 'Analyze a stock', value: '__analyze' },
              { label: 'Market overview', value: '__market' },
              { label: 'How EvenStocks works', value: '__how' },
              { label: 'Fun stock fact', value: '__fact' },
            ],
          );
          return true;
        } else {
          botSay(
            "Hmm, that doesn't look like a valid email. Could you double-check? Or type **skip** to continue without it.",
            [{ label: 'Skip for now', value: 'skip' }],
          );
          return true;
        }
      }

      default:
        return false;
    }
  }, [stage, botSay, nextFact]);

  /* ── Handle special quick-action commands ── */
  const handleSpecialAction = useCallback((value) => {
    switch (value) {
      case '__tip': {
        const tip = STOCK_TIPS[Math.floor(Math.random() * STOCK_TIPS.length)];
        botSay(
          `**Stock Tip**\n\n*"${tip}"*\n\nWant to learn more or ask about a specific stock?`,
          [
            { label: 'Another tip', value: '__tip' },
            { label: 'Fun stock fact', value: '__fact' },
            { label: 'Analyze a stock', value: '__analyze' },
          ],
        );
        return true;
      }
      case '__fact': {
        botSay(
          `**Did You Know?**\n\n*"${nextFact()}"*\n\nPretty interesting, right? Want more?`,
          [
            { label: 'Another fact', value: '__fact' },
            { label: 'Stock tip', value: '__tip' },
            { label: 'Ask a question', value: '__free' },
          ],
        );
        return true;
      }
      case '__analyze': {
        navigate('/chatbot');
        return true;
      }
      case '__market': {
        if (wsRef.current && wsRef.current.readyState === 1) {
          setMessages((prev) => [...prev, { role: 'user', content: 'Give me a brief Indian stock market overview for today' }]);
          wsRef.current.send(JSON.stringify({ action: 'message', content: 'Give me a brief Indian stock market overview for today. Include Sensex, Nifty sentiment and any notable movers.', stocks: [] }));
        } else {
          botSay(
            "**Market Quick Look**\n\nFor real-time market data and deep analysis, try our full **AI Chatbot** — it can pull live stock data and give you detailed reports!\n\nHere's a general tip: *\"Always check pre-market trends and global cues before market opens at 9:15 AM IST.\"*",
            [
              { label: 'Open full chatbot', value: '__analyze' },
              { label: 'Stock tip', value: '__tip' },
              { label: 'Fun fact', value: '__fact' },
            ],
          );
        }
        return true;
      }
      case '__how': {
        botSay(
          "**How EvenStocks Works**\n\n- **AI-Powered Analysis** — Our AI reads financial data of 2000+ stocks and gives you clear, actionable insights\n- **Tag Stocks with @** — In the full chatbot, type @ to select any stock and get instant analysis\n- **Compare Stocks** — Tag multiple stocks to get side-by-side comparisons\n- **Real-Time Data** — All numbers come from our database, not guesses\n\nWant to try it out?",
          [
            { label: 'Open full chatbot', value: '__analyze' },
            { label: 'Stock tip', value: '__tip' },
            { label: 'Fun fact', value: '__fact' },
          ],
        );
        return true;
      }
      case '__free': {
        setQuickActions([]);
        botSay("Go ahead — ask me anything about stocks or investing!", []);
        return true;
      }
      default:
        return false;
    }
  }, [botSay, nextFact, navigate]);

  /* ── Send message ── */
  const send = useCallback((text) => {
    const msg = (text || input).trim();
    if (!msg || streaming || typing) return;

    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setInput('');
    setQuickActions([]);

    // Check for special actions
    if (msg.startsWith('__') && handleSpecialAction(msg)) return;

    // CRM flow
    if (handleCrmResponse(msg)) return;

    // Free chat — send to WebSocket if connected
    if (wsRef.current && wsRef.current.readyState === 1) {
      wsRef.current.send(JSON.stringify({ action: 'message', content: msg, stocks: [] }));
    } else {
      // Fallback: engaging response without WS
      const lead = getStoredLead();
      const greeting = lead.name ? `${lead.name}, great question! ` : '';
      botSay(
        `${greeting}For the best stock analysis experience, try our **full AI Chatbot** — it can pull real data for 2000+ Indian stocks!\n\nIn the meantime, here's a tip: *"${STOCK_TIPS[Math.floor(Math.random() * STOCK_TIPS.length)]}"*`,
        [
          { label: 'Open full chatbot', value: '__analyze' },
          { label: 'Stock tip', value: '__tip' },
          { label: 'Fun fact', value: '__fact' },
        ],
      );
    }
  }, [input, streaming, typing, handleCrmResponse, handleSpecialAction, botSay]);

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const toggleChat = () => {
    setOpen((prev) => {
      if (!prev) setUnread(0);
      return !prev;
    });
  };

  const goToFullChat = () => navigate('/chatbot');

  return (
    <div className="fc-container">
      {/* Chat Window */}
      <div className={`fc-window ${open ? 'fc-open' : ''}`}>
        {/* Header */}
        <div className="fc-header">
          <div className="fc-header-left">
            <img src="/assets/img/logo-icon.png" alt="EvenStocks" className="fc-logo" />
            <div>
              <div className="fc-title">EvenStocks AI</div>
              <div className={`fc-status ${stage === STAGE.FREE_CHAT && connected ? 'fc-online' : 'fc-active'}`}>
                {stage === STAGE.FREE_CHAT && connected ? 'Online' : 'Chat with us'}
              </div>
            </div>
          </div>
          <div className="fc-header-actions">
            <button className="fc-expand-btn" onClick={goToFullChat} title="Open full chatbot">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="15 3 21 3 21 9" />
                <polyline points="9 21 3 21 3 15" />
                <line x1="21" y1="3" x2="14" y2="10" />
                <line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            </button>
            <button className="fc-close-btn" onClick={toggleChat}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="fc-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`fc-msg fc-msg-${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className="fc-avatar">
                  <img src="/assets/img/logo-icon.png" alt="" />
                </div>
              )}
              <div className={`fc-bubble fc-bubble-${msg.role}`}>
                {msg.role === 'assistant' ? (
                  msg.streaming && !msg.content ? (
                    <div className="fc-dots"><span></span><span></span><span></span></div>
                  ) : (
                    <span dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />
                  )
                ) : (
                  esc(msg.content)
                )}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {typing && (
            <div className="fc-msg fc-msg-assistant">
              <div className="fc-avatar">
                <img src="/assets/img/logo-icon.png" alt="" />
              </div>
              <div className="fc-bubble fc-bubble-assistant">
                <div className="fc-dots"><span></span><span></span><span></span></div>
              </div>
            </div>
          )}
          <div ref={msgEndRef} />
        </div>

        {/* Quick Actions */}
        {quickActions.length > 0 && !streaming && !typing && (
          <div className="fc-quick">
            {quickActions.map((a, i) => (
              <button key={i} className="fc-quick-btn" onClick={() => send(a.value)}>
                {a.label}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="fc-input-area">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder={
              stage === STAGE.ASK_NAME ? 'Type your name...'
                : stage === STAGE.ASK_EMAIL ? 'you@example.com or type skip'
                  : 'Ask about stocks...'
            }
            disabled={streaming || typing}
          />
          <button className="fc-send-btn" onClick={() => send()} disabled={!input.trim() || streaming || typing}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>

        {/* Footer */}
        <div className="fc-footer">
          <button className="fc-footer-link" onClick={goToFullChat}>
            Open full AI chatbot for deep stock analysis
          </button>
        </div>
      </div>

      {/* Floating Button */}
      <button className={`fc-fab ${open ? 'fc-fab-hidden' : ''}`} onClick={toggleChat}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        {unread > 0 && <span className="fc-badge">{unread}</span>}
        <span className="fc-tooltip">AI agent that learns your interests & personalises your experience</span>
      </button>
    </div>
  );
};

export default FloatingChat;
