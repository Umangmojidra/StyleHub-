"""
auth_routes.py - Authentication Blueprint
Handles user registration, login, logout, OTP verification, and profile.
"""
import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
from utils.db import query_db
from utils.auth import create_token, login_required, get_current_user
from utils.otp import generate_otp

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()


def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    return re.match(r'^\d{10}$', phone) is not None


# ─── Register ───────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if get_current_user():
        return redirect(url_for('products.index'))

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        phone    = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        errors = []
        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters.')
        if not validate_email(email):
            errors.append('Invalid email address.')
        if not validate_phone(phone):
            errors.append('Phone must be a 10-digit number.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html', name=name, email=email, phone=phone)

        existing = query_db('SELECT id FROM users WHERE email = %s', (email,), one=True)
        if existing:
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        otp = generate_otp()

        session['register_data'] = {
            'name': name,
            'email': email,
            'phone': phone,
            'password': password
        }
        session['otp'] = otp

        print(f"[OTP] {otp}")   # In production, send via email/SMS

        flash('OTP sent to your phone/email.', 'info')
        return redirect(url_for('auth.verify_otp'))

    return render_template('register.html')


# ─── Verify OTP ─────────────────────────────────────────────
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'register_data' not in session:
        flash('Please register first.', 'warning')
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        user_otp = request.form.get('otp', '').strip()

        try:
            if int(user_otp) == session.get('otp'):
                data    = session.get('register_data')
                pw_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')

                query_db(
                    'INSERT INTO users (name, email, phone, password, is_phone_verified) VALUES (%s,%s,%s,%s,%s)',
                    (data['name'], data['email'], data['phone'], pw_hash, True),
                    commit=True
                )

                session.pop('otp', None)
                session.pop('register_data', None)

                flash('Account verified and created! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Invalid OTP. Please try again.', 'danger')
        except (ValueError, TypeError):
            flash('Invalid OTP format.', 'danger')

    return render_template('verify_otp.html')


# ─── Login ──────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if get_current_user():
        return redirect(url_for('products.index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('login.html', email=email)

        user = query_db('SELECT * FROM users WHERE email = %s', (email,), one=True)

        if user and bcrypt.check_password_hash(user['password'], password):
            if user.get('status') == 'blocked':
                flash('Your account has been blocked. Contact support.', 'danger')
                return render_template('login.html', email=email)

            token = create_token(user['id'], user['email'], user['role'])
            session['token']     = token
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for('products.index'))

        flash('Invalid email or password.', 'danger')
        return render_template('login.html', email=email)

    return render_template('login.html')


# ─── Logout ─────────────────────────────────────────────────
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ─── Profile ────────────────────────────────────────────────
@auth_bp.route('/profile')
@login_required
def profile():
    user = query_db(
        'SELECT id, name, email, phone, role, created_at FROM users WHERE id = %s',
        (request.user['user_id'],), one=True
    )
    return render_template('profile.html', user=user)


# ─── API: Register ──────────────────────────────────────────
@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    data     = request.get_json()
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    phone    = data.get('phone', '').strip()
    password = data.get('password', '')

    if not all([name, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Invalid email'}), 400

    existing = query_db('SELECT id FROM users WHERE email = %s', (email,), one=True)
    if existing:
        return jsonify({'error': 'Email already registered'}), 409

    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    query_db(
        'INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)',
        (name, email, phone, pw_hash), commit=True
    )
    new_user = query_db('SELECT id FROM users WHERE email = %s', (email,), one=True)
    token = create_token(new_user['id'], email)
    return jsonify({'token': token, 'message': 'Registration successful'}), 201


# ─── API: Login ─────────────────────────────────────────────
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data     = request.get_json()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = query_db('SELECT * FROM users WHERE email = %s', (email,), one=True)
    if user and bcrypt.check_password_hash(user['password'], password):
        token = create_token(user['id'], user['email'], user['role'])
        return jsonify({'token': token, 'name': user['name'], 'role': user['role']})

    return jsonify({'error': 'Invalid credentials'}), 401


# ─── API: Profile ───────────────────────────────────────────
@auth_bp.route('/api/profile', methods=['GET'])
@login_required
def api_profile():
    user = query_db(
        'SELECT id, name, email, phone, role, created_at FROM users WHERE id = %s',
        (request.user['user_id'],), one=True
    )
    if user:
        user['created_at'] = str(user['created_at'])
    return jsonify(user)