const express = require('express');
const axios = require('axios');
const router = express.Router();

const API_BASE = process.env.EXTERNAL_API_BASE; // http://188.40.254.10:5809/api
const ANALYZE_BASE = process.env.ANALYZE_API_BASE; // http://188.40.254.10:5808

// ─── Helper: forward form data to external API ───
async function forwardPost(url, data) {
  const params = new URLSearchParams(data);
  const response = await axios.post(url, params.toString(), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    timeout: 30000,
  });
  return response.data;
}

// ─── Helper: forward multipart form data to external API ───
async function forwardMultipart(url, data) {
  const FormData = require('form-data');
  const form = new FormData();
  for (const [key, value] of Object.entries(data)) {
    form.append(key, value);
  }
  const response = await axios.post(url, form, {
    headers: form.getHeaders(),
    timeout: 30000,
  });
  return response.data;
}

// ─────────────────────────────────────────────────────────────
// The PHP post.php used a single endpoint with a `key` param.
// We keep the same pattern: POST /api/post with { key: "..." }
// so the React frontend doesn't need changes.
// ─────────────────────────────────────────────────────────────

router.post('/', async (req, res) => {
  // Support both JSON body and form-urlencoded (matches PHP behavior)
  const body = { ...req.body };
  const key = body.key;

  if (!key) {
    return res.status(400).json({ error: 'Missing key parameter' });
  }

  try {
    switch (key) {

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // LOGIN
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'login': {
        const user_email = body.loginEmail || '';
        const user_password = body.loginPassword || '';

        const data = await forwardMultipart(`${API_BASE}/login`, {
          user_email,
          user_password,
        });

        if (data.status === 1) {
          // Set cookies (matching PHP behavior: 30 day expiry)
          const cookieOpts = { maxAge: 86400 * 30 * 1000, httpOnly: false, path: '/' };
          res.cookie('username', data.username, cookieOpts);
          res.cookie('user_token', data.user_token, cookieOpts);

          return res.json({
            status: 'success',
            message: data.message || 'Login successful',
          });
        } else {
          return res.json({
            status: 'error',
            message: data.message || 'Invalid credentials',
          });
        }
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // SIGNUP
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'signup': {
        const fullName = body.fullName || '';
        const age = body.age || '';
        const signupEmail = body.signupEmail || '';
        const mobile = body.mobile || '';
        const userName = body.userName || '';
        const signupPassword = body.signupPassword || '';

        const data = await forwardPost(`${API_BASE}/add_user`, {
          user_name: fullName,
          user_email: signupEmail,
          user_password: signupPassword,
          user_age: age,
          user_mobile: mobile,
          username: userName,
          created_by: fullName,
        });

        return res.json({
          status: 'success',
          code: 200,
          message: data.message,
        });
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // SEND OTP
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'sendotp': {
        const email = body.forgotEmail || body.otpEmail || '';

        // Store email in cookie for password reset flow
        res.cookie('reset_email', email, { path: '/' });

        const data = await forwardMultipart(`${API_BASE}/send_otp`, {
          user_email: email,
        });

        return res.json(data);
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // VALIDATE OTP
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'otp_validate': {
        const otp = body.otp || '';
        const email = body.otpEmail || '';

        const data = await forwardMultipart(`${API_BASE}/verify_otp`, {
          user_email: email,
          otp: otp,
        });

        return res.json({
          status: 'success',
          message: data.message,
        });
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // RESEND OTP (signup flow)
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'resendotp': {
        const email = body.otpEmail || '';

        const data = await forwardMultipart(`${API_BASE}/resend_otp`, {
          user_email: email,
        });

        return res.json({
          status: 'success',
          message: data.message,
        });
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // RESEND OTP (forgot password flow)
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'resendotps': {
        const email = body.forgotEmail || '';

        const data = await forwardMultipart(`${API_BASE}/resend_otp`, {
          user_email: email,
        });

        return res.json({
          status: 'success',
          message: data.message,
        });
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // UPDATE PASSWORD (forgot password)
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'pwd': {
        const user_email = req.cookies.reset_email || '';
        const user_password = body.newPassword || '';

        if (!user_email || !user_password) {
          return res.json({ status: 'error', message: 'Email or password missing.' });
        }

        const data = await forwardMultipart(`${API_BASE}/forgot_password`, {
          user_email,
          new_password: user_password,
        });

        return res.json(data);
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // CONTACT FORM
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'contact': {
        const name = body.name || '';
        const email = body.email || '';
        const subject = body.subject || '';
        const message = body.message || '';

        const data = await forwardMultipart(`${API_BASE}/save_contact_info`, {
          name,
          email,
          subject,
          message,
        });

        return res.json(data);
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // CHECK USERNAME
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'checkUserName': {
        const userName = body.userName || '';

        const data = await forwardMultipart(`${API_BASE}/check_any`, {
          username: userName,
        });

        return res.json(data);
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // CHECK USER EMAIL
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'checkUserEmail': {
        const user_email = body.user_email || '';

        const data = await forwardMultipart(`${API_BASE}/check_any`, {
          user_email,
        });

        return res.json(data);
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // CHECK USER MOBILE NUMBER
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'checkUserNumber': {
        const user_mobile = body.user_mobile || '';

        const data = await forwardMultipart(`${API_BASE}/check_any`, {
          user_mobile,
        });

        return res.json(data);
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // CREATE ORDER (Razorpay)
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'create_order': {
        const username = body.username || '';
        const amount = body.amount || '';
        const plan_name = body.plan_name || '';

        if (!username || !amount || !plan_name) {
          return res.json({ status: 'error', message: 'Missing parameters' });
        }

        // Store in cookies (1 hour expiry)
        const cookieOpts = { maxAge: 3600 * 1000, httpOnly: false, path: '/' };
        res.cookie('username', username, cookieOpts);
        res.cookie('plan_name', plan_name, cookieOpts);

        const data = await forwardMultipart(`${API_BASE}/create_order`, {
          username,
          amount,
          plan_name,
        });

        // Also store order_id in cookie
        if (data && data.order_id) {
          res.cookie('order_id', data.order_id, cookieOpts);
        }

        return res.json(data);
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // VERIFY PAYMENT (Razorpay)
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'verify_payment': {
        const username = req.cookies.username || '';
        const plan_name = req.cookies.plan_name || 'edge';
        const razorpay_order_id = body.razorpay_order_id || '';
        const razorpay_payment_id = body.razorpay_payment_id || '';
        const razorpay_signature = body.razorpay_signature || '';

        if (!razorpay_order_id || !razorpay_payment_id || !razorpay_signature) {
          return res.json({ status: 'error', message: 'Missing Razorpay fields' });
        }

        // Step 1: Verify payment
        const verification = await forwardMultipart(`${API_BASE}/verify_payment`, {
          razorpay_order_id,
          razorpay_payment_id,
          razorpay_signature,
        });

        const isSuccess = verification && verification.status === 'success';
        const payment_status = isSuccess ? 'paid' : 'failed';

        // Step 2: Set plan
        const planResponse = await forwardMultipart(`${API_BASE}/set_plan`, {
          username,
          plan_name,
          order_id: razorpay_order_id,
          payment_status,
        });

        return res.json({
          status: isSuccess ? 'success' : 'fail',
          verification_message: verification.message || '',
          plan_response: planResponse,
        });
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // USER INFO
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'userinfo': {
        const username = req.cookies.username || '';
        const user_token = req.cookies.user_token || '';

        if (!username || !user_token) {
          return res.json({ status: 'error', message: 'Missing cookie data' });
        }

        const data = await forwardMultipart(`${API_BASE}/get_user_info`, {
          username,
          user_token,
        });

        return res.json(data);
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // HIT URL (Analyze stock - live)
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'hit_url': {
        const query = body.query || '';
        const res_type = body.res_type || '';
        const username = req.cookies.username || '';
        const user_token = req.cookies.user_token || '';

        if (!username || !user_token) {
          return res.json({
            status: 'error',
            message: 'Missing cookie data',
            debug: 'Cookie variables not found',
          });
        }

        const data = await forwardMultipart(`${ANALYZE_BASE}/analyze`, {
          query,
          res_type,
          username,
          user_token,
        });

        return res.json(data);
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // GET USER FEEDBACK
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'get_user_feedback': {
        const username = req.cookies.username || '';
        const user_token = req.cookies.user_token || '';

        const data = await forwardPost(`${API_BASE}/get_user_feedback`, {
          username,
          user_token,
        });

        return res.json(data);
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // ANALYZE (demo hardcoded response)
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'analyze_new':
      case 'analyze': {
        // These returned hardcoded demo data in the PHP version.
        // Forward to the real analyze endpoint instead.
        const query = body.query || '';
        const res_type = body.res_type || '';

        const data = await forwardMultipart(`${ANALYZE_BASE}/analyze`, {
          query,
          res_type,
        });

        return res.json(data);
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // ANALYZE NULL (fallback response)
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'analyze_null': {
        const result = {
          price: null,
          price_change: null,
          response: ' **I Can Help You Buy Only Trade Shares.**  \n  ',
          stock_name: null,
          trade_records: null,
          user_prompt: 'can i buy tata motors',
        };

        return res.status(201).json({
          status: 1,
          statusCode: 201,
          message: 'Data Fetched',
          result,
        });
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // REGISTER FORM DATA (legacy)
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      case 'register_form_data': {
        // This was a direct DB insert in PHP. Since we don't have
        // a direct DB connection in this Node proxy, forward to
        // external API or return success placeholder.
        return res.status(201).json({
          status: 1,
          statusCode: 201,
          message: 'Insert Success',
          result: { value: '1' },
        });
      }

      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      // DEFAULT
      // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      default:
        return res.status(400).json({ error: 'Bad Request', message: `Unknown key: ${key}` });
    }
  } catch (error) {
    console.error(`[POST /${key}] Error:`, error.message);
    return res.status(500).json({
      status: 'error',
      message: error.response?.data?.message || error.message || 'Internal server error',
    });
  }
});

module.exports = router;
