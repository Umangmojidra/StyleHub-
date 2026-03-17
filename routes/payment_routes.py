"""
payment_routes.py - Razorpay Payment Blueprint
Handles: create Razorpay order, verify payment signature, checkout page.
"""
import hmac
import hashlib
import razorpay
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from utils.db import query_db, get_connection
from utils.auth import login_required, get_current_user
from config import Config

payment_bp  = Blueprint('payment', __name__)
rz_client   = razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))


# ─── Checkout Page (address selection + payment) ─────────────
@payment_bp.route('/checkout')
@login_required
def checkout():
    user_id = request.user['user_id']

    # Get cart items
    cart_items = query_db(
        '''SELECT c.cart_id, c.quantity,
                  p.product_id, p.name, p.price, p.discount, p.image, p.stock,
                  ROUND(p.price * (1 - p.discount/100), 2) as effective_price
           FROM cart c JOIN products p ON c.product_id = p.product_id
           WHERE c.user_id = %s''',
        (user_id,)
    )

    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))

    subtotal  = sum(float(i['effective_price']) * i['quantity'] for i in cart_items)
    shipping  = 0 if subtotal >= 999 else 99
    total     = round(subtotal + shipping, 2)

    # Get saved addresses
    addresses = query_db('SELECT * FROM addresses WHERE user_id=%s ORDER BY is_default DESC', (user_id,))

    user = get_current_user()
    return render_template('checkout.html',
                           cart_items=cart_items,
                           subtotal=round(subtotal, 2),
                           shipping=shipping,
                           total=total,
                           addresses=addresses,
                           razorpay_key=Config.RAZORPAY_KEY_ID,
                           user=user)


# ─── Create Razorpay Order ───────────────────────────────────
@payment_bp.route('/payment/create-order', methods=['POST'])
@login_required
def create_razorpay_order():
    user_id    = request.user['user_id']
    data       = request.get_json() or {}
    address_id = data.get('address_id')

    if not address_id:
        return jsonify({'error': 'Please select a shipping address.'}), 400

    # Verify address belongs to user
    address = query_db('SELECT * FROM addresses WHERE id=%s AND user_id=%s',
                       (address_id, user_id), one=True)
    if not address:
        return jsonify({'error': 'Invalid address.'}), 400

    # Calculate cart total
    cart_items = query_db(
        '''SELECT c.quantity, p.price, p.discount
           FROM cart c JOIN products p ON c.product_id = p.product_id
           WHERE c.user_id = %s''',
        (user_id,)
    )
    if not cart_items:
        return jsonify({'error': 'Cart is empty.'}), 400

    subtotal = sum(float(i['price']) * (1 - float(i['discount']) / 100) * i['quantity'] for i in cart_items)
    shipping = 0 if subtotal >= 999 else 99
    total    = round(subtotal + shipping, 2)

    # Create Razorpay order (amount in paise)
    try:
        rz_order = rz_client.order.create({
            'amount':   int(total * 100),
            'currency': 'INR',
            'payment_capture': 1
        })
    except Exception as e:
        return jsonify({'error': f'Payment gateway error: {str(e)}'}), 500

    # Store pending address in session for verification step
    session['pending_address_id'] = address_id
    session['pending_rz_order_id'] = rz_order['id']

    return jsonify({
        'razorpay_order_id': rz_order['id'],
        'amount':            rz_order['amount'],
        'currency':          rz_order['currency'],
        'key':               Config.RAZORPAY_KEY_ID
    })


