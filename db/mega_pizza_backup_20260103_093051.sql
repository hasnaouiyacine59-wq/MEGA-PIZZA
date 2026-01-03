--
-- PostgreSQL database dump
--

\restrict e0fL0EUn4vJ7qdOT31HrpobuPcqYa4FQmxZqOtz1IxglIRPwO3KdWmeh5dQqure

-- Dumped from database version 15.15
-- Dumped by pg_dump version 15.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: assign_order_to_driver(character varying, integer); Type: PROCEDURE; Schema: public; Owner: mega_pizza_admin
--

CREATE PROCEDURE public.assign_order_to_driver(IN p_order_id character varying, IN p_driver_id integer DEFAULT NULL::integer)
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


ALTER PROCEDURE public.assign_order_to_driver(IN p_order_id character varying, IN p_driver_id integer) OWNER TO mega_pizza_admin;

--
-- Name: complete_delivery(character varying, integer); Type: PROCEDURE; Schema: public; Owner: mega_pizza_admin
--

CREATE PROCEDURE public.complete_delivery(IN p_order_id character varying, IN p_driver_rating integer DEFAULT NULL::integer)
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


ALTER PROCEDURE public.complete_delivery(IN p_order_id character varying, IN p_driver_rating integer) OWNER TO mega_pizza_admin;

--
-- Name: create_order(character varying, character varying, character varying, integer, character varying, jsonb, text, character varying); Type: PROCEDURE; Schema: public; Owner: mega_pizza_admin
--

CREATE PROCEDURE public.create_order(IN p_order_id character varying, IN p_customer_id character varying, IN p_restaurant_id character varying, IN p_address_id integer, IN p_delivery_type character varying, IN p_items jsonb, IN p_special_instructions text DEFAULT NULL::text, IN p_payment_method character varying DEFAULT 'cash'::character varying)
    LANGUAGE plpgsql
    AS $_$
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
$_$;


ALTER PROCEDURE public.create_order(IN p_order_id character varying, IN p_customer_id character varying, IN p_restaurant_id character varying, IN p_address_id integer, IN p_delivery_type character varying, IN p_items jsonb, IN p_special_instructions text, IN p_payment_method character varying) OWNER TO mega_pizza_admin;

--
-- Name: update_driver_location(integer, character varying); Type: PROCEDURE; Schema: public; Owner: mega_pizza_admin
--

CREATE PROCEDURE public.update_driver_location(IN p_driver_id integer, IN p_location character varying)
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


