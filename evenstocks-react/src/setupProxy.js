const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
  // Proxy WebSocket connections to Python backend
  app.use(
    '/ws',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      ws: true,
      changeOrigin: true,
    })
  );

  // Proxy stock API requests to Python backend
  app.use(
    '/api/stocks',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
    })
  );
};
