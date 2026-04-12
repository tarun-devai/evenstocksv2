import React, { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { checkUserEmail, loginUser, sendOtp, validateOtp, updatePassword } from '../services/api';
import '../styles/LoginPage.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  // Form states
  const [view, setView] = useState('login'); // login | forgot | otp | newPassword
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginEmailValid, setLoginEmailValid] = useState(null);
  const [loginEmailMsg, setLoginEmailMsg] = useState('');
  const [loginMessage, setLoginMessage] = useState('');
  const [signinDisabled, setSigninDisabled] = useState(true);
  const [showPassword, setShowPassword] = useState(false);

  // Forgot password
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotEmailValid, setForgotEmailValid] = useState(null);
  const [forgotEmailMsg, setForgotEmailMsg] = useState('');
  const [sendOtpDisabled, setSendOtpDisabled] = useState(true);

  // OTP
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [otpMessage, setOtpMessage] = useState('');
  const [resendTimer, setResendTimer] = useState(0);
  const otpRefs = useRef([]);

  // New Password
  const [newPassword, setNewPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [passwordMsg, setPasswordMsg] = useState('');
  const [pwValidations, setPwValidations] = useState({ lower: false, upper: false, number: false, special: false, length: false });

  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  // Login email validation
  const handleLoginEmailChange = async (value) => {
    setLoginEmail(value);
    setSigninDisabled(true);
    if (!value.trim()) { setLoginEmailValid(null); setLoginEmailMsg(''); return; }
    if (!emailPattern.test(value.trim())) { setLoginEmailValid(false); setLoginEmailMsg('Invalid Email!'); return; }
    setLoginEmailMsg('');
    setLoginEmailValid(null);
    try {
      const data = await checkUserEmail(value.trim());
      if (data.found === 1) { setLoginEmailValid(true); setLoginEmailMsg('Email is valid'); setSigninDisabled(false); }
      else { setLoginEmailValid(false); setLoginEmailMsg("Email doesn't exist!"); }
    } catch { setLoginEmailValid(false); setLoginEmailMsg('Server error. Try again.'); }
  };

  // Login submit
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginMessage('');
    try {
      const data = await loginUser(loginEmail, loginPassword);
      if (data.status === 1 || data.status === 'success') {
        login(data.username || loginEmail, data.token || 'session');
        navigate('/admins');
      } else {
        setLoginMessage(data.message || 'Login failed. Check your credentials.');
      }
    } catch { setLoginMessage('Server error. Try again.'); }
  };

  // Forgot email validation
  const handleForgotEmailChange = async (value) => {
    setForgotEmail(value);
    setSendOtpDisabled(true);
    if (!value.trim()) { setForgotEmailValid(null); setForgotEmailMsg(''); return; }
    if (!emailPattern.test(value.trim())) { setForgotEmailValid(false); setForgotEmailMsg('Invalid Email!'); return; }
    setForgotEmailMsg('');
    try {
      const data = await checkUserEmail(value.trim());
      if (data.found === 0) { setForgotEmailValid(false); setForgotEmailMsg("Email doesn't exist!"); }
      else { setForgotEmailValid(true); setForgotEmailMsg(''); setSendOtpDisabled(false); }
    } catch { setForgotEmailValid(false); setForgotEmailMsg('Server error.'); }
  };

  // Send OTP
  const handleSendOtp = async () => {
    setSendOtpDisabled(true);
    try {
      const data = await sendOtp(forgotEmail);
      if (data.status === 1) { setView('otp'); }
      else { setForgotEmailMsg(data.message || 'Failed to send OTP.'); }
    } catch { alert('Failed to send OTP.'); }
    setSendOtpDisabled(false);
  };

  // OTP input handling
  const handleOtpChange = (index, value) => {
    const v = value.replace(/\D/g, '');
    const newDigits = [...otpDigits];
    newDigits[index] = v;
    setOtpDigits(newDigits);
    if (v && index < 5) otpRefs.current[index + 1]?.focus();
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const paste = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '').slice(0, 6);
    const newDigits = [...otpDigits];
    paste.split('').forEach((char, i) => { if (i < 6) newDigits[i] = char; });
    setOtpDigits(newDigits);
    if (paste.length > 0) otpRefs.current[Math.min(paste.length - 1, 5)]?.focus();
  };

  // Verify OTP
  const handleVerifyOtp = async () => {
    const otp = otpDigits.join('');
    if (otp.length !== 6) { setOtpMessage('Please enter the complete 6-digit OTP.'); return; }
    try {
      const data = await validateOtp(forgotEmail, otp);
      if (data.message?.toLowerCase().includes('success')) { setView('newPassword'); }
      else { setOtpMessage(data.message || 'Invalid OTP.'); }
    } catch { setOtpMessage('Something went wrong.'); }
  };

  // Resend OTP
  const handleResendOtp = async () => {
    if (resendTimer > 0) return;
    setResendTimer(60);
    const interval = setInterval(() => {
      setResendTimer((prev) => { if (prev <= 1) { clearInterval(interval); return 0; } return prev - 1; });
    }, 1000);
    try { await sendOtp(forgotEmail); } catch {}
  };

  // Password validation
  const handleNewPasswordChange = (value) => {
    setNewPassword(value);
    const v = {
      lower: /[a-z]/.test(value), upper: /[A-Z]/.test(value),
      number: /[0-9]/.test(value), special: /[@$!%*?&]/.test(value), length: value.length >= 8,
    };
    setPwValidations(v);
  };

  const allPwValid = pwValidations.lower && pwValidations.upper && pwValidations.number && pwValidations.special && pwValidations.length;

  // Update password
  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    if (!allPwValid) return;
    try {
      const data = await updatePassword(forgotEmail, newPassword);
      setPasswordMsg(data.message || 'Password updated!');
      if (data.status === 1 || data.message?.toLowerCase().includes('success')) {
        setTimeout(() => setView('login'), 2000);
      }
    } catch { setPasswordMsg('Error updating password.'); }
  };

  return (
    <div className="login-page-container">
      <div className="container">
        {/* Left Section */}
        <div className="left-section">
          <div className="logo-section">
            <Link to="/"><img src="/assets/img/botimg.png" alt="EvenStocks logo" className="logo-img" /></Link>
          </div>
          <h1>Welcome Back</h1>
          <button className="sign-in-btn" onClick={() => navigate('/signup')}>SIGN UP</button>
          <div className="image-section">
            <img src="/assets/img/login.png" alt="Login illustration" className="below-button-img" />
          </div>
        </div>

        {/* Right Section */}
        <div className="right-section">
          {/* Login Form */}
          {view === 'login' && (
            <form onSubmit={handleLoginSubmit} id="loginForm">
              <div className="input-group">
                <input
                  type="email" placeholder="Email" required value={loginEmail}
                  onChange={(e) => handleLoginEmailChange(e.target.value)}
                  className={loginEmailValid === true ? 'valid' : loginEmailValid === false ? 'invalid' : ''}
                />
                {loginEmailMsg && <span className="error-message" style={{ color: loginEmailValid ? 'green' : 'red' }}>{loginEmailMsg}</span>}
              </div>
              <div className="input-group">
                <input
                  type={showPassword ? 'text' : 'password'} placeholder="Password" required
                  value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)}
                />
                {loginPassword && (
                  <span className="toggle-password" style={{ display: 'block' }} onClick={() => setShowPassword(!showPassword)}>
                    <i className={`fas ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                  </span>
                )}
              </div>
              <div className="forgot-password">
                <a href="#" onClick={(e) => { e.preventDefault(); setView('forgot'); }}>Forgot Password?</a>
              </div>
              <div style={{ textAlign: 'center' }}>
                <button type="submit" className="sign-up-btn" disabled={signinDisabled}>SIGN IN</button>
                {loginMessage && <div style={{ marginTop: '10px', fontSize: '14px', color: 'red' }}>{loginMessage}</div>}
              </div>
            </form>
          )}

          {/* Forgot Password Form */}
          {view === 'forgot' && (
            <form>
              <h2>Reset Password</h2>
              <p>Enter your email to receive OTP.</p>
              <div className="input-group">
                <input
                  type="email" placeholder="Email" required value={forgotEmail}
                  onChange={(e) => handleForgotEmailChange(e.target.value)}
                  className={forgotEmailValid === true ? 'valid' : forgotEmailValid === false ? 'invalid' : ''}
                />
                {forgotEmailMsg && <span className="error-message" style={{ color: forgotEmailValid ? 'green' : 'red' }}>{forgotEmailMsg}</span>}
              </div>
              <button type="button" className="sign-up-btn" disabled={sendOtpDisabled} onClick={handleSendOtp}>Send OTP</button>
            </form>
          )}

          {/* OTP Form */}
          {view === 'otp' && (
            <div id="otpForm" style={{ textAlign: 'center' }}>
              <h2>Verify OTP</h2>
              <p>Enter the 6-digit OTP sent to your email.</p>
              <div className="otp-input-group" style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '20px' }}>
                {otpDigits.map((digit, i) => (
                  <input
                    key={i} type="text" maxLength="1" className="otp-digit" value={digit}
                    ref={(el) => (otpRefs.current[i] = el)}
                    onChange={(e) => handleOtpChange(i, e.target.value)}
                    onKeyDown={(e) => handleOtpKeyDown(i, e)}
                    onPaste={i === 0 ? handleOtpPaste : undefined}
                    inputMode="numeric"
                  />
                ))}
              </div>
              {otpMessage && <div style={{ color: 'red', fontSize: '14px', marginBottom: '10px' }}>{otpMessage}</div>}
              <button type="button" className="sign-up-btn" onClick={handleVerifyOtp}>Verify OTP</button>
              <p>
                <a href="#" onClick={(e) => { e.preventDefault(); handleResendOtp(); }} style={{ color: resendTimer > 0 ? 'gray' : '#02634d', pointerEvents: resendTimer > 0 ? 'none' : 'auto' }}>
                  {resendTimer > 0 ? `Resend OTP in ${resendTimer}s` : 'Resend OTP'}
                </a>
              </p>
            </div>
          )}

          {/* New Password Form */}
          {view === 'newPassword' && (
            <form onSubmit={handleUpdatePassword}>
              <h2>Set New Password</h2>
              <p>Create a new strong password</p>
              <div className="input-group">
                <input
                  type={showNewPassword ? 'text' : 'password'} placeholder="New Password" required
                  value={newPassword} onChange={(e) => handleNewPasswordChange(e.target.value)}
                />
                {newPassword && (
                  <span className="toggle-password" style={{ display: 'block' }} onClick={() => setShowNewPassword(!showNewPassword)}>
                    <i className={`fas ${showNewPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                  </span>
                )}
              </div>
              {newPassword && !allPwValid && (
                <div id="passwordMessage" style={{ display: 'block' }}>
                  <p className={pwValidations.lower ? 'valid' : 'invalid'}>A <strong>lowercase</strong> letter</p>
                  <p className={pwValidations.upper ? 'valid' : 'invalid'}>An <strong>uppercase</strong> letter</p>
                  <p className={pwValidations.number ? 'valid' : 'invalid'}>A <strong>number</strong></p>
                  <p className={pwValidations.special ? 'valid' : 'invalid'}>A <strong>special character</strong></p>
                  <p className={pwValidations.length ? 'valid' : 'invalid'}>Minimum <strong>8 characters</strong></p>
                </div>
              )}
              {passwordMsg && <div className="form-message" style={{ color: passwordMsg.toLowerCase().includes('success') ? 'green' : 'red' }}>{passwordMsg}</div>}
              <button type="submit" className="sign-up-btn" disabled={!allPwValid}>Update Password</button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
