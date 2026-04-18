const express = require('express');
const axios = require('axios');

const router = express.Router();

const AGENTS_API_BASE = process.env.AGENTS_API_BASE || 'http://evenstocks-agents:5810';

// GET /api/agents/health — proxy to agents service health
router.get('/health', async (req, res) => {
  try {
    const resp = await axios.get(`${AGENTS_API_BASE}/health`, { timeout: 5000 });
    return res.json(resp.data);
  } catch (err) {
    return res.status(502).json({
      error: 'agents service unavailable',
      detail: err.message,
    });
  }
});

// GET /api/agents/analyze/:ticker — blocking one-shot analysis
router.get('/analyze/:ticker', async (req, res) => {
  const { ticker } = req.params;
  if (!ticker) {
    return res.status(400).json({ error: 'ticker is required' });
  }

  try {
    const resp = await axios.get(
      `${AGENTS_API_BASE}/analyze/${encodeURIComponent(ticker)}`,
      { timeout: 300000 } // 5 min — full debate pipeline can be slow
    );
    return res.json(resp.data);
  } catch (err) {
    const status = err.response?.status || 502;
    const detail = err.response?.data?.detail || err.message;
    return res.status(status).json({ error: 'agent analysis failed', detail });
  }
});

// GET /api/agents/analyze/:ticker/stream — SSE pass-through
router.get('/analyze/:ticker/stream', async (req, res) => {
  const { ticker } = req.params;
  if (!ticker) {
    return res.status(400).json({ error: 'ticker is required' });
  }

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');
  res.flushHeaders?.();

  let upstream;
  try {
    upstream = await axios.get(
      `${AGENTS_API_BASE}/analyze/${encodeURIComponent(ticker)}/stream`,
      { responseType: 'stream', timeout: 0 }
    );
  } catch (err) {
    const detail = err.response?.data?.detail || err.message;
    res.write(`event: error\ndata: ${JSON.stringify({ message: detail })}\n\n`);
    return res.end();
  }

  upstream.data.on('data', (chunk) => res.write(chunk));
  upstream.data.on('end', () => res.end());
  upstream.data.on('error', (err) => {
    res.write(`event: error\ndata: ${JSON.stringify({ message: err.message })}\n\n`);
    res.end();
  });

  req.on('close', () => {
    upstream.data.destroy();
  });
});

module.exports = router;
