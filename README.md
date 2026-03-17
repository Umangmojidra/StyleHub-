# 🛍️ StyleHub — Full-Stack E-Commerce Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask&logoColor=white"/>
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white"/>
  <img src="https://img.shields.io/badge/Razorpay-Payment%20Gateway-02042B?style=for-the-badge&logo=razorpay&logoColor=white"/>
  <img src="https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white"/>
</p>

<p align="center">
  <strong>A production-grade e-commerce web application with secure authentication, full cart & order management, Razorpay payment integration, and a feature-rich admin dashboard — built on Flask, MySQL, and JWT.</strong>
</p>

---

## 📌 Project Overview

**StyleHub** is a complete retail e-commerce platform designed to handle real-world shopping workflows — from OTP-verified registration to Razorpay checkout to admin-level order and inventory management. Built with a clean Blueprint-based architecture, it demonstrates full-stack web development with secure backend practices.

---

## ✨ Feature Highlights

| Module | Features |
|---|---|
| 🔐 **Auth** | Register, Login, Logout, OTP Verification, JWT Session, Role-based Access |
| 🛒 **Cart** | Add / Update / Remove items, Live subtotal & shipping recalculation |
| 📦 **Orders** | Place orders, Order history, Order detail view, COD + Razorpay support |
| 💳 **Payments** | Razorpay order creation, HMAC signature verification, Payment success flow |
| 🏪 **Products** | Listing with search, category filter, sort; Product detail with related items |
| 🛠️ **Admin Panel** | Dashboard KPIs, Product CRUD, Order management, User management, Sales analytics |

---

## 🏗️ Project Architecture

```
StyleHub/
│
├── app.py                        # Application entry point — Flask factory & blueprint registration
├── config.py                     # Centralised config loaded from environment variables
├── schema.sql                    # Full DB schema with auto-ID triggers (USR, CAT, PROD, ORD)
├── migration.sql                 # Database migration scripts
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
│
├── routes/                       # Blueprint modules (one per domain)
│   ├── auth_routes.py            # Register, Login, OTP, Profile, Logout
│   ├── product_routes.py         # Product listing, detail, search, filter, sort
│   ├── cart_routes.py            # Add, update, remove, view cart
│   ├── order_routes.py           # Place order, order history, order detail
│   ├── payment_routes.py         # Razorpay order creation & signature verification
│   └── admin_routes.py           # Admin dashboard, product CRUD, order & user management
│
├── utils/
│   ├── auth.py                   # JWT helpers: create_token, decode_token, @login_required, @admin_required
│   ├── db.py                     # PyMySQL helper: query_db(), get_connection()
│   └── otp.py                    # OTP generation utility
│
└── templates/                    # Jinja2 HTML templates
    ├── base.html                 # Base layout
    ├── products.html / product_detail.html
    ├── cart.html / checkout.html
    ├── orders.html / order_detail.html
    ├── login.html / register.html / verify_otp.html
    ├── dashboard.html / profile.html / addresses.html
    ├── payment_success.html
    ├── 404.html / 500.html
    └── admin/                    # Admin panel templates
        ├── dashboard.html
        ├── products.html / edit_product.html
        ├── orders.html / order_detail.html
        ├── users.html
        ├── payments.html
        └── base_admin.html
```

---

## 🗄️ Database Schema

**Auto-ID system** using MySQL triggers generates human-readable IDs:

| Table | Auto ID Format | Example |
|---|---|---|
| `users` | `USR00001` | USR00042 |
| `categories` | `CAT001` | CAT007 |
| `products` | `PROD0001` | PROD0128 |
| `orders` | `ORD00001` | ORD00391 |

**Core tables:** `users` · `categories` · `products` · `cart` · `orders` · `order_items` · `addresses` · `otp_verification`

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                          │
├─────────────────────────┬───────────────────────────────────┤
│  🔑 Authentication       │  JWT (HS256) with 24hr expiry     │
│                         │  Stored in server-side session     │
├─────────────────────────┼───────────────────────────────────┤
│  🔒 Password Hashing     │  Flask-Bcrypt (bcrypt algorithm)  │
├─────────────────────────┼───────────────────────────────────┤
│  📱 OTP Verification     │  6-digit OTP on registration      │
├─────────────────────────┼───────────────────────────────────┤
│  💳 Payment Security     │  Razorpay HMAC-SHA256 signature   │
│                         │  verification on every payment     │
├─────────────────────────┼───────────────────────────────────┤
│  🛡️ Access Control       │  @login_required decorator         │
│                         │  @admin_required decorator         │
├─────────────────────────┼───────────────────────────────────┤
│  🌿 Env Isolation        │  All secrets via .env + dotenv    │
└─────────────────────────┴───────────────────────────────────┘
```

---

## 💳 Payment Flow — Razorpay Integration

```
User clicks "Pay"
      │
      ▼
