import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/PrivacyTerms.css';

const PrivacyPage = () => {
  return (
    <div className="privacy-terms-page">
      <header className="pt-header">
        <Link to="/" className="back-btn">&larr; Back</Link>
        <div className="pt-header-center">
          <h1>Privacy Policy</h1>
          <p>Last Updated: 6th April 2025</p>
        </div>
      </header>

      <main className="pt-main">
        <section>
          <h2>1. Introduction</h2>
          <p>Welcome to EvenStocks AI ("we," "us," or "our"). This Privacy Policy explains how we collect, use, and protect your data when using our platform.</p>
        </section>

        <section>
          <h2>2. Data We Collect</h2>
          <ul>
            <li><strong>User-Provided Data:</strong> Queries, email addresses, payment details, feedback.</li>
            <li><strong>Automated Data:</strong> IP address, browser type, cookies, usage patterns.</li>
            <li><strong>Third-Party Data:</strong> Financial data from SEBI-approved providers.</li>
          </ul>
        </section>

        <section>
          <h2>3. How We Use Your Data</h2>
          <p>We use your data to provide AI-driven insights, improve our platform, process subscriptions, and comply with legal obligations.</p>
        </section>

        <section>
          <h2>4. Data Sharing</h2>
          <p>We do not sell your data. Limited sharing occurs with payment gateways, cloud services, and when legally required.</p>
        </section>

        <section>
          <h2>5. Security</h2>
          <p>We implement AES-256 encryption, regular audits, and restricted access to protect your data.</p>
        </section>

        <section>
          <h2>6. Your Rights</h2>
          <p>You can access, update, or delete your data, and opt out of marketing emails.</p>
        </section>

        <section>
          <h2>7. Third-Party Links</h2>
          <p>We are not responsible for external sites linked from our platform.</p>
        </section>

        <section>
          <h2>8. Policy Updates</h2>
          <p>Changes will be notified via email or platform alerts. Continued use implies acceptance.</p>
        </section>

        <section>
          <h2>Contact Us</h2>
          <p>For privacy concerns, email <a href="mailto:info@evenstocks.com">info@evenstocks.com</a></p>
        </section>
      </main>
    </div>
  );
};

export default PrivacyPage;
