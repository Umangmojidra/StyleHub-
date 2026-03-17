-- ============================================================
-- StyleHub E-Commerce — Database Schema v2
-- Custom Auto-ID Triggers: USR00001, CAT001, PROD0001, ORD00001
-- ============================================================

CREATE DATABASE IF NOT EXISTS ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ecommerce_db;

-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                  VARCHAR(10) PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    email               VARCHAR(150) UNIQUE NOT NULL,
    password            VARCHAR(255),
    phone               VARCHAR(20) UNIQUE,
    role                ENUM('admin','user') DEFAULT 'user',
    is_email_verified   BOOLEAN DEFAULT FALSE,
    is_phone_verified   BOOLEAN DEFAULT FALSE,
    status              ENUM('active','inactive','blocked') DEFAULT 'active',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login          DATETIME
);

-- Trigger: Auto-generate user ID -> USR00001, USR00002, ...
DROP TRIGGER IF EXISTS before_insert_users;

DELIMITER //

CREATE TRIGGER before_insert_users
BEFORE INSERT ON users
FOR EACH ROW
BEGIN
    DECLARE next_id INT;

    SELECT IFNULL(MAX(CAST(SUBSTRING(id, 4) AS UNSIGNED)), 0) + 1
    INTO next_id
    FROM users;

    SET NEW.id = CONCAT('USR', LPAD(next_id, 5, '0'));
END //

DELIMITER ;


-- ============================================================
-- TABLE: otp_verification
-- ============================================================
CREATE TABLE IF NOT EXISTS otp_verification (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     VARCHAR(10),
    otp_code    VARCHAR(6) NOT NULL,
    expires_at  DATETIME NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- ============================================================
-- TABLE: categories
-- ============================================================
CREATE TABLE IF NOT EXISTS categories (
    cat_id          VARCHAR(6) PRIMARY KEY,
    category_name   VARCHAR(100) NOT NULL,
    description     TEXT,
    status          ENUM('active','inactive') DEFAULT 'active'
);

-- Trigger: Auto-generate category ID -> CAT001, CAT002, ...
DROP TRIGGER IF EXISTS before_insert_category;

DELIMITER //

CREATE TRIGGER before_insert_category
BEFORE INSERT ON categories
FOR EACH ROW
BEGIN
    DECLARE next_id INT;

    SELECT IFNULL(MAX(CAST(SUBSTRING(cat_id, 4) AS UNSIGNED)), 0) + 1
    INTO next_id
    FROM categories;

    SET NEW.cat_id = CONCAT('CAT', LPAD(next_id, 3, '0'));
END //

DELIMITER ;


-- ============================================================
-- TABLE: products
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    product_id  VARCHAR(10) PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    description TEXT,
    cat_id      VARCHAR(6) NOT NULL,
    price       DECIMAL(10, 2) NOT NULL,
    discount    DECIMAL(5, 2) DEFAULT 0,
    size        VARCHAR(50),
    color       VARCHAR(50),
    stock       INT DEFAULT 0,
    image       VARCHAR(255),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cat_id) REFERENCES categories(cat_id)
);

-- Trigger: Auto-generate product ID -> PROD0001, PROD0002, ...
DROP TRIGGER IF EXISTS before_insert_products;

DELIMITER //

CREATE TRIGGER before_insert_products
BEFORE INSERT ON products
FOR EACH ROW
BEGIN
    DECLARE next_id INT;

    SELECT IFNULL(MAX(CAST(SUBSTRING(product_id, 5) AS UNSIGNED)), 0) + 1
    INTO next_id
    FROM products;

    SET NEW.product_id = CONCAT('PROD', LPAD(next_id, 4, '0'));
END //

DELIMITER ;


-- ============================================================
-- TABLE: cart
-- ============================================================
CREATE TABLE IF NOT EXISTS cart (
    cart_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id     VARCHAR(10) NOT NULL,
    product_id  VARCHAR(10) NOT NULL,
    quantity    INT NOT NULL DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_cart_item (user_id, product_id),
    FOREIGN KEY (user_id)    REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
) AUTO_INCREMENT = 20260001;


