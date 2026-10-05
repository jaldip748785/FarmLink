CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO categories (name, description) VALUES
('Vegetables', 'Fresh vegetables'),
('Fruits', 'Fresh fruits'),
('Grains', 'Food grains'),
('Pulses', 'Different types of pulses'),
('Dairy', 'Milk and dairy products'),
('Spices', 'Natural spices');