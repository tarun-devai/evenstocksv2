const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

export const apiPost = async (data) => {
  const response = await fetch(`${API_BASE_URL}/post`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return response.json();
};

export const apiGet = async (method) => {
  const response = await fetch(`${API_BASE_URL}/get?method=${method}`, {
    credentials: 'include',
  });
  return response.json();
};

export const checkUserEmail = async (email) => {
  return apiPost({ key: 'checkUserEmail', user_email: email });
};

export const checkUserName = async (userName) => {
  return apiPost({ key: 'checkUserName', userName });
};

export const checkUserNumber = async (mobile) => {
  return apiPost({ key: 'checkUserNumber', user_mobile: mobile });
};

export const loginUser = async (email, password) => {
  return apiPost({ key: 'login', loginEmail: email, loginPassword: password });
};

export const signupUser = async (formData) => {
  return apiPost({ key: 'signup', ...formData });
};

export const sendOtp = async (email) => {
  return apiPost({ key: 'sendotp', forgotEmail: email });
};

export const validateOtp = async (email, otp) => {
  return apiPost({ key: 'otp_validate', otpEmail: email, otp });
};

export const updatePassword = async (email, password) => {
  return apiPost({ key: 'pwd', forgotEmail: email, newPassword: password });
};

export const submitContact = async (data) => {
  return apiPost({ key: 'contact', ...data });
};

export const createOrder = async (username, amount, planName) => {
  return apiPost({ key: 'create_order', username, amount, plan_name: planName });
};

export const verifyPayment = async (orderId, paymentId, signature) => {
  return apiPost({
    key: 'verify_payment',
    razorpay_order_id: orderId,
    razorpay_payment_id: paymentId,
    razorpay_signature: signature,
  });
};

export const getAllSignedUpUsers = async () => {
  return apiGet('all_signedup_users');
};
