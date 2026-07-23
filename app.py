import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, OrderTransaction

from seed import seed_users

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'super-secret-flower-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flowershop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

BANK_API_URL = os.getenv('BANK_API_URL', 'http://localhost:5001/api/bank/initiate-payment')

PRODUCTS = [
    {"id": 1, "name": "Rose Bouquet", "price": 25.00},
    {"id": 2, "name": "Tulip Arrangement", "price": 18.50},
    {"id": 3, "name": "Orchid Pot", "price": 30.00},
    {"id": 4, "name": "Sunflower Bundle", "price": 15.00},
]

def seed_db(app):
    seed_users(app)

# --- AUTHENTICATION ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['acct_number'] = user.acct_number
            session['full_name'] = f"{user.first_name} {user.last_name}"
            return redirect(url_for('catalog'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- CATALOG & CART ROUTES ---
# Helper to get total item count in cart
def get_cart_count():
    cart = session.get('cart', {})
    return sum(cart.values())

@app.route('/')
def catalog():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cart_count = get_cart_count()
    return render_template('catalog.html', products=PRODUCTS, cart_count=cart_count)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart = session.get('cart', {})
    str_id = str(product_id)

    # Get quantity from the form input (defaults to 1 if not provided)
    qty = int(request.form.get('quantity', 1))

    cart[str_id] = cart.get(str_id, 0) + qty
    session['cart'] = cart

    flash("Item added to cart!", "success")
    # Redirect back to the catalog/home page instead of cart!
    return redirect(url_for('catalog'))



@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0.0
    for p_id, qty in cart.items():
        prod = next((p for p in PRODUCTS if p['id'] == int(p_id)), None)
        if prod:
            subtotal = prod['price'] * qty
            total += subtotal
            cart_items.append({**prod, 'qty': qty, 'subtotal': subtotal})
    return render_template('cart.html', items=cart_items, total=total)


# --- CHECKOUT & BANK INTEGRATION ---

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('catalog'))

    cart_items = []
    total_amt = 0.0
    for p_id, qty in cart.items():
        prod = next((p for p in PRODUCTS if p['id'] == int(p_id)), None)
        if prod:
            cart_items.append(prod['name'])
            total_amt += prod['price'] * qty

    if request.method == 'POST':
        order_id = f"ORD-{os.urandom(3).hex().upper()}"

        # Save order to DB as PENDING
        new_order = OrderTransaction(
            id=order_id,
            indiv_order_name=json.dumps(list(cart.keys())),
            indiv_order_amt=json.dumps([p['price'] for p in PRODUCTS if str(p['id']) in cart]),
            total_amt=total_amt,
            status='PENDING',
            acct_number=session['acct_number']  # Strict binding!
        )
        db.session.add(new_order)
        db.session.commit()

        # Request Bank API to generate QR Code for this ACCT_NUMBER
        try:
            bank_payload = {
                "order_id": order_id,
                "amount": total_amt,
                "payer_acct_number": session['acct_number']
            }
            # Here Bank will receive payload and create the QR code on their end
            # response = requests.post(BANK_API_URL, json=bank_payload)
        except Exception as e:
            print(f"Bank API Error: {e}")

        # Clear cart after creating order
        session.pop('cart', None)
        return redirect(url_for('checkout_waiting', order_id=order_id))

    return render_template('checkout.html', total=total_amt)


@app.route('/checkout/waiting/<order_id>')
def checkout_waiting(order_id):
    """Waiting page that polls bank payment status."""
    return render_template('waiting.html', order_id=order_id)

@app.route('/order/<order_id>/status')
def order_status(order_id):
    """Endpoint hit by waiting.html JavaScript polling."""
    order = OrderTransaction.query.get(order_id)
    if order:
        return jsonify({"order_id": order_id, "status": order.status})
    return jsonify({"order_id": order_id, "status": "NOT_FOUND"}), 404


@app.route('/callback/payment-status', methods=['POST'])
def payment_callback():
    """Bank calls this webhook when payment is completed on their end."""
    data = request.get_json() or {}
    order_id = data.get('order_id')
    bank_payer_acct = data.get('acct_number')

    order = OrderTransaction.query.get(order_id)
    if not order:
        return jsonify({"status": "ERROR", "message": "Order not found"}), 404

    # STRICT CHECK: Verify Bank Payer ACCT matches Ecommerce Order ACCT
    if order.acct_number != bank_payer_acct:
        order.status = 'FAILED_MISMATCH'
        db.session.commit()
        return jsonify({"status": "REJECTED", "message": "Account number mismatch!"}), 403

    order.status = 'PAID'
    db.session.commit()
    return jsonify({"status": "SUCCESS"}), 200


# --- SUCCESS & RECEIPT ---

@app.route('/success/<order_id>')
def success(order_id):
    order = OrderTransaction.query.get_or_404(order_id)
    return render_template('success.html', order=order)


@app.route('/receipt/<order_id>')
def receipt(order_id):
    order = OrderTransaction.query.get_or_404(order_id)
    user = User.query.filter_by(acct_number=order.acct_number).first()
    return render_template('receipt.html', order=order, user=user)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_db(app)
    app.run(host='0.0.0.0', port=5000, debug=True)