ALTER PROCEDURE public.update_driver_location(IN p_driver_id integer, IN p_location character varying) OWNER TO mega_pizza_admin;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: mega_pizza_admin
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO mega_pizza_admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: addresses; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.addresses (
    address_id integer NOT NULL,
    customer_id character varying(20),
    street text NOT NULL,
    city character varying(50) NOT NULL,
    state character varying(50),
    postal_code character varying(20),
    country character varying(50) DEFAULT 'USA'::character varying,
    latitude numeric(10,8),
    longitude numeric(11,8),
    is_default boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.addresses OWNER TO mega_pizza_admin;

--
-- Name: customers; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.customers (
    customer_id character varying(20) NOT NULL,
    name character varying(100) NOT NULL,
    phone_number character varying(20) NOT NULL,
    email character varying(100),
    user_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.customers OWNER TO mega_pizza_admin;

--
-- Name: drivers; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.drivers (
    driver_id integer NOT NULL,
    user_id integer,
    license_number character varying(50),
    vehicle_type character varying(20),
    vehicle_model character varying(50),
    license_plate character varying(20),
    is_available boolean DEFAULT true,
    current_location character varying(100),
    rating numeric(3,2) DEFAULT 0.00,
    total_deliveries integer DEFAULT 0,
    completed_deliveries integer DEFAULT 0,
    failed_deliveries integer DEFAULT 0,
    total_earnings numeric(10,2) DEFAULT 0.00,
    avg_delivery_time integer,
    shift_start time without time zone,
    shift_end time without time zone,
    is_on_shift boolean DEFAULT false,
    emergency_contact character varying(50),
    emergency_phone character varying(20),
    license_expiry date,
    insurance_expiry date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT drivers_rating_check CHECK (((rating >= (0)::numeric) AND (rating <= (5)::numeric))),
    CONSTRAINT drivers_vehicle_type_check CHECK (((vehicle_type)::text = ANY ((ARRAY['car'::character varying, 'motorcycle'::character varying, 'bicycle'::character varying, 'scooter'::character varying])::text[])))
);


ALTER TABLE public.drivers OWNER TO mega_pizza_admin;

--
-- Name: orders; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.orders (
    order_id character varying(30) NOT NULL,
    customer_id character varying(20),
    restaurant_id character varying(20),
    address_id integer,
    order_status character varying(20) DEFAULT 'pending'::character varying,
    delivery_type character varying(10),
    special_instructions text,
    subtotal numeric(10,2) NOT NULL,
    tax numeric(10,2) DEFAULT 0,
    delivery_fee numeric(10,2) DEFAULT 0,
    discount numeric(10,2) DEFAULT 0,
    total_amount numeric(10,2) NOT NULL,
    payment_method character varying(20),
    payment_status character varying(20) DEFAULT 'pending'::character varying,
    transaction_id character varying(100),
    driver_id integer,
    driver_rating integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    estimated_delivery timestamp without time zone,
    delivered_at timestamp without time zone,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT orders_delivery_fee_check CHECK ((delivery_fee >= (0)::numeric)),
    CONSTRAINT orders_delivery_type_check CHECK (((delivery_type)::text = ANY ((ARRAY['delivery'::character varying, 'pickup'::character varying])::text[]))),
    CONSTRAINT orders_discount_check CHECK ((discount >= (0)::numeric)),
    CONSTRAINT orders_driver_rating_check CHECK (((driver_rating >= 1) AND (driver_rating <= 5))),
    CONSTRAINT orders_order_status_check CHECK (((order_status)::text = ANY ((ARRAY['pending'::character varying, 'confirmed'::character varying, 'preparing'::character varying, 'ready'::character varying, 'out_for_delivery'::character varying, 'delivered'::character varying, 'cancelled'::character varying])::text[]))),
    CONSTRAINT orders_payment_status_check CHECK (((payment_status)::text = ANY ((ARRAY['pending'::character varying, 'paid'::character varying, 'failed'::character varying, 'refunded'::character varying])::text[]))),
    CONSTRAINT orders_subtotal_check CHECK ((subtotal >= (0)::numeric)),
    CONSTRAINT orders_tax_check CHECK ((tax >= (0)::numeric)),
    CONSTRAINT orders_total_amount_check CHECK ((total_amount >= (0)::numeric))
);


ALTER TABLE public.orders OWNER TO mega_pizza_admin;

--
-- Name: restaurants; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.restaurants (
    restaurant_id character varying(20) NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    address text NOT NULL,
    phone character varying(20),
    email character varying(100),
    latitude numeric(10,8),
    longitude numeric(11,8),
    delivery_radius integer,
    is_active boolean DEFAULT true,
    is_open boolean DEFAULT true,
    opening_time time without time zone,
    closing_time time without time zone,
    min_order_amount numeric(10,2) DEFAULT 0,
    delivery_fee numeric(10,2) DEFAULT 0,
    estimated_prep_time integer,
    rating numeric(3,2) DEFAULT 0.00,
    total_reviews integer DEFAULT 0,
    logo_url character varying(255),
    banner_url character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.restaurants OWNER TO mega_pizza_admin;

--
-- Name: users; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    public_id uuid DEFAULT gen_random_uuid(),
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) DEFAULT 'employee'::character varying,
    is_active boolean DEFAULT true,
    restaurant_id character varying(20),
    phone_number character varying(20),
    last_login timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'manager'::character varying, 'employee'::character varying, 'driver'::character varying, 'user'::character varying])::text[])))
);


ALTER TABLE public.users OWNER TO mega_pizza_admin;

--
-- Name: active_orders; Type: VIEW; Schema: public; Owner: mega_pizza_admin
--

CREATE VIEW public.active_orders AS
 SELECT o.order_id,
    o.customer_id,
    c.name AS customer_name,
    o.restaurant_id,
    r.name AS restaurant_name,
    o.order_status,
    o.delivery_type,
    o.total_amount,
    o.payment_status,
    o.driver_id,
    d.user_id AS driver_user_id,
    u.username AS driver_username,
    o.created_at,
    o.estimated_delivery,
    a.street AS delivery_address
   FROM (((((public.orders o
     JOIN public.customers c ON (((o.customer_id)::text = (c.customer_id)::text)))
     JOIN public.restaurants r ON (((o.restaurant_id)::text = (r.restaurant_id)::text)))
     LEFT JOIN public.addresses a ON ((o.address_id = a.address_id)))
     LEFT JOIN public.drivers d ON ((o.driver_id = d.driver_id)))
     LEFT JOIN public.users u ON ((d.user_id = u.user_id)))
  WHERE ((o.order_status)::text <> ALL ((ARRAY['delivered'::character varying, 'cancelled'::character varying])::text[]))
  ORDER BY
        CASE o.order_status
            WHEN 'out_for_delivery'::text THEN 1
            WHEN 'ready'::text THEN 2
            WHEN 'preparing'::text THEN 3
            WHEN 'confirmed'::text THEN 4
            ELSE 5
        END, o.created_at;


ALTER TABLE public.active_orders OWNER TO mega_pizza_admin;

--
-- Name: addresses_address_id_seq; Type: SEQUENCE; Schema: public; Owner: mega_pizza_admin
--

CREATE SEQUENCE public.addresses_address_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.addresses_address_id_seq OWNER TO mega_pizza_admin;

