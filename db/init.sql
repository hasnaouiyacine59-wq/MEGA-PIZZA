-- ============================================
-- MEGA PIZZA DELIVERY SYSTEM - DATABASE INIT
-- ============================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable Row Level Security (optional)
ALTER DATABASE mega_pizza_db SET "app.jwt_secret" TO 'your-jwt-secret-here';

-- ============================================
-- CREATE BASE TABLES (NO FOREIGN KEY DEPENDENCIES)
-- ============================================

-- Create Restaurants Table (independent)
CREATE TABLE IF NOT EXISTS restaurants (
    restaurant_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CREATE USERS TABLE (Authentication)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    public_id UUID DEFAULT gen_random_uuid() UNIQUE,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'employee' CHECK (role IN ('admin', 'manager', 'employee', 'driver', 'user')),
    is_active BOOLEAN DEFAULT true,
    restaurant_id VARCHAR(20) REFERENCES restaurants(restaurant_id),
    phone_number VARCHAR(20),
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CREATE DRIVERS TABLE (References users)
-- ============================================
CREATE TABLE IF NOT EXISTS drivers (
    driver_id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Driver-specific information
    license_number VARCHAR(50),
    vehicle_type VARCHAR(20) CHECK (vehicle_type IN ('car', 'motorcycle', 'bicycle', 'scooter')),
    vehicle_model VARCHAR(50),
    license_plate VARCHAR(20),
    
    -- Driver status
    is_available BOOLEAN DEFAULT true,
    current_location VARCHAR(100),
    rating DECIMAL(3, 2) DEFAULT 0.00 CHECK (rating >= 0 AND rating <= 5),
    
    -- Statistics
    total_deliveries INTEGER DEFAULT 0,
    completed_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0,
    total_earnings DECIMAL(10, 2) DEFAULT 0.00,
    avg_delivery_time INTEGER, -- in minutes
    
    -- Working hours
    shift_start TIME,
    shift_end TIME,
    is_on_shift BOOLEAN DEFAULT false,
    
    -- Emergency contact
    emergency_contact VARCHAR(50),
    emergency_phone VARCHAR(20),
    
    -- Document expiry dates
    license_expiry DATE,
    insurance_expiry DATE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CREATE CUSTOMERS TABLE (References users)
-- ============================================
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    user_id INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CREATE MENU ITEMS TABLE (References restaurants)
-- ============================================
CREATE TABLE IF NOT EXISTS menu_items (
    item_id VARCHAR(20) PRIMARY KEY,
    restaurant_id VARCHAR(20) REFERENCES restaurants(restaurant_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50),
    is_available BOOLEAN DEFAULT true,
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CREATE ADDRESSES TABLE (References customers)
-- ============================================
CREATE TABLE IF NOT EXISTS addresses (
    address_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(20) REFERENCES customers(customer_id),
    street TEXT NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CREATE ORDERS TABLE (References multiple tables)
-- ============================================
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(30) PRIMARY KEY,
    customer_id VARCHAR(20) REFERENCES customers(customer_id),
    restaurant_id VARCHAR(20) REFERENCES restaurants(restaurant_id),
    address_id INTEGER REFERENCES addresses(address_id),
    order_status VARCHAR(20) DEFAULT 'pending' CHECK (order_status IN ('pending', 'confirmed', 'preparing', 'ready', 'out_for_delivery', 'delivered', 'cancelled')),
    delivery_type VARCHAR(10) CHECK (delivery_type IN ('delivery', 'pickup')),
    special_instructions TEXT,
    subtotal DECIMAL(10, 2) NOT NULL CHECK (subtotal >= 0),
    tax DECIMAL(10, 2) DEFAULT 0 CHECK (tax >= 0),
    delivery_fee DECIMAL(10, 2) DEFAULT 0 CHECK (delivery_fee >= 0),
    discount DECIMAL(10, 2) DEFAULT 0 CHECK (discount >= 0),
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0),
    payment_method VARCHAR(20),
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    transaction_id VARCHAR(100),
    
    -- Driver reference
    driver_id INTEGER REFERENCES drivers(driver_id),
    driver_rating INTEGER CHECK (driver_rating >= 1 AND driver_rating <= 5),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimated_delivery TIMESTAMP,
    delivered_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CREATE ORDER ITEMS TABLE (References orders & menu_items)
-- ============================================
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id VARCHAR(30) REFERENCES orders(order_id) ON DELETE CASCADE,
    item_id VARCHAR(20) REFERENCES menu_items(item_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    customizations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CREATE ORDER STATUS HISTORY TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS order_status_history (
    history_id SERIAL PRIMARY KEY,
    order_id VARCHAR(30) REFERENCES orders(order_id),
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by INTEGER REFERENCES users(user_id)
);

-- ============================================
-- CREATE AUTHENTICATION TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS login_attempts (
    attempt_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(128) PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    token TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CREATE INDEXES
-- ============================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_restaurant ON users(restaurant_id);

-- Drivers indexes
CREATE INDEX IF NOT EXISTS idx_drivers_user ON drivers(user_id);
CREATE INDEX IF NOT EXISTS idx_drivers_available ON drivers(is_available) WHERE is_available = true;
CREATE INDEX IF NOT EXISTS idx_drivers_on_shift ON drivers(is_on_shift) WHERE is_on_shift = true;
CREATE INDEX IF NOT EXISTS idx_drivers_rating ON drivers(rating DESC);
CREATE INDEX IF NOT EXISTS idx_drivers_vehicle ON drivers(vehicle_type);

-- Customers indexes
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone_number);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_user ON customers(user_id);

-- Addresses indexes
CREATE INDEX IF NOT EXISTS idx_addresses_customer ON addresses(customer_id);
CREATE INDEX IF NOT EXISTS idx_addresses_location ON addresses(latitude, longitude);

-- Menu items indexes
CREATE INDEX IF NOT EXISTS idx_menu_items_restaurant ON menu_items(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category);
CREATE INDEX IF NOT EXISTS idx_menu_items_price ON menu_items(price);
CREATE INDEX IF NOT EXISTS idx_menu_items_available ON menu_items(is_available) WHERE is_available = true;

-- Orders indexes
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_restaurant ON orders(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_driver ON orders(driver_id);
CREATE INDEX IF NOT EXISTS idx_orders_delivery_type ON orders(delivery_type);
CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status);

-- Order items indexes
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_item ON order_items(item_id);

-- Authentication indexes
CREATE INDEX IF NOT EXISTS idx_login_attempts_user ON login_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(attempted_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires ON password_reset_tokens(expires_at);

-- Order status history indexes
CREATE INDEX IF NOT EXISTS idx_order_history_order ON order_status_history(order_id);
CREATE INDEX IF NOT EXISTS idx_order_history_changed_at ON order_status_history(changed_at);

-- ============================================
-- CREATE TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_menu_items_updated_at BEFORE UPDATE ON menu_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_drivers_updated_at BEFORE UPDATE ON drivers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- INSERT SAMPLE DATA
-- ============================================

-- Insert sample restaurants
INSERT INTO restaurants (restaurant_id, name, address, phone, is_active) 
VALUES 
    ('REST-001', 'Burger Palace', '123 Food Street, Springfield', '+1234567890', true),
    ('REST-002', 'Pizza Heaven', '456 Pizza Road, Metropolis', '+1234567891', true),
    ('REST-003', 'Taco Fiesta', '789 Taco Lane, Gotham', '+1234567892', true),
    ('REST-004', 'Sushi Express', '321 Sushi Blvd, Tokyo Town', '+1234567893', true),
    ('REST-005', 'Pasta Paradise', '654 Pasta Ave, Little Italy', '+1234567894', true)
ON CONFLICT (restaurant_id) DO NOTHING;

-- Create default admin user (password: Admin@123)
INSERT INTO users (username, email, password_hash, role, restaurant_id, phone_number, is_active) 
VALUES (
    'admin', 
    'admin@megapizza.com', 
    crypt('Admin@123', gen_salt('bf', 12)), 
    'admin', 
    'REST-001', 
    '+1234567891', 
    true
)
ON CONFLICT (username) DO NOTHING;

-- Create sample manager user (password: Manager@123)
INSERT INTO users (username, email, password_hash, role, restaurant_id, phone_number, is_active) 
VALUES (
    'manager1', 
    'manager@megapizza.com', 
    crypt('Manager@123', gen_salt('bf', 12)), 
    'manager', 
    'REST-002', 
    '+1234567895', 
    true
)
ON CONFLICT (username) DO NOTHING;

-- Create sample driver users (password: Driver@123)
INSERT INTO users (username, email, password_hash, role, phone_number, is_active) 
VALUES 
    (
        'driver1', 
        'driver1@megapizza.com', 
        crypt('Driver@123', gen_salt('bf', 12)), 
        'driver', 
        '+1234567892', 
        true
    ),
    (
        'driver2', 
        'driver2@megapizza.com', 
        crypt('Driver@123', gen_salt('bf', 12)), 
        'driver', 
        '+1234567896', 
        true
    ),
    (
        'driver3', 
        'driver3@megapizza.com', 
        crypt('Driver@123', gen_salt('bf', 12)), 
        'driver', 
        '+1234567897', 
        true
    )
ON CONFLICT (username) DO NOTHING;

-- Create sample customer user (password: Customer@123)
INSERT INTO users (username, email, password_hash, role, phone_number, is_active) 
VALUES (
    'customer1', 
    'customer@example.com', 
    crypt('Customer@123', gen_salt('bf', 12)), 
    'user', 
    '+1234567898', 
    true
)
ON CONFLICT (username) DO NOTHING;

-- Create driver profiles
INSERT INTO drivers (
    user_id, 
    license_number, 
    vehicle_type, 
    vehicle_model, 
    license_plate,
    is_available,
    rating,
    total_deliveries,
    completed_deliveries,
    total_earnings,
    avg_delivery_time,
    shift_start,
    shift_end,
    is_on_shift,
    emergency_contact,
    emergency_phone
)
SELECT 
    u.user_id,
    'DL' || (100000 + row_number() over ()),
    CASE (row_number() over ()) 
        WHEN 1 THEN 'motorcycle' 
        WHEN 2 THEN 'car' 
        ELSE 'bicycle' 
    END,
    CASE (row_number() over ()) 
        WHEN 1 THEN 'Yamaha FZ' 
        WHEN 2 THEN 'Toyota Corolla' 
        ELSE 'Giant Escape' 
    END,
    'MH-' || (10 + row_number() over ()) || '-AB-' || (1000 + row_number() over ()),
    true,
    4.5 - (row_number() over () * 0.1),
    25 + (row_number() over () * 5),
    24 + (row_number() over () * 5),
    350.00 + (row_number() over () * 100),
    15 + (row_number() over () * 2),
    '09:00:00',
    '17:00:00',
    true,
    'Emergency Contact ' || row_number() over (),
    '+1234567' || (890 + row_number() over ())
FROM users u 
WHERE u.username LIKE 'driver%'
ON CONFLICT (user_id) DO NOTHING;

-- Create sample customers
INSERT INTO customers (customer_id, name, phone_number, email, user_id) 
VALUES 
    ('CUST-001', 'John Doe', '+1234567800', 'john.doe@example.com', 
        (SELECT user_id FROM users WHERE username = 'customer1')),
    ('CUST-002', 'Jane Smith', '+1234567801', 'jane.smith@example.com', NULL),
    ('CUST-003', 'Bob Johnson', '+1234567802', 'bob.johnson@example.com', NULL),
    ('CUST-004', 'Alice Williams', '+1234567803', 'alice.williams@example.com', NULL),
    ('CUST-005', 'Charlie Brown', '+1234567804', 'charlie.brown@example.com', NULL)
ON CONFLICT (customer_id) DO NOTHING;

-- Create sample addresses
INSERT INTO addresses (customer_id, street, city, state, postal_code, country, is_default) 
VALUES 
    ('CUST-001', '123 Main St', 'Springfield', 'IL', '62701', 'USA', true),
    ('CUST-001', '456 Oak Ave', 'Springfield', 'IL', '62702', 'USA', false),
    ('CUST-002', '789 Pine Rd', 'Metropolis', 'NY', '10001', 'USA', true),
    ('CUST-003', '321 Elm St', 'Gotham', 'NJ', '07001', 'USA', true),
    ('CUST-004', '654 Maple Dr', 'Tokyo Town', 'CA', '90001', 'USA', true),
    ('CUST-005', '987 Cedar Ln', 'Little Italy', 'TX', '75001', 'USA', true)
ON CONFLICT DO NOTHING;

-- Create sample menu items
INSERT INTO menu_items (item_id, restaurant_id, name, description, price, category, is_available) 
VALUES 
    -- Pizza Heaven items
    ('PIZ-001', 'REST-002', 'Margherita Pizza', 'Classic pizza with tomato sauce and mozzarella', 12.99, 'Pizza', true),
    ('PIZ-002', 'REST-002', 'Pepperoni Pizza', 'Pizza with pepperoni and extra cheese', 14.99, 'Pizza', true),
    ('PIZ-003', 'REST-002', 'Vegetarian Pizza', 'Pizza with fresh vegetables and cheese', 13.99, 'Pizza', true),
    ('PIZ-004', 'REST-002', 'Hawaiian Pizza', 'Pizza with ham and pineapple', 15.99, 'Pizza', true),
    ('PIZ-005', 'REST-002', 'Meat Lovers Pizza', 'Pizza with all kinds of meat', 16.99, 'Pizza', true),
    
    -- Burger Palace items
    ('BUR-001', 'REST-001', 'Cheeseburger', 'Beef burger with cheese and lettuce', 9.99, 'Burgers', true),
    ('BUR-002', 'REST-001', 'Bacon Burger', 'Burger with crispy bacon', 11.99, 'Burgers', true),
    ('BUR-003', 'REST-001', 'Veggie Burger', 'Plant-based burger with veggies', 8.99, 'Burgers', true),
    ('BUR-004', 'REST-001', 'Double Cheeseburger', 'Double beef patty with double cheese', 13.99, 'Burgers', true),
    
    -- Taco Fiesta items
    ('TAC-001', 'REST-003', 'Beef Taco', 'Soft taco with seasoned beef', 3.99, 'Tacos', true),
    ('TAC-002', 'REST-003', 'Chicken Taco', 'Soft taco with grilled chicken', 3.99, 'Tacos', true),
    ('TAC-003', 'REST-003', 'Fish Taco', 'Taco with battered fish', 4.99, 'Tacos', true),
    ('TAC-004', 'REST-003', 'Vegetarian Taco', 'Taco with beans and veggies', 2.99, 'Tacos', true),
    
    -- Sushi Express items
    ('SUS-001', 'REST-004', 'California Roll', 'Crab, avocado, cucumber', 8.99, 'Sushi', true),
    ('SUS-002', 'REST-004', 'Salmon Nigiri', 'Fresh salmon on rice', 6.99, 'Sushi', true),
    ('SUS-003', 'REST-004', 'Dragon Roll', 'Eel and avocado roll', 12.99, 'Sushi', true),
    
    -- Pasta Paradise items
    ('PAS-001', 'REST-005', 'Spaghetti Carbonara', 'Spaghetti with egg and bacon', 11.99, 'Pasta', true),
    ('PAS-002', 'REST-005', 'Fettuccine Alfredo', 'Fettuccine with cream sauce', 10.99, 'Pasta', true),
    ('PAS-003', 'REST-005', 'Lasagna', 'Layered pasta with meat sauce', 13.99, 'Pasta', true)
ON CONFLICT (item_id) DO NOTHING;

-- Create sample orders
INSERT INTO orders (
    order_id, customer_id, restaurant_id, address_id, order_status, 
    delivery_type, subtotal, tax, delivery_fee, total_amount, 
    payment_method, payment_status, created_at
) 
VALUES 
    (
        'ORD-001-' || EXTRACT(YEAR FROM CURRENT_DATE), 
        'CUST-001', 
        'REST-002', 
        1, 
        'delivered',
        'delivery', 
        27.98, 
        2.23, 
        2.99, 
        33.20,
        'credit_card', 
        'paid', 
        CURRENT_TIMESTAMP - INTERVAL '2 hours'
    ),
    (
        'ORD-002-' || EXTRACT(YEAR FROM CURRENT_DATE), 
        'CUST-002', 
        'REST-001', 
        3, 
        'out_for_delivery',
        'delivery', 
        21.98, 
        1.76, 
        2.99, 
        26.73,
        'cash', 
        'paid', 
        CURRENT_TIMESTAMP - INTERVAL '1 hour'
    ),
    (
        'ORD-003-' || EXTRACT(YEAR FROM CURRENT_DATE), 
        'CUST-003', 
        'REST-003', 
        4, 
        'preparing',
        'pickup', 
        11.97, 
        0.96, 
        0.00, 
        12.93,
        'credit_card', 
        'paid', 
        CURRENT_TIMESTAMP - INTERVAL '30 minutes'
    ),
    (
        'ORD-004-' || EXTRACT(YEAR FROM CURRENT_DATE), 
        'CUST-004', 
        'REST-004', 
        5, 
        'pending',
        'delivery', 
        19.98, 
        1.60, 
        2.99, 
        24.57,
        'cash', 
        'pending', 
        CURRENT_TIMESTAMP
    )
ON CONFLICT (order_id) DO NOTHING;

-- Assign drivers to orders
UPDATE orders SET driver_id = (SELECT driver_id FROM drivers WHERE user_id = (SELECT user_id FROM users WHERE username = 'driver1')) 
WHERE order_id LIKE 'ORD-001%';

UPDATE orders SET driver_id = (SELECT driver_id FROM drivers WHERE user_id = (SELECT user_id FROM users WHERE username = 'driver2')) 
WHERE order_id LIKE 'ORD-002%';

-- Create order items
INSERT INTO order_items (order_id, item_id, quantity, unit_price) 
VALUES 
    ((SELECT order_id FROM orders WHERE order_id LIKE 'ORD-001%'), 'PIZ-001', 1, 12.99),
    ((SELECT order_id FROM orders WHERE order_id LIKE 'ORD-001%'), 'PIZ-002', 1, 14.99),
    ((SELECT order_id FROM orders WHERE order_id LIKE 'ORD-002%'), 'BUR-001', 2, 9.99),
    ((SELECT order_id FROM orders WHERE order_id LIKE 'ORD-002%'), 'BUR-004', 1, 13.99),
    ((SELECT order_id FROM orders WHERE order_id LIKE 'ORD-003%'), 'TAC-001', 3, 3.99),
    ((SELECT order_id FROM orders WHERE order_id LIKE 'ORD-004%'), 'SUS-001', 2, 8.99)
ON CONFLICT DO NOTHING;

-- ============================================
-- CREATE VIEWS
-- ============================================

-- View for active orders
CREATE OR REPLACE VIEW active_orders AS
SELECT 
    o.order_id,
    o.customer_id,
    c.name as customer_name,
    o.restaurant_id,
    r.name as restaurant_name,
    o.order_status,
    o.delivery_type,
    o.total_amount,
    o.payment_status,
    o.driver_id,
    d.user_id as driver_user_id,
    u.username as driver_username,
    o.created_at,
    o.estimated_delivery,
    a.street as delivery_address
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN restaurants r ON o.restaurant_id = r.restaurant_id
LEFT JOIN addresses a ON o.address_id = a.address_id
LEFT JOIN drivers d ON o.driver_id = d.driver_id
LEFT JOIN users u ON d.user_id = u.user_id
WHERE o.order_status NOT IN ('delivered', 'cancelled')
ORDER BY 
    CASE o.order_status
        WHEN 'out_for_delivery' THEN 1
        WHEN 'ready' THEN 2
        WHEN 'preparing' THEN 3
        WHEN 'confirmed' THEN 4
        ELSE 5
    END,
    o.created_at;

-- View for available drivers
CREATE OR REPLACE VIEW available_drivers AS
SELECT 
    d.driver_id,
    u.username,
    u.email,
    u.phone_number,
    d.vehicle_type,
    d.vehicle_model,
    d.license_plate,
    d.rating,
    d.current_location,
    d.total_deliveries,
    d.completed_deliveries,
    d.avg_delivery_time,
    d.shift_start,
    d.shift_end,
    d.is_on_shift,
    u.last_login
FROM drivers d
JOIN users u ON d.user_id = u.user_id
WHERE d.is_available = true 
    AND u.is_active = true
    AND (d.is_on_shift = true OR d.shift_start IS NULL)
ORDER BY d.rating DESC, d.total_deliveries DESC;

-- View for driver performance
CREATE OR REPLACE VIEW driver_performance AS
SELECT 
    d.driver_id,
    u.username,
    u.email,
    d.rating,
    d.total_deliveries,
    d.completed_deliveries,
    d.failed_deliveries,
    d.total_earnings,
    d.avg_delivery_time,
    ROUND((d.completed_deliveries::DECIMAL / NULLIF(d.total_deliveries, 0) * 100), 2) as success_rate,
    COUNT(o.order_id) as current_assignments,
    MAX(o.delivered_at) as last_delivery
FROM drivers d
JOIN users u ON d.user_id = u.user_id
LEFT JOIN orders o ON d.driver_id = o.driver_id AND o.order_status IN ('out_for_delivery', 'ready')
GROUP BY d.driver_id, u.username, u.email, d.rating, d.total_deliveries, d.completed_deliveries, 
         d.failed_deliveries, d.total_earnings, d.avg_delivery_time
ORDER BY d.rating DESC, success_rate DESC;

-- View for restaurant sales summary
CREATE OR REPLACE VIEW restaurant_sales AS
SELECT 
    r.restaurant_id,
    r.name as restaurant_name,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as avg_order_value,
    COUNT(DISTINCT o.customer_id) as unique_customers,
    MIN(o.created_at) as first_order_date,
    MAX(o.created_at) as last_order_date
FROM restaurants r
LEFT JOIN orders o ON r.restaurant_id = o.restaurant_id
WHERE o.order_status NOT IN ('cancelled')
   OR o.order_id IS NULL
GROUP BY r.restaurant_id, r.name
ORDER BY total_revenue DESC NULLS LAST;

-- View for customer order history
CREATE OR REPLACE VIEW customer_orders AS
SELECT 
    c.customer_id,
    c.name as customer_name,
    c.phone_number,
    c.email,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_spent,
    AVG(o.total_amount) as avg_order_value,
    MIN(o.created_at) as first_order,
    MAX(o.created_at) as last_order,
    STRING_AGG(DISTINCT r.name, ', ') as restaurants_ordered_from
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN restaurants r ON o.restaurant_id = r.restaurant_id
GROUP BY c.customer_id, c.name, c.phone_number, c.email
ORDER BY total_spent DESC NULLS LAST;

-- ============================================
-- CREATE STORED PROCEDURES
-- ============================================

-- Procedure to assign order to available driver
CREATE OR REPLACE PROCEDURE assign_order_to_driver(
    p_order_id VARCHAR(30),
    p_driver_id INTEGER DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_available_driver_id INTEGER;
    v_order_status VARCHAR(20);
BEGIN
    -- Check if order exists and is ready for delivery
    SELECT order_status INTO v_order_status
    FROM orders 
    WHERE order_id = p_order_id;
    
    IF v_order_status IS NULL THEN
        RAISE EXCEPTION 'Order % does not exist', p_order_id;
    END IF;
    
    IF v_order_status NOT IN ('ready', 'confirmed') THEN
        RAISE EXCEPTION 'Order % is not ready for delivery (current status: %)', p_order_id, v_order_status;
    END IF;
    
    -- If specific driver is requested
    IF p_driver_id IS NOT NULL THEN
        -- Check if driver is available
        IF EXISTS (SELECT 1 FROM drivers WHERE driver_id = p_driver_id AND is_available = true) THEN
            UPDATE orders 
            SET driver_id = p_driver_id, 
                order_status = 'out_for_delivery',
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = p_order_id;
            
            -- Mark driver as busy
            UPDATE drivers 
            SET is_available = false,
                updated_at = CURRENT_TIMESTAMP
            WHERE driver_id = p_driver_id;
            
            -- Log status change
            INSERT INTO order_status_history (order_id, old_status, new_status)
            VALUES (p_order_id, v_order_status, 'out_for_delivery');
            
            RAISE NOTICE 'Order % assigned to driver %', p_order_id, p_driver_id;
        ELSE
            RAISE EXCEPTION 'Driver % is not available', p_driver_id;
        END IF;
    ELSE
        -- Find best available driver (highest rating, least current deliveries)
        SELECT d.driver_id INTO v_available_driver_id
        FROM available_drivers d
        ORDER BY d.rating DESC, 
                 (SELECT COUNT(*) FROM orders o WHERE o.driver_id = d.driver_id AND o.order_status = 'out_for_delivery') ASC
        LIMIT 1;
        
        IF v_available_driver_id IS NOT NULL THEN
            UPDATE orders 
            SET driver_id = v_available_driver_id, 
                order_status = 'out_for_delivery',
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = p_order_id;
            
            -- Mark driver as busy
            UPDATE drivers 
            SET is_available = false,
                updated_at = CURRENT_TIMESTAMP
            WHERE driver_id = v_available_driver_id;
            
            -- Log status change
            INSERT INTO order_status_history (order_id, old_status, new_status)
            VALUES (p_order_id, v_order_status, 'out_for_delivery');
            
            RAISE NOTICE 'Order % automatically assigned to driver %', p_order_id, v_available_driver_id;
        ELSE
            RAISE EXCEPTION 'No available drivers found';
        END IF;
    END IF;
END;
$$;

-- Procedure to complete delivery
CREATE OR REPLACE PROCEDURE complete_delivery(
    p_order_id VARCHAR(30),
    p_driver_rating INTEGER DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_driver_id INTEGER;
    v_order_total DECIMAL(10, 2);
    v_order_status VARCHAR(20);
    v_delivery_time INTEGER;
BEGIN
    -- Get driver, order total, and status
    SELECT driver_id, total_amount, order_status INTO v_driver_id, v_order_total, v_order_status
    FROM orders 
    WHERE order_id = p_order_id;
    
    IF v_driver_id IS NULL THEN
        RAISE EXCEPTION 'Order % has no driver assigned', p_order_id;
    END IF;
    
    IF v_order_status != 'out_for_delivery' THEN
        RAISE EXCEPTION 'Order % is not out for delivery (current status: %)', p_order_id, v_order_status;
    END IF;
    
    -- Calculate delivery time in minutes
    SELECT EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at))/60 INTO v_delivery_time
    FROM orders 
    WHERE order_id = p_order_id;
    
    -- Update order status
    UPDATE orders 
    SET order_status = 'delivered',
        delivered_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP,
        driver_rating = p_driver_rating
    WHERE order_id = p_order_id;
    
    -- Update driver stats
    UPDATE drivers 
    SET 
        total_deliveries = total_deliveries + 1,
        completed_deliveries = completed_deliveries + 1,
        is_available = true,
        total_earnings = total_earnings + (v_order_total * 0.2), -- 20% commission
        rating = CASE 
                    WHEN p_driver_rating IS NOT NULL THEN 
                        (rating * total_deliveries + p_driver_rating) / (total_deliveries + 1)
                    ELSE rating
                 END,
        avg_delivery_time = COALESCE(
            (avg_delivery_time * total_deliveries + v_delivery_time) / (total_deliveries + 1),
            v_delivery_time
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE driver_id = v_driver_id;
    
    -- Log status change
    INSERT INTO order_status_history (order_id, old_status, new_status)
    VALUES (p_order_id, v_order_status, 'delivered');
    
    RAISE NOTICE 'Delivery completed for order % by driver %. Delivery time: % minutes', 
                 p_order_id, v_driver_id, ROUND(v_delivery_time, 2);
END;
$$;

-- Procedure to update driver location
CREATE OR REPLACE PROCEDURE update_driver_location(
    p_driver_id INTEGER,
    p_location VARCHAR(100)
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE drivers 
    SET current_location = p_location,
        updated_at = CURRENT_TIMESTAMP
    WHERE driver_id = p_driver_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Driver % not found', p_driver_id;
    END IF;
    
    RAISE NOTICE 'Driver % location updated to: %', p_driver_id, p_location;
END;
$$;

-- Procedure to create a new order
CREATE OR REPLACE PROCEDURE create_order(
    p_order_id VARCHAR(30),
    p_customer_id VARCHAR(20),
    p_restaurant_id VARCHAR(20),
    p_address_id INTEGER,
    p_delivery_type VARCHAR(10),
    p_items JSONB,
    p_special_instructions TEXT DEFAULT NULL,
    p_payment_method VARCHAR(20) DEFAULT 'cash'
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_subtotal DECIMAL(10, 2) := 0;
    v_item JSONB;
    v_item_record RECORD;
    v_tax DECIMAL(10, 2);
    v_delivery_fee DECIMAL(10, 2);
    v_total DECIMAL(10, 2);
    v_item_id VARCHAR(20);
    v_quantity INTEGER;
    v_unit_price DECIMAL(10, 2);
BEGIN
    -- Calculate subtotal from items
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        v_item_id := (v_item->>'item_id')::VARCHAR(20);
        v_quantity := (v_item->>'quantity')::INTEGER;
        
        -- Get item price
        SELECT price INTO v_unit_price
        FROM menu_items 
        WHERE item_id = v_item_id AND is_available = true;
        
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Item % not found or not available', v_item_id;
        END IF;
        
        v_subtotal := v_subtotal + (v_unit_price * v_quantity);
    END LOOP;
    
    -- Calculate tax (8%)
    v_tax := v_subtotal * 0.08;
    
    -- Calculate delivery fee
    IF p_delivery_type = 'delivery' THEN
        v_delivery_fee := 2.99;
    ELSE
        v_delivery_fee := 0;
    END IF;
    
    -- Calculate total
    v_total := v_subtotal + v_tax + v_delivery_fee;
    
    -- Create order
    INSERT INTO orders (
        order_id, customer_id, restaurant_id, address_id,
        order_status, delivery_type, special_instructions,
        subtotal, tax, delivery_fee, total_amount,
        payment_method, payment_status, created_at
    ) VALUES (
        p_order_id, p_customer_id, p_restaurant_id, p_address_id,
        'pending', p_delivery_type, p_special_instructions,
        v_subtotal, v_tax, v_delivery_fee, v_total,
        p_payment_method, 'pending', CURRENT_TIMESTAMP
    );
    
    -- Add order items
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        v_item_id := (v_item->>'item_id')::VARCHAR(20);
        v_quantity := (v_item->>'quantity')::INTEGER;
        
        -- Get item price again
        SELECT price INTO v_unit_price
        FROM menu_items 
        WHERE item_id = v_item_id;
        
        INSERT INTO order_items (order_id, item_id, quantity, unit_price)
        VALUES (p_order_id, v_item_id, v_quantity, v_unit_price);
    END LOOP;
    
    -- Log status change
    INSERT INTO order_status_history (order_id, old_status, new_status)
    VALUES (p_order_id, NULL, 'pending');
    
    RAISE NOTICE 'Order % created successfully. Total: $%', p_order_id, v_total;
END;
$$;

-- ============================================
-- GRANT PERMISSIONS
-- ============================================

-- Create mega_pizza_admin role if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mega_pizza_admin') THEN
        CREATE ROLE mega_pizza_admin WITH LOGIN PASSWORD 'SecurePass123!';
    END IF;
END $$;

-- Grant all privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mega_pizza_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mega_pizza_admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO mega_pizza_admin;
GRANT ALL PRIVILEGES ON ALL PROCEDURES IN SCHEMA public TO mega_pizza_admin;

-- Grant access to views
GRANT SELECT ON active_orders TO mega_pizza_admin;
GRANT SELECT ON available_drivers TO mega_pizza_admin;
GRANT SELECT ON driver_performance TO mega_pizza_admin;
GRANT SELECT ON restaurant_sales TO mega_pizza_admin;
GRANT SELECT ON customer_orders TO mega_pizza_admin;

-- ============================================
-- COMPLETION MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE '✅ MEGA PIZZA DATABASE INITIALIZED SUCCESSFULLY!';
    RAISE NOTICE '============================================';
    RAISE NOTICE '';
    RAISE NOTICE '📊 DATABASE STATISTICS:';
    RAISE NOTICE '   • % restaurants created', (SELECT COUNT(*) FROM restaurants);
    RAISE NOTICE '   • % users created', (SELECT COUNT(*) FROM users);
    RAISE NOTICE '   • % drivers registered', (SELECT COUNT(*) FROM drivers);
    RAISE NOTICE '   • % customers added', (SELECT COUNT(*) FROM customers);
    RAISE NOTICE '   • % menu items available', (SELECT COUNT(*) FROM menu_items);
    RAISE NOTICE '   • % sample orders created', (SELECT COUNT(*) FROM orders);
    RAISE NOTICE '';
    RAISE NOTICE '🔑 DEFAULT CREDENTIALS:';
    RAISE NOTICE '   👑 Admin:      admin / Admin@123';
    RAISE NOTICE '   📋 Manager:    manager1 / Manager@123';
    RAISE NOTICE '   🚗 Driver 1:   driver1 / Driver@123';
    RAISE NOTICE '   🚗 Driver 2:   driver2 / Driver@123';
    RAISE NOTICE '   🚗 Driver 3:   driver3 / Driver@123';
    RAISE NOTICE '   👤 Customer:   customer1 / Customer@123';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 DATABASE READY FOR MEGA PIZZA DELIVERY SYSTEM!';
    RAISE NOTICE '============================================';
END $$;