-- =====================================================
-- COMPLETE SUPABASE SETUP - ALL TABLES AND DATA
-- Generated: 2026-01-09T22:32:22.485321
-- =====================================================

-- STEP 1: DROP ALL TABLES
DROP TABLE IF EXISTS dealers CASCADE;
DROP TABLE IF EXISTS warehouses CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS brands CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS role_permissions CASCADE;
DROP TABLE IF EXISTS user_roles CASCADE;
DROP TABLE IF EXISTS permissions CASCADE;
DROP TABLE IF EXISTS modules CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS regions CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;

-- STEP 2: DROP AND CREATE ENUM TYPES
DROP TYPE IF EXISTS rolelevel CASCADE;
CREATE TYPE rolelevel AS ENUM ('SUPER_ADMIN', 'DIRECTOR', 'HEAD', 'MANAGER', 'EXECUTIVE');

DROP TYPE IF EXISTS regiontype CASCADE;
CREATE TYPE regiontype AS ENUM ('COUNTRY', 'ZONE', 'STATE', 'DISTRICT', 'CITY', 'AREA');

-- STEP 3: CREATE ALL TABLES

-- MODULES
CREATE TABLE modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- PERMISSIONS
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    module_id UUID REFERENCES modules(id) ON DELETE SET NULL,
    action VARCHAR(50),
    resource VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ROLES
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    level rolelevel NOT NULL DEFAULT 'EXECUTIVE',
    department VARCHAR(50),
    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- REGIONS
CREATE TABLE regions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    type regiontype NOT NULL DEFAULT 'STATE',
    parent_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- USERS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),
    employee_code VARCHAR(50) UNIQUE,
    department VARCHAR(100),
    designation VARCHAR(100),
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP
);

-- USER_ROLES
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, role_id)
);

-- ROLE_PERMISSIONS
CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(role_id, permission_id)
);

-- AUDIT_LOGS
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    old_values TEXT,
    new_values TEXT,
    description TEXT,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- CATEGORIES
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    image_url VARCHAR(500),
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    meta_title VARCHAR(200),
    meta_description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- BRANDS
CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    logo_url VARCHAR(500),
    banner_url VARCHAR(500),
    website VARCHAR(500),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- PRODUCTS
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(300) NOT NULL,
    slug VARCHAR(300) UNIQUE NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    model_number VARCHAR(100),
    short_description TEXT,
    description TEXT,
    features TEXT,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    brand_id UUID REFERENCES brands(id) ON DELETE SET NULL,
    mrp DECIMAL(12,2),
    selling_price DECIMAL(12,2),
    dealer_price DECIMAL(12,2),
    cost_price DECIMAL(12,2),
    hsn_code VARCHAR(20),
    gst_rate DECIMAL(5,2),
    warranty_months INTEGER,
    extended_warranty_available BOOLEAN DEFAULT FALSE,
    warranty_terms TEXT,
    weight_kg DECIMAL(8,2),
    length_cm DECIMAL(8,2),
    width_cm DECIMAL(8,2),
    height_cm DECIMAL(8,2),
    min_stock_level INTEGER,
    max_stock_level INTEGER,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    is_bestseller BOOLEAN DEFAULT FALSE,
    is_new_arrival BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    meta_title VARCHAR(200),
    meta_description TEXT,
    meta_keywords VARCHAR(500),
    extra_data TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP,
    model_code VARCHAR(50),
    item_type VARCHAR(20),
    dead_weight_kg DECIMAL(8,2),
    fg_code VARCHAR(50),
    part_code VARCHAR(50)
);

