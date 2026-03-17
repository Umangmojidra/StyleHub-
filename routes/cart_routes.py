"""
cart_routes.py - Cart Blueprint
Fixes: quantity controls, live subtotal/total/shipping recalc on every update.
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from utils.db import query_db
from utils.auth import login_required, get_current_user

cart_bp = Blueprint('cart', __name__)


def get_cart_items(user_id):
    """Fetch cart items with product details for a user."""
    return query_db(
        '''SELECT c.cart_id, c.quantity,
                  p.product_id, p.name, p.price, p.discount, p.image, p.stock,
                  ROUND(p.price * (1 - p.discount/100), 2) as effective_price
           FROM cart c
           JOIN products p ON c.product_id = p.product_id
           WHERE c.user_id = %s''',
        (user_id,)
    )


def calc_totals(items):
    subtotal = sum(float(i['effective_price']) * int(i['quantity']) for i in items)
    shipping = 0 if subtotal >= 999 else 99
    total    = subtotal + shipping
    return round(subtotal, 2), shipping, round(total, 2)


@cart_bp.route('/cart')
@login_required
def view_cart():
    user_id          = request.user['user_id']
    items            = get_cart_items(user_id)
    subtotal, shipping, total = calc_totals(items)
    user             = get_current_user()
    return render_template('cart.html',
                           items=items,
                           subtotal=subtotal,
                           shipping=shipping,
                           total=total,
                           user=user)


@cart_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    user_id    = request.user['user_id']
    # Support both form submissions and JSON (fetch) calls
    data       = request.get_json(silent=True, force=True) or {}
    product_id = request.form.get('product_id') or data.get('product_id')
    try:
        quantity = int(request.form.get('quantity') or data.get('quantity') or 1)
    except (ValueError, TypeError):
        quantity = 1

    if not product_id:
        if request.is_json:
            return jsonify({'error': 'Product ID required'}), 400
        flash('Invalid product.', 'danger')
        return redirect(url_for('products.index'))

    product = query_db(
        'SELECT product_id, stock FROM products WHERE product_id = %s',
        (product_id,), one=True
    )
    if not product:
        if request.is_json:
            return jsonify({'error': 'Product not found'}), 404
        flash('Product not found.', 'danger')
        return redirect(url_for('products.index'))

    existing = query_db(
        'SELECT cart_id, quantity FROM cart WHERE user_id=%s AND product_id=%s',
        (user_id, product_id), one=True
    )

    if existing:
        new_qty = existing['quantity'] + quantity
        if new_qty > product['stock']:
            msg = f'Only {product["stock"]} units available.'
            if request.is_json:
                return jsonify({'error': msg}), 400
            flash(msg, 'warning')
            return redirect(request.referrer or url_for('products.index'))
        query_db('UPDATE cart SET quantity=%s WHERE cart_id=%s',
                 (new_qty, existing['cart_id']), commit=True)
    else:
        if quantity > product['stock']:
            msg = f'Only {product["stock"]} units available.'
            if request.is_json:
                return jsonify({'error': msg}), 400
            flash(msg, 'warning')
            return redirect(request.referrer or url_for('products.index'))
        query_db(
            'INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)',
            (user_id, product_id, quantity), commit=True
        )

    if request.is_json:
        count = query_db('SELECT COUNT(*) as cnt FROM cart WHERE user_id=%s', (user_id,), one=True)
        return jsonify({'message': 'Added to cart', 'cart_count': count['cnt']})

    flash('Item added to cart!', 'success')
    return redirect(request.referrer or url_for('products.index'))


@cart_bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    user_id = request.user['user_id']
    data    = request.get_json(silent=True, force=True) or {}
    cart_id = request.form.get('cart_id') or data.get('cart_id')
    try:
        quantity = int(request.form.get('quantity') or data.get('quantity') or 1)
    except (ValueError, TypeError):
        quantity = 1

    if not cart_id:
        return jsonify({'error': 'Cart ID required'}), 400

    # Remove item if qty drops to 0
    if quantity < 1:
        query_db('DELETE FROM cart WHERE cart_id=%s AND user_id=%s',
                 (cart_id, user_id), commit=True)
        if request.is_json:
            items                     = get_cart_items(user_id)
            subtotal, shipping, total = calc_totals(items)
            return jsonify({
                'removed':  True,
                'subtotal': subtotal,
                'shipping': shipping,
                'total':    total,
                'cart_count': len(items)
            })
        flash('Item removed from cart.', 'info')
        return redirect(url_for('cart.view_cart'))

    item = query_db(
        '''SELECT c.cart_id, p.stock, p.price, p.discount,
                  ROUND(p.price * (1 - p.discount/100), 2) as effective_price
           FROM cart c
           JOIN products p ON c.product_id = p.product_id
           WHERE c.cart_id=%s AND c.user_id=%s''',
        (cart_id, user_id), one=True
    )
    if not item:
        return jsonify({'error': 'Cart item not found'}), 404

    if quantity > item['stock']:
        if request.is_json:
            return jsonify({'error': f'Only {item["stock"]} units available.'}), 400
        flash(f'Only {item["stock"]} units available.', 'warning')
        return redirect(url_for('cart.view_cart'))

    query_db('UPDATE cart SET quantity=%s WHERE cart_id=%s AND user_id=%s',
             (quantity, cart_id, user_id), commit=True)

    if request.is_json:
        items                     = get_cart_items(user_id)
        subtotal, shipping, total = calc_totals(items)
        row_total = round(float(item['effective_price']) * quantity, 2)
        return jsonify({
            'row_total': row_total,
            'subtotal':  subtotal,
            'shipping':  shipping,
            'total':     total,
            'cart_count': len(items)
        })

    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/cart/remove', methods=['POST'])
@login_required
def remove_from_cart():
    user_id = request.user['user_id']
    data    = request.get_json(silent=True, force=True) or {}
    cart_id = request.form.get('cart_id') or data.get('cart_id')

    if not cart_id:
        return jsonify({'error': 'Cart ID required'}), 400

    query_db('DELETE FROM cart WHERE cart_id=%s AND user_id=%s',
             (cart_id, user_id), commit=True)

    if request.is_json:
        items                     = get_cart_items(user_id)
        subtotal, shipping, total = calc_totals(items)
        return jsonify({
            'removed':  True,
            'subtotal': subtotal,
            'shipping': shipping,
            'total':    total,
            'cart_count': len(items)
        })

    flash('Item removed from cart.', 'success')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/api/cart', methods=['GET'])
@login_required
def api_get_cart():
    items  = get_cart_items(request.user['user_id'])
    result = []
    for i in items:
        result.append({
            'cart_id':         i['cart_id'],
            'product_id':      i['product_id'],
            'name':            i['name'],
            'quantity':        i['quantity'],
            'price':           float(i['price']),
            'discount':        float(i['discount']),
            'effective_price': float(i['effective_price']),
            'image':           i['image']
        })
    return jsonify(result)