POST /payment/create-order
  → Validates cart & address
  → Creates Razorpay order (INR, paise)
  → Returns { razorpay_order_id, amount, key }
      │
      ▼
Razorpay Checkout (client-side)
  → User completes payment
  → Returns { payment_id, order_id, signature }
      │
      ▼
POST /payment/verify
  → HMAC-SHA256 signature verification
  → On success → place order + clear cart
  → Redirect → /payment/success
```

---

## 🛠️ Admin Dashboard

The `/admin` panel provides full operational control:

- **KPI Cards** — Total orders, users, products, revenue at a glance
- **Sales Analytics** — Daily revenue (last 7 days), monthly trend (last 6 months)
- **Top Products** — Best-sellers ranked by units sold & revenue
- **Low Stock Alerts** — Products with stock < 5 flagged automatically
- **Order Management** — View, filter, and update order status (Pending → Shipped → Delivered)
- **Product CRUD** — Add, edit, delete products with category assignment
- **User Management** — View all users, block/unblock accounts
- **Payment Logs** — Full payment transaction history

---

## ⚙️ Getting Started

### Prerequisites

```
Python 3.12+
MySQL 8.0+
Razorpay account (test keys for development)
```

### 1. Clone & Install

```bash
git clone https://github.com/Umangmojidra/stylehub.git
cd stylehub

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
SECRET_KEY=your-super-secret-key
JWT_SECRET=your-jwt-secret

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=ecommerce_db

RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXXXXXXXXX

DEBUG=True
```

### 3. Set Up the Database

```bash
mysql -u root -p < schema.sql
```

### 4. Run the Application

```bash
python app.py
```

Visit: **http://localhost:5000**

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Flask 3.0.0 |
| **Database** | MySQL 8.0 via PyMySQL 1.1.0 |
| **Authentication** | PyJWT 2.8.0 + Flask-Bcrypt 1.0.1 |
| **Payment Gateway** | Razorpay SDK 1.4.1 |
| **Templating** | Jinja2 (Flask built-in) |
| **Environment Management** | python-dotenv 1.0.0 |
| **Password Security** | Werkzeug 3.0.1 + bcrypt |

---

## 📦 API Routes Reference

| Method | Route | Auth | Description |
|---|---|---|---|
| GET/POST | `/register` | Public | User registration + OTP trigger |
| GET/POST | `/verify-otp` | Session | OTP verification & account creation |
| GET/POST | `/login` | Public | Login + JWT issuance |
| GET | `/logout` | Login | Clear session |
| GET | `/` | Public | Product listing (search, filter, sort) |
| GET | `/product/<id>` | Public | Product detail + related items |
| GET | `/cart` | Login | View cart |
| POST | `/cart/add` | Login | Add item to cart |
| GET | `/checkout` | Login | Checkout with address selection |
| POST | `/payment/create-order` | Login | Create Razorpay order |
| POST | `/payment/verify` | Login | Verify payment + place order |
| GET | `/orders` | Login | Order history |
| GET | `/orders/<id>` | Login | Order detail |
| GET | `/admin/` | Admin | Admin dashboard |
| GET/POST | `/admin/products` | Admin | Product management |
| GET | `/admin/orders` | Admin | Order management |
| GET | `/admin/users` | Admin | User management |

---

## 🗂️ Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session secret | — |
| `JWT_SECRET` | JWT signing key | — |
| `DB_HOST` | MySQL host | `localhost` |
| `DB_PORT` | MySQL port | `3306` |
| `DB_USER` | MySQL username | `root` |
| `DB_PASSWORD` | MySQL password | — |
| `DB_NAME` | Database name | `ecommerce_db` |
| `RAZORPAY_KEY_ID` | Razorpay public key | — |
| `RAZORPAY_KEY_SECRET` | Razorpay secret key | — |
| `DEBUG` | Flask debug mode | `True` |

---

## 👤 Author

**Umang Mojidra**  
Full-Stack Developer | Python · Flask · MySQL  
[LinkedIn](https://linkedin.com/in/umangmojidra) • [GitHub](https://github.com/Umangmojidra) 

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  <i>Built to demonstrate end-to-end full-stack web development with secure authentication, payment integration, and admin operations.</i>
</p>
