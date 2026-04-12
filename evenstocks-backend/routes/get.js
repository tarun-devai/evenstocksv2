const express = require('express');
const axios = require('axios');
const router = express.Router();

const API_BASE = process.env.EXTERNAL_API_BASE; // http://188.40.254.10:5809/api

// ─────────────────────────────────────────────────────────────
// GET /api/get?method=all_signedup_users
// Mirrors the PHP get.php switch on `method` query param
// ─────────────────────────────────────────────────────────────

router.get('/', async (req, res) => {
  const method = req.query.method;

  if (!method) {
    return res.status(400).json({ error: 'Missing method parameter' });
  }

  try {
    switch (method) {

      case 'all_signedup_users': {
        const response = await axios.get(`${API_BASE}/all_signedup_users`, {
          timeout: 30000,
        });
        return res.json(response.data);
      }

      default:
        return res.status(400).json({ error: 'Bad Request' });
    }
  } catch (error) {
    console.error(`[GET /${method}] Error:`, error.message);
    const statusCode = error.response?.status || 500;
    return res.status(statusCode).json({
      error: true,
      message: 'Failed to fetch data',
      status: statusCode,
    });
  }
});

module.exports = router;
