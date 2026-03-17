"""
order_routes.py - Order Blueprint
Schema-compatible: orders.total_amount, orders.status (Pending/Paid/Shipped/Delivered/Cancelled),
                   products.product_id (VARCHAR), order_items references product_id VARCHAR
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from utils.db import query_db, get_connection
from utils.auth import login_required, get_current_user

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/orders')
@login_required
def view_orders():
    user_id = request.user['user_id']
    orders  = query_db('SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC', (user_id,))
    user    = get_current_user()
    return render_template('orders.html', orders=orders, user=user)


@orders_bp.route('/orders/<order_id>')
@login_required
def order_detail(order_id):
    user_id = request.user['user_id']
    order   = query_db('SELECT * FROM orders WHERE order_id=%s AND user_id=%s', (order_id, user_id), one=True)

    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('orders.view_orders'))

    items = query_db(
        '''SELECT oi.*, p.name, p.image FROM order_items oi
           LEFT JOIN products p ON oi.product_id = p.product_id
           WHERE oi.order_id = %s''',
        (order_id,)
    )
    user = get_current_user()
    return render_template('order_detail.html', order=order, items=items, user=user)


@orders_bp.route('/orders/place', methods=['POST'])
@login_required
def place_order():
    user_id    = request.user['user_id']
    payment_id = request.form.get('payment_id', 'COD')

    cart_items = query_db(
        '''SELECT c.quantity, p.product_id, p.price, p.discount, p.stock
           FROM cart c JOIN products p ON c.product_id = p.product_id
           WHERE c.user_id = %s''',
        (user_id,)
    )

    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))

    total = sum(float(i['price']) * (1 - float(i['discount']) / 100) * i['quantity'] for i in cart_items)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Insert order — trigger auto-assigns order_id
            cursor.execute(
                'INSERT INTO orders (user_id, total_amount, status, payment_id) VALUES (%s, %s, %s, %s)',
                (user_id, round(total, 2), 'Paid' if payment_id != 'COD' else 'Pending', payment_id)
            )
            # Retrieve the auto-generated order_id
            cursor.execute('SELECT order_id FROM orders WHERE user_id=%s ORDER BY created_at DESC LIMIT 1', (user_id,))
            order_row = cursor.fetchone()
            order_id  = order_row['order_id']

            for item in cart_items:
                effective_price = float(item['price']) * (1 - float(item['discount']) / 100)
                cursor.execute(
                    'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)',
                    (order_id, item['product_id'], item['quantity'], round(effective_price, 2))
                )
                cursor.execute(
                    'UPDATE products SET stock = stock - %s WHERE product_id = %s AND stock >= %s',
                    (item['quantity'], item['product_id'], item['quantity'])
                )

            cursor.execute('DELETE FROM cart WHERE user_id = %s', (user_id,))
            conn.commit()

    except Exception as e:
        conn.rollback()
        flash('Order placement failed. Please try again.', 'danger')
        return redirect(url_for('cart.view_cart'))
    finally:
        conn.close()

    flash(f'Order {order_id} placed successfully!', 'success')
    return redirect(url_for('orders.order_detail', order_id=order_id))


@orders_bp.route('/api/orders', methods=['POST'])
@login_required
def api_create_order():
    user_id    = request.user['user_id']
    data       = request.get_json() or {}
    payment_id = data.get('payment_id', 'COD')

    cart_items = query_db(
        '''SELECT c.quantity, p.product_id, p.price, p.discount, p.stock
           FROM cart c JOIN products p ON c.product_id = p.product_id
           WHERE c.user_id = %s''',
        (user_id,)
    )

    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400

    total = sum(float(i['price']) * (1 - float(i['discount']) / 100) * i['quantity'] for i in cart_items)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO orders (user_id, total_amount, status, payment_id) VALUES (%s, %s, %s, %s)',
                (user_id, round(total, 2), 'Paid' if payment_id != 'COD' else 'Pending', payment_id)
            )
            cursor.execute('SELECT order_id FROM orders WHERE user_id=%s ORDER BY created_at DESC LIMIT 1', (user_id,))
            order_id = cursor.fetchone()['order_id']

            for item in cart_items:
                effective_price = float(item['price']) * (1 - float(item['discount']) / 100)
                cursor.execute(
                    'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)',
                    (order_id, item['product_id'], item['quantity'], round(effective_price, 2))
                )
                cursor.execute(
                    'UPDATE products SET stock = stock - %s WHERE product_id = %s',
                    (item['quantity'], item['product_id'])
                )
            cursor.execute('DELETE FROM cart WHERE user_id = %s', (user_id,))
            conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Order creation failed'}), 500
    finally:
        conn.close()

    return jsonify({'order_id': order_id, 'total': round(total, 2), 'message': 'Order placed'}), 201


@orders_bp.route('/api/orders', methods=['GET'])
@login_required
def api_list_orders():
    orders = query_db('SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC',
                      (request.user['user_id'],))
    for o in orders:
        o['total_amount'] = float(o['total_amount'])
        o['created_at']   = str(o['created_at'])
    return jsonify(orders)