--
-- Name: addresses_address_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mega_pizza_admin
--

ALTER SEQUENCE public.addresses_address_id_seq OWNED BY public.addresses.address_id;


--
-- Name: available_drivers; Type: VIEW; Schema: public; Owner: mega_pizza_admin
--

CREATE VIEW public.available_drivers AS
 SELECT d.driver_id,
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
   FROM (public.drivers d
     JOIN public.users u ON ((d.user_id = u.user_id)))
  WHERE ((d.is_available = true) AND (u.is_active = true) AND ((d.is_on_shift = true) OR (d.shift_start IS NULL)))
  ORDER BY d.rating DESC, d.total_deliveries DESC;


ALTER TABLE public.available_drivers OWNER TO mega_pizza_admin;

--
-- Name: customer_orders; Type: VIEW; Schema: public; Owner: mega_pizza_admin
--

CREATE VIEW public.customer_orders AS
 SELECT c.customer_id,
    c.name AS customer_name,
    c.phone_number,
    c.email,
    count(o.order_id) AS total_orders,
    sum(o.total_amount) AS total_spent,
    avg(o.total_amount) AS avg_order_value,
    min(o.created_at) AS first_order,
    max(o.created_at) AS last_order,
    string_agg(DISTINCT (r.name)::text, ', '::text) AS restaurants_ordered_from
   FROM ((public.customers c
     LEFT JOIN public.orders o ON (((c.customer_id)::text = (o.customer_id)::text)))
     LEFT JOIN public.restaurants r ON (((o.restaurant_id)::text = (r.restaurant_id)::text)))
  GROUP BY c.customer_id, c.name, c.phone_number, c.email
  ORDER BY (sum(o.total_amount)) DESC NULLS LAST;


ALTER TABLE public.customer_orders OWNER TO mega_pizza_admin;

--
-- Name: driver_performance; Type: VIEW; Schema: public; Owner: mega_pizza_admin
--

CREATE VIEW public.driver_performance AS
 SELECT d.driver_id,
    u.username,
    u.email,
    d.rating,
    d.total_deliveries,
    d.completed_deliveries,
    d.failed_deliveries,
    d.total_earnings,
    d.avg_delivery_time,
    round((((d.completed_deliveries)::numeric / (NULLIF(d.total_deliveries, 0))::numeric) * (100)::numeric), 2) AS success_rate,
    count(o.order_id) AS current_assignments,
    max(o.delivered_at) AS last_delivery
   FROM ((public.drivers d
     JOIN public.users u ON ((d.user_id = u.user_id)))
     LEFT JOIN public.orders o ON (((d.driver_id = o.driver_id) AND ((o.order_status)::text = ANY ((ARRAY['out_for_delivery'::character varying, 'ready'::character varying])::text[])))))
  GROUP BY d.driver_id, u.username, u.email, d.rating, d.total_deliveries, d.completed_deliveries, d.failed_deliveries, d.total_earnings, d.avg_delivery_time
  ORDER BY d.rating DESC, (round((((d.completed_deliveries)::numeric / (NULLIF(d.total_deliveries, 0))::numeric) * (100)::numeric), 2)) DESC;


ALTER TABLE public.driver_performance OWNER TO mega_pizza_admin;

--
-- Name: drivers_driver_id_seq; Type: SEQUENCE; Schema: public; Owner: mega_pizza_admin
--

CREATE SEQUENCE public.drivers_driver_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.drivers_driver_id_seq OWNER TO mega_pizza_admin;

--
-- Name: drivers_driver_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mega_pizza_admin
--

ALTER SEQUENCE public.drivers_driver_id_seq OWNED BY public.drivers.driver_id;


