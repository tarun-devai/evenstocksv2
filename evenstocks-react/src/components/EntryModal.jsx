import React from 'react';
import { useNavigate } from 'react-router-dom';

const EntryModal = ({ show, onClose }) => {
  const navigate = useNavigate();

  if (!show) return null;

  return (
    <div className="glass-modal-overlay" style={{ display: 'flex' }}>
      <div className="glass-modal">
        <div className="glass-modal-header">
          <span className="glass-modal-title">
            <span className="glass-icon">&#x1F514;</span> Welcome to InvestBot
          </span>
          <span className="glass-modal-close" onClick={onClose}>&times;</span>
        </div>
        <div className="glass-modal-body">
          <h3 className="glass-modal-heading">Enjoy 10 Free Tokens</h3>
          <p className="glass-modal-text">
            Sign in now to receive <strong>10 free search tokens</strong> and start exploring AI-powered insights with InvestBot.
          </p>
        </div>
        <div className="glass-modal-footer">
          <button className="glass-btn-primary" onClick={() => navigate('/login')}>Sign In</button>
          <button className="glass-btn-outline" onClick={onClose}>Maybe Later</button>
        </div>
      </div>
    </div>
  );
};

export default EntryModal;
