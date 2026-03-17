"""
product_routes.py - Product Blueprint
Schema-compatible: products.product_id, products.cat_id, categories.cat_id
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort
from utils.db import query_db
from utils.auth import login_required, admin_required, get_current_user

products_bp = Blueprint('products', __name__)


# -----------------------------
# PRODUCTS LIST PAGE
# -----------------------------
@products_bp.route('/')
def index():
    search = request.args.get('q', '').strip()
    cat_id = request.args.get('category', '')
    sort   = request.args.get('sort', 'newest')

    sql  = '''
        SELECT p.*, c.category_name
        FROM products p
        LEFT JOIN categories c ON p.cat_id = c.cat_id
        WHERE p.stock > 0
    '''
    args = []

    if search:
        sql  += ' AND (p.name LIKE %s OR p.description LIKE %s)'
        args += [f'%{search}%', f'%{search}%']

    if cat_id:
        sql  += ' AND p.cat_id = %s'
        args.append(cat_id)

    order_map = {
        'newest': 'p.created_at DESC',
        'price_asc': 'p.price ASC',
        'price_desc': 'p.price DESC',
        'name': 'p.name ASC'
    }

    sql += f' ORDER BY {order_map.get(sort, "p.created_at DESC")}'

    products   = query_db(sql, tuple(args))
    categories = query_db("SELECT * FROM categories WHERE status = 'active'")
    user       = get_current_user()

    return render_template(
        'products.html',
        products=products,
        categories=categories,
        search=search,
        selected_category=cat_id,
        sort=sort,
        user=user
    )


# -----------------------------
# PRODUCT DETAIL PAGE
# -----------------------------
@products_bp.route('/product/<product_id>')
def detail(product_id):

    product = query_db(
        '''
        SELECT p.*, c.category_name
        FROM products p
        LEFT JOIN categories c ON p.cat_id = c.cat_id
        WHERE p.product_id = %s
        ''',
        (product_id,),
        one=True
    )

    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('products.index'))

    related = query_db(
        '''
        SELECT * FROM products
        WHERE cat_id = %s AND product_id != %s AND stock > 0
        LIMIT 4
        ''',
        (product['cat_id'], product_id)
    )

    user = get_current_user()

    return render_template(
        'product_detail.html',
        product=product,
        related=related,
        user=user
    )


# -----------------------------
# USER DASHBOARD
# -----------------------------
@products_bp.route('/dashboard')
@login_required
def dashboard():

    user_payload = request.user
    user_id = user_payload['user_id']

    # Get full user info from database
    user = query_db(
        "SELECT * FROM users WHERE id = %s",
        (user_id,),
        one=True
    )

    order_count = query_db(
        "SELECT COUNT(*) as cnt FROM orders WHERE user_id = %s",
        (user_id,),
        one=True
    )

    cart_count = query_db(
        "SELECT COUNT(*) as cnt FROM cart WHERE user_id = %s",
        (user_id,),
        one=True
    )

    recent_orders = query_db(
        """
        SELECT * FROM orders
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (user_id,)
    )

    return render_template(
        "dashboard.html",
        user=user,
        order_count=order_count['cnt'],
        cart_count=cart_count['cnt'],
        recent_orders=recent_orders
    )


# -----------------------------
# API - PRODUCT LIST
# -----------------------------
@products_bp.route('/api/products', methods=['GET'])
def api_list():

    search = request.args.get('q', '')
    cat_id = request.args.get('category', '')

    sql = '''
        SELECT p.*, c.category_name
        FROM products p
        LEFT JOIN categories c ON p.cat_id = c.cat_id
        WHERE p.stock > 0
    '''

    args = []

    if search:
        sql += ' AND (p.name LIKE %s OR p.description LIKE %s)'
        args += [f'%{search}%', f'%{search}%']

    if cat_id:
        sql += ' AND p.cat_id = %s'
        args.append(cat_id)

    sql += ' ORDER BY p.created_at DESC'

    products = query_db(sql, tuple(args))

    for p in products:
        p['price']      = float(p['price'])
        p['discount']   = float(p['discount'])
        p['created_at'] = str(p['created_at'])

    return jsonify(products)


# -----------------------------
# API - PRODUCT DETAIL
# -----------------------------
@products_bp.route('/api/products/<product_id>', methods=['GET'])
def api_detail(product_id):

    product = query_db(
        '''
        SELECT p.*, c.category_name
        FROM products p
        LEFT JOIN categories c ON p.cat_id = c.cat_id
        WHERE p.product_id = %s
        ''',
        (product_id,),
        one=True
    )

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    product['price']      = float(product['price'])
    product['discount']   = float(product['discount'])
    product['created_at'] = str(product['created_at'])

    return jsonify(product)


# -----------------------------
# API - CREATE PRODUCT
# -----------------------------
@products_bp.route('/api/products', methods=['POST'])
@admin_required
def api_create():

    data = request.get_json()

    if not all(k in data for k in ['name', 'price', 'stock', 'cat_id']):
        return jsonify({'error': 'Missing required fields'}), 400

    query_db(
        '''
        INSERT INTO products
        (name, description, cat_id, price, discount, size, color, stock, image)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''',
        (
            data.get('name'),
            data.get('description'),
            data.get('cat_id'),
            data.get('price'),
            data.get('discount', 0),
            data.get('size'),
            data.get('color'),
            data.get('stock'),
            data.get('image')
        ),
        commit=True
    )

    new_p = query_db(
        'SELECT product_id FROM products ORDER BY created_at DESC LIMIT 1',
        one=True
    )

    return jsonify({'product_id': new_p['product_id'], 'message': 'Product created'}), 201


# -----------------------------
# API - UPDATE PRODUCT
# -----------------------------
@products_bp.route('/api/products/<product_id>', methods=['PUT'])
@admin_required
def api_update(product_id):

    data = request.get_json()

    query_db(
        '''
        UPDATE products
        SET name=%s, description=%s, price=%s, discount=%s,
            size=%s, color=%s, stock=%s, image=%s, cat_id=%s
        WHERE product_id=%s
        ''',
        (
            data.get('name'),
            data.get('description'),
            data.get('price'),
            data.get('discount', 0),
            data.get('size'),
            data.get('color'),
            data.get('stock'),
            data.get('image'),
            data.get('cat_id'),
            product_id
        ),
        commit=True
    )

    return jsonify({'message': 'Product updated'})


# -----------------------------
# API - DELETE PRODUCT
# -----------------------------
@products_bp.route('/api/products/<product_id>', methods=['DELETE'])
@admin_required
def api_delete(product_id):

    query_db(
        'DELETE FROM products WHERE product_id = %s',
        (product_id,),
        commit=True
    )

    return jsonify({'message': 'Product deleted'})