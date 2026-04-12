import React from 'react';
import '../styles/CheckoutPage.css';

const CheckoutPage = () => {
  return (
    <div className="checkout-body">
      <div className="checkout-container">
        <div className="shoppingCart">
          <h1>Shopping Cart</h1>
          <table className="checkout-table">
            <thead>
              <tr>
                <th>Item</th>
                <th className="price">Price</th>
                <th className="subtotal">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="imageTitle">
                  <img
                    src="https://www.sonatawatches.in/dw/image/v2/BKDD_PRD/on/demandware.static/-/Sites-titan-master-catalog/default/dwc041fffc/images/Sonata/Catalog/SP80062KM01W_1.jpg?sw=600&sh=600"
                    alt="Watch"
                  />
                  <p>Rolex Datejust 36mm Steel Watch Diamonds &amp; Emeralds Bezel/Lugs/Gray Diamond Dial</p>
                </td>
                <td className="price">$7,600.00</td>
                <td className="subtotal">$7,600.00</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="orderSummary">
          <h2>Order Summary</h2>
          <div className="totalPrice">
            <p>Subtotal <span>$7,600.00</span></p>
            <p>Shipping <span>$5.00</span></p>
            <p className="total">Order Total <span>$7,605.00</span></p>
          </div>
          <div className="proceed_section">
            <button>PROCEED TO CHECKOUT</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;
