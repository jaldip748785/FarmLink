-- FarmLink Bargaining and Orders Database Schema Updates

-- Add bargaining options to products
ALTER TABLE products ADD COLUMN allow_bargaining BOOLEAN DEFAULT FALSE;
ALTER TABLE products ADD COLUMN min_price DECIMAL(10, 2) DEFAULT 0.00;

-- Bargaining Sessions Table
CREATE TABLE IF NOT EXISTS bargaining_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    buyer_id INT NOT NULL,
    farmer_id INT NOT NULL,
    quantity INT NOT NULL,
    listed_price DECIMAL(10, 2) NOT NULL,
    final_price DECIMAL(10, 2) DEFAULT NULL,
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, NEGOTIATING, ACCEPTED, REJECTED, EXPIRED, CANCELLED, COMPLETED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Bargaining Offers Table (to maintain negotiation log history)
CREATE TABLE IF NOT EXISTS bargaining_offers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    offer_price DECIMAL(10, 2) NOT NULL,
    quantity INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    message TEXT DEFAULT NULL,
    offer_type VARCHAR(50) NOT NULL, -- INITIAL, COUNTER, ACCEPTANCE
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, ACCEPTED, REJECTED, EXPIRED, CANCELLED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (session_id) REFERENCES bargaining_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Orders Table (to store locked price and checkout details)
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    buyer_id INT NOT NULL,
    farmer_id INT NOT NULL,
    quantity INT NOT NULL,
    original_price DECIMAL(10, 2) NOT NULL,
    negotiated_price DECIMAL(10, 2) DEFAULT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    bargaining_session_id INT DEFAULT NULL,
    status VARCHAR(50) DEFAULT 'Pending', -- Pending, Confirmed, Processing, Shipped, Out for Delivery, Delivered, Cancelled
    payment_method VARCHAR(50) DEFAULT 'cash_on_delivery', -- online_payment, cash_on_delivery
    payment_status VARCHAR(50) DEFAULT 'Pending', -- Pending, Paid, Failed, Refunded
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (bargaining_session_id) REFERENCES bargaining_sessions(id) ON DELETE SET NULL
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    link VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add payment method and status columns to orders table

