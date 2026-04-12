import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/PrivacyTerms.css';

const TermsPage = () => {
  return (
    <div className="privacy-terms-page">
      <header className="pt-header">
        <Link to="/" className="back-btn">&larr; Back</Link>
        <div className="pt-header-center">
          <h1>Terms of Use</h1>
          <p>Last Updated: 6th April 2025</p>
        </div>
      </header>

      <main className="pt-main">
        <section>
          <h2>1. Acceptance</h2>
          <p>By using EvenStocks AI, you agree to these Terms. If you disagree, refrain from accessing the platform.</p>
        </section>

        <section>
          <h2>2. Eligibility</h2>
          <ul>
            <li><strong>Age Requirement:</strong> Users must be 18+ or have legal guardian consent.</li>
            <li><strong>Account Security:</strong> Subscribers are responsible for account security and accurate payment details.</li>
          </ul>
        </section>

        <section>
          <h2>3. Services</h2>
          <ul>
            <li><strong>AI Recommendations:</strong> EvenStocks AI provides data-driven insights but does not guarantee returns.</li>
            <li><strong>Real-Time Data:</strong> Sourced from third parties; delays or inaccuracies may occur.</li>
            <li><strong>Subscription Plans:</strong> Auto-renew unless canceled 7 days before billing cycle.</li>
          </ul>
        </section>

        <section>
          <h2>4. Prohibited Activities</h2>
          <ul>
            <li>Reverse-engineering, scraping, or exploiting the platform for commercial gain.</li>
            <li>Using AI outputs for illegal trading practices (e.g., market manipulation).</li>
            <li>Sharing login credentials or violating Indian IT Act 2000.</li>
          </ul>
        </section>

        <section>
          <h2>5. Intellectual Property</h2>
          <ul>
            <li>All content (charts, reports, algorithms) is owned by EvenStocks AI.</li>
            <li>Limited, non-commercial use permitted with proper attribution.</li>
          </ul>
        </section>

        <section>
          <h2>6. Disclaimers</h2>
          <ul>
            <li><strong>No Financial Advice:</strong> Insights are informational, not a substitute for professional advice.</li>
            <li><strong>"As-Is" Basis:</strong> We disclaim warranties for uptime, accuracy, or fitness for purpose.</li>
          </ul>
        </section>

        <section>
          <h2>7. Limitation of Liability</h2>
          <p>We are not liable for:</p>
          <ul>
            <li>Investment losses from using our platform.</li>
            <li>Third-party data errors or service interruptions.</li>
          </ul>
        </section>

        <section>
          <h2>8. Termination</h2>
          <p>We reserve the right to suspend accounts for breaches, fraud, or abusive behavior.</p>
        </section>

        <section>
          <h2>9. Governing Law</h2>
          <p>Disputes will be resolved under Indian law, with jurisdiction in Mumbai Courts.</p>
        </section>

        <section>
          <h2>10. Updates</h2>
          <p>Revised Terms will be posted on this page.</p>
        </section>

        <section>
          <h2>Contact Us</h2>
          <p>For Terms-related queries, email <a href="mailto:info@evenstocks.com">info@evenstocks.com</a></p>
        </section>
      </main>
    </div>
  );
};

export default TermsPage;
