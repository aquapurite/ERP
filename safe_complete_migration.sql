-- =====================================================
-- SAFE COMPLETE MIGRATION FOR SUPABASE
-- This script safely creates all missing tables
-- without affecting existing data
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- PART 1: FIX EXISTING TABLES (add missing columns)
-- =====================================================

-- Add missing columns to user_roles if needed
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_roles' AND column_name = 'is_primary') THEN
        ALTER TABLE user_roles ADD COLUMN is_primary BOOLEAN DEFAULT FALSE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_roles' AND column_name = 'valid_from') THEN
        ALTER TABLE user_roles ADD COLUMN valid_from TIMESTAMPTZ DEFAULT NOW();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_roles' AND column_name = 'valid_until') THEN
        ALTER TABLE user_roles ADD COLUMN valid_until TIMESTAMPTZ;
    END IF;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- =====================================================
-- PART 2: APPROVAL TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_number VARCHAR(30) UNIQUE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_number VARCHAR(50) NOT NULL,
    amount NUMERIC(14, 2) NOT NULL DEFAULT 0,
    approval_level VARCHAR(20) NOT NULL DEFAULT 'LEVEL_1',
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    priority INTEGER DEFAULT 5,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    requested_by UUID,
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    current_approver_id UUID,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    approval_comments TEXT,
    rejected_by UUID,
    rejected_at TIMESTAMPTZ,
    rejection_reason TEXT,
    due_date TIMESTAMPTZ,
    is_overdue BOOLEAN DEFAULT FALSE,
    escalated_at TIMESTAMPTZ,
    escalated_to UUID,
    escalation_reason TEXT,
    extra_info JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS approval_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_request_id UUID,
    action VARCHAR(50) NOT NULL,
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    performed_by UUID,
    comments TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 3: AUDIT LOGS
