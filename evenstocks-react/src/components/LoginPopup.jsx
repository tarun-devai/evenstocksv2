import React from 'react';
import { Link } from 'react-router-dom';

const LoginPopup = ({ show, onClose }) => {
  if (!show) return null;

  return (
    <>
      <div
        id="modal-overlay"
        onClick={onClose}
        style={{
          position: 'fixed', top: 0, left: 0, zIndex: 1999,
          width: '100%', height: '100%', backgroundColor: 'rgba(0, 0, 0, 0.5)',
        }}
      />
      <div
        id="login-popup"
        style={{
          display: 'block', position: 'fixed', zIndex: 2000, top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)', background: '#ffffff', borderRadius: '18px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.2)', padding: '30px 25px', width: '90%',
          maxWidth: '400px', textAlign: 'center', fontFamily: "'Segoe UI', sans-serif",
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute', top: '12px', right: '15px', background: 'transparent',
            border: 'none', fontSize: '20px', fontWeight: 'bold', color: '#222', cursor: 'pointer',
          }}
        >
          &times;
        </button>
        <h2 style={{ marginBottom: '10px', color: '#022b1d' }}>
          Welcome to <span style={{ color: '#02634D' }}>EvenStocks</span>
        </h2>
        <p style={{ marginBottom: '25px', color: '#333' }}>
          Sign Up to access premium insights and trading tools.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '15px', flexWrap: 'wrap' }}>
          <Link
            to="/login"
            style={{
              background: 'linear-gradient(135deg, #2ca089, #012c3b)', color: 'white',
              padding: '10px 24px', borderRadius: '10px', textDecoration: 'none', fontWeight: 600,
            }}
          >
            Login
          </Link>
          <Link
            to="/signup"
            style={{
              background: 'linear-gradient(135deg, #34d058, #017a39)', color: 'white',
              padding: '10px 24px', borderRadius: '10px', textDecoration: 'none', fontWeight: 600,
            }}
          >
            Sign Up
          </Link>
        </div>
      </div>
    </>
  );
};

export default LoginPopup;
