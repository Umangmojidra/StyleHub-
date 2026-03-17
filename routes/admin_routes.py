"""
admin_routes.py - Admin Panel Blueprint
Full admin dashboard: sales monitoring, product CRUD, orders, users, payments.
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from utils.db import query_db
from utils.auth import admin_required, get_current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ─── Admin Dashboard ────────────────────────────────────────
@admin_bp.route('/')
@admin_required
def dashboard():
    total_orders   = query_db('SELECT COUNT(*) as cnt FROM orders', one=True)['cnt']
    total_users    = query_db("SELECT COUNT(*) as cnt FROM users WHERE role='user'", one=True)['cnt']
    total_products = query_db('SELECT COUNT(*) as cnt FROM products', one=True)['cnt']
    total_revenue  = query_db(
        "SELECT IFNULL(SUM(total_amount),0) as rev FROM orders WHERE status != 'Cancelled'",
        one=True
    )['rev']

    # Orders by status
    status_counts = query_db("SELECT status, COUNT(*) as cnt FROM orders GROUP BY status")

    # Recent 10 orders
    recent_orders = query_db(
        '''SELECT o.*, u.name as user_name, u.email as user_email
           FROM orders o JOIN users u ON o.user_id = u.id
           ORDER BY o.created_at DESC LIMIT 10'''
    )

    # Low stock products (stock < 5)
    low_stock = query_db('SELECT * FROM products WHERE stock < 5 ORDER BY stock ASC LIMIT 8')

    # Revenue last 7 days
    daily_revenue = query_db(
        """SELECT DATE(created_at) as day, SUM(total_amount) as revenue
           FROM orders WHERE status != 'Cancelled'
           AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
           GROUP BY DATE(created_at) ORDER BY day ASC"""
    )

    # Top 5 best-selling products
    top_products = query_db(
        """SELECT p.name, p.image, SUM(oi.quantity) as units_sold,
                  SUM(oi.quantity * oi.price) as revenue
           FROM order_items oi
           JOIN products p ON oi.product_id = p.product_id
           JOIN orders o ON oi.order_id = o.order_id
           WHERE o.status != 'Cancelled'
           GROUP BY p.product_id, p.name, p.image
           ORDER BY units_sold DESC LIMIT 5"""
    )

    # Monthly revenue (last 6 months)
    monthly_revenue = query_db(
        """SELECT DATE_FORMAT(created_at, '%%b %%Y') as month,
                  SUM(total_amount) as revenue,
                  COUNT(*) as orders
           FROM orders WHERE status != 'Cancelled'
           AND created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
           GROUP BY DATE_FORMAT(created_at, '%%Y-%%m'), DATE_FORMAT(created_at, '%%b %%Y')
           ORDER BY DATE_FORMAT(created_at, '%%Y-%%m') ASC"""
    )

    user = get_current_user()
    return render_template('admin/dashboard.html',
                           user=user,
                           total_orders=total_orders,
                           total_users=total_users,
                           total_products=total_products,
                           total_revenue=float(total_revenue),
                           status_counts=status_counts,
                           recent_orders=recent_orders,
                           low_stock=low_stock,
                           daily_revenue=daily_revenue,
                           top_products=top_products,
                           monthly_revenue=monthly_revenue)


# ─── All Orders ─────────────────────────────────────────────
@admin_bp.route('/orders')
@admin_required
def orders():
    status_filter = request.args.get('status', '')
    search        = request.args.get('q', '').strip()

    sql  = '''SELECT o.*, u.name as user_name, u.email as user_email,
                     a.city, a.state, a.pincode
              FROM orders o
              JOIN users u ON o.user_id = u.id
              LEFT JOIN addresses a ON o.address_id = a.id
              WHERE 1=1'''
    args = []

    if status_filter:
        sql  += ' AND o.status = %s'
        args.append(status_filter)
    if search:
        sql  += ' AND (o.order_id LIKE %s OR u.name LIKE %s OR u.email LIKE %s)'
        args += [f'%{search}%', f'%{search}%', f'%{search}%']

    sql += ' ORDER BY o.created_at DESC'
    all_orders = query_db(sql, tuple(args))
    user = get_current_user()
    return render_template('admin/orders.html',
                           orders=all_orders,
                           status_filter=status_filter,
                           search=search,
                           user=user)


# ─── Order Detail ────────────────────────────────────────────
@admin_bp.route('/orders/<order_id>')
@admin_required
def order_detail(order_id):
    order = query_db(
        '''SELECT o.*, u.name as user_name, u.email as user_email, u.phone as user_phone,
                  a.full_name as addr_name, a.phone as addr_phone,
                  a.address_line, a.city, a.state, a.pincode
           FROM orders o
           JOIN users u ON o.user_id = u.id
           LEFT JOIN addresses a ON o.address_id = a.id
           WHERE o.order_id = %s''',
        (order_id,), one=True
    )
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('admin.orders'))

    items = query_db(
        '''SELECT oi.*, p.name, p.image, p.product_id
           FROM order_items oi
           LEFT JOIN products p ON oi.product_id = p.product_id
           WHERE oi.order_id = %s''',
        (order_id,)
    )
    user = get_current_user()
    return render_template('admin/order_detail.html', order=order, items=items, user=user)


# ─── Update Order Status ─────────────────────────────────────
@admin_bp.route('/orders/<order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    new_status = request.form.get('status') or (request.get_json() or {}).get('status')
    valid = ['Pending', 'Paid', 'Shipped', 'Delivered', 'Cancelled']

    if new_status not in valid:
        if request.is_json:
            return jsonify({'error': 'Invalid status'}), 400
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    if new_status == 'Cancelled':
        items = query_db('SELECT product_id, quantity FROM order_items WHERE order_id=%s', (order_id,))
        for item in items:
            query_db('UPDATE products SET stock = stock + %s WHERE product_id = %s',
                     (item['quantity'], item['product_id']), commit=True)

    query_db('UPDATE orders SET status=%s WHERE order_id=%s', (new_status, order_id), commit=True)

    if request.is_json:
        return jsonify({'message': f'Status updated to {new_status}'})

    flash(f'Order {order_id} status updated to {new_status}.', 'success')
    return redirect(url_for('admin.order_detail', order_id=order_id))


# ─── All Users ───────────────────────────────────────────────
@admin_bp.route('/users')
@admin_required
def users():
    search = request.args.get('q', '').strip()
    sql    = 'SELECT id, name, email, phone, role, status, created_at FROM users WHERE 1=1'
    args   = []

    if search:
        sql  += ' AND (name LIKE %s OR email LIKE %s)'
        args += [f'%{search}%', f'%{search}%']

    sql  += ' ORDER BY created_at DESC'
    all_users = query_db(sql, tuple(args))
    user = get_current_user()
    return render_template('admin/users.html', users=all_users, search=search, user=user)


# ─── Block / Unblock User ────────────────────────────────────
@admin_bp.route('/users/<user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):
    target = query_db('SELECT status, role FROM users WHERE id=%s', (user_id,), one=True)
    if not target:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.users'))
    if target['role'] == 'admin':
        flash('Cannot block an admin account.', 'warning')
        return redirect(url_for('admin.users'))

    new_status = 'blocked' if target['status'] == 'active' else 'active'
    query_db('UPDATE users SET status=%s WHERE id=%s', (new_status, user_id), commit=True)
    flash(f'User {user_id} is now {new_status}.', 'success')
    return redirect(url_for('admin.users'))


# ─── Products List (Admin) ───────────────────────────────────
@admin_bp.route('/products')
@admin_required
def products():
    search       = request.args.get('q', '').strip()
    cat_filter   = request.args.get('cat', '').strip()
    stock_filter = request.args.get('stock', '').strip()  # out / low / ok

    sql  = '''SELECT p.*, c.category_name FROM products p
              LEFT JOIN categories c ON p.cat_id = c.cat_id
              WHERE 1=1'''
    args = []

    if search:
        sql  += ' AND (p.name LIKE %s OR p.product_id LIKE %s)'
        args += [f'%{search}%', f'%{search}%']
    if cat_filter:
        sql  += ' AND p.cat_id = %s'
        args.append(cat_filter)
    if stock_filter == 'out':
        sql += ' AND p.stock = 0'
    elif stock_filter == 'low':
        sql += ' AND p.stock > 0 AND p.stock < 10'
    elif stock_filter == 'ok':
        sql += ' AND p.stock >= 10'

    sql += ' ORDER BY p.stock ASC, p.created_at DESC'

    all_products = query_db(sql, tuple(args))
    categories   = query_db("SELECT * FROM categories WHERE status='active'")

    # Inventory summary stats
    inv = query_db('''SELECT
        COUNT(*)                              AS total,
        SUM(stock = 0)                        AS out_of_stock,
        SUM(stock > 0 AND stock < 10)         AS low_stock,
        SUM(stock >= 10)                      AS in_stock,
        IFNULL(SUM(stock * price), 0)         AS inventory_value
        FROM products''', one=True)

    user = get_current_user()
    return render_template('admin/products.html',
                           products=all_products,
                           categories=categories,
                           search=search,
                           cat_filter=cat_filter,
                           stock_filter=stock_filter,
                           inv=inv,
                           user=user)


# ─── Add Product ────────────────────────────────────────────
@admin_bp.route('/products/add', methods=['POST'])
@admin_required
def add_product():
    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    cat_id      = request.form.get('cat_id', '').strip()
    price       = request.form.get('price', '0').strip()
    discount    = request.form.get('discount', '0').strip()
    stock       = request.form.get('stock', '0').strip()
    image       = request.form.get('image', '').strip()
    size        = request.form.get('size', '').strip()
    color       = request.form.get('color', '').strip()

    errors = []
    if not name:
        errors.append('Product name is required.')
    if not cat_id:
        errors.append('Please select a category.')
    try:
        price    = float(price)
        discount = float(discount)
        stock    = int(stock)
        if price <= 0:
            errors.append('Price must be greater than 0.')
        if not (0 <= discount <= 100):
            errors.append('Discount must be between 0 and 100.')
        if stock < 0:
            errors.append('Stock cannot be negative.')
    except ValueError:
        errors.append('Invalid price, discount, or stock value.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('admin.products'))

    query_db(
        '''INSERT INTO products (name, description, cat_id, price, discount, stock, image, size, color)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
        (name, description, cat_id, price, discount, stock,
         image or None, size or None, color or None),
        commit=True
    )
    flash(f'Product "{name}" added successfully.', 'success')
    return redirect(url_for('admin.products'))


# ─── Edit Product (GET form data) ───────────────────────────
@admin_bp.route('/products/<product_id>/edit', methods=['GET'])
@admin_required
def edit_product_form(product_id):
    product    = query_db('SELECT * FROM products WHERE product_id=%s', (product_id,), one=True)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin.products'))
    categories = query_db("SELECT * FROM categories WHERE status='active'")
    user       = get_current_user()
    return render_template('admin/edit_product.html',
                           product=product, categories=categories, user=user)


# ─── Update Product ─────────────────────────────────────────
@admin_bp.route('/products/<product_id>/update', methods=['POST'])
@admin_required
def update_product(product_id):
    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    cat_id      = request.form.get('cat_id', '').strip()
    price       = request.form.get('price', '0').strip()
    discount    = request.form.get('discount', '0').strip()
    stock       = request.form.get('stock', '0').strip()
    image       = request.form.get('image', '').strip()

    errors = []
    if not name:
        errors.append('Product name is required.')
    try:
        price    = float(price)
        discount = float(discount)
        stock    = int(stock)
        if price <= 0:
            errors.append('Price must be greater than 0.')
        if not (0 <= discount <= 100):
            errors.append('Discount must be between 0 and 100.')
        if stock < 0:
            errors.append('Stock cannot be negative.')
    except ValueError:
        errors.append('Invalid price, discount, or stock value.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('admin.edit_product_form', product_id=product_id))

    query_db(
        '''UPDATE products
           SET name=%s, description=%s, cat_id=%s, price=%s, discount=%s, stock=%s, image=%s
           WHERE product_id=%s''',
        (name, description, cat_id or None, price, discount, stock,
         image or None, product_id),
        commit=True
    )
    flash(f'Product "{name}" updated successfully.', 'success')
    return redirect(url_for('admin.products'))


# ─── Delete Product ─────────────────────────────────────────
@admin_bp.route('/products/<product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = query_db('SELECT name FROM products WHERE product_id=%s', (product_id,), one=True)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin.products'))

    # Remove from carts first to avoid FK issues
    query_db('DELETE FROM cart WHERE product_id=%s', (product_id,), commit=True)
    query_db('DELETE FROM products WHERE product_id=%s', (product_id,), commit=True)
    flash(f'Product "{product["name"]}" deleted.', 'success')
    return redirect(url_for('admin.products'))




# ─── Quick Stock Update ──────────────────────────────────────
@admin_bp.route('/products/<product_id>/stock', methods=['POST'])
@admin_required
def update_stock(product_id):
    try:
        new_stock = int(request.form.get('stock', -1))
    except ValueError:
        flash('Invalid stock value.', 'danger')
        return redirect(url_for('admin.products'))

    if new_stock < 0:
        flash('Stock cannot be negative.', 'danger')
        return redirect(url_for('admin.products'))

    product = query_db('SELECT name FROM products WHERE product_id=%s', (product_id,), one=True)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin.products'))

    query_db('UPDATE products SET stock=%s WHERE product_id=%s',
             (new_stock, product_id), commit=True)
    flash(f'Stock updated to {new_stock} for "{product["name"]}".', 'success')
    return redirect(url_for('admin.products'))

# ─── Sales Report ───────────────────────────────────────────
@admin_bp.route('/sales')
@admin_required
def sales():
    # Overall totals
    totals = query_db(
        """SELECT COUNT(*) as total_orders,
                  IFNULL(SUM(total_amount),0) as total_revenue,
                  IFNULL(AVG(total_amount),0) as avg_order_value
           FROM orders WHERE status != 'Cancelled'""",
        one=True
    )

    # Monthly breakdown (last 12 months)
    monthly = query_db(
        """SELECT DATE_FORMAT(created_at, '%%b %%Y') as month,
                  COUNT(*) as orders,
                  SUM(total_amount) as revenue
           FROM orders WHERE status != 'Cancelled'
           AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
           GROUP BY DATE_FORMAT(created_at, '%%Y-%%m'), DATE_FORMAT(created_at, '%%b %%Y')
           ORDER BY DATE_FORMAT(created_at, '%%Y-%%m') ASC"""
    )

    # Top 10 selling products
    top_products = query_db(
        """SELECT p.product_id, p.name, p.image, p.price,
                  SUM(oi.quantity) as units_sold,
                  SUM(oi.quantity * oi.price) as revenue
           FROM order_items oi
           JOIN products p ON oi.product_id = p.product_id
           JOIN orders o ON oi.order_id = o.order_id
           WHERE o.status != 'Cancelled'
           GROUP BY p.product_id, p.name, p.image, p.price
           ORDER BY units_sold DESC LIMIT 10"""
    )

    # Revenue by category
    by_category = query_db(
        """SELECT c.category_name,
                  SUM(oi.quantity * oi.price) as revenue,
                  SUM(oi.quantity) as units_sold
           FROM order_items oi
           JOIN products p ON oi.product_id = p.product_id
           JOIN categories c ON p.cat_id = c.cat_id
           JOIN orders o ON oi.order_id = o.order_id
           WHERE o.status != 'Cancelled'
           GROUP BY c.cat_id, c.category_name
           ORDER BY revenue DESC"""
    )

    # Order status breakdown
    status_breakdown = query_db(
        "SELECT status, COUNT(*) as cnt, IFNULL(SUM(total_amount),0) as revenue FROM orders GROUP BY status"
    )

    user = get_current_user()
    return render_template('admin/sales.html',
                           totals=totals,
                           monthly=monthly,
                           top_products=top_products,
                           by_category=by_category,
                           status_breakdown=status_breakdown,
                           user=user)


# ─── Payments Report ────────────────────────────────────────
@admin_bp.route('/payments')
@admin_required
def payments():
    all_orders = query_db(
        '''SELECT o.order_id, o.total_amount, o.status,
                  o.razorpay_order_id, o.razorpay_payment_id,
                  o.created_at,
                  u.name as user_name, u.email as user_email
           FROM orders o JOIN users u ON o.user_id = u.id
           ORDER BY o.created_at DESC'''
    )
    total_paid = query_db(
        "SELECT IFNULL(SUM(total_amount),0) as t FROM orders WHERE status IN ('Paid','Shipped','Delivered')",
        one=True
    )['t']
    user = get_current_user()
    return render_template('admin/payments.html',
                           orders=all_orders,
                           total_paid=float(total_paid),
                           user=user)
