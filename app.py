import io
import base64
import json
import os
import qrcode
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

# Configuration (Uses defaults for local dev; overridable via Env Vars)
BANK_PUBLIC_BASE = os.getenv('BANK_PUBLIC_BASE', 'http://localhost:5001')
MERCHANT_ACCOUNT = os.getenv('MERCHANT_ACCOUNT', 'bloomcart-flowers')

# Local order state dictionary for frontend testing
LOCAL_ORDERS = {}

# Catalog (Group 4: Flower Shop)
PRODUCTS = [
    {"id": 1, "name": "Rose Bouquet", "price": 25.00},
    {"id": 2, "name": "Tulip Arrangement", "price": 18.50},
    {"id": 3, "name": "Orchid Pot", "price": 30.00},
    {"id": 4, "name": "Sunflower Bundle", "price": 15.00},
    {"id": 5, "name": "Custom Gift Card", "price": 5.00}
]


def generate_qr_base64(qr_data):
    """Generates a QR code image as a Base64 string in memory."""
    # Convert dict to JSON string if passed as a dict, or use string as-is
    if isinstance(qr_data, dict):
        qr_data = json.dumps(qr_data)

    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=3
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"


@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200


@app.route('/')
def index():
    return render_template('index.html', products=PRODUCTS, merchant=MERCHANT_ACCOUNT)


@app.route('/checkout/<int:product_id>', methods=['POST'])
def checkout(product_id):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return "Product not found", 404

    order_id = f"ORD-{os.urandom(3).hex().upper()}"
    amount = product["price"]

    # -------------------------------------------------------------
    # FOR TESTING: Encode a direct YouTube link into the QR code!
    # When scanned by a smartphone camera, it opens YouTube directly.
    # -------------------------------------------------------------
    qr_data = f"https://www.youtube.com/watch?v=dQw4w9WgXcQ&order_id={order_id}&amount={amount}"

    qr_image = generate_qr_base64(qr_data)

    bank_confirm_url = f"{BANK_PUBLIC_BASE}/pay-confirm?order_id={order_id}&amount={amount}&merchant={MERCHANT_ACCOUNT}"
    LOCAL_ORDERS[order_id] = {"amount": amount, "status": "PENDING"}

    return render_template(
        'checkout.html',
        order_id=order_id,
        amount=amount,
        product_name=product["name"],
        qr_image=qr_image,
        bank_confirm_url=bank_confirm_url,
        status="PENDING"
    )


@app.route('/order/<order_id>/status')
def order_status(order_id):
    """Endpoint for JavaScript frontend to poll order status."""
    order = LOCAL_ORDERS.get(order_id, {"status": "NOT_FOUND"})
    return jsonify({"order_id": order_id, "status": order.get("status")})


@app.route('/callback/payment', methods=['POST'])
def payment_callback():
    """Callback endpoint hit by the Banking app upon successful payment."""
    data = request.get_json() or {}
    order_id = data.get('order_id')

    if order_id in LOCAL_ORDERS:
        LOCAL_ORDERS[order_id]['status'] = 'PAID'
        return jsonify({"status": "SUCCESS", "message": "Order marked as PAID"}), 200

    return jsonify({"status": "FAILED", "message": "Order not found"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)