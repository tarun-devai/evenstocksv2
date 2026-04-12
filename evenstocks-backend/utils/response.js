/**
 * Standard JSON response helper — mirrors the PHP config.php json() function
 */
function jsonResponse(data, message, statusCode, status) {
  return {
    status,
    statusCode,
    message,
    result: data ?? {},
  };
}

function sendSuccess(res, data, message = 'Success', httpCode = 200) {
  return res.status(httpCode).json(jsonResponse(data, message, httpCode, 1));
}

function sendError(res, message = 'Error', httpCode = 400) {
  return res.status(httpCode).json(jsonResponse(null, message, httpCode, 0));
}

module.exports = { jsonResponse, sendSuccess, sendError };