--
-- Name: login_attempts; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.login_attempts (
    attempt_id integer NOT NULL,
    user_id integer,
    ip_address inet,
    user_agent text,
    success boolean,
    attempted_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.login_attempts OWNER TO mega_pizza_admin;

--
-- Name: login_attempts_attempt_id_seq; Type: SEQUENCE; Schema: public; Owner: mega_pizza_admin
--

CREATE SEQUENCE public.login_attempts_attempt_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.login_attempts_attempt_id_seq OWNER TO mega_pizza_admin;

--
-- Name: login_attempts_attempt_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mega_pizza_admin
--

ALTER SEQUENCE public.login_attempts_attempt_id_seq OWNED BY public.login_attempts.attempt_id;


--
-- Name: menu_items; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.menu_items (
    item_id character varying(20) NOT NULL,
    restaurant_id character varying(20),
    name character varying(100) NOT NULL,
    description text,
    price numeric(10,2) NOT NULL,
    category character varying(50),
    is_available boolean DEFAULT true,
    image_url character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.menu_items OWNER TO mega_pizza_admin;

--
-- Name: order_items; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.order_items (
    order_item_id integer NOT NULL,
    order_id character varying(30),
    item_id character varying(20),
    quantity integer NOT NULL,
    unit_price numeric(10,2) NOT NULL,
    customizations jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT order_items_quantity_check CHECK ((quantity > 0)),
    CONSTRAINT order_items_unit_price_check CHECK ((unit_price >= (0)::numeric))
);


ALTER TABLE public.order_items OWNER TO mega_pizza_admin;

--
-- Name: order_items_order_item_id_seq; Type: SEQUENCE; Schema: public; Owner: mega_pizza_admin
--

CREATE SEQUENCE public.order_items_order_item_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.order_items_order_item_id_seq OWNER TO mega_pizza_admin;

--
-- Name: order_items_order_item_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mega_pizza_admin
--

ALTER SEQUENCE public.order_items_order_item_id_seq OWNED BY public.order_items.order_item_id;


--
-- Name: order_status_history; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.order_status_history (
    history_id integer NOT NULL,
    order_id character varying(30),
    old_status character varying(20),
    new_status character varying(20) NOT NULL,
    changed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    changed_by integer
);


ALTER TABLE public.order_status_history OWNER TO mega_pizza_admin;

--
-- Name: order_status_history_history_id_seq; Type: SEQUENCE; Schema: public; Owner: mega_pizza_admin
--

CREATE SEQUENCE public.order_status_history_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.order_status_history_history_id_seq OWNER TO mega_pizza_admin;

--
-- Name: order_status_history_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mega_pizza_admin
--

ALTER SEQUENCE public.order_status_history_history_id_seq OWNED BY public.order_status_history.history_id;


--
-- Name: password_reset_tokens; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.password_reset_tokens (
    token_id integer NOT NULL,
    user_id integer,
    token character varying(255) NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    used boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.password_reset_tokens OWNER TO mega_pizza_admin;

--
-- Name: password_reset_tokens_token_id_seq; Type: SEQUENCE; Schema: public; Owner: mega_pizza_admin
--

CREATE SEQUENCE public.password_reset_tokens_token_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.password_reset_tokens_token_id_seq OWNER TO mega_pizza_admin;

--
-- Name: password_reset_tokens_token_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mega_pizza_admin
--

ALTER SEQUENCE public.password_reset_tokens_token_id_seq OWNED BY public.password_reset_tokens.token_id;


--
-- Name: restaurant_sales; Type: VIEW; Schema: public; Owner: mega_pizza_admin
--

CREATE VIEW public.restaurant_sales AS
 SELECT r.restaurant_id,
    r.name AS restaurant_name,
    count(o.order_id) AS total_orders,
    sum(o.total_amount) AS total_revenue,
    avg(o.total_amount) AS avg_order_value,
    count(DISTINCT o.customer_id) AS unique_customers,
    min(o.created_at) AS first_order_date,
    max(o.created_at) AS last_order_date
   FROM (public.restaurants r
     LEFT JOIN public.orders o ON (((r.restaurant_id)::text = (o.restaurant_id)::text)))
  WHERE (((o.order_status)::text <> 'cancelled'::text) OR (o.order_id IS NULL))
  GROUP BY r.restaurant_id, r.name
  ORDER BY (sum(o.total_amount)) DESC NULLS LAST;


ALTER TABLE public.restaurant_sales OWNER TO mega_pizza_admin;

--
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: mega_pizza_admin
--

CREATE TABLE public.user_sessions (
    session_id character varying(128) NOT NULL,
    user_id integer,
    token text NOT NULL,
    ip_address inet,
    user_agent text,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_sessions OWNER TO mega_pizza_admin;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: mega_pizza_admin
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_user_id_seq OWNER TO mega_pizza_admin;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mega_pizza_admin
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: addresses address_id; Type: DEFAULT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.addresses ALTER COLUMN address_id SET DEFAULT nextval('public.addresses_address_id_seq'::regclass);


--
-- Name: drivers driver_id; Type: DEFAULT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.drivers ALTER COLUMN driver_id SET DEFAULT nextval('public.drivers_driver_id_seq'::regclass);


--
-- Name: login_attempts attempt_id; Type: DEFAULT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.login_attempts ALTER COLUMN attempt_id SET DEFAULT nextval('public.login_attempts_attempt_id_seq'::regclass);


--
-- Name: order_items order_item_id; Type: DEFAULT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.order_items ALTER COLUMN order_item_id SET DEFAULT nextval('public.order_items_order_item_id_seq'::regclass);


--
-- Name: order_status_history history_id; Type: DEFAULT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.order_status_history ALTER COLUMN history_id SET DEFAULT nextval('public.order_status_history_history_id_seq'::regclass);


--
-- Name: password_reset_tokens token_id; Type: DEFAULT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.password_reset_tokens ALTER COLUMN token_id SET DEFAULT nextval('public.password_reset_tokens_token_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Data for Name: addresses; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.addresses (address_id, customer_id, street, city, state, postal_code, country, latitude, longitude, is_default, created_at) FROM stdin;
1	CUST-001	123 Main St	Springfield	IL	62701	USA	\N	\N	t	2026-01-02 16:30:39.250832
2	CUST-001	456 Oak Ave	Springfield	IL	62702	USA	\N	\N	f	2026-01-02 16:30:39.250832
3	CUST-002	789 Pine Rd	Metropolis	NY	10001	USA	\N	\N	t	2026-01-02 16:30:39.250832
4	CUST-003	321 Elm St	Gotham	NJ	07001	USA	\N	\N	t	2026-01-02 16:30:39.250832
5	CUST-004	654 Maple Dr	Tokyo Town	CA	90001	USA	\N	\N	t	2026-01-02 16:30:39.250832
6	CUST-005	987 Cedar Ln	Little Italy	TX	75001	USA	\N	\N	t	2026-01-02 16:30:39.250832
\.


--
-- Data for Name: customers; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.customers (customer_id, name, phone_number, email, user_id, created_at) FROM stdin;
CUST-001	John Doe	+1234567800	john.doe@example.com	6	2026-01-02 16:30:39.240462
CUST-002	Jane Smith	+1234567801	jane.smith@example.com	\N	2026-01-02 16:30:39.240462
CUST-003	Bob Johnson	+1234567802	bob.johnson@example.com	\N	2026-01-02 16:30:39.240462
CUST-004	Alice Williams	+1234567803	alice.williams@example.com	\N	2026-01-02 16:30:39.240462
CUST-005	Charlie Brown	+1234567804	charlie.brown@example.com	\N	2026-01-02 16:30:39.240462
\.


--
-- Data for Name: drivers; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.drivers (driver_id, user_id, license_number, vehicle_type, vehicle_model, license_plate, is_available, current_location, rating, total_deliveries, completed_deliveries, failed_deliveries, total_earnings, avg_delivery_time, shift_start, shift_end, is_on_shift, emergency_contact, emergency_phone, license_expiry, insurance_expiry, created_at, updated_at) FROM stdin;
2	4	DL100002	car	Toyota Corolla	MH-12-AB-1002	f	\N	4.30	35	34	0	550.00	19	09:00:00	17:00:00	t	Emergency Contact 2	+1234567892	\N	\N	2026-01-02 16:30:39.230249	2026-01-03 15:06:59.896617
15	21	DRIVER_LICENCE	bicycle	push	ABC-123	f	\N	0.00	0	0	0	0.00	\N	08:31:00	08:31:00	f	000000000	11111111111	\N	\N	2026-01-03 13:30:48.473328	2026-01-03 15:07:04.78462
\.


--
-- Data for Name: login_attempts; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.login_attempts (attempt_id, user_id, ip_address, user_agent, success, attempted_at) FROM stdin;
\.


--
-- Data for Name: menu_items; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.menu_items (item_id, restaurant_id, name, description, price, category, is_available, image_url, created_at, updated_at) FROM stdin;
PIZ-001	REST-002	Margherita Pizza	Classic pizza with tomato sauce and mozzarella	12.99	Pizza	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
PIZ-002	REST-002	Pepperoni Pizza	Pizza with pepperoni and extra cheese	14.99	Pizza	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
PIZ-003	REST-002	Vegetarian Pizza	Pizza with fresh vegetables and cheese	13.99	Pizza	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
PIZ-004	REST-002	Hawaiian Pizza	Pizza with ham and pineapple	15.99	Pizza	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
PIZ-005	REST-002	Meat Lovers Pizza	Pizza with all kinds of meat	16.99	Pizza	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
BUR-001	REST-001	Cheeseburger	Beef burger with cheese and lettuce	9.99	Burgers	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
BUR-002	REST-001	Bacon Burger	Burger with crispy bacon	11.99	Burgers	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
BUR-003	REST-001	Veggie Burger	Plant-based burger with veggies	8.99	Burgers	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
BUR-004	REST-001	Double Cheeseburger	Double beef patty with double cheese	13.99	Burgers	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
TAC-001	REST-003	Beef Taco	Soft taco with seasoned beef	3.99	Tacos	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
TAC-002	REST-003	Chicken Taco	Soft taco with grilled chicken	3.99	Tacos	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
TAC-003	REST-003	Fish Taco	Taco with battered fish	4.99	Tacos	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
TAC-004	REST-003	Vegetarian Taco	Taco with beans and veggies	2.99	Tacos	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
SUS-001	REST-004	California Roll	Crab, avocado, cucumber	8.99	Sushi	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
SUS-002	REST-004	Salmon Nigiri	Fresh salmon on rice	6.99	Sushi	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
SUS-003	REST-004	Dragon Roll	Eel and avocado roll	12.99	Sushi	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
PAS-001	REST-005	Spaghetti Carbonara	Spaghetti with egg and bacon	11.99	Pasta	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
PAS-002	REST-005	Fettuccine Alfredo	Fettuccine with cream sauce	10.99	Pasta	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
PAS-003	REST-005	Lasagna	Layered pasta with meat sauce	13.99	Pasta	t	\N	2026-01-02 16:30:39.2613	2026-01-02 16:30:39.2613
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.order_items (order_item_id, order_id, item_id, quantity, unit_price, customizations, created_at) FROM stdin;
1	ORD-001-2026	PIZ-001	1	12.99	\N	2026-01-02 16:30:39.302292
2	ORD-001-2026	PIZ-002	1	14.99	\N	2026-01-02 16:30:39.302292
3	ORD-002-2026	BUR-001	2	9.99	\N	2026-01-02 16:30:39.302292
4	ORD-002-2026	BUR-004	1	13.99	\N	2026-01-02 16:30:39.302292
5	ORD-003-2026	TAC-001	3	3.99	\N	2026-01-02 16:30:39.302292
6	ORD-004-2026	SUS-001	2	8.99	\N	2026-01-02 16:30:39.302292
\.


--
-- Data for Name: order_status_history; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.order_status_history (history_id, order_id, old_status, new_status, changed_at, changed_by) FROM stdin;
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.orders (order_id, customer_id, restaurant_id, address_id, order_status, delivery_type, special_instructions, subtotal, tax, delivery_fee, discount, total_amount, payment_method, payment_status, transaction_id, driver_id, driver_rating, created_at, estimated_delivery, delivered_at, updated_at) FROM stdin;
ORD-003-2026	CUST-003	REST-003	4	preparing	pickup	\N	11.97	0.96	0.00	0.00	12.93	credit_card	paid	\N	\N	\N	2026-01-02 16:00:39.271489	\N	\N	2026-01-02 16:30:39.271489
ORD-004-2026	CUST-004	REST-004	5	pending	delivery	\N	19.98	1.60	2.99	0.00	24.57	cash	pending	\N	\N	\N	2026-01-02 16:30:39.271489	\N	\N	2026-01-02 16:30:39.271489
ORD-002-2026	CUST-002	REST-001	3	out_for_delivery	delivery	\N	21.98	1.76	2.99	0.00	26.73	cash	paid	\N	2	\N	2026-01-02 15:30:39.271489	\N	\N	2026-01-02 16:30:39.292021
ORD-001-2026	CUST-001	REST-002	1	delivered	delivery	\N	27.98	2.23	2.99	0.00	33.20	credit_card	paid	\N	\N	\N	2026-01-02 14:30:39.271489	\N	\N	2026-01-03 13:22:11.676788
\.


--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.password_reset_tokens (token_id, user_id, token, expires_at, used, created_at) FROM stdin;
\.


--
-- Data for Name: restaurants; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.restaurants (restaurant_id, name, description, address, phone, email, latitude, longitude, delivery_radius, is_active, is_open, opening_time, closing_time, min_order_amount, delivery_fee, estimated_prep_time, rating, total_reviews, logo_url, banner_url, created_at, updated_at) FROM stdin;
REST-001	Burger Palace	Best burgers in town!	123 Food Street, Springfield	+1234567890	contact@burgerpalace.com	40.71277600	-74.00597400	5	t	t	09:00:00	22:00:00	10.00	2.99	20	4.50	120	\N	\N	2026-01-02 16:30:37.524408	2026-01-02 16:30:37.524408
REST-002	Pizza Heaven	Heavenly pizza made with love	456 Pizza Road, Metropolis	+1234567891	info@pizzaheaven.com	40.75889600	-73.98513000	6	t	t	10:00:00	23:00:00	12.00	2.99	15	4.70	200	\N	\N	2026-01-02 16:30:37.524408	2026-01-02 16:30:37.524408
REST-003	Taco Fiesta	Authentic Mexican tacos	789 Taco Lane, Gotham	+1234567892	hello@tacofiesta.com	40.74881700	-73.98542800	4	t	t	11:00:00	22:00:00	8.00	1.99	10	4.30	85	\N	\N	2026-01-02 16:30:37.524408	2026-01-02 16:30:37.524408
REST-004	Sushi Express	Fresh sushi delivered fast	321 Sushi Blvd, Tokyo Town	+1234567893	order@sushiexpress.com	40.71428300	-74.00613900	5	t	t	12:00:00	23:00:00	15.00	3.99	25	4.60	150	\N	\N	2026-01-02 16:30:37.524408	2026-01-02 16:30:37.524408
REST-005	Pasta Paradise	Homemade Italian pasta	654 Pasta Ave, Little Italy	+1234567894	service@pastaparadise.com	40.72082400	-73.99733000	5	t	t	10:30:00	22:30:00	12.00	2.99	18	4.40	95	\N	\N	2026-01-02 16:30:37.524408	2026-01-02 16:30:37.524408
\.


--
-- Data for Name: user_sessions; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.user_sessions (session_id, user_id, token, ip_address, user_agent, expires_at, created_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: mega_pizza_admin
--

COPY public.users (user_id, public_id, username, email, password_hash, role, is_active, restaurant_id, phone_number, last_login, created_at, updated_at) FROM stdin;
1	6aaa4796-8b4f-473a-bbad-23c7991bfcf2	admin	admin@megapizza.com	$2a$12$48zXJuCEfMATn9aTPZzFJ.SA7uPCFMrXISQ923vlEtk0PaclGqwOu	admin	t	REST-001	+1234567891	\N	2026-01-02 16:30:37.534667	2026-01-02 16:30:37.534667
2	354b6aad-abce-4921-a5f2-f682c66b2b01	manager1	manager@megapizza.com	$2a$12$nk6xfQRKJXSvmG64qbWx8e9LV.sn8AauxbFbebOIrdxOfJ6BtB242	manager	t	REST-002	+1234567895	\N	2026-01-02 16:30:37.873884	2026-01-02 16:30:37.873884
6	c6b200e6-dc41-454f-8bea-c387cdfba4cb	customer1	customer@example.com	$2a$12$OBzPU0zPy2p4Fqn5YjFyTuHH8Fnc2.cJf8/CvZYqawM7LUJwZVOEi	user	t	\N	+1234567898	\N	2026-01-02 16:30:38.952627	2026-01-02 16:30:38.952627
21	\N	hasnaoui yacineh	yacine23@home.colh	$2b$12$zPDYxVnfx9wvubXvsJ.WOeejDfOR6jiHiGt4Rx16XatKfMGecaasO	driver	t	\N	0778358004	\N	2026-01-03 13:30:48.470386	2026-01-03 13:30:48.470394
4	d3b85c8d-56ef-4b11-b78e-fe9103629e79	amine boulahlaletinaoui	amine@megapizza.com	$2a$12$vEbeP/oNv.qjfszRZ4R8Dey/I0S7HEsOGJ/six5s6637HgLhhTSA2	driver	t	\N	+1234567800	\N	2026-01-02 16:30:38.151197	2026-01-03 15:14:35.775927
\.


--
-- Name: addresses_address_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mega_pizza_admin
--

SELECT pg_catalog.setval('public.addresses_address_id_seq', 6, true);


--
-- Name: drivers_driver_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mega_pizza_admin
--

SELECT pg_catalog.setval('public.drivers_driver_id_seq', 15, true);


--
-- Name: login_attempts_attempt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mega_pizza_admin
--

SELECT pg_catalog.setval('public.login_attempts_attempt_id_seq', 1, false);


--
-- Name: order_items_order_item_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mega_pizza_admin
--

SELECT pg_catalog.setval('public.order_items_order_item_id_seq', 6, true);


--
-- Name: order_status_history_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mega_pizza_admin
--

SELECT pg_catalog.setval('public.order_status_history_history_id_seq', 1, false);


--
-- Name: password_reset_tokens_token_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mega_pizza_admin
--

SELECT pg_catalog.setval('public.password_reset_tokens_token_id_seq', 1, false);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mega_pizza_admin
--

SELECT pg_catalog.setval('public.users_user_id_seq', 21, true);


--
-- Name: addresses addresses_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.addresses
    ADD CONSTRAINT addresses_pkey PRIMARY KEY (address_id);


--
-- Name: customers customers_email_key; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_email_key UNIQUE (email);


--
-- Name: customers customers_phone_number_key; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_phone_number_key UNIQUE (phone_number);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (customer_id);


--
-- Name: drivers drivers_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_pkey PRIMARY KEY (driver_id);


--
-- Name: drivers drivers_user_id_key; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_user_id_key UNIQUE (user_id);


--
-- Name: login_attempts login_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.login_attempts
    ADD CONSTRAINT login_attempts_pkey PRIMARY KEY (attempt_id);


--
-- Name: menu_items menu_items_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_pkey PRIMARY KEY (item_id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (order_item_id);


--
-- Name: order_status_history order_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.order_status_history
    ADD CONSTRAINT order_status_history_pkey PRIMARY KEY (history_id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (order_id);


--
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (token_id);


--
-- Name: password_reset_tokens password_reset_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_token_key UNIQUE (token);


--
-- Name: restaurants restaurants_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_pkey PRIMARY KEY (restaurant_id);


--
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (session_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: users users_public_id_key; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_public_id_key UNIQUE (public_id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_addresses_customer; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_addresses_customer ON public.addresses USING btree (customer_id);


--
-- Name: idx_addresses_location; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_addresses_location ON public.addresses USING btree (latitude, longitude);


--
-- Name: idx_customers_email; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_customers_email ON public.customers USING btree (email);


--
-- Name: idx_customers_phone; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_customers_phone ON public.customers USING btree (phone_number);


--
-- Name: idx_customers_user; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_customers_user ON public.customers USING btree (user_id);


--
-- Name: idx_drivers_available; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_drivers_available ON public.drivers USING btree (is_available) WHERE (is_available = true);


--
-- Name: idx_drivers_on_shift; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_drivers_on_shift ON public.drivers USING btree (is_on_shift) WHERE (is_on_shift = true);


--
-- Name: idx_drivers_rating; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_drivers_rating ON public.drivers USING btree (rating DESC);


--
-- Name: idx_drivers_user; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_drivers_user ON public.drivers USING btree (user_id);


--
-- Name: idx_drivers_vehicle; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_drivers_vehicle ON public.drivers USING btree (vehicle_type);


--
-- Name: idx_login_attempts_time; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_login_attempts_time ON public.login_attempts USING btree (attempted_at);


--
-- Name: idx_login_attempts_user; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_login_attempts_user ON public.login_attempts USING btree (user_id);


--
-- Name: idx_menu_items_available; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_menu_items_available ON public.menu_items USING btree (is_available) WHERE (is_available = true);


--
-- Name: idx_menu_items_category; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_menu_items_category ON public.menu_items USING btree (category);


--
-- Name: idx_menu_items_price; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_menu_items_price ON public.menu_items USING btree (price);


--
-- Name: idx_menu_items_restaurant; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_menu_items_restaurant ON public.menu_items USING btree (restaurant_id);


--
-- Name: idx_order_history_changed_at; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_order_history_changed_at ON public.order_status_history USING btree (changed_at);


--
-- Name: idx_order_history_order; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_order_history_order ON public.order_status_history USING btree (order_id);


--
-- Name: idx_order_items_item; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_order_items_item ON public.order_items USING btree (item_id);


--
-- Name: idx_order_items_order; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_order_items_order ON public.order_items USING btree (order_id);


--
-- Name: idx_orders_created; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_orders_created ON public.orders USING btree (created_at);


--
-- Name: idx_orders_customer; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_orders_customer ON public.orders USING btree (customer_id);


--
-- Name: idx_orders_delivery_type; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_orders_delivery_type ON public.orders USING btree (delivery_type);


--
-- Name: idx_orders_driver; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_orders_driver ON public.orders USING btree (driver_id);


--
-- Name: idx_orders_payment_status; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_orders_payment_status ON public.orders USING btree (payment_status);


--
-- Name: idx_orders_restaurant; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_orders_restaurant ON public.orders USING btree (restaurant_id);


--
-- Name: idx_orders_status; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_orders_status ON public.orders USING btree (order_status);


--
-- Name: idx_password_reset_tokens_expires; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_password_reset_tokens_expires ON public.password_reset_tokens USING btree (expires_at);


--
-- Name: idx_password_reset_tokens_token; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_password_reset_tokens_token ON public.password_reset_tokens USING btree (token);


--
-- Name: idx_user_sessions_expires; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_user_sessions_expires ON public.user_sessions USING btree (expires_at);


--
-- Name: idx_user_sessions_user; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_user_sessions_user ON public.user_sessions USING btree (user_id);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_restaurant; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_users_restaurant ON public.users USING btree (restaurant_id);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: mega_pizza_admin
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- Name: drivers update_drivers_updated_at; Type: TRIGGER; Schema: public; Owner: mega_pizza_admin
--

CREATE TRIGGER update_drivers_updated_at BEFORE UPDATE ON public.drivers FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: menu_items update_menu_items_updated_at; Type: TRIGGER; Schema: public; Owner: mega_pizza_admin
--

CREATE TRIGGER update_menu_items_updated_at BEFORE UPDATE ON public.menu_items FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: orders update_orders_updated_at; Type: TRIGGER; Schema: public; Owner: mega_pizza_admin
--

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: restaurants update_restaurants_updated_at; Type: TRIGGER; Schema: public; Owner: mega_pizza_admin
--

CREATE TRIGGER update_restaurants_updated_at BEFORE UPDATE ON public.restaurants FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: mega_pizza_admin
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: addresses addresses_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.addresses
    ADD CONSTRAINT addresses_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);


--
-- Name: customers customers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: drivers drivers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: login_attempts login_attempts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.login_attempts
    ADD CONSTRAINT login_attempts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: menu_items menu_items_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(restaurant_id);


--
-- Name: order_items order_items_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.menu_items(item_id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(order_id) ON DELETE CASCADE;


--
-- Name: order_status_history order_status_history_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.order_status_history
    ADD CONSTRAINT order_status_history_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(user_id);


--
-- Name: order_status_history order_status_history_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.order_status_history
    ADD CONSTRAINT order_status_history_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- Name: orders orders_address_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_address_id_fkey FOREIGN KEY (address_id) REFERENCES public.addresses(address_id);


--
-- Name: orders orders_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);


--
-- Name: orders orders_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(driver_id);


--
-- Name: orders orders_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(restaurant_id);


--
-- Name: password_reset_tokens password_reset_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: users users_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mega_pizza_admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(restaurant_id);


--
-- PostgreSQL database dump complete
--

\unrestrict e0fL0EUn4vJ7qdOT31HrpobuPcqYa4FQmxZqOtz1IxglIRPwO3KdWmeh5dQqure

