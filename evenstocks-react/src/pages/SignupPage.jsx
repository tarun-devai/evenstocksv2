import React, { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { checkUserEmail, checkUserName, checkUserNumber, signupUser, validateOtp } from '../services/api';
import '../styles/SignupPage.css';

const SignupPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { isDark } = useTheme();

  const [view, setView] = useState('signup'); // signup | otp
  const [form, setForm] = useState({ fullName: '', age: '', signupEmail: '', mobile: '', userName: '', signupPassword: '', confirmPassword: '' });
  const [errors, setErrors] = useState({});
  const [validFields, setValidFields] = useState({});
  const [termsChecked, setTermsChecked] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [pwValidations, setPwValidations] = useState({ lower: false, upper: false, number: false, special: false, length: false });
  const [showPwMsg, setShowPwMsg] = useState(false);

  // OTP
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [otpMessage, setOtpMessage] = useState('');
  const [resendTimer, setResendTimer] = useState(0);
  const otpRefs = useRef([]);
  const [canSubmit, setCanSubmit] = useState(true);

  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;

  const setError = (field, msg) => setErrors((prev) => ({ ...prev, [field]: msg }));
  const clearError = (field) => setErrors((prev) => { const n = { ...prev }; delete n[field]; return n; });
  const setValid = (field, v) => setValidFields((prev) => ({ ...prev, [field]: v }));

  const updateForm = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  // Field handlers
  const handleFullName = (value) => {
    const v = value.replace(/[^a-zA-Z\s]/g, '');
    updateForm('fullName', v);
    if (v.trim()) { clearError('fullName'); setValid('fullName', true); }
    else { setValid('fullName', false); }
  };

  const handleAge = (value) => {
    const v = value.replace(/\D/g, '').slice(0, 3);
    updateForm('age', v);
    if (v) { clearError('age'); setValid('age', true); } else { setValid('age', false); }
  };

  const handleEmail = async (value) => {
    updateForm('signupEmail', value);
    if (!value.trim()) { clearError('signupEmail'); setValid('signupEmail', false); return; }
    if (!emailPattern.test(value.trim())) { setError('signupEmail', 'Invalid Email!'); setValid('signupEmail', false); return; }
    clearError('signupEmail');
    try {
      const data = await checkUserEmail(value.trim());
      if (data.found === 1) { setError('signupEmail', 'Email already exists!'); setValid('signupEmail', false); }
      else { clearError('signupEmail'); setValid('signupEmail', true); }
    } catch { setValid('signupEmail', false); }
  };

  const handleMobile = async (value) => {
    const v = value.replace(/\D/g, '').slice(0, 10);
    updateForm('mobile', v);
    if (!v) { clearError('mobile'); setValid('mobile', false); return; }
    if (!/^[6-9]\d{9}$/.test(v)) { setError('mobile', 'Enter a valid mobile number!'); setValid('mobile', false); return; }
    clearError('mobile');
    try {
      const data = await checkUserNumber(v);
      const found = data.found !== undefined ? data.found : data.message?.found;
      if (found === 1) { setError('mobile', 'Already Exists'); setValid('mobile', false); }
      else { clearError('mobile'); setValid('mobile', true); }
    } catch { setValid('mobile', false); }
  };

  const handleUserName = async (value) => {
    const v = value.toLowerCase().replace(/[^a-z]/g, '').slice(0, 10);
    updateForm('userName', v);
    if (!v) { clearError('userName'); setValid('userName', false); return; }
    if (v.length < 6) { setError('userName', 'Must be 6 to 10 lowercase characters.'); setValid('userName', false); return; }
    clearError('userName');
    try {
      const data = await checkUserName(v);
      const found = data.found !== undefined ? data.found : data.message?.found;
      if (found === 1) { setError('userName', 'Username already exists!'); setValid('userName', false); }
      else { clearError('userName'); setValid('userName', true); }
    } catch { setValid('userName', false); }
  };

  const handlePassword = (value) => {
    updateForm('signupPassword', value);
    const v = {
      lower: /[a-z]/.test(value), upper: /[A-Z]/.test(value),
      number: /[0-9]/.test(value), special: /[@$!%*?&]/.test(value), length: value.length >= 8,
    };
    setPwValidations(v);
    setShowPwMsg(value.length > 0 && !(v.lower && v.upper && v.number && v.special && v.length));
    if (v.lower && v.upper && v.number && v.special && v.length) { setValid('signupPassword', true); clearError('signupPassword'); }
    else { setValid('signupPassword', false); }
    // Re-validate confirm
    if (form.confirmPassword && form.confirmPassword !== value) { setError('confirmPassword', "Passwords don't match!"); setValid('confirmPassword', false); }
    else if (form.confirmPassword && form.confirmPassword === value) { clearError('confirmPassword'); setValid('confirmPassword', true); }
  };

  const handleConfirmPassword = (value) => {
    updateForm('confirmPassword', value);
    if (value !== form.signupPassword) { setError('confirmPassword', "Passwords don't match!"); setValid('confirmPassword', false); }
    else { clearError('confirmPassword'); setValid('confirmPassword', true); }
  };

  const allValid = validFields.fullName && validFields.age && validFields.signupEmail && validFields.mobile && validFields.userName && validFields.signupPassword && validFields.confirmPassword && termsChecked;

  // Submit signup
  const handleSignupSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit || !allValid) return;
    setCanSubmit(false);
    setTimeout(() => setCanSubmit(true), 30000);
    try {
      const data = await signupUser(form);
      if (data.status === 1 || data.status === 'success') { setView('otp'); }
      else { alert(data.message || 'Signup failed.'); }
    } catch { alert('Server error.'); setCanSubmit(true); }
  };

  // OTP
  const handleOtpChange = (index, value) => {
    const v = value.replace(/\D/g, '');
    const newDigits = [...otpDigits];
    newDigits[index] = v;
    setOtpDigits(newDigits);
    if (v && index < 5) otpRefs.current[index + 1]?.focus();
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) otpRefs.current[index - 1]?.focus();
  };

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const paste = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '').slice(0, 6);
    const newDigits = [...otpDigits];
    paste.split('').forEach((char, i) => { if (i < 6) newDigits[i] = char; });
    setOtpDigits(newDigits);
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    const otp = otpDigits.join('');
    if (otp.length !== 6) { setOtpMessage('Please enter the complete 6-digit OTP.'); return; }
    try {
      const data = await validateOtp(form.signupEmail, otp);
      if (data.status === 1 || data.message?.toLowerCase().includes('success')) {
        login(form.userName, data.token || 'session');
        navigate('/admins');
      } else { setOtpMessage(data.message || 'Invalid OTP.'); }
    } catch { setOtpMessage('Something went wrong.'); }
  };

  const handleResendOtp = () => {
    if (resendTimer > 0) return;
    setResendTimer(60);
    const interval = setInterval(() => {
      setResendTimer((prev) => { if (prev <= 1) { clearInterval(interval); return 0; } return prev - 1; });
    }, 1000);
  };

  const getInputClass = (field) => {
    if (validFields[field] === true) return 'valid';
    if (errors[field]) return 'invalid';
    return '';
  };

  return (
    <div className={`signup-page-container${isDark ? ' signup-dark' : ''}`}>
      <div className="container">
        <div className="left-section">
          <div className="logo-section">
            <Link to="/"><img src="/assets/img/botimg.png" alt="EvenStocks logo" className="logo-img" /></Link>
          </div>
          <h1>Create Account</h1>
          <button className="sign-in-btn" onClick={() => navigate('/login')}>SIGN IN</button>
          <div className="image-section">
            <img src="/assets/img/signup.png" alt="Signup illustration" className="below-button-img" />
          </div>
        </div>

        <div className="right-section">
          {view === 'signup' && (
            <form onSubmit={handleSignupSubmit} id="signupForm">
              <div className="input-group">
                <input type="text" placeholder="Full Name" required value={form.fullName} onChange={(e) => handleFullName(e.target.value)} className={getInputClass('fullName')} />
                {errors.fullName && <div className="error">{errors.fullName}</div>}
              </div>
              <div className="input-group">
                <input type="number" placeholder="Age" required value={form.age} onChange={(e) => handleAge(e.target.value)} className={getInputClass('age')} />
              </div>
              <div className="input-group">
                <input type="email" placeholder="Email" required value={form.signupEmail} onChange={(e) => handleEmail(e.target.value)} className={getInputClass('signupEmail')} />
                {errors.signupEmail && <div className="error">{errors.signupEmail}</div>}
              </div>
              <div className="input-group">
                <input type="tel" placeholder="Mobile Number" required value={form.mobile} onChange={(e) => handleMobile(e.target.value)} className={getInputClass('mobile')} />
                {errors.mobile && <div className="error">{errors.mobile}</div>}
              </div>
              <div className="input-group">
                <input type="text" placeholder="User Name" required value={form.userName} onChange={(e) => handleUserName(e.target.value)} className={getInputClass('userName')} />
                {errors.userName && <div className="error">{errors.userName}</div>}
              </div>
              <div className="input-group">
                <input
                  type={showPassword ? 'text' : 'password'} placeholder="Password" required
                  value={form.signupPassword} onChange={(e) => handlePassword(e.target.value)} className={getInputClass('signupPassword')}
                />
                {form.signupPassword && (
                  <span className="toggle-password" style={{ display: 'block' }} onClick={() => setShowPassword(!showPassword)}>
                    <i className={`fas ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                  </span>
                )}
              </div>
              {showPwMsg && (
                <div id="passwordMessage" style={{ display: 'block' }}>
                  <p className={pwValidations.lower ? 'valid' : 'invalid'}>A <b>lowercase</b> letter</p>
                  <p className={pwValidations.upper ? 'valid' : 'invalid'}>An <b>uppercase</b> letter</p>
                  <p className={pwValidations.number ? 'valid' : 'invalid'}>A <b>number</b></p>
                  <p className={pwValidations.special ? 'valid' : 'invalid'}>A <b>special character</b></p>
                  <p className={pwValidations.length ? 'valid' : 'invalid'}>Minimum <b>8 characters</b></p>
                </div>
              )}
              <div className="input-group">
                <input
                  type={showConfirmPassword ? 'text' : 'password'} placeholder="Confirm Password" required
                  disabled={!validFields.signupPassword} value={form.confirmPassword}
                  onChange={(e) => handleConfirmPassword(e.target.value)} className={getInputClass('confirmPassword')}
                />
                {form.confirmPassword && (
                  <span className="toggle-password" style={{ display: 'block' }} onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
                    <i className={`fas ${showConfirmPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                  </span>
                )}
                {errors.confirmPassword && <div className="error">{errors.confirmPassword}</div>}
              </div>
              <div className="terms">
                <input type="checkbox" id="termsCheckbox" checked={termsChecked} onChange={(e) => setTermsChecked(e.target.checked)} />
                <label htmlFor="termsCheckbox">I agree to the <Link to="/terms">Terms and Conditions</Link></label>
              </div>
              <button type="submit" className="sign-up-btn" disabled={!allValid || !canSubmit}>SIGN UP</button>
            </form>
          )}

          {view === 'otp' && (
            <div className="otp-form-wrapper">
              <form onSubmit={handleVerifyOtp} id="otpForm">
                <h2>Enter OTP</h2>
                <p>A verification code has been sent to your email address.</p>
                <div className="otp-input-group">
                  <div id="otp-boxes" style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
                    {otpDigits.map((digit, i) => (
                      <input
                        key={i} type="text" maxLength="1" className="otp-digit" value={digit}
                        ref={(el) => (otpRefs.current[i] = el)}
                        onChange={(e) => handleOtpChange(i, e.target.value)}
                        onKeyDown={(e) => handleOtpKeyDown(i, e)}
                        onPaste={i === 0 ? handleOtpPaste : undefined}
                      />
                    ))}
                  </div>
                </div>
                {otpMessage && <div style={{ color: 'red', fontSize: '14px', marginTop: '8px' }}>{otpMessage}</div>}
                <button type="submit" className="sign-up-btn">VERIFY OTP</button>
                <p>
                  <a href="#" onClick={(e) => { e.preventDefault(); handleResendOtp(); }} style={{ color: resendTimer > 0 ? 'gray' : '#02634d' }}>
                    {resendTimer > 0 ? `Resend OTP (${resendTimer}s)` : 'Resend OTP'}
                  </a>
                </p>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