-- =====================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 4: PRODUCT TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    barcode VARCHAR(50),
    description TEXT,
    short_description VARCHAR(500),
    category_id UUID,
    brand_id UUID,
    hsn_code VARCHAR(20),
    gst_rate NUMERIC(5, 2) DEFAULT 18.00,
    mrp NUMERIC(12, 2) NOT NULL DEFAULT 0,
    selling_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    cost_price NUMERIC(12, 2) DEFAULT 0,
    weight_kg NUMERIC(10, 3),
    length_cm NUMERIC(10, 2),
    width_cm NUMERIC(10, 2),
    height_cm NUMERIC(10, 2),
    warranty_months INTEGER DEFAULT 12,
    is_active BOOLEAN DEFAULT TRUE,
    is_serialized BOOLEAN DEFAULT TRUE,
    requires_installation BOOLEAN DEFAULT FALSE,
    installation_charges NUMERIC(10, 2) DEFAULT 0,
    images JSONB DEFAULT '[]',
    specifications JSONB DEFAULT '{}',
    meta_title VARCHAR(255),
    meta_description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    variant_attributes JSONB DEFAULT '{}',
    mrp NUMERIC(12, 2),
    selling_price NUMERIC(12, 2),
    cost_price NUMERIC(12, 2),
    weight_kg NUMERIC(10, 3),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 5: CUSTOMER TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_code VARCHAR(20) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20) NOT NULL,
    alt_phone VARCHAR(20),
    customer_type VARCHAR(20) DEFAULT 'INDIVIDUAL',
    gstin VARCHAR(15),
    pan VARCHAR(10),
    company_name VARCHAR(255),
    date_of_birth DATE,
    anniversary_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    source VARCHAR(50),
    notes TEXT,
    tags JSONB DEFAULT '[]',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS customer_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID,
    address_type VARCHAR(20) DEFAULT 'HOME',
    is_default BOOLEAN DEFAULT FALSE,
    contact_name VARCHAR(200),
    contact_phone VARCHAR(20),
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    landmark VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    country VARCHAR(50) DEFAULT 'India',
    latitude FLOAT,
    longitude FLOAT,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 6: ORDER TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(30) UNIQUE NOT NULL,
    customer_id UUID,
    channel_id UUID,
    warehouse_id UUID,
    status VARCHAR(30) DEFAULT 'NEW',
    order_type VARCHAR(20) DEFAULT 'REGULAR',
    order_source VARCHAR(30) DEFAULT 'WEBSITE',
    payment_mode VARCHAR(20) DEFAULT 'COD',
    payment_status VARCHAR(20) DEFAULT 'PENDING',
    shipping_address_id UUID,
    billing_address_id UUID,
    subtotal NUMERIC(12, 2) DEFAULT 0,
    discount_amount NUMERIC(12, 2) DEFAULT 0,
    tax_amount NUMERIC(12, 2) DEFAULT 0,
    shipping_amount NUMERIC(12, 2) DEFAULT 0,
    total_amount NUMERIC(12, 2) DEFAULT 0,
    paid_amount NUMERIC(12, 2) DEFAULT 0,
    due_amount NUMERIC(12, 2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'INR',
    notes TEXT,
    internal_notes TEXT,
    priority VARCHAR(10) DEFAULT 'NORMAL',
    promised_delivery_date DATE,
    requires_installation BOOLEAN DEFAULT FALSE,
    installation_date DATE,
    installation_slot VARCHAR(20),
    cancellation_reason TEXT,
    cancelled_at TIMESTAMPTZ,
    cancelled_by UUID,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID,
    product_id UUID,
    variant_id UUID,
    sku VARCHAR(50),
    product_name VARCHAR(255),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    discount_percent NUMERIC(5, 2) DEFAULT 0,
    discount_amount NUMERIC(12, 2) DEFAULT 0,
    tax_percent NUMERIC(5, 2) DEFAULT 18.00,
    tax_amount NUMERIC(12, 2) DEFAULT 0,
    total_amount NUMERIC(12, 2) DEFAULT 0,
    hsn_code VARCHAR(20),
    serial_numbers JSONB DEFAULT '[]',
    status VARCHAR(30) DEFAULT 'PENDING',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 7: INVENTORY TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS stock_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID,
    variant_id UUID,
    warehouse_id UUID,
    serial_number VARCHAR(100) UNIQUE,
    batch_number VARCHAR(50),
    status VARCHAR(30) DEFAULT 'AVAILABLE',
    condition VARCHAR(20) DEFAULT 'NEW',
    cost_price NUMERIC(12, 2),
    received_date DATE,
    expiry_date DATE,
    grn_number VARCHAR(30),
    purchase_order_id UUID,
    vendor_id UUID,
    order_id UUID,
    location_code VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID,
    variant_id UUID,
    warehouse_id UUID,
    total_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    damaged_quantity INTEGER DEFAULT 0,
    in_transit_quantity INTEGER DEFAULT 0,
    reorder_level INTEGER DEFAULT 10,
    reorder_quantity INTEGER DEFAULT 50,
    last_received_date TIMESTAMPTZ,
    last_sold_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_inventory_product_warehouse UNIQUE (product_id, variant_id, warehouse_id)
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID,
    variant_id UUID,
    warehouse_id UUID,
    stock_item_id UUID,
    movement_type VARCHAR(30) NOT NULL,
    quantity INTEGER NOT NULL,
    reference_type VARCHAR(50),
    reference_id UUID,
    reference_number VARCHAR(50),
    from_location VARCHAR(50),
    to_location VARCHAR(50),
    notes TEXT,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 8: VENDOR & PURCHASE TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    vendor_type VARCHAR(30) DEFAULT 'SUPPLIER',
    status VARCHAR(20) DEFAULT 'ACTIVE',
    email VARCHAR(255),
    phone VARCHAR(20),
    alt_phone VARCHAR(20),
    website VARCHAR(255),
    gstin VARCHAR(15),
    pan VARCHAR(10),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    country VARCHAR(50) DEFAULT 'India',
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(30),
    bank_ifsc VARCHAR(15),
    payment_terms INTEGER DEFAULT 30,
    credit_limit NUMERIC(14, 2) DEFAULT 0,
    current_balance NUMERIC(14, 2) DEFAULT 0,
    rating NUMERIC(3, 2),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number VARCHAR(30) UNIQUE NOT NULL,
    vendor_id UUID,
    warehouse_id UUID,
    status VARCHAR(20) DEFAULT 'DRAFT',
    order_date DATE DEFAULT CURRENT_DATE,
    expected_delivery_date DATE,
    subtotal NUMERIC(14, 2) DEFAULT 0,
    tax_amount NUMERIC(14, 2) DEFAULT 0,
    discount_amount NUMERIC(14, 2) DEFAULT 0,
    shipping_amount NUMERIC(14, 2) DEFAULT 0,
    total_amount NUMERIC(14, 2) DEFAULT 0,
    paid_amount NUMERIC(14, 2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'INR',
    payment_terms INTEGER DEFAULT 30,
    notes TEXT,
    internal_notes TEXT,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID,
    product_id UUID,
    variant_id UUID,
    sku VARCHAR(50),
    product_name VARCHAR(255),
    quantity INTEGER NOT NULL DEFAULT 1,
    received_quantity INTEGER DEFAULT 0,
    unit_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    tax_percent NUMERIC(5, 2) DEFAULT 18.00,
    tax_amount NUMERIC(12, 2) DEFAULT 0,
    discount_percent NUMERIC(5, 2) DEFAULT 0,
    discount_amount NUMERIC(12, 2) DEFAULT 0,
    total_amount NUMERIC(12, 2) DEFAULT 0,
    hsn_code VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 9: SERVICE & INSTALLATION TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS technicians (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technician_code VARCHAR(20) UNIQUE NOT NULL,
    user_id UUID,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20) NOT NULL,
    alt_phone VARCHAR(20),
    technician_type VARCHAR(30) DEFAULT 'INTERNAL',
    skill_level VARCHAR(20) DEFAULT 'JUNIOR',
    status VARCHAR(20) DEFAULT 'ACTIVE',
    region_id UUID,
    address_line1 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    id_proof_type VARCHAR(30),
    id_proof_number VARCHAR(50),
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(30),
    bank_ifsc VARCHAR(15),
    is_available BOOLEAN DEFAULT TRUE,
    current_location_lat FLOAT,
    current_location_lng FLOAT,
    rating NUMERIC(3, 2) DEFAULT 5.00,
    total_jobs INTEGER DEFAULT 0,
    completed_jobs INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS service_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number VARCHAR(30) UNIQUE NOT NULL,
    customer_id UUID,
    order_id UUID,
    product_id UUID,
    serial_number VARCHAR(100),
    service_type VARCHAR(30) NOT NULL,
    priority VARCHAR(20) DEFAULT 'NORMAL',
    status VARCHAR(30) DEFAULT 'NEW',
    source VARCHAR(30) DEFAULT 'CALL',
    issue_category VARCHAR(100),
    issue_description TEXT,
    customer_address_id UUID,
    technician_id UUID,
    scheduled_date DATE,
    scheduled_slot VARCHAR(20),
    completed_at TIMESTAMPTZ,
    resolution_notes TEXT,
    customer_feedback TEXT,
    customer_rating INTEGER,
    spare_parts_used JSONB DEFAULT '[]',
    charges NUMERIC(10, 2) DEFAULT 0,
    is_warranty BOOLEAN DEFAULT FALSE,
    warranty_status VARCHAR(30),
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS installations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installation_number VARCHAR(30) UNIQUE NOT NULL,
    order_id UUID,
    customer_id UUID,
    product_id UUID,
    serial_number VARCHAR(100),
    status VARCHAR(30) DEFAULT 'PENDING',
    technician_id UUID,
    scheduled_date DATE,
    scheduled_slot VARCHAR(20),
    completed_at TIMESTAMPTZ,
    installation_notes TEXT,
    customer_signature TEXT,
    photos JSONB DEFAULT '[]',
    checklist JSONB DEFAULT '{}',
    charges NUMERIC(10, 2) DEFAULT 0,
    is_paid BOOLEAN DEFAULT FALSE,
    customer_feedback TEXT,
    customer_rating INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 10: SHIPMENT TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS transporters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    transporter_type VARCHAR(30) DEFAULT 'COURIER',
    status VARCHAR(20) DEFAULT 'ACTIVE',
    contact_name VARCHAR(200),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    website VARCHAR(255),
    tracking_url_template VARCHAR(500),
    api_endpoint VARCHAR(500),
    api_key VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_number VARCHAR(30) UNIQUE NOT NULL,
    order_id UUID,
    warehouse_id UUID,
    transporter_id UUID,
    status VARCHAR(30) DEFAULT 'CREATED',
    awb_number VARCHAR(50),
    ship_to_name VARCHAR(200),
    ship_to_phone VARCHAR(20),
    ship_to_address TEXT,
    ship_to_city VARCHAR(100),
    ship_to_state VARCHAR(100),
    ship_to_pincode VARCHAR(10),
    weight_kg NUMERIC(10, 3),
    dimensions VARCHAR(50),
    no_of_boxes INTEGER DEFAULT 1,
    shipping_charges NUMERIC(10, 2) DEFAULT 0,
    cod_amount NUMERIC(12, 2) DEFAULT 0,
    is_cod BOOLEAN DEFAULT FALSE,
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    delivery_proof TEXT,
    notes TEXT,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 11: CHANNEL TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS sales_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    display_name VARCHAR(200),
    channel_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    seller_id VARCHAR(100),
    api_endpoint VARCHAR(500),
    api_key VARCHAR(255),
    api_secret VARCHAR(255),
    webhook_url VARCHAR(500),
    default_warehouse_id UUID,
    fulfillment_type VARCHAR(30),
    auto_confirm_orders BOOLEAN DEFAULT FALSE,
    auto_allocate_inventory BOOLEAN DEFAULT TRUE,
    commission_percentage NUMERIC(5, 2),
    fixed_fee_per_order NUMERIC(10, 2),
    payment_cycle_days INTEGER DEFAULT 7,
    return_window_days INTEGER DEFAULT 7,
    replacement_window_days INTEGER DEFAULT 7,
    config JSONB DEFAULT '{}',
    sync_enabled BOOLEAN DEFAULT TRUE,
    sync_interval_minutes INTEGER DEFAULT 30,
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 12: CREATE INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_entity ON approval_requests(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_orders_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_stock_items_serial ON stock_items(serial_number);
CREATE INDEX IF NOT EXISTS idx_stock_items_warehouse ON stock_items(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_service_requests_ticket ON service_requests(ticket_number);
CREATE INDEX IF NOT EXISTS idx_shipments_awb ON shipments(awb_number);

-- =====================================================
-- PART 13: ENSURE ADMIN HAS ROLE
-- =====================================================

-- First add code column to roles if missing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'roles' AND column_name = 'code') THEN
        ALTER TABLE roles ADD COLUMN code VARCHAR(50);
        UPDATE roles SET code = UPPER(REPLACE(name, ' ', '_')) WHERE code IS NULL;
    END IF;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- Assign admin role (using name as fallback)
INSERT INTO user_roles (id, user_id, role_id, assigned_at)
SELECT gen_random_uuid(), u.id, r.id, NOW()
FROM users u, roles r
WHERE u.email = 'admin@aquapurite.com'
AND (r.name ILIKE '%super%' OR r.name ILIKE '%admin%')
AND NOT EXISTS (
    SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = r.id
)
LIMIT 1;

-- =====================================================
-- DONE
-- =====================================================

SELECT 'Migration completed successfully! All tables created.' as result;
