// ── DOM refs ──────────────────────────────────────────────
const msgBox = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const stopBtn = document.getElementById("stopBtn");
const statusEl = document.getElementById("status");
const acDropdown = document.getElementById("autocomplete");
const welcomeEl = document.getElementById("welcome");
const scrollBtn = document.getElementById("scrollBtn");
const toastEl = document.getElementById("toast");

let ws, streaming = false, currentBubble = null;
let selectedStocks = [];
let acResults = [];
let acIndex = -1;
let acTimeout = null;
let lastAtPos = -1;

// ── WebSocket ─────────────────────────────────────────────
function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws/chat`);

  ws.onopen = () => {
    statusEl.textContent = "Online";
    statusEl.className = "status active";
    sendBtn.disabled = !getMessageText();
  };

  ws.onclose = () => {
    statusEl.textContent = "Disconnected";
    statusEl.className = "status";
    sendBtn.disabled = true;
    setTimeout(connect, 2000);
  };

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);

    if (data.type === "autocomplete") {
      acResults = data.results;
      acIndex = -1;
      renderAutocomplete();
      return;
    }

    if (data.type === "stream_start") {
      streaming = true;
      toggleButtons();
      if (welcomeEl) welcomeEl.style.display = "none";
      currentBubble = addMessage("assistant", "");
      const el = currentBubble.querySelector(".content");
      el.innerHTML = '<div class="thinking-dots"><span></span><span></span><span></span></div>';
    }

    if (data.type === "stream_delta" && currentBubble) {
      const el = currentBubble.querySelector(".content");
      const raw = (el._rawText || "") + data.content;
      el._rawText = raw;
      el.innerHTML = renderMarkdown(raw) + '<span class="cursor"></span>';
      addCopyButtons(el);
      scrollToBottom();
    }

    if (data.type === "stream_end") {
      streaming = false;
      toggleButtons();
      if (currentBubble) {
        const el = currentBubble.querySelector(".content");
        el.innerHTML = renderMarkdown(el._rawText || "");
        addCopyButtons(el);

        // Add copy message button
        const actions = document.createElement("div");
        actions.className = "msg-actions";
        actions.innerHTML = `<button class="msg-action-btn" onclick="copyMessage(this)">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          Copy
        </button>`;
        currentBubble.querySelector(".body").appendChild(actions);

        if (data.usage) {
          const badge = document.createElement("div");
          badge.className = "usage-badge";
          badge.textContent = `${data.usage.input_tokens} in / ${data.usage.output_tokens} out`;
          currentBubble.after(badge);
        }
      }
      currentBubble = null;
      inputEl.focus();
    }

    if (data.type === "cleared") {
      msgBox.innerHTML = "";
      if (welcomeEl) { msgBox.appendChild(welcomeEl); welcomeEl.style.display = ""; }
      selectedStocks = [];
      renderInputTags();
    }

    if (data.type === "error") {
      addMessage("assistant", data.message);
    }
  };
}

// ── Toast ─────────────────────────────────────────────────
function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 2000);
}

// ── Copy helpers ──────────────────────────────────────────
function copyMessage(btn) {
  const msg = btn.closest(".msg");
  const content = msg.querySelector(".content");
  const text = content._rawText || content.textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.classList.add("copied");
    btn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied`;
    showToast("Copied to clipboard");
    setTimeout(() => {
      btn.classList.remove("copied");
      btn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg> Copy`;
    }, 2000);
  });
}

function copyCodeBlock(btn) {
  const pre = btn.closest("pre");
  const code = pre.querySelector("code").textContent;
  navigator.clipboard.writeText(code).then(() => {
    btn.classList.add("copied");
    btn.textContent = "Copied!";
    setTimeout(() => { btn.classList.remove("copied"); btn.textContent = "Copy"; }, 2000);
  });
}

function addCopyButtons(el) {
  el.querySelectorAll("pre").forEach(pre => {
    if (!pre.querySelector(".copy-btn")) {
      const btn = document.createElement("button");
      btn.className = "copy-btn";
      btn.textContent = "Copy";
      btn.onclick = function() { copyCodeBlock(this); };
      pre.style.position = "relative";
      pre.appendChild(btn);
    }
  });
}

// ── Scroll to bottom ──────────────────────────────────────
function scrollToBottom() {
  msgBox.scrollTop = msgBox.scrollHeight;
}

msgBox.addEventListener("scroll", () => {
  const nearBottom = msgBox.scrollHeight - msgBox.scrollTop - msgBox.clientHeight < 100;
  scrollBtn.classList.toggle("visible", !nearBottom);
});

// ── Autocomplete ──────────────────────────────────────────

function onInput() {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 100) + "px";
  sendBtn.disabled = !getMessageText();

  const text = inputEl.value;
  const cursorPos = inputEl.selectionStart;
  const beforeCursor = text.slice(0, cursorPos);
  const atIdx = beforeCursor.lastIndexOf("@");

  if (atIdx !== -1) {
    const query = beforeCursor.slice(atIdx + 1);
    if (!query.includes("\n") && query.length >= 1 && query.length < 50) {
      lastAtPos = atIdx;
      clearTimeout(acTimeout);
      acTimeout = setTimeout(() => {
        if (ws && ws.readyState === 1) {
          ws.send(JSON.stringify({ action: "autocomplete", query }));
        }
      }, 200);
      return;
    }
  }
  hideAutocomplete();
}

function renderAutocomplete() {
  if (!acResults.length) {
    if (lastAtPos !== -1) {
      acDropdown.innerHTML = '<div class="ac-empty">No stocks found</div>';
      acDropdown.classList.add("show");
    }
    return;
  }

  const query = inputEl.value.slice(lastAtPos + 1, inputEl.selectionStart).toLowerCase();
  let html = '<div class="ac-header">Select a stock</div>';

  acResults.forEach((r, i) => {
    const name = r.stock_name.replace(/_/g, " ");
    const lower = name.toLowerCase();
    const mIdx = lower.indexOf(query);
    let nameHtml;
    if (mIdx !== -1 && query) {
      nameHtml = esc(name.slice(0, mIdx))
        + '<span class="ac-highlight">' + esc(name.slice(mIdx, mIdx + query.length)) + '</span>'
        + esc(name.slice(mIdx + query.length));
    } else {
      nameHtml = esc(name);
    }
    const cls = i === acIndex ? " active" : "";
    html += `<div class="ac-item${cls}" data-idx="${i}" onmousedown="selectAC(${i})">
      <span class="ac-name">${nameHtml}</span>
      <span class="ac-meta">
        ${r.market_cap ? "<span>" + esc(r.market_cap) + "</span>" : ""}
        ${r.current_price ? "<span>" + esc(r.current_price) + "</span>" : ""}
        ${r.stock_pe ? "<span>PE: " + esc(r.stock_pe) + "</span>" : ""}
      </span>
    </div>`;
  });

  acDropdown.innerHTML = html;
  acDropdown.classList.add("show");
}

function selectAC(idx) {
  const stock = acResults[idx];
  if (!stock) return;

  if (!selectedStocks.find(s => s.stock_name === stock.stock_name)) {
    selectedStocks.push(stock);
    renderInputTags();
    showToast(`${stock.stock_name.replace(/_/g, " ")} added`);
  }

  const text = inputEl.value;
  const cursorPos = inputEl.selectionStart;
  const before = text.slice(0, lastAtPos);
  const after = text.slice(cursorPos);
  inputEl.value = before + after;
  inputEl.selectionStart = inputEl.selectionEnd = before.length;

  hideAutocomplete();
  inputEl.focus();
  sendBtn.disabled = !getMessageText();
}

function hideAutocomplete() {
  acDropdown.classList.remove("show");
  acResults = [];
  acIndex = -1;
  lastAtPos = -1;
}

// ── Input tags (shown inside chat when sending) ───────────

function renderInputTags() {
  let container = document.getElementById("inputTags");
  if (!container) {
    container = document.createElement("div");
    container.id = "inputTags";
    container.className = "input-tags";
    const wrapper = document.querySelector(".input-wrapper");
    wrapper.insertBefore(container, wrapper.firstChild);
  }
  container.innerHTML = selectedStocks.map((s, i) =>
    `<span class="stock-tag">${esc(s.stock_name.replace(/_/g, " "))}
      <span class="remove-tag" onclick="removeTag(${i})">&times;</span>
    </span>`
  ).join("");
}

function removeTag(idx) {
  const name = selectedStocks[idx].stock_name.replace(/_/g, " ");
  selectedStocks.splice(idx, 1);
  renderInputTags();
  showToast(`${name} removed`);
}

// ── Messages ──────────────────────────────────────────────

function getMessageText() {
  return inputEl.value.replace(/@\S*/g, "").trim();
}

function addMessage(role, text, stocks) {
  const div = document.createElement("div");
  div.className = "msg " + role;

  let badges = "";
  if (role === "user" && stocks && stocks.length) {
    badges = '<div class="msg-stocks">' +
      stocks.map(s => `<span class="badge">${esc(s.replace(/_/g, " "))}</span>`).join("") +
      "</div>";
  }

  const icon = role === "user" ? "&#9679;" : "&#9670;";
  const label = role === "user" ? "You" : "EvenStocks AI";

  div.innerHTML = `
    <div class="avatar">${icon}</div>
    <div class="body">
      <div class="role">${label}</div>
      ${badges}
      <div class="content">${role === "user" ? esc(text) : text}</div>
    </div>`;
  msgBox.appendChild(div);
  scrollToBottom();
  return div;
}

function send() {
  const text = getMessageText();
  if (!text || streaming) return;

  const stockNames = selectedStocks.map(s => s.stock_name);
  addMessage("user", text, stockNames);

  ws.send(JSON.stringify({
    action: "message",
    content: text,
    stocks: stockNames,
  }));

  inputEl.value = "";
  inputEl.style.height = "auto";
  sendBtn.disabled = true;

  const tagsEl = document.getElementById("inputTags");
  if (tagsEl) tagsEl.innerHTML = "";
}

function stopGen() { ws.send(JSON.stringify({ action: "stop" })); }
function clearChat() { ws.send(JSON.stringify({ action: "clear" })); inputEl.value = ""; }
function toggleButtons() {
  sendBtn.style.display = streaming ? "none" : "flex";
  stopBtn.style.display = streaming ? "flex" : "none";
  sendBtn.disabled = !getMessageText();
}

// ── Keyboard ──────────────────────────────────────────────

function handleKey(e) {
  if (acDropdown.classList.contains("show")) {
    if (e.key === "ArrowDown") { e.preventDefault(); acIndex = Math.min(acIndex + 1, acResults.length - 1); renderAutocomplete(); return; }
    if (e.key === "ArrowUp") { e.preventDefault(); acIndex = Math.max(acIndex - 1, 0); renderAutocomplete(); return; }
    if ((e.key === "Enter" || e.key === "Tab") && acIndex >= 0) { e.preventDefault(); selectAC(acIndex); return; }
    if (e.key === "Escape") { hideAutocomplete(); return; }
  }
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  sendBtn.disabled = !getMessageText();
}

// ── Welcome chips ─────────────────────────────────────────

function insertExample(text) {
  inputEl.value = text;
  inputEl.focus();
  inputEl.selectionStart = inputEl.selectionEnd = text.length;
  onInput();
}

// ── Markdown renderer ─────────────────────────────────────

function renderMarkdown(text) {
  let h = esc(text);
  h = h.replace(/```(\w*)\n([\s\S]*?)```/g, "<pre><code>$2</code></pre>");
  h = h.replace(/`([^`]+)`/g, "<code>$1</code>");
  h = h.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  h = h.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  h = h.replace(/^# (.+)$/gm, "<h1>$1</h1>");
  h = h.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  h = h.replace(/\*(.+?)\*/g, "<em>$1</em>");
  h = h.replace(/^- (.+)$/gm, "<li>$1</li>");
  h = h.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");
  h = h.replace(/\n{3,}/g, "\n\n");
  h = h.replace(/\n\n/g, "<br>");
  h = h.replace(/\n/g, "<br>");
  h = h.replace(/<br><\/ul>/g, "</ul>");
  h = h.replace(/<ul><br>/g, "<ul>");
  return h;
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

document.addEventListener("click", (e) => {
  if (!e.target.closest(".input-wrapper")) hideAutocomplete();
});

connect();
