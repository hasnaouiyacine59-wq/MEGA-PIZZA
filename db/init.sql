-- Initialize FastFood Database Schema
-- Create the mega_pizza_admin user FIRST
/*DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mega_pizza_admin') THEN
          CREATE USER mega_pizza_admin WITH PASSWORD 'SecurePass123!';
    END IF;
END $$;*/
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable Row Level Security (optional)
ALTER DATABASE mega_pizza_db SET "app.jwt_secret" TO 'your-jwt-secret-here';

-- ============================================
-- CREATE DRIVERS TABLE (NEW)
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

-- Create Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Addresses Table
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

-- Create Restaurants Table
CREATE TABLE IF NOT EXISTS restaurants (
    restaurant_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Menu Items Table
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

-- Create Users Table (Authentication)
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

-- Link customers to users
ALTER TABLE customers ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(user_id);

-- ============================================
-- UPDATE ORDERS TABLE TO USE DRIVERS TABLE
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
    
    -- CHANGED: Reference drivers table instead of users table
    driver_id INTEGER REFERENCES drivers(driver_id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimated_delivery TIMESTAMP,
    delivered_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id VARCHAR(30) REFERENCES orders(order_id) ON DELETE CASCADE,
    item_id VARCHAR(20) REFERENCES menu_items(item_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    customizations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Order Status History Table
CREATE TABLE IF NOT EXISTS order_status_history (
    history_id SERIAL PRIMARY KEY,
    order_id VARCHAR(30) REFERENCES orders(order_id),
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by INTEGER REFERENCES users(user_id)
);

-- Create Authentication Tables
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
-- CREATE INDEXES FOR DRIVERS TABLE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_drivers_user ON drivers(user_id);
CREATE INDEX IF NOT EXISTS idx_drivers_available ON drivers(is_available) WHERE is_available = true;
CREATE INDEX IF NOT EXISTS idx_drivers_on_shift ON drivers(is_on_shift) WHERE is_on_shift = true;
CREATE INDEX IF NOT EXISTS idx_drivers_rating ON drivers(rating DESC);
CREATE INDEX IF NOT EXISTS idx_drivers_vehicle ON drivers(vehicle_type);

-- Existing Indexes
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone_number);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_addresses_customer ON addresses(customer_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_restaurant ON menu_items(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_restaurant ON orders(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_driver ON orders(driver_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_item ON order_items(item_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_login_attempts_user ON login_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(attempted_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);

-- ============================================
-- CREATE SAMPLE DATA
-- ============================================
INSERT INTO restaurants (restaurant_id, name, address, phone, is_active) 
VALUES 
    ('REST-001', 'Burger Palace', '123 Food Street, Springfield', '+1234567890', true),
    ('REST-002', 'Pizza Heaven', '456 Pizza Road, Metropolis', '+1234567891', true),
    ('REST-003', 'Taco Fiesta', '789 Taco Lane, Gotham', '+1234567892', true)
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

-- Create sample driver user (password: Driver@123)
INSERT INTO users (username, email, password_hash, role, phone_number, is_active) 
VALUES (
    'driver1', 
    'driver1@megapizza.com', 
    crypt('Driver@123', gen_salt('bf', 12)), 
    'driver', 
    '+1234567892', 
    true
)
ON CONFLICT (username) DO NOTHING;

-- Create driver profile for the driver user
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
    avg_delivery_time
)
SELECT 
    u.user_id,
    'DL123456',
    'motorcycle',
    'Yamaha FZ',
    'MH-12-AB-1234',
    true,
    4.5,
    25,
    24,
    350.00,
    15
FROM users u 
WHERE u.username = 'driver1'
ON CONFLICT (user_id) DO NOTHING;

-- Create sample menu items
INSERT INTO menu_items (item_id, restaurant_id, name, description, price, category, is_available) 
VALUES 
    ('PIZ-001', 'REST-002', 'Margherita Pizza', 'Classic pizza with tomato sauce and mozzarella', 12.99, 'Pizza', true),
    ('PIZ-002', 'REST-002', 'Pepperoni Pizza', 'Pizza with pepperoni and extra cheese', 14.99, 'Pizza', true),
    ('BUR-001', 'REST-001', 'Cheeseburger', 'Beef burger with cheese and lettuce', 9.99, 'Burgers', true),
    ('TAC-001', 'REST-003', 'Beef Taco', 'Soft taco with seasoned beef', 3.99, 'Tacos', true)
ON CONFLICT (item_id) DO NOTHING;

-- ============================================
-- CREATE TRIGGERS
-- ============================================
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
-- CREATE USEFUL VIEWS
-- ============================================
-- View for active orders
CREATE OR REPLACE VIEW active_orders AS
SELECT 
    o.*, 
    c.name as customer_name, 
    r.name as restaurant_name,
    d.user_id as driver_user_id,
    u.username as driver_username
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN restaurants r ON o.restaurant_id = r.restaurant_id
LEFT JOIN drivers d ON o.driver_id = d.driver_id
LEFT JOIN users u ON d.user_id = u.user_id
WHERE o.order_status NOT IN ('delivered', 'cancelled')
ORDER BY o.created_at DESC;

-- View for available drivers
CREATE OR REPLACE VIEW available_drivers AS
SELECT 
    d.*,
    u.username,
    u.email,
    u.phone_number,
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
    d.rating,
    d.total_deliveries,
    d.completed_deliveries,
    d.failed_deliveries,
    d.total_earnings,
    d.avg_delivery_time,
    ROUND((d.completed_deliveries::DECIMAL / NULLIF(d.total_deliveries, 0) * 100), 2) as success_rate,
    COUNT(o.order_id) as current_assignments
FROM drivers d
JOIN users u ON d.user_id = u.user_id
LEFT JOIN orders o ON d.driver_id = o.driver_id AND o.order_status IN ('out_for_delivery', 'ready')
GROUP BY d.driver_id, u.username, d.rating, d.total_deliveries, d.completed_deliveries, d.failed_deliveries, d.total_earnings, d.avg_delivery_time
ORDER BY d.rating DESC, success_rate DESC;

-- ============================================
-- CREATE STORED PROCEDURES FOR DRIVER MANAGEMENT
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
BEGIN
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
    v_driver_commission DECIMAL(10, 2);
BEGIN
    -- Get driver and order total
    SELECT driver_id, total_amount INTO v_driver_id, v_order_total
    FROM orders 
    WHERE order_id = p_order_id;
    
    IF v_driver_id IS NULL THEN
        RAISE EXCEPTION 'Order % has no driver assigned', p_order_id;
    END IF;
    
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
        updated_at = CURRENT_TIMESTAMP
    WHERE driver_id = v_driver_id;
    
    RAISE NOTICE 'Delivery completed for order % by driver %', p_order_id, v_driver_id;
END;
$$;

-- ============================================
-- GRANT PERMISSIONS
-- ============================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mega_pizza_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mega_pizza_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mega_pizza_admin;
GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA public TO mega_pizza_admin;

-- Grant access to views
GRANT SELECT ON active_orders TO mega_pizza_admin;
GRANT SELECT ON available_drivers TO mega_pizza_admin;
GRANT SELECT ON driver_performance TO mega_pizza_admin;

-- ============================================
-- FINAL MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '✅ Database schema created successfully!';
    RAISE NOTICE '✅ Driver table added with all relationships';
    RAISE NOTICE '✅ Sample data inserted (admin, driver, restaurants, menu items)';
    RAISE NOTICE '✅ Views and stored procedures created for driver management';
    RAISE NOTICE '';
    RAISE NOTICE '🔑 Default Credentials:';
    RAISE NOTICE '   Admin: admin / Admin@123';
    RAISE NOTICE '   Driver: driver1 / Driver@123';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Database is ready for Mega Pizza Delivery System!';
END $$;