-- WAREHOUSES
CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    warehouse_type VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    country VARCHAR(100) DEFAULT 'India',
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    contact_name VARCHAR(100),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    total_capacity DECIMAL(12,2) DEFAULT 0,
    current_utilization DECIMAL(12,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    can_fulfill_orders BOOLEAN DEFAULT TRUE,
    can_receive_transfers BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- DEALERS (FULL SCHEMA - 81 columns)
CREATE TABLE dealers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dealer_code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    legal_name VARCHAR(200) NOT NULL,
    display_name VARCHAR(200),
    dealer_type VARCHAR(13) NOT NULL,
    status VARCHAR(16) NOT NULL,
    tier VARCHAR(8) NOT NULL,
    parent_dealer_id UUID REFERENCES dealers(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    gstin VARCHAR(15) NOT NULL,
    pan VARCHAR(10) NOT NULL,
    tan VARCHAR(10),
    gst_registration_type VARCHAR(30) NOT NULL,
    is_msme BOOLEAN NOT NULL DEFAULT FALSE,
    msme_number VARCHAR(30),
    contact_person VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    alternate_phone VARCHAR(20),
    whatsapp VARCHAR(20),
    registered_address_line1 VARCHAR(255) NOT NULL,
    registered_address_line2 VARCHAR(255),
    registered_city VARCHAR(100) NOT NULL,
    registered_district VARCHAR(100) NOT NULL,
    registered_state VARCHAR(100) NOT NULL,
    registered_state_code VARCHAR(2) NOT NULL,
    registered_pincode VARCHAR(10) NOT NULL,
    shipping_address_line1 VARCHAR(255),
    shipping_address_line2 VARCHAR(255),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(100),
    shipping_pincode VARCHAR(10),
    region VARCHAR(50) NOT NULL,
    state VARCHAR(100) NOT NULL,
    territory VARCHAR(100),
    assigned_pincodes TEXT,
    business_type VARCHAR(50) NOT NULL,
    establishment_year INTEGER,
    annual_turnover DECIMAL(14,2),
    shop_area_sqft INTEGER,
    no_of_employees INTEGER,
    existing_brands TEXT,
    bank_name VARCHAR(200),
    bank_branch VARCHAR(200),
    bank_account_number VARCHAR(30),
    bank_ifsc VARCHAR(11),
    bank_account_name VARCHAR(200),
    credit_limit DECIMAL(14,2) NOT NULL DEFAULT 0,
    credit_days INTEGER NOT NULL DEFAULT 30,
    credit_status VARCHAR(7) NOT NULL DEFAULT 'ACTIVE',
    outstanding_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    overdue_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    security_deposit DECIMAL(14,2) NOT NULL DEFAULT 0,
    security_deposit_paid BOOLEAN NOT NULL DEFAULT FALSE,
    default_warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    sales_rep_id UUID REFERENCES users(id) ON DELETE SET NULL,
    area_sales_manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    agreement_start_date DATE,
    agreement_end_date DATE,
    agreement_document_url VARCHAR(500),
    gst_certificate_url VARCHAR(500),
    pan_card_url VARCHAR(500),
    shop_photo_url VARCHAR(500),
    cancelled_cheque_url VARCHAR(500),
    kyc_verified BOOLEAN NOT NULL DEFAULT FALSE,
    kyc_verified_at TIMESTAMP,
    kyc_verified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    total_orders INTEGER NOT NULL DEFAULT 0,
    total_revenue DECIMAL(14,2) NOT NULL DEFAULT 0,
    last_order_date TIMESTAMP,
    average_order_value DECIMAL(12,2),
    dealer_rating DECIMAL(3,2),
    payment_rating DECIMAL(3,2),
    can_place_orders BOOLEAN NOT NULL DEFAULT TRUE,
    receive_promotions BOOLEAN NOT NULL DEFAULT TRUE,
    portal_access BOOLEAN NOT NULL DEFAULT TRUE,
    internal_notes TEXT,
    onboarded_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- STEP 4: CREATE INDEXES
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_permissions_code ON permissions(code);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_brand ON products(brand_id);
CREATE INDEX idx_dealers_code ON dealers(dealer_code);
CREATE INDEX idx_dealers_gstin ON dealers(gstin);

-- STEP 5: INSERT DATA

-- MODULES (10 rows)
INSERT INTO modules (id, name, code, description, icon, sort_order, is_active, created_at, updated_at) VALUES ('d3fcdaf8-4476-4f99-afd7-4e3a93e3c568', 'Dashboard', 'DASHBOARD', NULL, NULL, 0, TRUE, '2026-01-05 14:52:59.168701', '2026-01-05 14:52:59.168702');
INSERT INTO modules (id, name, code, description, icon, sort_order, is_active, created_at, updated_at) VALUES ('c125b2c8-78e7-448d-b782-0930ec7dc990', 'User Management', 'USER_MGMT', NULL, NULL, 0, TRUE, '2026-01-05 14:52:59.168703', '2026-01-05 14:52:59.168703');
INSERT INTO modules (id, name, code, description, icon, sort_order, is_active, created_at, updated_at) VALUES ('dc3ddcb2-598c-48ab-b613-16eaa020b0ce', 'Role Management', 'ROLE_MGMT', NULL, NULL, 0, TRUE, '2026-01-05 14:52:59.168704', '2026-01-05 14:52:59.168704');
INSERT INTO modules (id, name, code, description, icon, sort_order, is_active, created_at, updated_at) VALUES ('e12a0f47-9dd7-4baf-ab16-3904879d3842', 'Product Catalog', 'PRODUCTS', NULL, NULL, 0, TRUE, '2026-01-05 14:52:59.168705', '2026-01-05 14:52:59.168706');
INSERT INTO modules (id, name, code, description, icon, sort_order, is_active, created_at, updated_at) VALUES ('91080601-f84a-4728-b0a7-6c234fc09dcf', 'Orders', 'ORDERS', NULL, NULL, 0, TRUE, '2026-01-05 14:52:59.168706', '2026-01-05 14:52:59.168707');
INSERT INTO modules (id, name, code, description, icon, sort_order, is_active, created_at, updated_at) VALUES ('df1fae9e-84cd-4465-8729-3408d1547fbb', 'Inventory', 'INVENTORY', NULL, NULL, 0, TRUE, '2026-01-05 14:52:59.168707', '2026-01-05 14:52:59.168708');
INSERT INTO modules (id, name, code, description, icon, sort_order, is_active, created_at, updated_at) VALUES ('f79f8ff8-3f22-4074-a478-3534139e584e', 'Service Management', 'SERVICE', NULL, NULL, 0, TRUE, '2026-01-05 14:52:59.168708', '2026-01-05 14:52:59.168709');
INSERT INTO modules (id, name, code, description, icon, sort_order, is_active, created_at, updated_at) VALUES ('4bee2c37-3433-411d-a2d5-dacc43e73e96', 'Customer Management', 'CUSTOMERS', NULL, NULL, 0, TRUE, '2026-01-05 14:52:59.168709', '2026-01-05 14:52:59.168710');
INSERT INTO modules (id, name, code, description, icon, sort_order, is_active, created_at, updated_at) VALUES ('caa06b81-bf03-4f2b-a9d9-267ce925df29', 'Reports', 'REPORTS', NULL, NULL, 0, TRUE, '2026-01-05 14:52:59.168710', '2026-01-05 14:52:59.168711');
INSERT INTO modules (id, name, code, description, icon, sort_order, is_active, created_at, updated_at) VALUES ('2a5cecc5-4fa0-41d4-b99f-93c470a26bf7', 'Settings', 'SETTINGS', NULL, NULL, 0, TRUE, '2026-01-05 14:52:59.168711', '2026-01-05 14:52:59.168712');

-- PERMISSIONS (40 rows)
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('2cfac7f2-b8f0-43b6-8258-2caee226a2c4', 'View Dashboard', 'DASHBOARD_VIEW', NULL, 'd3fcdaf8-4476-4f99-afd7-4e3a93e3c568', 'view', TRUE, '2026-01-05 14:52:59.171118', '2026-01-05 14:52:59.171119');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('6229662f-3bf0-417f-bcf0-6b901c04f1c1', 'Create Dashboard', 'DASHBOARD_CREATE', NULL, 'd3fcdaf8-4476-4f99-afd7-4e3a93e3c568', 'create', TRUE, '2026-01-05 14:52:59.171120', '2026-01-05 14:52:59.171120');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('ef3dddbb-eedc-4290-8e88-1631c86ae065', 'Update Dashboard', 'DASHBOARD_UPDATE', NULL, 'd3fcdaf8-4476-4f99-afd7-4e3a93e3c568', 'update', TRUE, '2026-01-05 14:52:59.171121', '2026-01-05 14:52:59.171121');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('207a4d2c-cf96-4ffc-93e4-87081cf1070f', 'Delete Dashboard', 'DASHBOARD_DELETE', NULL, 'd3fcdaf8-4476-4f99-afd7-4e3a93e3c568', 'delete', TRUE, '2026-01-05 14:52:59.171122', '2026-01-05 14:52:59.171122');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('6dd98961-3fe1-48ad-8e4d-4e487a3e1800', 'View User Management', 'USER_MGMT_VIEW', NULL, 'c125b2c8-78e7-448d-b782-0930ec7dc990', 'view', TRUE, '2026-01-05 14:52:59.171123', '2026-01-05 14:52:59.171123');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('f6c6b676-ffaa-41ab-ace0-afd2724fc09b', 'Create User Management', 'USER_MGMT_CREATE', NULL, 'c125b2c8-78e7-448d-b782-0930ec7dc990', 'create', TRUE, '2026-01-05 14:52:59.171124', '2026-01-05 14:52:59.171124');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('671040ea-3998-43a7-a3ad-a319dbabfbaf', 'Update User Management', 'USER_MGMT_UPDATE', NULL, 'c125b2c8-78e7-448d-b782-0930ec7dc990', 'update', TRUE, '2026-01-05 14:52:59.171125', '2026-01-05 14:52:59.171125');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('ad89b5fb-4a0c-4a53-8e06-620e624cbdbf', 'Delete User Management', 'USER_MGMT_DELETE', NULL, 'c125b2c8-78e7-448d-b782-0930ec7dc990', 'delete', TRUE, '2026-01-05 14:52:59.171126', '2026-01-05 14:52:59.171126');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('b114217f-d4be-4477-b438-bd61ae790c31', 'View Role Management', 'ROLE_MGMT_VIEW', NULL, 'dc3ddcb2-598c-48ab-b613-16eaa020b0ce', 'view', TRUE, '2026-01-05 14:52:59.171127', '2026-01-05 14:52:59.171127');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('21563edf-1064-4934-9e6d-467473354691', 'Create Role Management', 'ROLE_MGMT_CREATE', NULL, 'dc3ddcb2-598c-48ab-b613-16eaa020b0ce', 'create', TRUE, '2026-01-05 14:52:59.171128', '2026-01-05 14:52:59.171128');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('6bcebeb9-0b43-4a66-9a91-846e67baaeeb', 'Update Role Management', 'ROLE_MGMT_UPDATE', NULL, 'dc3ddcb2-598c-48ab-b613-16eaa020b0ce', 'update', TRUE, '2026-01-05 14:52:59.171128', '2026-01-05 14:52:59.171129');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('fcaa5f63-3028-4edc-b962-edfeb117361d', 'Delete Role Management', 'ROLE_MGMT_DELETE', NULL, 'dc3ddcb2-598c-48ab-b613-16eaa020b0ce', 'delete', TRUE, '2026-01-05 14:52:59.171129', '2026-01-05 14:52:59.171130');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('9613a2dc-5cf2-42d2-97d6-a34e20628807', 'View Product Catalog', 'PRODUCTS_VIEW', NULL, 'e12a0f47-9dd7-4baf-ab16-3904879d3842', 'view', TRUE, '2026-01-05 14:52:59.171130', '2026-01-05 14:52:59.171131');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('ec3809a2-ec27-4a9a-bc75-d6c3c4a094a9', 'Create Product Catalog', 'PRODUCTS_CREATE', NULL, 'e12a0f47-9dd7-4baf-ab16-3904879d3842', 'create', TRUE, '2026-01-05 14:52:59.171131', '2026-01-05 14:52:59.171132');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('1da11e0b-ab40-4100-86b9-e1f9f1b98ada', 'Update Product Catalog', 'PRODUCTS_UPDATE', NULL, 'e12a0f47-9dd7-4baf-ab16-3904879d3842', 'update', TRUE, '2026-01-05 14:52:59.171132', '2026-01-05 14:52:59.171133');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('b5abfeb6-ecbe-4c62-82d6-f0c2053019fa', 'Delete Product Catalog', 'PRODUCTS_DELETE', NULL, 'e12a0f47-9dd7-4baf-ab16-3904879d3842', 'delete', TRUE, '2026-01-05 14:52:59.171133', '2026-01-05 14:52:59.171133');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('f7c43d3a-329b-4e76-a90d-e08b1a683112', 'View Orders', 'ORDERS_VIEW', NULL, '91080601-f84a-4728-b0a7-6c234fc09dcf', 'view', TRUE, '2026-01-05 14:52:59.171134', '2026-01-05 14:52:59.171134');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('28b6dc01-4ae3-4a6b-b209-fe7b809b15d4', 'Create Orders', 'ORDERS_CREATE', NULL, '91080601-f84a-4728-b0a7-6c234fc09dcf', 'create', TRUE, '2026-01-05 14:52:59.171135', '2026-01-05 14:52:59.171135');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('1cb0ef53-c078-4505-bcdc-6e39e7d970f6', 'Update Orders', 'ORDERS_UPDATE', NULL, '91080601-f84a-4728-b0a7-6c234fc09dcf', 'update', TRUE, '2026-01-05 14:52:59.171136', '2026-01-05 14:52:59.171136');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('8cacddb4-2cf6-4255-b636-b2584e805cf3', 'Delete Orders', 'ORDERS_DELETE', NULL, '91080601-f84a-4728-b0a7-6c234fc09dcf', 'delete', TRUE, '2026-01-05 14:52:59.171137', '2026-01-05 14:52:59.171137');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('9d56d4cb-9464-48a7-a465-1eef78892f93', 'View Inventory', 'INVENTORY_VIEW', NULL, 'df1fae9e-84cd-4465-8729-3408d1547fbb', 'view', TRUE, '2026-01-05 14:52:59.171137', '2026-01-05 14:52:59.171138');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('55778053-9900-4410-8cf5-688b3811d74f', 'Create Inventory', 'INVENTORY_CREATE', NULL, 'df1fae9e-84cd-4465-8729-3408d1547fbb', 'create', TRUE, '2026-01-05 14:52:59.171138', '2026-01-05 14:52:59.171139');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('fd12e7e7-158f-4bf8-880b-6a1dafdfb809', 'Update Inventory', 'INVENTORY_UPDATE', NULL, 'df1fae9e-84cd-4465-8729-3408d1547fbb', 'update', TRUE, '2026-01-05 14:52:59.171139', '2026-01-05 14:52:59.171140');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('a245b27b-9aba-488f-a66a-29502f7fd344', 'Delete Inventory', 'INVENTORY_DELETE', NULL, 'df1fae9e-84cd-4465-8729-3408d1547fbb', 'delete', TRUE, '2026-01-05 14:52:59.171140', '2026-01-05 14:52:59.171140');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('3225aeff-f5bf-499d-b438-407e8638b4f3', 'View Service Management', 'SERVICE_VIEW', NULL, 'f79f8ff8-3f22-4074-a478-3534139e584e', 'view', TRUE, '2026-01-05 14:52:59.171141', '2026-01-05 14:52:59.171141');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('77069f71-84a4-4384-90f6-e4ba7ffdc564', 'Create Service Management', 'SERVICE_CREATE', NULL, 'f79f8ff8-3f22-4074-a478-3534139e584e', 'create', TRUE, '2026-01-05 14:52:59.171142', '2026-01-05 14:52:59.171142');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('de16a54c-e61c-4c15-84d5-892765a0893b', 'Update Service Management', 'SERVICE_UPDATE', NULL, 'f79f8ff8-3f22-4074-a478-3534139e584e', 'update', TRUE, '2026-01-05 14:52:59.171148', '2026-01-05 14:52:59.171148');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('cdaca1d0-418e-4080-b0b0-318ac9055226', 'Delete Service Management', 'SERVICE_DELETE', NULL, 'f79f8ff8-3f22-4074-a478-3534139e584e', 'delete', TRUE, '2026-01-05 14:52:59.171149', '2026-01-05 14:52:59.171149');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('6e4d07aa-b879-40b2-bbd2-2bf3f27e0422', 'View Customer Management', 'CUSTOMERS_VIEW', NULL, '4bee2c37-3433-411d-a2d5-dacc43e73e96', 'view', TRUE, '2026-01-05 14:52:59.171150', '2026-01-05 14:52:59.171150');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('94cecc9a-c31c-4cc1-a09e-c278d8a168a4', 'Create Customer Management', 'CUSTOMERS_CREATE', NULL, '4bee2c37-3433-411d-a2d5-dacc43e73e96', 'create', TRUE, '2026-01-05 14:52:59.171151', '2026-01-05 14:52:59.171151');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('c1b36d89-a935-47b0-afb5-ff303648c558', 'Update Customer Management', 'CUSTOMERS_UPDATE', NULL, '4bee2c37-3433-411d-a2d5-dacc43e73e96', 'update', TRUE, '2026-01-05 14:52:59.171151', '2026-01-05 14:52:59.171152');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('07ded5ac-d58e-48d1-ae5c-9aa1e71cfbf9', 'Delete Customer Management', 'CUSTOMERS_DELETE', NULL, '4bee2c37-3433-411d-a2d5-dacc43e73e96', 'delete', TRUE, '2026-01-05 14:52:59.171152', '2026-01-05 14:52:59.171153');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('42968b3e-4c96-4467-b2ff-d1446200fc07', 'View Reports', 'REPORTS_VIEW', NULL, 'caa06b81-bf03-4f2b-a9d9-267ce925df29', 'view', TRUE, '2026-01-05 14:52:59.171153', '2026-01-05 14:52:59.171154');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('0d0adaa9-08fb-4049-a834-31ed046d4cb3', 'Create Reports', 'REPORTS_CREATE', NULL, 'caa06b81-bf03-4f2b-a9d9-267ce925df29', 'create', TRUE, '2026-01-05 14:52:59.171154', '2026-01-05 14:52:59.171154');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('02619a93-fb64-4c54-87d1-03c8a2d9f77e', 'Update Reports', 'REPORTS_UPDATE', NULL, 'caa06b81-bf03-4f2b-a9d9-267ce925df29', 'update', TRUE, '2026-01-05 14:52:59.171155', '2026-01-05 14:52:59.171155');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('a035e019-533a-4f83-9a3e-ecba8c82ccbc', 'Delete Reports', 'REPORTS_DELETE', NULL, 'caa06b81-bf03-4f2b-a9d9-267ce925df29', 'delete', TRUE, '2026-01-05 14:52:59.171156', '2026-01-05 14:52:59.171156');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('910f89ec-c0ae-42af-96e9-d31547d8b938', 'View Settings', 'SETTINGS_VIEW', NULL, '2a5cecc5-4fa0-41d4-b99f-93c470a26bf7', 'view', TRUE, '2026-01-05 14:52:59.171157', '2026-01-05 14:52:59.171157');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('053311fe-e163-4eee-acb9-e04286573bf8', 'Create Settings', 'SETTINGS_CREATE', NULL, '2a5cecc5-4fa0-41d4-b99f-93c470a26bf7', 'create', TRUE, '2026-01-05 14:52:59.171157', '2026-01-05 14:52:59.171158');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('6d8dda46-ce41-4c7b-8262-e89603020a2f', 'Update Settings', 'SETTINGS_UPDATE', NULL, '2a5cecc5-4fa0-41d4-b99f-93c470a26bf7', 'update', TRUE, '2026-01-05 14:52:59.171158', '2026-01-05 14:52:59.171159');
INSERT INTO permissions (id, name, code, description, module_id, action, is_active, created_at, updated_at) VALUES ('be80d3ab-00a2-4d56-9a24-f651f74d8cbe', 'Delete Settings', 'SETTINGS_DELETE', NULL, '2a5cecc5-4fa0-41d4-b99f-93c470a26bf7', 'delete', TRUE, '2026-01-05 14:52:59.171159', '2026-01-05 14:52:59.171160');

-- ROLES (5 rows)
INSERT INTO roles (id, name, code, description, level, department, is_system, is_active, created_at, updated_at) VALUES ('389c2074-b07c-4d2f-b264-ad36f202843e', 'Super Admin', 'SUPER_ADMIN', 'Full system access', 'SUPER_ADMIN', NULL, TRUE, TRUE, '2026-01-05 14:52:59.170009', '2026-01-05 14:52:59.170011');
INSERT INTO roles (id, name, code, description, level, department, is_system, is_active, created_at, updated_at) VALUES ('ccd48b1a-71cd-455a-9faf-28a3e396e722', 'Director', 'DIRECTOR', 'Director level access', 'DIRECTOR', NULL, TRUE, TRUE, '2026-01-05 14:52:59.170012', '2026-01-05 14:52:59.170012');
INSERT INTO roles (id, name, code, description, level, department, is_system, is_active, created_at, updated_at) VALUES ('95449480-bead-4fcb-ad6b-52d8e94c384a', 'Manager', 'MANAGER', 'Management access', 'MANAGER', NULL, FALSE, TRUE, '2026-01-05 14:52:59.170389', '2026-01-05 14:52:59.170390');
INSERT INTO roles (id, name, code, description, level, department, is_system, is_active, created_at, updated_at) VALUES ('1c06bc19-4282-4841-a7c5-32bdd95ad9a6', 'System', 'SYSTEM', 'System role for automated processes', 'SUPER_ADMIN', NULL, TRUE, TRUE, '2026-01-06 03:32:25.955834', '2026-01-06 03:32:25.955837');
INSERT INTO roles (id, name, code, description, level, department, is_system, is_active, created_at, updated_at) VALUES ('84511147-75b2-4628-9d31-23d24b18880c', 'Test Role 3', 'TEST_ROLE_3', 'A test role', 'EXECUTIVE', NULL, FALSE, TRUE, '2026-01-08 04:33:55.059246', '2026-01-08 04:33:55.059248');

-- REGIONS (3 rows)
INSERT INTO regions (id, name, code, type, parent_id, description, is_active, created_at, updated_at) VALUES ('4cb641f0-aa29-4fbc-869e-6e74bf0f41ff', 'India', 'IN', 'COUNTRY', NULL, NULL, TRUE, '2026-01-05 14:52:59.169341', '2026-01-05 14:52:59.169342');
INSERT INTO regions (id, name, code, type, parent_id, description, is_active, created_at, updated_at) VALUES ('3639d0bd-a5c8-44b7-ac09-a929c35f0900', 'North Region', 'NORTH', 'ZONE', '4cb641f0-aa29-4fbc-869e-6e74bf0f41ff', NULL, TRUE, '2026-01-05 14:52:59.169343', '2026-01-05 14:52:59.169343');
INSERT INTO regions (id, name, code, type, parent_id, description, is_active, created_at, updated_at) VALUES ('8234d1da-47b8-4f27-8819-dedf668e7aef', 'Delhi', 'DL', 'STATE', '3639d0bd-a5c8-44b7-ac09-a929c35f0900', NULL, TRUE, '2026-01-05 14:52:59.169344', '2026-01-05 14:52:59.169344');

-- USERS (3 rows)
INSERT INTO users (id, email, phone, password_hash, first_name, last_name, avatar_url, employee_code, department, designation, region_id, is_active, is_verified, created_at, updated_at, last_login_at) VALUES ('460f1851-68f1-42b9-916e-48067d3c5231', 'admin@consumer.com', '+919999000001', '$2b$12$/RtpJ21Bh0NbQYAgqFOnuOtPRAHxIXVJI0//iBAeA6GUyyKn7Zx3C', 'Admin', 'User', NULL, NULL, 'Administration', 'System Administrator', '4cb641f0-aa29-4fbc-869e-6e74bf0f41ff', TRUE, TRUE, '2026-01-05 14:52:59.173706', '2026-01-08 09:06:11.297599', '2026-01-08 09:06:11.295100');
INSERT INTO users (id, email, phone, password_hash, first_name, last_name, avatar_url, employee_code, department, designation, region_id, is_active, is_verified, created_at, updated_at, last_login_at) VALUES ('7a973c20-4656-40e2-ae9a-e9732d8ea45d', 'accounts@aquapurite.com', '8802696256', '$2b$12$kr36ilm/Erq3kwVQgeQjce9e7oX5VgHDpRo5QLAhfgQowZOyv.mFW', 'Prashant ', 'Dhingra', NULL, NULL, 'Accounts', 'Manager', NULL, TRUE, FALSE, '2026-01-07 17:06:24.924381', '2026-01-07 17:06:24.924385', NULL);
INSERT INTO users (id, email, phone, password_hash, first_name, last_name, avatar_url, employee_code, department, designation, region_id, is_active, is_verified, created_at, updated_at, last_login_at) VALUES ('1ed49d65-62fe-4fc0-89d7-fcfaebbeff79', 'themanagingdirector@aquapurite.com', '9013034083', '$2b$12$NxdN.yNJSd1fxjcM7nIkOuKRXRFEKc17CSgOu.sr8C471UBdhNoXS', 'Anupam ', 'Singh', NULL, NULL, 'Management', 'Director', NULL, TRUE, FALSE, '2026-01-07 17:07:41.520918', '2026-01-07 17:07:41.520921', NULL);

-- USER_ROLES (2 rows)
INSERT INTO user_roles (id, user_id, role_id, assigned_by, assigned_at) VALUES ('3b959023-e786-41a4-94a9-f444b6432138', '460f1851-68f1-42b9-916e-48067d3c5231', '389c2074-b07c-4d2f-b264-ad36f202843e', NULL, '2026-01-05 14:52:59.162870');

-- ROLE_PERMISSIONS (0 rows)

-- CATEGORIES (9 rows)
INSERT INTO categories (id, name, slug, description, parent_id, image_url, icon, sort_order, meta_title, meta_description, is_active, is_featured, created_at, updated_at) VALUES ('516e8464-6c6c-4b88-9fee-6ea7a28a8900', 'Water Purifiers', 'water-purifiers', NULL, NULL, NULL, NULL, 1, NULL, NULL, TRUE, FALSE, '2026-01-05 14:52:59.167875', '2026-01-05 14:52:59.167876');
INSERT INTO categories (id, name, slug, description, parent_id, image_url, icon, sort_order, meta_title, meta_description, is_active, is_featured, created_at, updated_at) VALUES ('a7f26822-dee3-4084-9044-1cc68be12252', 'Air Purifiers', 'air-purifiers', NULL, NULL, NULL, NULL, 2, NULL, NULL, TRUE, FALSE, '2026-01-05 14:52:59.167877', '2026-01-05 14:52:59.167878');
INSERT INTO categories (id, name, slug, description, parent_id, image_url, icon, sort_order, meta_title, meta_description, is_active, is_featured, created_at, updated_at) VALUES ('75a2cf5a-2d63-4d1e-9348-d22953397c74', 'RO Systems', 'ro-systems', NULL, '516e8464-6c6c-4b88-9fee-6ea7a28a8900', NULL, NULL, 1, NULL, NULL, TRUE, FALSE, '2026-01-05 14:52:59.167878', '2026-01-05 14:52:59.167879');
INSERT INTO categories (id, name, slug, description, parent_id, image_url, icon, sort_order, meta_title, meta_description, is_active, is_featured, created_at, updated_at) VALUES ('e40136d9-383d-47ab-8a60-ac3ce50f814a', 'UV Systems', 'uv-systems', NULL, '516e8464-6c6c-4b88-9fee-6ea7a28a8900', NULL, NULL, 2, NULL, NULL, TRUE, FALSE, '2026-01-05 14:52:59.167879', '2026-01-05 14:52:59.167880');
INSERT INTO categories (id, name, slug, description, parent_id, image_url, icon, sort_order, meta_title, meta_description, is_active, is_featured, created_at, updated_at) VALUES ('cc93ae5f-a2f3-4e9c-9c39-30b79330be77', 'RO Water Purifiers', 'ro-water-purifiers', 'Reverse Osmosis water purifiers for TDS reduction', NULL, '/images/categories/ro-icon.png', 'ro', 0, NULL, NULL, TRUE, FALSE, '2026-01-07 02:30:35.315425', '2026-01-07 02:30:35.315426');
INSERT INTO categories (id, name, slug, description, parent_id, image_url, icon, sort_order, meta_title, meta_description, is_active, is_featured, created_at, updated_at) VALUES ('d3c8e19c-b8d8-41c1-9382-151415e5612b', 'UV Water Purifiers', 'uv-water-purifiers', 'UV sterilization water purifiers', NULL, '/images/categories/uv-icon.png', 'uv', 1, NULL, NULL, TRUE, FALSE, '2026-01-07 02:30:35.316305', '2026-01-07 02:30:35.316306');
INSERT INTO categories (id, name, slug, description, parent_id, image_url, icon, sort_order, meta_title, meta_description, is_active, is_featured, created_at, updated_at) VALUES ('a4d49b27-2dcf-45fb-83d6-e550c4726e50', 'RO+UV Water Purifiers', 'ro-uv-water-purifiers', 'Combined RO and UV water purifiers for comprehensive purification', NULL, '/images/categories/ro-uv-icon.png', 'ro-uv', 2, NULL, NULL, TRUE, FALSE, '2026-01-07 02:30:35.316942', '2026-01-07 02:30:35.316943');
INSERT INTO categories (id, name, slug, description, parent_id, image_url, icon, sort_order, meta_title, meta_description, is_active, is_featured, created_at, updated_at) VALUES ('557cd594-c60a-4eef-a696-deddcbb03f9a', 'Hot & Cold Water Purifiers', 'hot-cold-water-purifiers', 'Multi-temperature water dispensing purifiers', NULL, '/images/categories/hot-cold-icon.png', 'hot-cold', 3, NULL, NULL, TRUE, FALSE, '2026-01-07 02:30:35.317717', '2026-01-07 02:30:35.317718');
INSERT INTO categories (id, name, slug, description, parent_id, image_url, icon, sort_order, meta_title, meta_description, is_active, is_featured, created_at, updated_at) VALUES ('d491b161-30c9-47e7-a21a-21b41d6325a7', 'Spare Parts', 'spare-parts', 'Replacement parts and consumables for water purifiers', NULL, NULL, NULL, 0, NULL, NULL, TRUE, FALSE, '2026-01-07 08:07:56.572138', '2026-01-07 08:07:56.572142');

-- BRANDS (3 rows)
INSERT INTO brands (id, name, slug, description, logo_url, banner_url, website, contact_email, contact_phone, sort_order, is_active, is_featured, created_at, updated_at) VALUES ('88d242df-5fda-4fdb-9676-ee40bf97e1a5', 'AquaPure', 'aquapure', NULL, NULL, NULL, NULL, NULL, NULL, 0, FALSE, FALSE, '2026-01-05 14:52:59.166139', '2026-01-08 00:31:31.519262');
INSERT INTO brands (id, name, slug, description, logo_url, banner_url, website, contact_email, contact_phone, sort_order, is_active, is_featured, created_at, updated_at) VALUES ('c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 'Aquapurite', 'aquapurite', 'Premium water purification solutions', '/images/brands/aquapurite-logo.png', NULL, 'https://aquapurite.com', NULL, NULL, 0, TRUE, TRUE, '2026-01-07 02:30:35.313390', '2026-01-07 02:30:35.313393');
INSERT INTO brands (id, name, slug, description, logo_url, banner_url, website, contact_email, contact_phone, sort_order, is_active, is_featured, created_at, updated_at) VALUES ('559e5217-5c6c-45b4-a1c6-7f9620823d20', 'Test Brand 2', 'test-brand-2', 'A test brand', NULL, NULL, NULL, NULL, NULL, 0, TRUE, FALSE, '2026-01-08 04:32:11.011229', '2026-01-08 04:32:11.011235');

-- PRODUCTS (23 rows)
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('407c6c26-2622-4884-9cc6-77847df7c3a2', 'AquaPure RO Premium', 'aquapure-ro-premium', 'AP-RO-001', 'AP-RO-PREM-7L', '7-stage RO water purifier with TDS controller', NULL, NULL, '75a2cf5a-2d63-4d1e-9348-d22953397c74', '88d242df-5fda-4fdb-9676-ee40bf97e1a5', 19999, 14999, NULL, NULL, NULL, 18, 24, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, TRUE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-05 14:52:59.172554', '2026-01-05 14:52:59.172555', NULL, NULL, 'FG', NULL, NULL, NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('ccad4541-38ce-4d55-b910-e9193dbee710', 'AquaPure UV Compact', 'aquapure-uv-compact', 'AP-UV-001', 'AP-UV-COMP-5L', 'Compact UV water purifier for municipal water', NULL, NULL, 'e40136d9-383d-47ab-8a60-ac3ce50f814a', '88d242df-5fda-4fdb-9676-ee40bf97e1a5', 9999, 7999, NULL, NULL, NULL, 18, 12, FALSE, NULL, NULL, 40, 25, 50, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-05 14:52:59.173160', '2026-01-06 16:41:51.275823', NULL, 'UVC', 'FG', 4.5, 'WPRAUVCOMP001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('6cde9e89-1783-4777-a1fd-6264a9974874', 'Aquapurite Blitz', 'aquapurite-blitz', 'AP-BLITZ-001', 'BLITZ-RO-UV', 'RO+UV water purifier with Zinc Copper enrichment and pH Balance technology', '<h2>Aquapurite Blitz - Advanced RO+UV Water Purifier</h2>
<p>Experience the purest water with Aquapurite Blitz featuring advanced RO+UV purification technology.</p>
<h3>Key Features:</h3>
<ul>
<li>9-Stage Purification Process</li>
<li>RO + UV + UF Technology</li>
<li>Zinc & Copper Enrichment</li>
<li>pH Balance Technology</li>
<li>TDS Controller</li>
<li>10L Storage Tank</li>
</ul>', 'RO+UV+UF, Zinc Copper, pH Balance, 9-Stage Purification, 10L Tank, Smart LED Indicators', 'a4d49b27-2dcf-45fb-83d6-e550c4726e50', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 17999, 14999, 11999, 9500, '84212110', 18, 12, TRUE, NULL, NULL, 38, 27, 54, 10, NULL, 'ACTIVE', TRUE, TRUE, FALSE, TRUE, 0, NULL, NULL, NULL, NULL, '2026-01-07 02:30:35.320924', '2026-01-07 02:30:35.320925', NULL, NULL, 'FG', 9.5, NULL, NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('4dd27b51-d013-4499-bb7c-a3899576b240', 'Aquapurite i Elitz', 'aquapurite-i-elitz', 'AP-IELITZ-001', 'IELITZ-HOT-COLD', 'Premium Hot/Cold/Ambient RO water purifier with instant heating technology', '<h2>Aquapurite i Elitz - Hot, Cold & Ambient Water Purifier</h2>
<p>The ultimate convenience with 3-temperature water dispensing and advanced RO purification.</p>
<h3>Key Features:</h3>
<ul>
<li>Hot, Cold & Ambient Water</li>
<li>Instant Heating Technology</li>
<li>RO + UV + UF Purification</li>
<li>12L Storage Tank</li>
<li>Touch Panel Controls</li>
<li>Energy Saving Mode</li>
</ul>', 'Hot/Cold/Ambient, RO+UV+UF, Touch Controls, 12L Tank, Energy Saving, Child Lock', '557cd594-c60a-4eef-a696-deddcbb03f9a', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 34999, 26999, 21999, 18000, '84212110', 18, 12, TRUE, NULL, NULL, 42, 32, 58, 10, NULL, 'ACTIVE', TRUE, TRUE, FALSE, TRUE, 0, NULL, NULL, NULL, NULL, '2026-01-07 02:30:35.322121', '2026-01-07 02:30:35.322122', NULL, 'IEL', 'FG', 14, 'WPRAIEL001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('dc25a19f-8b21-4c9a-8d0a-1249571d6679', 'Aquapurite i Premiuo', 'aquapurite-i-premiuo', 'AP-IPREMIUO-001', 'IPREMIUO-HOT-AMB', 'Hot & Ambient RO water purifier with premium design and instant heating', '<h2>Aquapurite i Premiuo - Hot & Ambient Water Purifier</h2>
<p>Premium design meets functionality with hot and ambient water dispensing.</p>
<h3>Key Features:</h3>
<ul>
<li>Hot & Ambient Water</li>
<li>Instant Hot Water</li>
<li>RO + UV Purification</li>
<li>10L Storage Tank</li>
<li>Sleek Design</li>
<li>Auto-Shutoff</li>
</ul>', 'Hot/Ambient, RO+UV, Instant Heat, 10L Tank, Auto-Shutoff, Premium Design', '557cd594-c60a-4eef-a696-deddcbb03f9a', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 29999, 23999, 19500, 15500, '84212110', 18, 12, TRUE, NULL, NULL, 40, 30, 55, 10, NULL, 'ACTIVE', TRUE, TRUE, FALSE, TRUE, 0, NULL, NULL, NULL, NULL, '2026-01-07 02:30:35.324380', '2026-01-07 02:30:35.324381', NULL, 'IPM', 'FG', 12, 'WPRAIPREM001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('99f7d2c8-7546-44f9-aeac-79e703d13774', 'Aquapurite Neura', 'aquapurite-neura', 'AP-NEURA-001', 'NEURA-RO-UV', 'Smart RO+UV water purifier with Zinc Copper enrichment and IOT connectivity', '<h2>Aquapurite Neura - Smart RO+UV Water Purifier</h2>
<p>Intelligent water purification with advanced mineral enrichment technology.</p>
<h3>Key Features:</h3>
<ul>
<li>Smart IOT Connectivity</li>
<li>RO + UV + UF Technology</li>
<li>Zinc & Copper Enrichment</li>
<li>Real-time TDS Display</li>
<li>Filter Life Indicator</li>
<li>8L Storage Tank</li>
</ul>', 'RO+UV+UF, Zinc Copper, Smart IOT, TDS Display, 8L Tank, Filter Indicator', 'a4d49b27-2dcf-45fb-83d6-e550c4726e50', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 16999, 13999, 10999, 8500, '84212110', 18, 12, TRUE, NULL, NULL, 36, 26, 52, 10, NULL, 'ACTIVE', TRUE, TRUE, FALSE, TRUE, 0, NULL, NULL, NULL, NULL, '2026-01-07 02:30:35.325817', '2026-01-07 02:30:35.325818', NULL, 'NEU', 'FG', 8.5, 'WPRANEU001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('f55f8107-6c2f-486b-9501-4b0720cb55af', 'Aquapurite Premiuo UV', 'aquapurite-premiuo-uv', 'AP-PREMIUOUV-001', 'PREMIUO-UV', 'Compact UV water purifier for low TDS water with advanced UV sterilization', '<h2>Aquapurite Premiuo UV - Compact UV Water Purifier</h2>
<p>Perfect for municipal/low TDS water with powerful UV sterilization.</p>
<h3>Key Features:</h3>
<ul>
<li>UV + UF Purification</li>
<li>Ideal for Low TDS Water</li>
<li>Compact Design</li>
<li>No Water Wastage</li>
<li>6L Storage Tank</li>
<li>Easy Installation</li>
</ul>', 'UV+UF, Zero Water Wastage, Compact Design, 6L Tank, Auto-Shutoff', 'd3c8e19c-b8d8-41c1-9382-151415e5612b', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 8999, 6999, 5499, 4200, '84212110', 18, 12, TRUE, NULL, NULL, 32, 24, 48, 10, NULL, 'ACTIVE', TRUE, TRUE, FALSE, TRUE, 0, NULL, NULL, NULL, NULL, '2026-01-07 02:30:35.327344', '2026-01-07 02:30:35.327344', NULL, 'PUV', 'FG', 5.5, 'WPRAPUV001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('29ab9706-77d0-4582-9b6e-75dbdb28e3ca', 'Sediment Filter (PP Yarn Wound)', 'sp-sdf-001', 'SP-SDF-001', NULL, 'PP Yarn Wound Sediment Filter for pre-filtration', 'PP Yarn Wound Sediment Filter for pre-filtration', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 250, 180, NULL, 97, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410451', '2026-01-07 08:15:09.410454', NULL, 'SDF', 'SP', NULL, 'SPSDF001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('d39a787c-23c0-434f-95a1-7dcaeb46524f', 'Sediment Filter (Spun Filter)', 'sp-sdf-002', 'SP-SDF-002', NULL, 'Spun Filter for sediment removal', 'Spun Filter for sediment removal', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 200, 150, NULL, 76, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410460', '2026-01-07 08:15:09.410460', NULL, 'SDF', 'SP', NULL, 'SPSDF002', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('d0c0f205-c758-46d7-ab7f-4e735568d86b', 'Pre Carbon Block (Premium)', 'sp-pcb-001', 'SP-PCB-001', NULL, 'Premium Pre Carbon Block Filter for chlorine removal', 'Premium Pre Carbon Block Filter for chlorine removal', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 350, 280, NULL, 114, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410464', '2026-01-07 08:15:09.410464', NULL, 'PCB', 'SP', NULL, 'SPPCB001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('03f43e45-6250-410b-a588-23ffe8e13ca4', 'Pre Carbon Block (Regular)', 'sp-pcb-002', 'SP-PCB-002', NULL, 'Regular Pre Carbon Block Filter', 'Regular Pre Carbon Block Filter', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 300, 220, NULL, 111, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410467', '2026-01-07 08:15:09.410468', NULL, 'PCB', 'SP', NULL, 'SPPCB002', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('795b436c-ca92-48a9-b0ca-29b821d75169', 'Alkaline Mineral Block (Premium)', 'sp-alk-001', 'SP-ALK-001', NULL, 'Premium Alkaline Mineral Filter for pH balance', 'Premium Alkaline Mineral Filter for pH balance', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 200, 150, NULL, 61, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410471', '2026-01-07 08:15:09.410471', NULL, 'ALK', 'SP', NULL, 'SPALK001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('a2496867-121f-4aaa-a371-5726809d3770', 'Post Carbon with Copper (Regular)', 'sp-poc-001', 'SP-POC-001', NULL, 'Post Carbon Filter with Copper infusion', 'Post Carbon Filter with Copper infusion', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 180, 130, NULL, 58, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410475', '2026-01-07 08:15:09.410475', NULL, 'POC', 'SP', NULL, 'SPPOC001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('b53fe7f4-2a4d-46e5-ac4b-0d4834bf793c', 'Membrane (Premium)', 'sp-mbf-001', 'SP-MBF-001', NULL, 'Premium RO Membrane 100 GPD', 'Premium RO Membrane 100 GPD', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 1200, 900, NULL, 398, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410478', '2026-01-07 08:15:09.410478', NULL, 'MBF', 'SP', NULL, 'SPMBF001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('a52d1f09-a203-43db-ba7c-6838527641ee', 'Membrane (Regular)', 'sp-mbf-002', 'SP-MBF-002', NULL, 'Regular RO Membrane 75 GPD', 'Regular RO Membrane 75 GPD', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 1000, 750, NULL, 375, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410481', '2026-01-07 08:15:09.410482', NULL, 'MBF', 'SP', NULL, 'SPMBF002', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('ad994f12-6cf7-4c9d-b5ec-dc5916bf8d2b', 'Pre-Filter Multi Layer Candle', 'sp-pfc-001', 'SP-PFC-001', NULL, 'Multi-layer candle pre-filter for sediment removal', 'Multi-layer candle pre-filter for sediment removal', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 600, 450, NULL, 245, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410485', '2026-01-07 08:15:09.410485', NULL, 'PFC', 'SP', NULL, 'SPPFC001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('7bbbc1c7-bbb0-4895-bd0e-6df029057d57', 'Iron Remover Cartridge', 'sp-irc-001', 'SP-IRC-001', NULL, 'Iron remover cartridge for high iron water', 'Iron remover cartridge for high iron water', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 1500, 1100, NULL, 790, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410488', '2026-01-07 08:15:09.410488', NULL, 'IRC', 'SP', NULL, 'SPIRC001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('833f0fce-af34-4782-bd45-62d966ce27ac', 'HMR Cartridge', 'sp-hmr-001', 'SP-HMR-001', NULL, 'Heavy Metal Remover Cartridge', 'Heavy Metal Remover Cartridge', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 1500, 1100, NULL, 801, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410491', '2026-01-07 08:15:09.410492', NULL, 'HMR', 'SP', NULL, 'SPHMR001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('35ec8b29-04f5-45a7-b3a8-78c72536d9dc', 'Prefilter with Multilayer Candle', 'sp-pfc-002', 'SP-PFC-002', NULL, 'Complete prefilter assembly with multilayer candle', 'Complete prefilter assembly with multilayer candle', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 700, 500, NULL, 280, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410495', '2026-01-07 08:15:09.410495', NULL, 'PFC', 'SP', NULL, 'SPPFC002', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('7d14eafb-501a-46e0-91b8-a4619fff8466', 'Prefilter with Spun Filter', 'sp-pfs-001', 'SP-PFS-001', NULL, 'Complete prefilter assembly with spun filter', 'Complete prefilter assembly with spun filter', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 550, 400, NULL, 225, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410498', '2026-01-07 08:15:09.410499', NULL, 'PFS', 'SP', NULL, 'SPPFS001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('41c4b2ca-ae0b-4f02-8258-2012b346a80e', 'Heavy Metal Remover', 'sp-hmr-002', 'SP-HMR-002', NULL, 'Heavy metal remover filter for arsenic, lead removal', 'Heavy metal remover filter for arsenic, lead removal', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 1800, 1300, NULL, 850, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410501', '2026-01-07 08:15:09.410502', NULL, 'HMR', 'SP', NULL, 'SPHMR002', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('f4c0317f-b573-4422-9081-56353a386863', 'Plastic PRV', 'sp-prv-001', 'SP-PRV-001', NULL, 'Plastic Pressure Reducing Valve', 'Plastic Pressure Reducing Valve', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 350, 250, NULL, 180, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410505', '2026-01-07 08:15:09.410505', NULL, 'PRV', 'SP', NULL, 'SPPRV001', NULL);
INSERT INTO products (id, name, slug, sku, model_number, short_description, description, features, category_id, brand_id, mrp, selling_price, dealer_price, cost_price, hsn_code, gst_rate, warranty_months, extended_warranty_available, warranty_terms, weight_kg, length_cm, width_cm, height_cm, min_stock_level, max_stock_level, status, is_active, is_featured, is_bestseller, is_new_arrival, sort_order, meta_title, meta_description, meta_keywords, extra_data, created_at, updated_at, published_at, model_code, item_type, dead_weight_kg, fg_code, part_code) VALUES ('920748a6-c870-461f-aad4-2a671ed9fe66', 'Brass Diverter Valve', 'sp-bdv-001', 'SP-BDV-001', NULL, 'Brass diverter valve for water purifier installation', 'Brass diverter valve for water purifier installation', NULL, 'd491b161-30c9-47e7-a21a-21b41d6325a7', 'c8a6afb6-2ad3-4ba0-8760-140dd62180d5', 300, 220, NULL, 150, '84212190', 18, 6, FALSE, NULL, NULL, NULL, NULL, NULL, 10, NULL, 'ACTIVE', TRUE, FALSE, FALSE, FALSE, 0, NULL, NULL, NULL, NULL, '2026-01-07 08:15:09.410508', '2026-01-07 08:15:09.410508', NULL, 'BDV', 'SP', NULL, 'SPBDV001', NULL);

-- WAREHOUSES (4 rows)
INSERT INTO warehouses (id, code, name, warehouse_type, address_line1, address_line2, city, state, pincode, country, latitude, longitude, contact_name, contact_phone, contact_email, region_id, manager_id, total_capacity, current_utilization, is_active, is_default, can_fulfill_orders, can_receive_transfers, notes, created_at, updated_at) VALUES ('c0f09920-b71a-497b-ba03-c54be4bca7e1', 'WH-DEL-001', 'Central Warehouse Delhi', 'MAIN', 'Industrial Area, Phase 1', NULL, 'Delhi', 'Delhi', '110001', 'India', NULL, NULL, NULL, NULL, NULL, '8234d1da-47b8-4f27-8819-dedf668e7aef', NULL, 0.0, 0.0, TRUE, FALSE, TRUE, TRUE, NULL, '2026-01-05 14:52:59.175048', '2026-01-05 14:52:59.175049');
INSERT INTO warehouses (id, code, name, warehouse_type, address_line1, address_line2, city, state, pincode, country, latitude, longitude, contact_name, contact_phone, contact_email, region_id, manager_id, total_capacity, current_utilization, is_active, is_default, can_fulfill_orders, can_receive_transfers, notes, created_at, updated_at) VALUES ('32bbea22-735d-49c4-b086-b80c9623ec25', 'SC-DEL-001', 'Service Center Delhi', 'SERVICE_CENTER', 'Service Hub, Connaught Place', NULL, 'Delhi', 'Delhi', '110001', 'India', NULL, NULL, NULL, NULL, NULL, '8234d1da-47b8-4f27-8819-dedf668e7aef', NULL, 0.0, 0.0, FALSE, FALSE, TRUE, TRUE, NULL, '2026-01-05 14:52:59.175051', '2026-01-08 04:31:44.214635');
INSERT INTO warehouses (id, code, name, warehouse_type, address_line1, address_line2, city, state, pincode, country, latitude, longitude, contact_name, contact_phone, contact_email, region_id, manager_id, total_capacity, current_utilization, is_active, is_default, can_fulfill_orders, can_receive_transfers, notes, created_at, updated_at) VALUES ('b89dc1da-0f89-4f19-a057-e8f2efe34614', 'WH-TEST-001', 'Test Warehouse', 'MAIN', 'Test Address', NULL, 'Mumbai', 'Maharashtra', '400001', 'India', NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.0, 0.0, FALSE, FALSE, TRUE, TRUE, NULL, '2026-01-08 04:18:28.847114', '2026-01-08 04:20:21.124799');
INSERT INTO warehouses (id, code, name, warehouse_type, address_line1, address_line2, city, state, pincode, country, latitude, longitude, contact_name, contact_phone, contact_email, region_id, manager_id, total_capacity, current_utilization, is_active, is_default, can_fulfill_orders, can_receive_transfers, notes, created_at, updated_at) VALUES ('5ee92653-59c3-46d6-86a8-2684e14d75e0', 'TST-WH-002', 'Test Warehouse API', 'MAIN', '123 Test Street', NULL, 'Mumbai', 'Maharashtra', '400001', 'India', NULL, NULL, NULL, NULL, NULL, NULL, NULL, 1000.0, 0.0, FALSE, FALSE, TRUE, TRUE, NULL, '2026-01-08 04:31:32.394196', '2026-01-08 04:32:38.420423');

-- DEALERS (1 rows)
INSERT INTO dealers (id, dealer_code, name, legal_name, display_name, dealer_type, status, tier, parent_dealer_id, user_id, gstin, pan, tan, gst_registration_type, is_msme, msme_number, contact_person, email, phone, alternate_phone, whatsapp, registered_address_line1, registered_address_line2, registered_city, registered_district, registered_state, registered_state_code, registered_pincode, shipping_address_line1, shipping_address_line2, shipping_city, shipping_state, shipping_pincode, region, state, territory, assigned_pincodes, business_type, establishment_year, annual_turnover, shop_area_sqft, no_of_employees, existing_brands, bank_name, bank_branch, bank_account_number, bank_ifsc, bank_account_name, credit_limit, credit_days, credit_status, outstanding_amount, overdue_amount, security_deposit, security_deposit_paid, default_warehouse_id, sales_rep_id, area_sales_manager_id, agreement_start_date, agreement_end_date, agreement_document_url, gst_certificate_url, pan_card_url, shop_photo_url, cancelled_cheque_url, kyc_verified, kyc_verified_at, kyc_verified_by, total_orders, total_revenue, last_order_date, average_order_value, dealer_rating, payment_rating, can_place_orders, receive_promotions, portal_access, internal_notes, onboarded_at, created_at, updated_at) VALUES ('0b1c5845-d4a2-4cd3-98ca-3fb55ff162ae', 'DLR-00001', 'Test Dealer API Fix', 'Test Dealer API Fix Pvt Ltd', NULL, 'DEALER', 'PENDING_APPROVAL', 'STANDARD', NULL, NULL, '27AAAAA1234Z1Z5', 'AAAAA1234Z', NULL, 'REGULAR', FALSE, NULL, 'Test Contact', 'test.dealer.fix@example.com', '9998887770', NULL, NULL, '123 Test Street', NULL, 'Mumbai', 'Mumbai', 'Maharashtra', '27', '400001', NULL, NULL, NULL, NULL, NULL, 'WEST', 'Maharashtra', NULL, NULL, 'PROPRIETORSHIP', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 30, 'ACTIVE', 5000, 0, 0, FALSE, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, TRUE, TRUE, TRUE, NULL, NULL, '2026-01-08 06:28:54.324314', '2026-01-08 06:28:54.324319');