# ─── Verify Payment & Place Order ───────────────────────────
@payment_bp.route('/payment/verify', methods=['POST'])
@login_required
def verify_payment():
    user_id = request.user['user_id']
    data    = request.get_json() or {}

    razorpay_order_id   = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature  = data.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return jsonify({'error': 'Missing payment details'}), 400

    # ── Signature verification (HMAC SHA256) ──
    body      = f'{razorpay_order_id}|{razorpay_payment_id}'
    expected  = hmac.new(
        Config.RAZORPAY_KEY_SECRET.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if expected != razorpay_signature:
        return jsonify({'error': 'Payment verification failed. Invalid signature.'}), 400

    # ── Signature valid — place the order ──
    address_id = session.get('pending_address_id')
    if not address_id:
        return jsonify({'error': 'Session expired. Please retry checkout.'}), 400

    # Fetch address for snapshot
    address = query_db('SELECT * FROM addresses WHERE id=%s AND user_id=%s',
                       (address_id, user_id), one=True)
    if not address:
        return jsonify({'error': 'Address not found.'}), 400

    shipping_snapshot = (f"{address['full_name']}, {address['address_line']}, "
                         f"{address['city']}, {address['state']} - {address['pincode']}, "
                         f"Ph: {address['phone']}")

    cart_items = query_db(
        '''SELECT c.quantity, p.product_id, p.price, p.discount, p.stock
           FROM cart c JOIN products p ON c.product_id = p.product_id
           WHERE c.user_id = %s''',
        (user_id,)
    )
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400

    subtotal = sum(float(i['price']) * (1 - float(i['discount']) / 100) * i['quantity'] for i in cart_items)
    shipping = 0 if subtotal >= 999 else 99
    total    = round(subtotal + shipping, 2)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Insert order with Razorpay details
            cursor.execute(
                '''INSERT INTO orders
                   (user_id, total_amount, status, payment_id,
                    razorpay_order_id, razorpay_payment_id, razorpay_signature,
                    address_id, shipping_snapshot)
                   VALUES (%s, %s, 'Paid', %s, %s, %s, %s, %s, %s)''',
                (user_id, total, razorpay_payment_id,
                 razorpay_order_id, razorpay_payment_id, razorpay_signature,
                 address_id, shipping_snapshot)
            )
            cursor.execute(
                'SELECT order_id FROM orders WHERE user_id=%s ORDER BY created_at DESC LIMIT 1',
                (user_id,)
            )
            order_id = cursor.fetchone()['order_id']

            for item in cart_items:
                eff = float(item['price']) * (1 - float(item['discount']) / 100)
                cursor.execute(
                    'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s,%s,%s,%s)',
                    (order_id, item['product_id'], item['quantity'], round(eff, 2))
                )
                cursor.execute(
                    'UPDATE products SET stock = stock - %s WHERE product_id=%s AND stock >= %s',
                    (item['quantity'], item['product_id'], item['quantity'])
                )

            cursor.execute('DELETE FROM cart WHERE user_id=%s', (user_id,))
            conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Order creation failed after payment. Contact support.'}), 500
    finally:
        conn.close()

    # Clear session
    session.pop('pending_address_id', None)
    session.pop('pending_rz_order_id', None)

    return jsonify({'success': True, 'order_id': order_id})


# ─── Payment Success Page ────────────────────────────────────
@payment_bp.route('/payment/success/<order_id>')
@login_required
def payment_success(order_id):
    user_id = request.user['user_id']
    order   = query_db('SELECT * FROM orders WHERE order_id=%s AND user_id=%s',
                       (order_id, user_id), one=True)
    if not order:
        return redirect(url_for('orders.view_orders'))
    user = get_current_user()
    return render_template('payment_success.html', order=order, user=user)


# ─── Address Management ──────────────────────────────────────
@payment_bp.route('/addresses')
@login_required
def list_addresses():
    user_id   = request.user['user_id']
    addresses = query_db('SELECT * FROM addresses WHERE user_id=%s ORDER BY is_default DESC', (user_id,))
    user      = get_current_user()
    return render_template('addresses.html', addresses=addresses, user=user)


@payment_bp.route('/addresses/add', methods=['POST'])
@login_required
def add_address():
    user_id   = request.user['user_id']
    full_name = request.form.get('full_name', '').strip()
    phone     = request.form.get('phone', '').strip()
    addr_line = request.form.get('address_line', '').strip()
    city      = request.form.get('city', '').strip()
    state     = request.form.get('state', '').strip()
    pincode   = request.form.get('pincode', '').strip()
    is_default= 1 if request.form.get('is_default') else 0

    if not all([full_name, phone, addr_line, city, state, pincode]):
        flash('All address fields are required.', 'danger')
        return redirect(request.referrer or url_for('payment.list_addresses'))

    # If setting as default, clear previous defaults
    if is_default:
        query_db('UPDATE addresses SET is_default=0 WHERE user_id=%s', (user_id,), commit=True)

    query_db(
        'INSERT INTO addresses (user_id, full_name, phone, address_line, city, state, pincode, is_default) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
        (user_id, full_name, phone, addr_line, city, state, pincode, is_default),
        commit=True
    )
    flash('Address added successfully!', 'success')
    return redirect(request.referrer or url_for('payment.list_addresses'))


@payment_bp.route('/addresses/<int:addr_id>/delete', methods=['POST'])
@login_required
def delete_address(addr_id):
    user_id = request.user['user_id']
    query_db('DELETE FROM addresses WHERE id=%s AND user_id=%s', (addr_id, user_id), commit=True)
    flash('Address removed.', 'info')
    return redirect(url_for('payment.list_addresses'))


@payment_bp.route('/addresses/<int:addr_id>/default', methods=['POST'])
@login_required
def set_default_address(addr_id):
    user_id = request.user['user_id']
    query_db('UPDATE addresses SET is_default=0 WHERE user_id=%s', (user_id,), commit=True)
    query_db('UPDATE addresses SET is_default=1 WHERE id=%s AND user_id=%s', (addr_id, user_id), commit=True)
    flash('Default address updated.', 'success')
    return redirect(url_for('payment.list_addresses'))