-- ============================================================
-- TABLE: addresses
-- ============================================================
CREATE TABLE IF NOT EXISTS addresses (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         VARCHAR(10) NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    phone           VARCHAR(20) NOT NULL,
    address_line    VARCHAR(255) NOT NULL,
    city            VARCHAR(100) NOT NULL,
    state           VARCHAR(100) NOT NULL,
    pincode         VARCHAR(10)  NOT NULL,
    is_default      TINYINT(1)   DEFAULT 0,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- ============================================================
-- TABLE: orders
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    order_id            VARCHAR(10) PRIMARY KEY,
    user_id             VARCHAR(10) NOT NULL,
    total_amount        DECIMAL(10, 2) NOT NULL,
    payment_id          VARCHAR(100),
    status              ENUM('Pending','Paid','Shipped','Delivered','Cancelled') DEFAULT 'Pending',
    razorpay_order_id   VARCHAR(100),
    razorpay_payment_id VARCHAR(100),
    razorpay_signature  VARCHAR(255),
    address_id          INT,
    shipping_snapshot   TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Trigger: Auto-generate order ID -> ORD00001, ORD00002, ...
DROP TRIGGER IF EXISTS before_insert_orders;

DELIMITER //

CREATE TRIGGER before_insert_orders
BEFORE INSERT ON orders
FOR EACH ROW
BEGIN
    DECLARE next_id INT;

    SELECT IFNULL(MAX(CAST(SUBSTRING(order_id, 4) AS UNSIGNED)), 0) + 1
    INTO next_id
    FROM orders;

    SET NEW.order_id = CONCAT('ORD', LPAD(next_id, 5, '0'));
END //

DELIMITER ;


-- ============================================================
-- TABLE: order_items
-- ============================================================
CREATE TABLE IF NOT EXISTS order_items (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    order_id    VARCHAR(10) NOT NULL,
    product_id  VARCHAR(10),
    quantity    INT NOT NULL,
    price       DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL
);


-- ============================================================
-- SEED DATA
-- ============================================================

-- Admin user (password: Admin@123)
-- We bypass the trigger by providing the ID explicitly
INSERT IGNORE INTO users (id, name, email, phone, password, role, is_email_verified, status)
VALUES (
    'USR00001',
    'Admin User',
    'admin@shop.com',
    '9999999999',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewJyJXRXJMLBYoVa',
    'admin',
    TRUE,
    'active'
);

-- Categories (hard-code IDs to guarantee seed order)
INSERT IGNORE INTO categories (cat_id, category_name, description) VALUES
('CAT001', 'Men',                'Clothing and accessories for men'),
('CAT002', 'Women',              'Clothing and accessories for women'),
('CAT003', 'Kids',               'Clothing and accessories for kids'),
('CAT004', 'Accessories',        'Bags, belts, watches and more'),
('CAT005', 'Seasonal Collection','Latest seasonal and festive collections');

-- Products (trigger fires and assigns PROD0001 ... PROD0008)
INSERT INTO products (name, description, cat_id, price, discount, size, color, stock, image) VALUES
('Classic White Oxford Shirt',
 'Premium cotton slim-fit shirt, perfect for formal and casual wear.',
 'CAT001', 1299.00, 10, 'S,M,L,XL', 'White', 50,
 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=400&q=80'),

('Slim Fit Chinos',
 'Comfortable stretch chinos in khaki tone. Everyday essential.',
 'CAT001', 1799.00, 15, 'S,M,L,XL', 'Khaki', 40,
 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400&q=80'),

('Floral Wrap Dress',
 'Elegant floral print wrap dress, ideal for brunch and outings.',
 'CAT002', 2199.00, 20, 'XS,S,M,L', 'Multicolor', 30,
 'https://images.unsplash.com/photo-1612336307429-8a898d10e223?w=400&q=80'),

('High-Waist Jeans',
 'Trendy high-waist blue denim jeans with a comfortable stretch fit.',
 'CAT002', 2499.00, 10, 'S,M,L,XL', 'Blue', 45,
 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400&q=80'),

('Kids Graphic Tee',
 'Fun printed cotton t-shirt for kids. Available in vibrant colors.',
 'CAT003', 599.00, 5, 'XS,S,M', 'Red', 80,
 'https://images.unsplash.com/photo-1622290291468-a28f7a7dc6a8?w=400&q=80'),

('Leather Crossbody Bag',
 'Genuine leather mini crossbody bag with adjustable strap.',
 'CAT004', 3499.00, 0, 'One Size', 'Tan', 20,
 'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400&q=80'),

('Aviator Sunglasses',
 'UV400 protected classic aviator sunglasses. Style meets function.',
 'CAT004', 899.00, 25, 'One Size', 'Gold', 60,
 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&q=80'),

('Festive Kurta Set',
 'Premium silk-blend kurta with matching pyjama. Perfect for occasions.',
 'CAT005', 3999.00, 30, 'S,M,L,XL,XXL', 'Navy Blue', 25,
 'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=400&q=80');
