import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import '../styles/ProfilePage.css';

const ProfilePage = () => {
  const { user, isLoggedIn, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('account');
  const [notifications, setNotifications] = useState({ email: true, price: true, news: false });

  const username = user?.username || 'Guest';
  const initials = username.slice(0, 2).toUpperCase();

  const planBadge = { label: 'Free', color: '#888' };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const tabs = [
    { id: 'account', label: 'Account', icon: '👤' },
    { id: 'plan', label: 'Plan & Billing', icon: '💳' },
    { id: 'wallet', label: 'Wallet', icon: '💰' },
    { id: 'notifications', label: 'Notifications', icon: '🔔' },
    { id: 'security', label: 'Security', icon: '🔒' },
  ];

  return (
    <div className={`profile-page ${isDark ? 'dark' : 'light'}`}>
      {/* Top Bar */}
      <header className="profile-topbar">
        <button className="profile-back-btn" onClick={() => navigate('/')}>
          ← Back to EvenStocks
        </button>
        <span className="profile-topbar-title">Profile & Settings</span>
        <button className="profile-theme-btn" onClick={toggleTheme}>
          {isDark ? '☀️' : '🌙'}
        </button>
      </header>

      <div className="profile-layout">
        {/* Sidebar */}
        <aside className="profile-sidebar">
          {/* User Card */}
          <div className="profile-user-card">
            <div className="profile-avatar">{initials}</div>
            <div className="profile-user-info">
              <div className="profile-username">{username}</div>
              <span className="profile-plan-badge">{planBadge.label}</span>
            </div>
          </div>

          <nav className="profile-nav">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`profile-nav-btn ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="profile-nav-icon">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>

          <button className="profile-logout-btn" onClick={handleLogout}>
            ↩ Sign Out
          </button>
        </aside>

        {/* Main Content */}
        <main className="profile-main">
          {/* Account Tab */}
          {activeTab === 'account' && (
            <div className="profile-section">
              <h2 className="profile-section-title">Account Details</h2>
              <div className="profile-card">
                <div className="profile-avatar-large">{initials}</div>
                <div className="profile-field-group">
                  <div className="profile-field">
                    <label>Username</label>
                    <div className="profile-field-value">{username}</div>
                  </div>
                  <div className="profile-field">
                    <label>Email</label>
                    <div className="profile-field-value">{user?.email || `${username.toLowerCase()}@example.com`}</div>
                  </div>
                  <div className="profile-field">
                    <label>Member Since</label>
                    <div className="profile-field-value">April 2025</div>
                  </div>
                  <div className="profile-field">
                    <label>Plan</label>
                    <div className="profile-field-value">
                      <span className="profile-plan-badge">{planBadge.label}</span>
                    </div>
                  </div>
                </div>
                <button className="profile-action-btn" onClick={() => navigate('/checkout')}>
                  Upgrade to Pro →
                </button>
              </div>
            </div>
          )}

          {/* Plan & Billing */}
          {activeTab === 'plan' && (
            <div className="profile-section">
              <h2 className="profile-section-title">Plan & Billing</h2>
              <div className="profile-plan-grid">
                {[
                  { name: 'Free', price: '₹0', features: ['10 AI queries/day', 'Basic stock data', 'Community access'], current: true },
                  { name: 'Pro', price: '₹499/mo', features: ['Unlimited AI queries', 'Full financial data', 'Portfolio tracking', 'Priority support'], current: false },
                  { name: 'Elite', price: '₹999/mo', features: ['Everything in Pro', 'Real-time alerts', 'Advanced screener', 'API access'], current: false },
                ].map(plan => (
                  <div key={plan.name} className={`profile-plan-card ${plan.current ? 'current' : ''}`}>
                    <div className="plan-header">
                      <span className="plan-name">{plan.name}</span>
                      {plan.current && <span className="plan-current-badge">Current</span>}
                    </div>
                    <div className="plan-price">{plan.price}</div>
                    <ul className="plan-features">
                      {plan.features.map((f, i) => <li key={i}>✓ {f}</li>)}
                    </ul>
                    {!plan.current && (
                      <button className="plan-upgrade-btn" onClick={() => navigate('/checkout')}>
                        Upgrade
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Wallet */}
          {activeTab === 'wallet' && (
            <div className="profile-section">
              <h2 className="profile-section-title">Wallet & Credits</h2>
              <div className="profile-wallet-grid">
                <div className="profile-card wallet-balance-card">
                  <div className="wallet-label">Available Credits</div>
                  <div className="wallet-balance">₹0.00</div>
                  <button className="profile-action-btn">Add Credits</button>
                </div>
                <div className="profile-card wallet-balance-card">
                  <div className="wallet-label">AI Queries Used Today</div>
                  <div className="wallet-balance">0 / 10</div>
                  <div className="wallet-progress-bar"><div className="wallet-progress-fill" style={{width:'0%'}}></div></div>
                </div>
              </div>
              <div className="profile-card" style={{marginTop:'16px'}}>
                <div className="profile-section-title" style={{fontSize:'15px',marginBottom:'12px'}}>Transaction History</div>
                <div className="wallet-empty">No transactions yet</div>
              </div>
            </div>
          )}

          {/* Notifications */}
          {activeTab === 'notifications' && (
            <div className="profile-section">
              <h2 className="profile-section-title">Notification Preferences</h2>
              <div className="profile-card">
                {[
                  { key: 'email', label: 'Email Notifications', desc: 'Receive market summaries and alerts via email' },
                  { key: 'price', label: 'Price Alerts', desc: 'Get notified when watchlist stocks hit your target' },
                  { key: 'news', label: 'Market News', desc: 'Daily market news digest' },
                ].map(item => (
                  <div key={item.key} className="notification-row">
                    <div>
                      <div className="notif-label">{item.label}</div>
                      <div className="notif-desc">{item.desc}</div>
                    </div>
                    <button
                      className={`toggle-btn ${notifications[item.key] ? 'on' : 'off'}`}
                      onClick={() => setNotifications(prev => ({...prev, [item.key]: !prev[item.key]}))}
                    >
                      <span className="toggle-thumb"></span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Security */}
          {activeTab === 'security' && (
            <div className="profile-section">
              <h2 className="profile-section-title">Security</h2>
              <div className="profile-card">
                <div className="security-row">
                  <div>
                    <div className="security-label">Password</div>
                    <div className="security-desc">Last changed: Never</div>
                  </div>
                  <button className="profile-action-btn-sm">Change Password</button>
                </div>
                <div className="security-row">
                  <div>
                    <div className="security-label">Two-Factor Authentication</div>
                    <div className="security-desc">Add an extra layer of security</div>
                  </div>
                  <button className="profile-action-btn-sm">Enable 2FA</button>
                </div>
                <div className="security-row danger-row">
                  <div>
                    <div className="security-label" style={{color:'#e53e3e'}}>Delete Account</div>
                    <div className="security-desc">Permanently delete your account and all data</div>
                  </div>
                  <button className="profile-danger-btn-sm">Delete</button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default ProfilePage;
