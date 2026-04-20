import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import '../styles/chatbot.css';

const WS_URL = process.env.REACT_APP_CHATBOT_WS_URL || 'ws://localhost:8001';

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
  h = h.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  h = h.replace(/\*(.+?)\*/g, '<em>$1</em>');
  h = h.replace(/^- (.+)$/gm, '<li>$1</li>');
  h = h.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
  h = h.replace(/\n{3,}/g, '\n\n');
  h = h.replace(/\n\n/g, '<br>');
  h = h.replace(/\n/g, '<br>');
  h = h.replace(/<br><\/ul>/g, '</ul>');
  h = h.replace(/<ul><br>/g, '<ul>');
  return h;
}

const FOLLOW_UP_SUGGESTIONS = {
  analysis: [
    'What are the key risks?',
    'Compare with sector peers',
    'Is this good for long term?',
    'What about recent quarterly results?',
  ],
  general: [
    'Show me top gainers today',
    'Which sectors are performing well?',
    'Suggest stocks under 500',
    'What are safe dividend stocks?',
  ],
};

const ChatBotPage = () => {
  const { isLoggedIn } = useAuth();
  const navigate = useNavigate();

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [connected, setConnected] = useState(false);
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [acResults, setAcResults] = useState([]);
  const [acIndex, setAcIndex] = useState(-1);
  const [showAc, setShowAc] = useState(false);
  const [toast, setToast] = useState('');
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [reactions, setReactions] = useState({});

  const wsRef = useRef(null);
  const msgBoxRef = useRef(null);
  const inputRef = useRef(null);
  const streamBufRef = useRef('');
  const acTimeoutRef = useRef(null);
  const lastAtPosRef = useRef(-1);

  // Auto-scroll
  const scrollToBottom = useCallback(() => {
    if (msgBoxRef.current) {
      msgBoxRef.current.scrollTop = msgBoxRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

  // Scroll button visibility
  const handleScroll = useCallback(() => {
    if (msgBoxRef.current) {
      const { scrollHeight, scrollTop, clientHeight } = msgBoxRef.current;
      setShowScrollBtn(scrollHeight - scrollTop - clientHeight > 100);
    }
  }, []);

  // Toast
  const showToast = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 2000);
  }, []);

  // WebSocket connection
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(`${WS_URL}/ws/chat`);

      ws.onopen = () => {
        setConnected(true);
        wsRef.current = ws;
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        setTimeout(connect, 2000);
      };

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);

        if (data.type === 'autocomplete') {
          setAcResults(data.results || []);
          setAcIndex(-1);
          setShowAc(true);
          return;
        }

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
            if (last && last.role === 'assistant' && last.streaming) {
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
            if (last && last.role === 'assistant') {
              updated[updated.length - 1] = {
                ...last,
                streaming: false,
                usage: data.usage,
              };
            }
            return updated;
          });
          return;
        }

        if (data.type === 'cleared') {
          setMessages([]);
          setSelectedStocks([]);
          return;
        }

        if (data.type === 'error') {
          setMessages((prev) => [...prev, { role: 'assistant', content: data.message }]);
        }
      };
    };

    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Send message
  const getMessageText = () => input.replace(/@\S*/g, '').trim();

  const send = () => {
    const text = getMessageText();
    if (!text || streaming || !wsRef.current) return;

    const stockNames = selectedStocks.map((s) => s.stock_name);

    setMessages((prev) => [...prev, { role: 'user', content: text, stocks: stockNames }]);

    wsRef.current.send(
      JSON.stringify({
        action: 'message',
        content: text,
        stocks: stockNames,
      })
    );

    setInput('');
    setSelectedStocks([]);
  };

  const stopGen = () => {
    if (wsRef.current) wsRef.current.send(JSON.stringify({ action: 'stop' }));
  };

  const clearChat = () => {
    if (wsRef.current) wsRef.current.send(JSON.stringify({ action: 'clear' }));
    setInput('');
  };

  // Autocomplete
  const onInputChange = (e) => {
    const val = e.target.value;
    setInput(val);

    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px';

    const cursorPos = e.target.selectionStart;
    const beforeCursor = val.slice(0, cursorPos);
    const atIdx = beforeCursor.lastIndexOf('@');

    if (atIdx !== -1) {
      const query = beforeCursor.slice(atIdx + 1);
      if (!query.includes('\n') && query.length >= 1 && query.length < 50) {
        lastAtPosRef.current = atIdx;
        clearTimeout(acTimeoutRef.current);
        acTimeoutRef.current = setTimeout(() => {
          if (wsRef.current && wsRef.current.readyState === 1) {
            wsRef.current.send(JSON.stringify({ action: 'autocomplete', query }));
          }
        }, 200);
        return;
      }
    }
    setShowAc(false);
    setAcResults([]);
  };

  const selectStock = (idx) => {
    const stock = acResults[idx];
    if (!stock) return;

    if (!selectedStocks.find((s) => s.stock_name === stock.stock_name)) {
      setSelectedStocks((prev) => [...prev, stock]);
      showToast(`${stock.stock_name.replace(/_/g, ' ')} added`);
    }

    // Remove @query from input
    const atPos = lastAtPosRef.current;
    const cursorPos = inputRef.current.selectionStart;
    const before = input.slice(0, atPos);
    const after = input.slice(cursorPos);
    setInput(before + after);

    setShowAc(false);
    setAcResults([]);
    inputRef.current.focus();
  };

  const removeStock = (idx) => {
    const name = selectedStocks[idx].stock_name.replace(/_/g, ' ');
    setSelectedStocks((prev) => prev.filter((_, i) => i !== idx));
    showToast(`${name} removed`);
  };

  const handleKey = (e) => {
    if (showAc && acResults.length) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setAcIndex((prev) => Math.min(prev + 1, acResults.length - 1));
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setAcIndex((prev) => Math.max(prev - 1, 0));
        return;
      }
      if ((e.key === 'Enter' || e.key === 'Tab') && acIndex >= 0) {
        e.preventDefault();
        selectStock(acIndex);
        return;
      }
      if (e.key === 'Escape') {
        setShowAc(false);
        return;
      }
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const insertExample = (text) => {
    setInput(text);
    inputRef.current.focus();
    setTimeout(() => {
      if (wsRef.current && wsRef.current.readyState === 1) {
        const atIdx = text.lastIndexOf('@');
        if (atIdx !== -1) {
          const query = text.slice(atIdx + 1).trim();
          lastAtPosRef.current = atIdx;
          wsRef.current.send(JSON.stringify({ action: 'autocomplete', query }));
        }
      }
    }, 100);
  };

  // Copy helpers
  const copyText = (text) => {
    navigator.clipboard.writeText(text).then(() => showToast('Copied to clipboard'));
  };

  // Reactions
  const toggleReaction = (msgIndex, type) => {
    setReactions((prev) => {
      const key = `${msgIndex}-${type}`;
      const current = prev[msgIndex];
      if (current === type) {
        const next = { ...prev };
        delete next[msgIndex];
        return next;
      }
      return { ...prev, [msgIndex]: type };
    });
    showToast(type === 'up' ? 'Marked as helpful' : 'Thanks for feedback');
  };

  // Export chat
  const exportChat = () => {
    if (messages.length === 0) {
      showToast('No messages to export');
      return;
    }
    const text = messages
      .map((m) => `${m.role === 'user' ? 'You' : 'EvenStocks AI'}:\n${m.content}\n`)
      .join('\n---\n\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evenstocks-chat-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Chat exported');
  };

  // Insert follow-up suggestion
  const sendSuggestion = (text) => {
    if (streaming) return;
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    if (wsRef.current && wsRef.current.readyState === 1) {
      wsRef.current.send(
        JSON.stringify({ action: 'message', content: text, stocks: selectedStocks.map((s) => s.stock_name) })
      );
    }
  };

  // Determine which follow-up chips to show
  const getFollowUpSuggestions = () => {
    if (messages.length === 0 || streaming) return [];
    const last = messages[messages.length - 1];
    if (last.role !== 'assistant' || last.streaming) return [];
    const hasStockContext = messages.some((m) => m.role === 'user' && m.stocks && m.stocks.length > 0);
    return hasStockContext ? FOLLOW_UP_SUGGESTIONS.analysis : FOLLOW_UP_SUGGESTIONS.general;
  };

  return (
    <div className="chatbot-page">
      {/* Header */}
      <div className="header">
        <div className="header-left">
          <img src="/assets/img/logo-icon.png" alt="EvenStocks" className="logo" />
          <div>
            <h1>EvenStocks</h1>
            <div className={`status${connected ? ' active' : ''}`}>
              {connected ? 'Online' : 'Connecting...'}
            </div>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-clear" onClick={exportChat} title="Export chat">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{verticalAlign: 'middle', marginRight: '4px'}}>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Export
          </button>
          <button className="btn-clear" onClick={clearChat}>
            New Chat
          </button>
          <button className="btn-back" onClick={() => navigate(isLoggedIn ? '/admins' : '/')}>
            Back
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="messages" ref={msgBoxRef} onScroll={handleScroll}>
        {messages.length === 0 && (
          <div className="welcome">
            <img src="/assets/img/logo-icon.png" alt="" className="welcome-logo" />
            <h2>EvenStocks AI Analyst</h2>
            <p>
              Type <strong>@</strong> followed by a stock name to search and tag stocks.
              <br />
              Select one or multiple stocks, then ask any question.
            </p>
            <div className="welcome-examples">
              <span className="example-chip" onClick={() => insertExample('@Tata ')}>
                @Tata Motors
              </span>
              <span className="example-chip" onClick={() => insertExample('@Infosys ')}>
                @Infosys
              </span>
              <span className="example-chip" onClick={() => insertExample('@Reliance ')}>
                @Reliance
              </span>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.role}`}>
            <div className="avatar">
              {msg.role === 'user' ? '\u25CF' : '\u25C6'}
            </div>
            <div className="body">
              <div className="role">
                {msg.role === 'user' ? 'You' : 'EvenStocks AI'}
              </div>
              {msg.role === 'user' && msg.stocks && msg.stocks.length > 0 && (
                <div className="msg-stocks">
                  {msg.stocks.map((s, j) => (
                    <span key={j} className="badge">
                      {s.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              )}
              <div className="content">
                {msg.role === 'user' ? (
                  esc(msg.content)
                ) : msg.streaming ? (
                  <span
                    dangerouslySetInnerHTML={{
                      __html: msg.content
                        ? renderMarkdown(msg.content) + '<span class="cursor"></span>'
                        : '<div class="thinking-dots"><span></span><span></span><span></span></div>',
                    }}
                  />
                ) : (
                  <span dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />
                )}
              </div>
              {msg.role === 'assistant' && !msg.streaming && msg.content && (
                <div className="msg-actions">
                  <button className="msg-action-btn" onClick={() => copyText(msg.content)}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="9" y="9" width="13" height="13" rx="2"/>
                      <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                    </svg>
                    Copy
                  </button>
                  <button
                    className={`msg-action-btn${reactions[i] === 'up' ? ' reacted' : ''}`}
                    onClick={() => toggleReaction(i, 'up')}
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill={reactions[i] === 'up' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
                      <path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3H14z"/>
                      <path d="M7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3"/>
                    </svg>
                  </button>
                  <button
                    className={`msg-action-btn${reactions[i] === 'down' ? ' reacted' : ''}`}
                    onClick={() => toggleReaction(i, 'down')}
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill={reactions[i] === 'down' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
                      <path d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3H10z"/>
                      <path d="M17 2h3a2 2 0 012 2v7a2 2 0 01-2 2h-3"/>
                    </svg>
                  </button>
                </div>
              )}
              {msg.usage && (
                <div className="usage-badge">
                  {msg.usage.input_tokens} in / {msg.usage.output_tokens} out
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Follow-up suggestions */}
      {getFollowUpSuggestions().length > 0 && (
        <div className="follow-up-bar">
          <div className="follow-up-inner">
            {getFollowUpSuggestions().map((s, i) => (
              <button key={i} className="follow-up-chip" onClick={() => sendSuggestion(s)}>
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Scroll to bottom button */}
      <button
        className={`scroll-bottom${showScrollBtn ? ' visible' : ''}`}
        onClick={scrollToBottom}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>

      {/* Toast */}
      <div className={`toast${toast ? ' show' : ''}`}>{toast}</div>

      {/* Input area */}
      <div className="input-area">
        <div className="input-wrapper">
          {selectedStocks.length > 0 && (
            <div className="input-tags">
              {selectedStocks.map((s, i) => (
                <span key={i} className="stock-tag">
                  {s.stock_name.replace(/_/g, ' ')}
                  <span className="remove-tag" onClick={() => removeStock(i)}>
                    &times;
                  </span>
                </span>
              ))}
            </div>
          )}
          <div className="input-row">
            <textarea
              ref={inputRef}
              rows="1"
              value={input}
              placeholder="Type @ to search stocks, then ask your question..."
              onChange={onInputChange}
              onKeyDown={handleKey}
            />
            {!streaming ? (
              <button
                className="btn-send"
                onClick={send}
                disabled={!getMessageText() || !connected}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            ) : (
              <button className="btn-stop" onClick={stopGen}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="4" y="4" width="16" height="16" rx="2" />
                </svg>
              </button>
            )}
          </div>

          {/* Autocomplete dropdown */}
          {showAc && (
            <div className="autocomplete-dropdown">
              {acResults.length === 0 ? (
                <div className="ac-empty">No stocks found</div>
              ) : (
                <>
                  <div className="ac-header">Select a stock</div>
                  {acResults.map((r, i) => (
                    <div
                      key={i}
                      className={`ac-item${i === acIndex ? ' active' : ''}`}
                      onMouseDown={() => selectStock(i)}
                    >
                      <span className="ac-name">
                        {r.stock_name.replace(/_/g, ' ')}
                      </span>
                      <span className="ac-meta">
                        {r.market_cap && <span>{r.market_cap}</span>}
                        {r.current_price && <span>{r.current_price}</span>}
                        {r.stock_pe && <span>PE: {r.stock_pe}</span>}
                      </span>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
        <div className="footer">EvenStocks &middot; AI-Powered Stock Analysis &middot; Type @ to tag stocks</div>
      </div>
    </div>
  );
};

export default ChatBotPage;
