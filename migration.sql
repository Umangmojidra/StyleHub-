-- ============================================================
-- MIGRATION: Add shipping addresses + Razorpay payment support
-- Run this file AFTER your existing schema.sql is already loaded
-- ============================================================

USE ecommerce_db;

-- ──────────────────────────────────────────────
-- 1. SHIPPING ADDRESSES TABLE
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS addresses (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      VARCHAR(10) NOT NULL,
    full_name    VARCHAR(100) NOT NULL,
    phone        VARCHAR(20) NOT NULL,
    address_line VARCHAR(255) NOT NULL,
    city         VARCHAR(100) NOT NULL,
    state        VARCHAR(100) NOT NULL,
    pincode      VARCHAR(10) NOT NULL,
    is_default   BOOLEAN DEFAULT FALSE,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ──────────────────────────────────────────────
-- 2. ADD RAZORPAY + ADDRESS FIELDS TO ORDERS
-- ──────────────────────────────────────────────
ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS razorpay_order_id   VARCHAR(100) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS razorpay_payment_id  VARCHAR(100) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS razorpay_signature   VARCHAR(255) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS address_id           INT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS shipping_snapshot    TEXT DEFAULT NULL,
    ADD CONSTRAINT fk_orders_address
        FOREIGN KEY (address_id) REFERENCES addresses(id) ON DELETE SET NULL;

-- ──────────────────────────────────────────────
-- 3. VERIFY
-- ──────────────────────────────────────────────
SELECT 'Migration complete!' AS status;
SELECT TABLE_NAME FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'ecommerce_db';
