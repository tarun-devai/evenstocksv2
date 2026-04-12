import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { verifyPayment } from '../services/api';

const RazorpayPayment = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const razorpayId = searchParams.get('razorpay_id') || '';
  const amount = searchParams.get('amount') || '100';
  const orderId = searchParams.get('order_id') || '';

  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = () => {
      const options = {
        key: razorpayId,
        amount: parseInt(amount) * 100,
        currency: 'INR',
        name: 'Even Stocks',
        description: 'Test Transaction',
        order_id: orderId,
        handler: async (response) => {
          try {
            const data = await verifyPayment(
              response.razorpay_order_id,
              response.razorpay_payment_id,
              response.razorpay_signature
            );
            if (data.status === 'success') {
              alert('Payment Verified!');
              navigate('/admins');
            } else {
              alert('Verification failed: ' + (data.message || ''));
            }
          } catch (err) {
            alert('Network error.');
            console.error(err);
          }
        },
        theme: { color: '#3399cc' },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    };
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, [razorpayId, amount, orderId, navigate]);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <p>Loading payment gateway...</p>
    </div>
  );
};

export default RazorpayPayment;
