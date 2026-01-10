-- =====================================================
-- COMPLETE SUPABASE MIGRATION SCRIPT
-- Consumer Durable ERP System
-- Generated: 2026-01-10
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- PART 1: DROP EXISTING ENUM TYPES (if any)
-- =====================================================

DO $$
BEGIN
    -- User/Role Enums
    DROP TYPE IF EXISTS user_status CASCADE;
    DROP TYPE IF EXISTS user_type CASCADE;

    -- Approval Enums
    DROP TYPE IF EXISTS approval_status CASCADE;
    DROP TYPE IF EXISTS approval_action CASCADE;
    DROP TYPE IF EXISTS entity_type CASCADE;

    -- Customer Enums
    DROP TYPE IF EXISTS customer_type CASCADE;
    DROP TYPE IF EXISTS customer_status CASCADE;
    DROP TYPE IF EXISTS address_type CASCADE;

    -- Product Enums
    DROP TYPE IF EXISTS product_status CASCADE;
    DROP TYPE IF EXISTS product_type CASCADE;

    -- Order Enums
    DROP TYPE IF EXISTS order_status CASCADE;
    DROP TYPE IF EXISTS order_type CASCADE;
    DROP TYPE IF EXISTS payment_status CASCADE;
    DROP TYPE IF EXISTS order_source CASCADE;

    -- Service Enums
    DROP TYPE IF EXISTS service_type CASCADE;
    DROP TYPE IF EXISTS service_priority CASCADE;
    DROP TYPE IF EXISTS service_status CASCADE;
    DROP TYPE IF EXISTS service_source CASCADE;

    -- AMC Enums
    DROP TYPE IF EXISTS amc_type CASCADE;
    DROP TYPE IF EXISTS amc_status CASCADE;

    -- Technician Enums
    DROP TYPE IF EXISTS technician_status CASCADE;
    DROP TYPE IF EXISTS technician_type CASCADE;
    DROP TYPE IF EXISTS skill_level CASCADE;

    -- Inventory Enums
    DROP TYPE IF EXISTS stock_item_status CASCADE;
    DROP TYPE IF EXISTS stock_movement_type CASCADE;

    -- Transfer Enums
    DROP TYPE IF EXISTS transfer_status CASCADE;
    DROP TYPE IF EXISTS transfer_type CASCADE;

    -- Installation Enums
    DROP TYPE IF EXISTS installation_status CASCADE;

    -- Shipment Enums
    DROP TYPE IF EXISTS shipment_status CASCADE;
    DROP TYPE IF EXISTS payment_mode CASCADE;
    DROP TYPE IF EXISTS packaging_type CASCADE;

    -- Manifest Enums
    DROP TYPE IF EXISTS manifest_status CASCADE;
    DROP TYPE IF EXISTS business_type CASCADE;

    -- Transporter Enums
    DROP TYPE IF EXISTS transporter_type CASCADE;

    -- WMS Enums
    DROP TYPE IF EXISTS zone_type CASCADE;
    DROP TYPE IF EXISTS bin_type CASCADE;

    -- Purchase Enums
    DROP TYPE IF EXISTS requisition_status CASCADE;
    DROP TYPE IF EXISTS po_status CASCADE;
    DROP TYPE IF EXISTS grn_status CASCADE;
    DROP TYPE IF EXISTS vendor_invoice_status CASCADE;
    DROP TYPE IF EXISTS quality_check_result CASCADE;
    DROP TYPE IF EXISTS delivery_lot_status CASCADE;
    DROP TYPE IF EXISTS proforma_status CASCADE;

    -- Vendor Enums
    DROP TYPE IF EXISTS vendor_status CASCADE;
    DROP TYPE IF EXISTS vendor_type CASCADE;

    -- Dealer Enums
    DROP TYPE IF EXISTS dealer_status CASCADE;
    DROP TYPE IF EXISTS dealer_type CASCADE;

    -- Lead Enums
    DROP TYPE IF EXISTS lead_source CASCADE;
    DROP TYPE IF EXISTS lead_status CASCADE;
    DROP TYPE IF EXISTS lead_priority CASCADE;
    DROP TYPE IF EXISTS lead_type CASCADE;
    DROP TYPE IF EXISTS lead_interest CASCADE;
    DROP TYPE IF EXISTS activity_type CASCADE;
    DROP TYPE IF EXISTS lost_reason CASCADE;

    -- Call Center Enums
    DROP TYPE IF EXISTS call_type CASCADE;
    DROP TYPE IF EXISTS call_category CASCADE;
    DROP TYPE IF EXISTS call_status CASCADE;
    DROP TYPE IF EXISTS call_outcome CASCADE;
    DROP TYPE IF EXISTS customer_sentiment CASCADE;
    DROP TYPE IF EXISTS call_priority CASCADE;
    DROP TYPE IF EXISTS callback_status CASCADE;
    DROP TYPE IF EXISTS qa_status CASCADE;

    -- Franchisee Enums
    DROP TYPE IF EXISTS franchisee_status CASCADE;
    DROP TYPE IF EXISTS franchisee_type CASCADE;
    DROP TYPE IF EXISTS franchisee_tier CASCADE;
    DROP TYPE IF EXISTS contract_status CASCADE;
    DROP TYPE IF EXISTS territory_status CASCADE;
    DROP TYPE IF EXISTS training_status CASCADE;
    DROP TYPE IF EXISTS training_type CASCADE;
    DROP TYPE IF EXISTS support_ticket_status CASCADE;
    DROP TYPE IF EXISTS support_ticket_priority CASCADE;
    DROP TYPE IF EXISTS support_ticket_category CASCADE;
    DROP TYPE IF EXISTS audit_status CASCADE;
    DROP TYPE IF EXISTS audit_type CASCADE;
    DROP TYPE IF EXISTS audit_result CASCADE;
    DROP TYPE IF EXISTS service_capability CASCADE;

END $$;

-- =====================================================
-- PART 2: CREATE ENUM TYPES
-- =====================================================

-- Approval Enums
CREATE TYPE approval_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'ESCALATED');
CREATE TYPE approval_action AS ENUM ('APPROVE', 'REJECT', 'ESCALATE', 'REQUEST_INFO', 'DELEGATE');
CREATE TYPE entity_type AS ENUM ('PURCHASE_ORDER', 'PURCHASE_REQUISITION', 'STOCK_TRANSFER', 'EXPENSE', 'LEAVE_REQUEST', 'VENDOR', 'PRICE_CHANGE', 'DISCOUNT', 'CREDIT_NOTE', 'REFUND', 'WRITE_OFF');

-- Customer Enums
CREATE TYPE customer_type AS ENUM ('INDIVIDUAL', 'BUSINESS', 'GOVERNMENT', 'INSTITUTIONAL');
CREATE TYPE customer_status AS ENUM ('ACTIVE', 'INACTIVE', 'BLOCKED', 'PROSPECT');
CREATE TYPE address_type AS ENUM ('HOME', 'OFFICE', 'BILLING', 'SHIPPING', 'OTHER');

-- Product Enums
CREATE TYPE product_status AS ENUM ('DRAFT', 'ACTIVE', 'INACTIVE', 'DISCONTINUED', 'OUT_OF_STOCK');
CREATE TYPE product_type AS ENUM ('PHYSICAL', 'SERVICE', 'SPARE_PART', 'CONSUMABLE', 'ACCESSORY');

-- Order Enums
CREATE TYPE order_status AS ENUM ('DRAFT', 'PENDING', 'CONFIRMED', 'PROCESSING', 'READY_TO_SHIP', 'SHIPPED', 'DELIVERED', 'COMPLETED', 'CANCELLED', 'RETURNED', 'REFUNDED', 'ON_HOLD');
CREATE TYPE order_type AS ENUM ('B2C', 'B2B', 'REPLACEMENT', 'WARRANTY', 'INTERNAL');
CREATE TYPE payment_status AS ENUM ('PENDING', 'PARTIAL', 'PAID', 'REFUNDED', 'FAILED', 'CANCELLED');
CREATE TYPE order_source AS ENUM ('WEBSITE', 'MOBILE_APP', 'CALL_CENTER', 'DEALER', 'FRANCHISEE', 'MARKETPLACE', 'WALK_IN', 'REFERRAL');

-- Service Enums
CREATE TYPE service_type AS ENUM ('installation', 'warranty_repair', 'paid_repair', 'amc_service', 'demo', 'preventive_maintenance', 'complaint', 'filter_change', 'inspection', 'uninstallation');
CREATE TYPE service_priority AS ENUM ('low', 'normal', 'high', 'urgent', 'critical');
CREATE TYPE service_status AS ENUM ('draft', 'pending', 'assigned', 'scheduled', 'en_route', 'in_progress', 'parts_required', 'on_hold', 'completed', 'closed', 'cancelled', 'reopened');
CREATE TYPE service_source AS ENUM ('call_center', 'website', 'mobile_app', 'walk_in', 'email', 'whatsapp', 'auto_amc', 'referral', 'system');

-- AMC Enums
CREATE TYPE amc_type AS ENUM ('standard', 'comprehensive', 'extended_warranty', 'platinum');
CREATE TYPE amc_status AS ENUM ('draft', 'pending_payment', 'active', 'expired', 'cancelled', 'renewed');

-- Technician Enums
CREATE TYPE technician_status AS ENUM ('active', 'inactive', 'on_leave', 'training', 'resigned');
CREATE TYPE technician_type AS ENUM ('internal', 'external', 'freelance');
CREATE TYPE skill_level AS ENUM ('trainee', 'junior', 'senior', 'expert', 'master');

-- Inventory Enums
CREATE TYPE stock_item_status AS ENUM ('available', 'reserved', 'allocated', 'picked', 'packed', 'in_transit', 'shipped', 'damaged', 'defective', 'sold', 'returned', 'quarantine', 'scrapped');
CREATE TYPE stock_movement_type AS ENUM ('receipt', 'issue', 'transfer_in', 'transfer_out', 'return_in', 'return_out', 'adjustment_plus', 'adjustment_minus', 'damage', 'scrap', 'cycle_count');

-- Transfer Enums
CREATE TYPE transfer_status AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'in_transit', 'partially_received', 'received', 'cancelled');
CREATE TYPE transfer_type AS ENUM ('stock_transfer', 'replenishment', 'return_to_main', 'inter_region', 'dealer_supply');

-- Installation Enums
CREATE TYPE installation_status AS ENUM ('pending', 'scheduled', 'in_progress', 'completed', 'cancelled', 'failed');

-- Shipment Enums
CREATE TYPE shipment_status AS ENUM ('CREATED', 'PACKED', 'READY_FOR_PICKUP', 'MANIFESTED', 'PICKED_UP', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED', 'DELIVERY_FAILED', 'RTO_INITIATED', 'RTO_IN_TRANSIT', 'RTO_DELIVERED', 'CANCELLED', 'LOST');
CREATE TYPE payment_mode AS ENUM ('PREPAID', 'COD');
CREATE TYPE packaging_type AS ENUM ('BOX', 'ENVELOPE', 'POLY_BAG', 'PALLET', 'CUSTOM');

-- Manifest Enums
CREATE TYPE manifest_status AS ENUM ('DRAFT', 'PENDING', 'CONFIRMED', 'HANDED_OVER', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED');
CREATE TYPE business_type AS ENUM ('B2C', 'B2B');

-- Transporter Enums
CREATE TYPE transporter_type AS ENUM ('COURIER', 'SELF_SHIP', 'MARKETPLACE', 'LOCAL', 'FRANCHISE');

-- WMS Enums
CREATE TYPE zone_type AS ENUM ('RECEIVING', 'STORAGE', 'PICKING', 'PACKING', 'SHIPPING', 'RETURNS', 'QUARANTINE', 'COLD_STORAGE', 'HAZMAT');
CREATE TYPE bin_type AS ENUM ('SHELF', 'RACK', 'FLOOR', 'PALLET', 'CONTAINER', 'CAGE', 'BULK');

-- Purchase Enums
CREATE TYPE requisition_status AS ENUM ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'CONVERTED', 'CANCELLED');
CREATE TYPE po_status AS ENUM ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'SENT_TO_VENDOR', 'ACKNOWLEDGED', 'PARTIALLY_RECEIVED', 'FULLY_RECEIVED', 'CLOSED', 'CANCELLED');
CREATE TYPE grn_status AS ENUM ('DRAFT', 'PENDING_QC', 'QC_PASSED', 'QC_FAILED', 'PARTIALLY_ACCEPTED', 'ACCEPTED', 'REJECTED', 'PUT_AWAY_PENDING', 'PUT_AWAY_COMPLETE', 'CANCELLED');
CREATE TYPE vendor_invoice_status AS ENUM ('RECEIVED', 'UNDER_VERIFICATION', 'MATCHED', 'PARTIALLY_MATCHED', 'MISMATCH', 'APPROVED', 'PAYMENT_INITIATED', 'PAID', 'DISPUTED', 'CANCELLED');
CREATE TYPE quality_check_result AS ENUM ('PASSED', 'FAILED', 'CONDITIONAL', 'PENDING');
CREATE TYPE delivery_lot_status AS ENUM ('pending', 'advance_pending', 'advance_paid', 'delivered', 'payment_pending', 'completed', 'cancelled');
CREATE TYPE proforma_status AS ENUM ('RECEIVED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'CONVERTED_TO_PO', 'EXPIRED', 'CANCELLED');

-- Vendor Enums
CREATE TYPE vendor_status AS ENUM ('ACTIVE', 'INACTIVE', 'BLOCKED', 'PENDING_APPROVAL');
CREATE TYPE vendor_type AS ENUM ('MANUFACTURER', 'DISTRIBUTOR', 'WHOLESALER', 'SERVICE_PROVIDER', 'OEM');

-- Dealer Enums
CREATE TYPE dealer_status AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'TERMINATED');
CREATE TYPE dealer_type AS ENUM ('AUTHORIZED', 'PREMIUM', 'RETAIL', 'WHOLESALE', 'FRANCHISE');

-- Lead Enums
CREATE TYPE lead_source AS ENUM ('WEBSITE', 'PHONE_CALL', 'WALK_IN', 'REFERRAL', 'SOCIAL_MEDIA', 'EMAIL_CAMPAIGN', 'SMS_CAMPAIGN', 'EXHIBITION', 'ADVERTISEMENT', 'PARTNER', 'DEALER', 'FRANCHISEE', 'AMAZON', 'FLIPKART', 'OTHER_MARKETPLACE', 'COLD_CALL', 'OTHER');
CREATE TYPE lead_status AS ENUM ('NEW', 'CONTACTED', 'QUALIFIED', 'PROPOSAL_SENT', 'NEGOTIATION', 'WON', 'LOST', 'NURTURING', 'DISQUALIFIED', 'DUPLICATE');
CREATE TYPE lead_priority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE lead_type AS ENUM ('INDIVIDUAL', 'BUSINESS', 'GOVERNMENT', 'INSTITUTIONAL');
CREATE TYPE lead_interest AS ENUM ('NEW_PURCHASE', 'REPLACEMENT', 'UPGRADE', 'AMC', 'DEMO', 'INQUIRY');
CREATE TYPE activity_type AS ENUM ('CALL', 'EMAIL', 'SMS', 'WHATSAPP', 'MEETING', 'DEMO', 'SITE_VISIT', 'PROPOSAL', 'NEGOTIATION', 'FOLLOW_UP', 'NOTE', 'STATUS_CHANGE', 'ASSIGNMENT', 'CONVERSION');
CREATE TYPE lost_reason AS ENUM ('PRICE_TOO_HIGH', 'COMPETITOR_CHOSEN', 'BUDGET_CONSTRAINTS', 'NOT_INTERESTED', 'NO_RESPONSE', 'WRONG_TIMING', 'PRODUCT_NOT_FIT', 'LOCATION_NOT_SERVICEABLE', 'CUSTOMER_POSTPONED', 'OTHER');

-- Call Center Enums
CREATE TYPE call_type AS ENUM ('INBOUND', 'OUTBOUND', 'CALLBACK', 'MISSED', 'ABANDONED');
CREATE TYPE call_category AS ENUM ('SALES', 'SERVICE', 'COMPLAINT', 'INQUIRY', 'FEEDBACK', 'FOLLOW_UP', 'AMC', 'INSTALLATION', 'OTHER');
CREATE TYPE call_status AS ENUM ('RINGING', 'ANSWERED', 'MISSED', 'BUSY', 'NO_ANSWER', 'VOICEMAIL', 'FAILED', 'COMPLETED');
CREATE TYPE call_outcome AS ENUM ('RESOLVED', 'ESCALATED', 'CALLBACK_SCHEDULED', 'TRANSFERRED', 'ORDER_PLACED', 'SERVICE_BOOKED', 'LEAD_CREATED', 'NO_ACTION', 'FOLLOW_UP_REQUIRED');
CREATE TYPE customer_sentiment AS ENUM ('VERY_POSITIVE', 'POSITIVE', 'NEUTRAL', 'NEGATIVE', 'VERY_NEGATIVE');
CREATE TYPE call_priority AS ENUM ('LOW', 'NORMAL', 'HIGH', 'URGENT');
CREATE TYPE callback_status AS ENUM ('PENDING', 'COMPLETED', 'MISSED', 'CANCELLED', 'RESCHEDULED');
CREATE TYPE qa_status AS ENUM ('PENDING', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'NEEDS_TRAINING');

-- Franchisee Enums
CREATE TYPE franchisee_status AS ENUM ('PROSPECT', 'APPROVED', 'ACTIVE', 'SUSPENDED', 'TERMINATED');
CREATE TYPE franchisee_type AS ENUM ('SALES', 'SERVICE', 'SALES_AND_SERVICE');
CREATE TYPE franchisee_tier AS ENUM ('BRONZE', 'SILVER', 'GOLD', 'PLATINUM');
CREATE TYPE contract_status AS ENUM ('DRAFT', 'PENDING_APPROVAL', 'ACTIVE', 'EXPIRED', 'TERMINATED', 'RENEWED');
CREATE TYPE territory_status AS ENUM ('AVAILABLE', 'ASSIGNED', 'DISPUTED', 'INACTIVE');
CREATE TYPE training_status AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED');
CREATE TYPE training_type AS ENUM ('ONBOARDING', 'PRODUCT', 'SERVICE', 'SALES', 'COMPLIANCE', 'REFRESHER');
CREATE TYPE support_ticket_status AS ENUM ('OPEN', 'IN_PROGRESS', 'WAITING_FOR_INFO', 'RESOLVED', 'CLOSED', 'REOPENED');
CREATE TYPE support_ticket_priority AS ENUM ('LOW', 'NORMAL', 'HIGH', 'URGENT');
CREATE TYPE support_ticket_category AS ENUM ('TECHNICAL', 'BILLING', 'INVENTORY', 'TRAINING', 'MARKETING', 'OTHER');
CREATE TYPE audit_status AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
CREATE TYPE audit_type AS ENUM ('COMPLIANCE', 'FINANCIAL', 'OPERATIONAL', 'QUALITY', 'INVENTORY');
CREATE TYPE audit_result AS ENUM ('PASS', 'FAIL', 'CONDITIONAL', 'PENDING');
CREATE TYPE service_capability AS ENUM ('INSTALLATION', 'REPAIR', 'AMC', 'DEMO');

-- =====================================================
-- PART 3: BASE TABLES (No FK dependencies)
-- =====================================================

-- Modules table
CREATE TABLE IF NOT EXISTS modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Regions table
CREATE TABLE IF NOT EXISTS regions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    level INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_regions_parent ON regions(parent_id);
CREATE INDEX IF NOT EXISTS idx_regions_code ON regions(code);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(250) UNIQUE,
    description TEXT,
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    image_url VARCHAR(500),
    icon VARCHAR(100),
    level INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    meta_title VARCHAR(200),
    meta_description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories(slug);

-- Brands table
CREATE TABLE IF NOT EXISTS brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(250) UNIQUE,
    description TEXT,
    logo_url VARCHAR(500),
    website VARCHAR(500),
    is_own_brand BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_brands_slug ON brands(slug);

-- Transporters table
CREATE TABLE IF NOT EXISTS transporters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    transporter_type transporter_type DEFAULT 'COURIER' NOT NULL,
    api_endpoint VARCHAR(500),
    api_key VARCHAR(255),
    api_secret VARCHAR(255),
    webhook_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    supports_cod BOOLEAN DEFAULT TRUE,
    supports_prepaid BOOLEAN DEFAULT TRUE,
    supports_reverse_pickup BOOLEAN DEFAULT FALSE,
    supports_surface BOOLEAN DEFAULT TRUE,
    supports_express BOOLEAN DEFAULT FALSE,
    max_weight_kg FLOAT,
    min_weight_kg FLOAT DEFAULT 0.0,
    base_rate FLOAT,
    rate_per_kg FLOAT,
    cod_charges FLOAT,
    cod_percentage FLOAT,
    contact_name VARCHAR(200),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    address TEXT,
    tracking_url_template VARCHAR(500),
    awb_prefix VARCHAR(20),
    awb_sequence_start INTEGER DEFAULT 1,
    awb_sequence_current INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 100,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_transporters_code ON transporters(code);

-- Call Dispositions table
CREATE TABLE IF NOT EXISTS call_dispositions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    category call_category,
    requires_callback BOOLEAN DEFAULT FALSE,
    requires_ticket BOOLEAN DEFAULT FALSE,
    is_resolved BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Lead Score Rules table
CREATE TABLE IF NOT EXISTS lead_score_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    field VARCHAR(50) NOT NULL,
    operator VARCHAR(20) NOT NULL,
    value VARCHAR(255) NOT NULL,
    score_points INTEGER NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 4: USER AND PERMISSION TABLES
-- =====================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url VARCHAR(500),
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMPTZ,
    last_login_ip VARCHAR(50),
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ,
    must_change_password BOOLEAN DEFAULT FALSE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);

-- User Roles junction table (many-to-many)
CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE NOT NULL,
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_user_role UNIQUE (user_id, role_id)
);
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);

-- Permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    module_id UUID REFERENCES modules(id) ON DELETE CASCADE NOT NULL,
    action VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_module_action UNIQUE (module_id, action)
);

-- Role Permissions table
CREATE TABLE IF NOT EXISTS role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE NOT NULL,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE NOT NULL,
    granted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id)
);

-- =====================================================
-- PART 5: WAREHOUSE AND WMS TABLES
-- =====================================================

-- Warehouses table
CREATE TABLE IF NOT EXISTS warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    warehouse_type VARCHAR(50) DEFAULT 'MAIN',
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    country VARCHAR(50) DEFAULT 'India',
    latitude FLOAT,
    longitude FLOAT,
    contact_name VARCHAR(200),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    gstin VARCHAR(15),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_warehouses_code ON warehouses(code);
CREATE INDEX IF NOT EXISTS idx_warehouses_region ON warehouses(region_id);

-- Warehouse Zones table
CREATE TABLE IF NOT EXISTS warehouse_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE CASCADE NOT NULL,
    zone_code VARCHAR(20) NOT NULL,
    zone_name VARCHAR(200) NOT NULL,
    description TEXT,
    zone_type zone_type DEFAULT 'STORAGE' NOT NULL,
    floor_number INTEGER,
    area_sqft FLOAT,
    max_capacity INTEGER,
    current_capacity INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_pickable BOOLEAN DEFAULT TRUE,
    is_receivable BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_warehouse_zone_code UNIQUE (warehouse_id, zone_code)
);
CREATE INDEX IF NOT EXISTS idx_warehouse_zones_warehouse ON warehouse_zones(warehouse_id);

-- Warehouse Bins table
CREATE TABLE IF NOT EXISTS warehouse_bins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE CASCADE NOT NULL,
    zone_id UUID REFERENCES warehouse_zones(id) ON DELETE SET NULL,
    bin_code VARCHAR(50) NOT NULL,
    bin_name VARCHAR(200),
    barcode VARCHAR(100) UNIQUE,
    aisle VARCHAR(10),
    rack VARCHAR(10),
    shelf VARCHAR(10),
    position VARCHAR(10),
    bin_type bin_type DEFAULT 'SHELF' NOT NULL,
    length FLOAT,
    width FLOAT,
    height FLOAT,
    max_capacity INTEGER,
    max_weight_kg FLOAT,
    current_items INTEGER DEFAULT 0,
    current_weight_kg FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    is_reserved BOOLEAN DEFAULT FALSE,
    is_pickable BOOLEAN DEFAULT TRUE,
    is_receivable BOOLEAN DEFAULT TRUE,
    reserved_product_id UUID,
    pick_sequence INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_activity_at TIMESTAMPTZ,
    CONSTRAINT uq_warehouse_bin_code UNIQUE (warehouse_id, bin_code)
);
CREATE INDEX IF NOT EXISTS idx_warehouse_bins_warehouse ON warehouse_bins(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_bins_zone ON warehouse_bins(zone_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_bins_barcode ON warehouse_bins(barcode);

-- PutAway Rules table
CREATE TABLE IF NOT EXISTS putaway_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE CASCADE NOT NULL,
    rule_name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    product_id UUID,
    brand_id UUID REFERENCES brands(id) ON DELETE SET NULL,
    target_zone_id UUID REFERENCES warehouse_zones(id) ON DELETE CASCADE NOT NULL,
    target_bin_pattern VARCHAR(100),
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_putaway_rule UNIQUE (warehouse_id, category_id, priority)
);
CREATE INDEX IF NOT EXISTS idx_putaway_rules_warehouse ON putaway_rules(warehouse_id);

-- =====================================================
-- PART 6: VENDORS AND DEALERS
-- =====================================================

-- Vendors table
CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    vendor_type vendor_type DEFAULT 'MANUFACTURER',
    status vendor_status DEFAULT 'PENDING_APPROVAL',
    contact_name VARCHAR(200),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    website VARCHAR(500),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    country VARCHAR(50) DEFAULT 'India',
    gstin VARCHAR(15),
    pan_number VARCHAR(10),
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(50),
    bank_ifsc VARCHAR(20),
    payment_terms VARCHAR(100),
    credit_days INTEGER DEFAULT 30,
    credit_limit NUMERIC(14,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    rating FLOAT DEFAULT 0,
    notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_vendors_code ON vendors(code);
CREATE INDEX IF NOT EXISTS idx_vendors_status ON vendors(status);

-- Dealers table
CREATE TABLE IF NOT EXISTS dealers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    dealer_type dealer_type DEFAULT 'AUTHORIZED',
    status dealer_status DEFAULT 'ACTIVE',
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    contact_name VARCHAR(200),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    gstin VARCHAR(15),
    pan_number VARCHAR(10),
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(50),
    bank_ifsc VARCHAR(20),
    credit_limit NUMERIC(14,2) DEFAULT 0,
    current_balance NUMERIC(14,2) DEFAULT 0,
    margin_percentage NUMERIC(5,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    assigned_warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    account_manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dealers_code ON dealers(code);
CREATE INDEX IF NOT EXISTS idx_dealers_region ON dealers(region_id);

-- Franchisees table
CREATE TABLE IF NOT EXISTS franchisees (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    franchisee_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    franchisee_type franchisee_type DEFAULT 'SALES_AND_SERVICE',
    tier franchisee_tier DEFAULT 'BRONZE',
    status franchisee_status DEFAULT 'PROSPECT',
    owner_name VARCHAR(200) NOT NULL,
    owner_phone VARCHAR(20) NOT NULL,
    owner_email VARCHAR(255),
    business_name VARCHAR(200),
    gstin VARCHAR(15),
    pan_number VARCHAR(10),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    latitude FLOAT,
    longitude FLOAT,
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(50),
    bank_ifsc VARCHAR(20),
    commission_rate NUMERIC(5,2) DEFAULT 0,
    security_deposit NUMERIC(12,2) DEFAULT 0,
    credit_limit NUMERIC(12,2) DEFAULT 0,
    current_balance NUMERIC(12,2) DEFAULT 0,
    service_capabilities JSONB,
    product_categories JSONB,
    operating_hours JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    account_manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    onboarded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    onboarded_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_franchisees_code ON franchisees(franchisee_code);
CREATE INDEX IF NOT EXISTS idx_franchisees_region ON franchisees(region_id);

-- =====================================================
-- PART 7: PRODUCTS
-- =====================================================

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(300) UNIQUE,
    description TEXT,
    short_description VARCHAR(500),
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    brand_id UUID REFERENCES brands(id) ON DELETE SET NULL,
    product_type product_type DEFAULT 'PHYSICAL',
    status product_status DEFAULT 'DRAFT',
    mrp NUMERIC(12,2) DEFAULT 0,
    selling_price NUMERIC(12,2) DEFAULT 0,
    cost_price NUMERIC(12,2) DEFAULT 0,
    tax_rate NUMERIC(5,2) DEFAULT 18,
    hsn_code VARCHAR(10),
    weight_kg FLOAT,
    length_cm FLOAT,
    width_cm FLOAT,
    height_cm FLOAT,
    warranty_months INTEGER DEFAULT 12,
    is_serialized BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    images JSONB,
    specifications JSONB,
    features JSONB,
    meta_title VARCHAR(200),
    meta_description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);

-- Product Variants table
CREATE TABLE IF NOT EXISTS product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    attributes JSONB,
    mrp NUMERIC(12,2) DEFAULT 0,
    selling_price NUMERIC(12,2) DEFAULT 0,
    cost_price NUMERIC(12,2) DEFAULT 0,
    weight_kg FLOAT,
    images JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_product_variants_product ON product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_product_variants_sku ON product_variants(sku);

-- Update warehouse_bins with product FK
ALTER TABLE warehouse_bins ADD CONSTRAINT fk_warehouse_bins_product
    FOREIGN KEY (reserved_product_id) REFERENCES products(id) ON DELETE SET NULL;

-- Update putaway_rules with product FK
ALTER TABLE putaway_rules ADD CONSTRAINT fk_putaway_rules_product
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL;

-- =====================================================
-- PART 8: CUSTOMERS
-- =====================================================

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_number VARCHAR(30) UNIQUE NOT NULL,
    customer_type customer_type DEFAULT 'INDIVIDUAL',
    status customer_status DEFAULT 'ACTIVE',
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20) NOT NULL,
    alternate_phone VARCHAR(20),
    whatsapp_number VARCHAR(20),
    company_name VARCHAR(200),
    gstin VARCHAR(15),
    date_of_birth DATE,
    anniversary_date DATE,
    gender VARCHAR(10),
    profile_image_url VARCHAR(500),
    source order_source,
    source_details VARCHAR(200),
    referred_by UUID,
    dealer_id UUID REFERENCES dealers(id) ON DELETE SET NULL,
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    total_orders INTEGER DEFAULT 0,
    total_spent NUMERIC(14,2) DEFAULT 0,
    loyalty_points INTEGER DEFAULT 0,
    tags JSONB,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_customers_number ON customers(customer_number);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- Customer Addresses table
CREATE TABLE IF NOT EXISTS customer_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE NOT NULL,
    address_type address_type DEFAULT 'HOME',
    label VARCHAR(50),
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    landmark VARCHAR(200),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    country VARCHAR(50) DEFAULT 'India',
    latitude FLOAT,
    longitude FLOAT,
    contact_name VARCHAR(200),
    contact_phone VARCHAR(20),
    is_default BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_customer_addresses_customer ON customer_addresses(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_addresses_pincode ON customer_addresses(pincode);

-- =====================================================
-- PART 9: APPROVAL TABLES (CRITICAL)
-- =====================================================

-- Approval Requests table
CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_number VARCHAR(30) UNIQUE NOT NULL,
    entity_type entity_type NOT NULL,
    entity_id UUID NOT NULL,
    entity_number VARCHAR(50),
    status approval_status DEFAULT 'PENDING' NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    amount NUMERIC(14,2),
    currency VARCHAR(3) DEFAULT 'INR',
    current_level INTEGER DEFAULT 1,
    max_level INTEGER DEFAULT 1,
    requested_by UUID REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
    requested_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    final_approver_id UUID REFERENCES users(id) ON DELETE SET NULL,
    final_action approval_action,
    final_remarks TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_approval_requests_number ON approval_requests(request_number);
CREATE INDEX IF NOT EXISTS idx_approval_requests_entity ON approval_requests(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_requested_by ON approval_requests(requested_by);

-- Approval History table
CREATE TABLE IF NOT EXISTS approval_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_request_id UUID REFERENCES approval_requests(id) ON DELETE CASCADE NOT NULL,
    level INTEGER NOT NULL,
    approver_id UUID REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
    action approval_action NOT NULL,
    remarks TEXT,
    acted_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    delegated_to UUID REFERENCES users(id) ON DELETE SET NULL,
    delegation_reason TEXT,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_approval_history_request ON approval_history(approval_request_id);
CREATE INDEX IF NOT EXISTS idx_approval_history_approver ON approval_history(approver_id);

-- Approval Rules table (for automatic routing)
CREATE TABLE IF NOT EXISTS approval_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    entity_type entity_type NOT NULL,
    min_amount NUMERIC(14,2),
    max_amount NUMERIC(14,2),
    level INTEGER DEFAULT 1,
    approver_role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
    approver_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    auto_approve BOOLEAN DEFAULT FALSE,
    auto_approve_conditions JSONB,
    escalation_hours INTEGER DEFAULT 24,
    escalate_to_role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 100,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_approval_rules_entity ON approval_rules(entity_type);

-- Approval Delegates table (out of office delegation)
CREATE TABLE IF NOT EXISTS approval_delegates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delegator_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    delegate_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    entity_types JSONB,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_approval_delegate UNIQUE (delegator_id, delegate_id, start_date)
);
CREATE INDEX IF NOT EXISTS idx_approval_delegates_delegator ON approval_delegates(delegator_id);

-- =====================================================
-- PART 10: ORDERS
-- =====================================================

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(30) UNIQUE NOT NULL,
    order_type order_type DEFAULT 'B2C',
    status order_status DEFAULT 'DRAFT',
    customer_id UUID REFERENCES customers(id) ON DELETE RESTRICT NOT NULL,
    billing_address_id UUID REFERENCES customer_addresses(id) ON DELETE SET NULL,
    shipping_address_id UUID REFERENCES customer_addresses(id) ON DELETE SET NULL,
    dealer_id UUID REFERENCES dealers(id) ON DELETE SET NULL,
    source order_source DEFAULT 'WEBSITE',
    source_reference VARCHAR(100),
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    subtotal NUMERIC(14,2) DEFAULT 0,
    discount_amount NUMERIC(12,2) DEFAULT 0,
    discount_code VARCHAR(50),
    tax_amount NUMERIC(12,2) DEFAULT 0,
    shipping_amount NUMERIC(12,2) DEFAULT 0,
    grand_total NUMERIC(14,2) DEFAULT 0,
    paid_amount NUMERIC(14,2) DEFAULT 0,
    balance_due NUMERIC(14,2) DEFAULT 0,
    payment_status payment_status DEFAULT 'PENDING',
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    billing_address JSONB,
    shipping_address JSONB,
    customer_notes TEXT,
    internal_notes TEXT,
    tags JSONB,
    is_gift BOOLEAN DEFAULT FALSE,
    gift_message TEXT,
    confirmed_at TIMESTAMPTZ,
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    cancellation_reason TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);

-- Order Items table
CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT NOT NULL,
    variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    sku VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(12,2) NOT NULL,
    discount_amount NUMERIC(12,2) DEFAULT 0,
    tax_rate NUMERIC(5,2) DEFAULT 18,
    tax_amount NUMERIC(12,2) DEFAULT 0,
    total_amount NUMERIC(12,2) NOT NULL,
    serial_numbers JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);

-- =====================================================
-- PART 11: INVENTORY AND STOCK
-- =====================================================

-- Stock Items table
CREATE TABLE IF NOT EXISTS stock_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT NOT NULL,
    variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE RESTRICT NOT NULL,
    serial_number VARCHAR(100) UNIQUE,
    batch_number VARCHAR(50),
    barcode VARCHAR(100),
    status stock_item_status DEFAULT 'available',
    purchase_order_id UUID,
    grn_number VARCHAR(50),
    vendor_id UUID,
    purchase_price FLOAT DEFAULT 0,
    landed_cost FLOAT DEFAULT 0,
    manufacturing_date DATE,
    expiry_date DATE,
    warranty_start_date DATE,
    warranty_end_date DATE,
    received_date TIMESTAMPTZ DEFAULT NOW(),
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    order_item_id UUID,
    allocated_at TIMESTAMPTZ,
    bin_id UUID REFERENCES warehouse_bins(id) ON DELETE SET NULL,
    rack_location VARCHAR(50),
    bin_number VARCHAR(50),
    quality_grade VARCHAR(20),
    inspection_status VARCHAR(50),
    inspection_notes TEXT,
    last_movement_date TIMESTAMPTZ,
    last_counted_date TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_stock_items_product ON stock_items(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_items_warehouse ON stock_items(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_items_serial ON stock_items(serial_number);
CREATE INDEX IF NOT EXISTS idx_stock_items_status ON stock_items(status);
CREATE INDEX IF NOT EXISTS idx_stock_items_bin ON stock_items(bin_id);

-- Inventory Summary table
CREATE TABLE IF NOT EXISTS inventory_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE NOT NULL,
    variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    total_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    allocated_quantity INTEGER DEFAULT 0,
    damaged_quantity INTEGER DEFAULT 0,
    in_transit_quantity INTEGER DEFAULT 0,
    reorder_level INTEGER DEFAULT 10,
    minimum_stock INTEGER DEFAULT 5,
    maximum_stock INTEGER DEFAULT 1000,
    average_cost FLOAT DEFAULT 0,
    total_value FLOAT DEFAULT 0,
    last_stock_in_date TIMESTAMPTZ,
    last_stock_out_date TIMESTAMPTZ,
    last_audit_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_inventory_summary UNIQUE (warehouse_id, product_id, variant_id)
);
CREATE INDEX IF NOT EXISTS idx_inventory_summary_warehouse ON inventory_summary(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_inventory_summary_product ON inventory_summary(product_id);

-- Stock Movements table
CREATE TABLE IF NOT EXISTS stock_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movement_number VARCHAR(50) UNIQUE NOT NULL,
    movement_type stock_movement_type NOT NULL,
    movement_date TIMESTAMPTZ DEFAULT NOW(),
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE RESTRICT NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT NOT NULL,
    variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    stock_item_id UUID REFERENCES stock_items(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL,
    balance_before INTEGER DEFAULT 0,
    balance_after INTEGER DEFAULT 0,
    reference_type VARCHAR(50),
    reference_id UUID,
    reference_number VARCHAR(100),
    unit_cost FLOAT DEFAULT 0,
    total_cost FLOAT DEFAULT 0,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stock_movements_number ON stock_movements(movement_number);
CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_stock_movements_warehouse ON stock_movements(warehouse_id);

-- Stock Transfers table
CREATE TABLE IF NOT EXISTS stock_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_number VARCHAR(50) UNIQUE NOT NULL,
    transfer_type transfer_type DEFAULT 'stock_transfer',
    status transfer_status DEFAULT 'draft',
    from_warehouse_id UUID REFERENCES warehouses(id) ON DELETE RESTRICT NOT NULL,
    to_warehouse_id UUID REFERENCES warehouses(id) ON DELETE RESTRICT NOT NULL,
    request_date TIMESTAMPTZ DEFAULT NOW(),
    expected_date TIMESTAMPTZ,
    dispatch_date TIMESTAMPTZ,
    received_date TIMESTAMPTZ,
    requested_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    dispatched_by UUID REFERENCES users(id) ON DELETE SET NULL,
    received_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,
    total_items INTEGER DEFAULT 0,
    total_quantity INTEGER DEFAULT 0,
    total_value FLOAT DEFAULT 0,
    received_quantity INTEGER DEFAULT 0,
    vehicle_number VARCHAR(50),
    driver_name VARCHAR(100),
    driver_phone VARCHAR(20),
    challan_number VARCHAR(50),
    eway_bill_number VARCHAR(50),
    notes TEXT,
    internal_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_stock_transfers_number ON stock_transfers(transfer_number);
CREATE INDEX IF NOT EXISTS idx_stock_transfers_status ON stock_transfers(status);

-- Stock Transfer Items table
CREATE TABLE IF NOT EXISTS stock_transfer_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_id UUID REFERENCES stock_transfers(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT NOT NULL,
    variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    requested_quantity INTEGER NOT NULL,
    approved_quantity INTEGER,
    dispatched_quantity INTEGER,
    received_quantity INTEGER DEFAULT 0,
    damaged_quantity INTEGER DEFAULT 0,
    unit_cost FLOAT DEFAULT 0,
    total_cost FLOAT DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stock_transfer_items_transfer ON stock_transfer_items(transfer_id);

-- Stock Transfer Serials table
CREATE TABLE IF NOT EXISTS stock_transfer_serials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_item_id UUID REFERENCES stock_transfer_items(id) ON DELETE CASCADE NOT NULL,
    stock_item_id UUID REFERENCES stock_items(id) ON DELETE RESTRICT NOT NULL,
    is_dispatched INTEGER DEFAULT 0,
    is_received INTEGER DEFAULT 0,
    is_damaged INTEGER DEFAULT 0,
    received_at TIMESTAMPTZ,
    damage_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 12: TECHNICIANS
-- =====================================================

-- Technicians table
CREATE TABLE IF NOT EXISTS technicians (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    phone VARCHAR(20) NOT NULL,
    alternate_phone VARCHAR(20),
    email VARCHAR(100),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    technician_type technician_type DEFAULT 'internal',
    status technician_status DEFAULT 'active',
    date_of_joining DATE,
    date_of_leaving DATE,
    skill_level skill_level DEFAULT 'junior',
    specializations JSONB,
    certifications JSONB,
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    assigned_warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    service_pincodes JSONB,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    aadhaar_number VARCHAR(20),
    pan_number VARCHAR(20),
    driving_license VARCHAR(50),
    id_proof_url VARCHAR(500),
    photo_url VARCHAR(500),
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(50),
    ifsc_code VARCHAR(20),
    total_jobs_completed INTEGER DEFAULT 0,
    average_rating FLOAT DEFAULT 0,
    total_ratings INTEGER DEFAULT 0,
    current_month_jobs INTEGER DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE,
    last_job_date TIMESTAMPTZ,
    current_location_lat FLOAT,
    current_location_lng FLOAT,
    location_updated_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_technicians_code ON technicians(employee_code);
CREATE INDEX IF NOT EXISTS idx_technicians_phone ON technicians(phone);
CREATE INDEX IF NOT EXISTS idx_technicians_status ON technicians(status);

-- Technician Leaves table
CREATE TABLE IF NOT EXISTS technician_leaves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technician_id UUID REFERENCES technicians(id) ON DELETE CASCADE NOT NULL,
    leave_type VARCHAR(50),
    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    reason TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_technician_leaves_technician ON technician_leaves(technician_id);

-- =====================================================
-- PART 13: INSTALLATIONS AND SERVICE
-- =====================================================

-- Installations table
CREATE TABLE IF NOT EXISTS installations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installation_number VARCHAR(50) UNIQUE NOT NULL,
    status installation_status DEFAULT 'pending',
    customer_id UUID REFERENCES customers(id) ON DELETE RESTRICT NOT NULL,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    order_item_id UUID,
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT NOT NULL,
    variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    serial_number VARCHAR(100) UNIQUE,
    stock_item_id UUID REFERENCES stock_items(id) ON DELETE SET NULL,
    address_id UUID REFERENCES customer_addresses(id) ON DELETE SET NULL,
    installation_address JSONB,
    installation_pincode VARCHAR(10),
    installation_city VARCHAR(100),
    latitude FLOAT,
    longitude FLOAT,
    preferred_date DATE,
    preferred_time_slot VARCHAR(50),
    scheduled_date DATE,
    scheduled_time_slot VARCHAR(50),
    technician_id UUID REFERENCES technicians(id) ON DELETE SET NULL,
    franchisee_id VARCHAR(36) REFERENCES franchisees(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    installation_date DATE,
    installation_notes TEXT,
    pre_installation_checklist JSONB,
    post_installation_checklist JSONB,
    installation_photos JSONB,
    accessories_used JSONB,
    input_tds INTEGER,
    output_tds INTEGER,
    warranty_start_date DATE,
    warranty_end_date DATE,
    warranty_months INTEGER DEFAULT 12,
    extended_warranty_months INTEGER DEFAULT 0,
    warranty_card_number VARCHAR(50) UNIQUE,
    warranty_card_url VARCHAR(500),
    customer_signature_url VARCHAR(500),
    customer_feedback TEXT,
    customer_rating INTEGER,
    demo_given BOOLEAN DEFAULT FALSE,
    demo_notes TEXT,
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    notes TEXT,
    internal_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_installations_number ON installations(installation_number);
CREATE INDEX IF NOT EXISTS idx_installations_customer ON installations(customer_id);
CREATE INDEX IF NOT EXISTS idx_installations_status ON installations(status);
CREATE INDEX IF NOT EXISTS idx_installations_serial ON installations(serial_number);

-- AMC Contracts table
CREATE TABLE IF NOT EXISTS amc_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    amc_type amc_type DEFAULT 'standard',
    status amc_status DEFAULT 'draft',
    customer_id UUID REFERENCES customers(id) ON DELETE RESTRICT NOT NULL,
    customer_address_id UUID REFERENCES customer_addresses(id) ON DELETE SET NULL,
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT NOT NULL,
    installation_id UUID REFERENCES installations(id) ON DELETE SET NULL,
    serial_number VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_months INTEGER DEFAULT 12,
    total_services INTEGER DEFAULT 2,
    services_used INTEGER DEFAULT 0,
    services_remaining INTEGER DEFAULT 2,
    base_price FLOAT DEFAULT 0,
    tax_amount FLOAT DEFAULT 0,
    discount_amount FLOAT DEFAULT 0,
    total_amount FLOAT DEFAULT 0,
    payment_status VARCHAR(50) DEFAULT 'pending',
    payment_mode VARCHAR(50),
    payment_reference VARCHAR(100),
    paid_at TIMESTAMPTZ,
    parts_covered BOOLEAN DEFAULT FALSE,
    labor_covered BOOLEAN DEFAULT TRUE,
    emergency_support BOOLEAN DEFAULT FALSE,
    priority_service BOOLEAN DEFAULT FALSE,
    discount_on_parts FLOAT DEFAULT 0,
    terms_and_conditions TEXT,
    is_renewable BOOLEAN DEFAULT TRUE,
    renewal_reminder_sent BOOLEAN DEFAULT FALSE,
    renewed_from_id UUID REFERENCES amc_contracts(id) ON DELETE SET NULL,
    renewed_to_id UUID REFERENCES amc_contracts(id) ON DELETE SET NULL,
    service_schedule JSONB,
    next_service_due DATE,
    notes TEXT,
    internal_notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_amc_contracts_number ON amc_contracts(contract_number);
CREATE INDEX IF NOT EXISTS idx_amc_contracts_customer ON amc_contracts(customer_id);
CREATE INDEX IF NOT EXISTS idx_amc_contracts_status ON amc_contracts(status);
CREATE INDEX IF NOT EXISTS idx_amc_contracts_serial ON amc_contracts(serial_number);

-- AMC Plans table
CREATE TABLE IF NOT EXISTS amc_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    amc_type amc_type DEFAULT 'standard',
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    product_ids JSONB,
    duration_months INTEGER DEFAULT 12,
    base_price FLOAT DEFAULT 0,
    tax_rate FLOAT DEFAULT 18,
    services_included INTEGER DEFAULT 2,
    parts_covered BOOLEAN DEFAULT FALSE,
    labor_covered BOOLEAN DEFAULT TRUE,
    emergency_support BOOLEAN DEFAULT FALSE,
    priority_service BOOLEAN DEFAULT FALSE,
    discount_on_parts FLOAT DEFAULT 0,
    terms_and_conditions TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Service Requests table
CREATE TABLE IF NOT EXISTS service_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    service_type service_type NOT NULL,
    source service_source DEFAULT 'call_center',
    priority service_priority DEFAULT 'normal',
    status service_status DEFAULT 'pending',
    customer_id UUID REFERENCES customers(id) ON DELETE RESTRICT NOT NULL,
    customer_address_id UUID REFERENCES customer_addresses(id) ON DELETE SET NULL,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    order_item_id UUID,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    serial_number VARCHAR(100),
    installation_id UUID REFERENCES installations(id) ON DELETE SET NULL,
    amc_id UUID REFERENCES amc_contracts(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    symptoms JSONB,
    customer_reported_issue TEXT,
    service_address JSONB,
    service_pincode VARCHAR(10),
    service_city VARCHAR(100),
    service_state VARCHAR(100),
    latitude FLOAT,
    longitude FLOAT,
    technician_id UUID REFERENCES technicians(id) ON DELETE SET NULL,
    franchisee_id VARCHAR(36) REFERENCES franchisees(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ,
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    preferred_date DATE,
    preferred_time_slot VARCHAR(50),
    scheduled_date DATE,
    scheduled_time_slot VARCHAR(50),
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    sla_breach_at TIMESTAMPTZ,
    is_sla_breached BOOLEAN DEFAULT FALSE,
    resolution_type VARCHAR(50),
    resolution_notes TEXT,
    root_cause TEXT,
    action_taken TEXT,
    parts_used JSONB,
    total_parts_cost FLOAT DEFAULT 0,
    labor_charges FLOAT DEFAULT 0,
    service_charges FLOAT DEFAULT 0,
    travel_charges FLOAT DEFAULT 0,
    total_charges FLOAT DEFAULT 0,
    is_chargeable BOOLEAN DEFAULT FALSE,
    payment_status VARCHAR(50),
    payment_collected FLOAT DEFAULT 0,
    payment_mode VARCHAR(50),
    customer_rating INTEGER,
    customer_feedback TEXT,
    feedback_date TIMESTAMPTZ,
    images_before JSONB,
    images_after JSONB,
    customer_signature_url VARCHAR(500),
    internal_notes TEXT,
    escalation_level INTEGER DEFAULT 0,
    escalated_to UUID REFERENCES users(id) ON DELETE SET NULL,
    escalation_reason TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_service_requests_ticket ON service_requests(ticket_number);
CREATE INDEX IF NOT EXISTS idx_service_requests_customer ON service_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_service_requests_status ON service_requests(status);
CREATE INDEX IF NOT EXISTS idx_service_requests_type ON service_requests(service_type);
CREATE INDEX IF NOT EXISTS idx_service_requests_priority ON service_requests(priority);
CREATE INDEX IF NOT EXISTS idx_service_requests_pincode ON service_requests(service_pincode);
CREATE INDEX IF NOT EXISTS idx_service_requests_serial ON service_requests(serial_number);

-- Service Status History table
CREATE TABLE IF NOT EXISTS service_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_request_id UUID REFERENCES service_requests(id) ON DELETE CASCADE NOT NULL,
    from_status service_status,
    to_status service_status NOT NULL,
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_service_status_history_request ON service_status_history(service_request_id);

-- Technician Job History table
CREATE TABLE IF NOT EXISTS technician_job_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technician_id UUID REFERENCES technicians(id) ON DELETE CASCADE NOT NULL,
    service_request_id UUID REFERENCES service_requests(id) ON DELETE CASCADE NOT NULL,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    time_taken_minutes INTEGER,
    status VARCHAR(50),
    reassignment_reason TEXT,
    customer_rating INTEGER,
    customer_feedback TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_technician_job_history_technician ON technician_job_history(technician_id);
CREATE INDEX IF NOT EXISTS idx_technician_job_history_service ON technician_job_history(service_request_id);

-- Parts Requests table
CREATE TABLE IF NOT EXISTS parts_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_number VARCHAR(50) UNIQUE NOT NULL,
    service_request_id UUID REFERENCES service_requests(id) ON DELETE CASCADE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    items JSONB,
    from_warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    requested_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    dispatched_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_parts_requests_number ON parts_requests(request_number);
CREATE INDEX IF NOT EXISTS idx_parts_requests_service ON parts_requests(service_request_id);

-- Warranty Claims table
CREATE TABLE IF NOT EXISTS warranty_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    installation_id UUID REFERENCES installations(id) ON DELETE RESTRICT NOT NULL,
    service_request_id UUID REFERENCES service_requests(id) ON DELETE SET NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE RESTRICT NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT NOT NULL,
    serial_number VARCHAR(100) NOT NULL,
    claim_type VARCHAR(50),
    issue_description TEXT NOT NULL,
    diagnosis TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    is_valid_claim BOOLEAN,
    rejection_reason TEXT,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    resolution_type VARCHAR(50),
    resolution_notes TEXT,
    replacement_serial VARCHAR(100),
    refund_amount FLOAT,
    parts_cost FLOAT DEFAULT 0,
    labor_cost FLOAT DEFAULT 0,
    total_cost FLOAT DEFAULT 0,
    claim_date DATE,
    resolved_date DATE,
    notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_warranty_claims_number ON warranty_claims(claim_number);
CREATE INDEX IF NOT EXISTS idx_warranty_claims_installation ON warranty_claims(installation_id);
CREATE INDEX IF NOT EXISTS idx_warranty_claims_serial ON warranty_claims(serial_number);

-- =====================================================
-- PART 14: SHIPMENTS AND MANIFESTS
-- =====================================================

-- Manifests table
CREATE TABLE IF NOT EXISTS manifests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manifest_number VARCHAR(30) UNIQUE NOT NULL,
    status manifest_status DEFAULT 'DRAFT' NOT NULL,
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE RESTRICT NOT NULL,
    transporter_id UUID REFERENCES transporters(id) ON DELETE RESTRICT NOT NULL,
    business_type business_type DEFAULT 'B2C',
    manifest_date DATE NOT NULL,
    total_shipments INTEGER DEFAULT 0,
    total_weight_kg FLOAT DEFAULT 0.0,
    total_cod_amount FLOAT DEFAULT 0.0,
    pickup_scheduled_at TIMESTAMPTZ,
    pickup_completed_at TIMESTAMPTZ,
    handed_over_to VARCHAR(200),
    handover_remarks TEXT,
    manifest_pdf_url VARCHAR(500),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    closed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_manifests_number ON manifests(manifest_number);
CREATE INDEX IF NOT EXISTS idx_manifests_status ON manifests(status);
CREATE INDEX IF NOT EXISTS idx_manifests_date ON manifests(manifest_date);

-- Shipments table
CREATE TABLE IF NOT EXISTS shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_number VARCHAR(30) UNIQUE NOT NULL,
    order_id UUID REFERENCES orders(id) ON DELETE RESTRICT NOT NULL,
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE RESTRICT NOT NULL,
    transporter_id UUID REFERENCES transporters(id) ON DELETE SET NULL,
    manifest_id UUID REFERENCES manifests(id) ON DELETE SET NULL,
    awb_number VARCHAR(100) UNIQUE,
    tracking_number VARCHAR(100),
    status shipment_status DEFAULT 'CREATED' NOT NULL,
    payment_mode payment_mode DEFAULT 'PREPAID' NOT NULL,
    cod_amount FLOAT,
    cod_collected BOOLEAN DEFAULT FALSE,
    cod_collected_at TIMESTAMPTZ,
    packaging_type packaging_type DEFAULT 'BOX' NOT NULL,
    no_of_boxes INTEGER DEFAULT 1,
    weight_kg FLOAT DEFAULT 0.0,
    volumetric_weight_kg FLOAT,
    chargeable_weight_kg FLOAT,
    length_cm FLOAT,
    breadth_cm FLOAT,
    height_cm FLOAT,
    ship_to_name VARCHAR(200) NOT NULL,
    ship_to_phone VARCHAR(20) NOT NULL,
    ship_to_email VARCHAR(255),
    ship_to_address JSONB NOT NULL,
    ship_to_pincode VARCHAR(10) NOT NULL,
    ship_to_city VARCHAR(100),
    ship_to_state VARCHAR(100),
    expected_delivery_date DATE,
    promised_delivery_date DATE,
    actual_delivery_date DATE,
    delivery_attempts INTEGER DEFAULT 0,
    max_delivery_attempts INTEGER DEFAULT 3,
    delivered_to VARCHAR(200),
    delivery_relation VARCHAR(100),
    delivery_remarks TEXT,
    pod_image_url VARCHAR(500),
    pod_signature_url VARCHAR(500),
    pod_latitude FLOAT,
    pod_longitude FLOAT,
    shipping_label_url VARCHAR(500),
    invoice_url VARCHAR(500),
    rto_reason TEXT,
    rto_initiated_at TIMESTAMPTZ,
    rto_delivered_at TIMESTAMPTZ,
    shipping_charge FLOAT DEFAULT 0.0,
    cod_charge FLOAT DEFAULT 0.0,
    insurance_charge FLOAT DEFAULT 0.0,
    total_shipping_cost FLOAT DEFAULT 0.0,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    packed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    packed_at TIMESTAMPTZ,
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    cancellation_reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_shipments_number ON shipments(shipment_number);
CREATE INDEX IF NOT EXISTS idx_shipments_order ON shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_shipments_awb ON shipments(awb_number);
CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(status);
CREATE INDEX IF NOT EXISTS idx_shipments_pincode ON shipments(ship_to_pincode);
CREATE INDEX IF NOT EXISTS idx_shipments_manifest ON shipments(manifest_id);

-- Manifest Items table
CREATE TABLE IF NOT EXISTS manifest_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manifest_id UUID REFERENCES manifests(id) ON DELETE CASCADE NOT NULL,
    shipment_id UUID UNIQUE REFERENCES shipments(id) ON DELETE CASCADE NOT NULL,
    sequence_number INTEGER NOT NULL,
    awb_number VARCHAR(100),
    weight_kg FLOAT DEFAULT 0.0,
    cod_amount FLOAT DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'pending',
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_manifest_items_manifest ON manifest_items(manifest_id);

-- Shipment Tracking table
CREATE TABLE IF NOT EXISTS shipment_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID REFERENCES shipments(id) ON DELETE CASCADE NOT NULL,
    status shipment_status NOT NULL,
    status_code VARCHAR(50),
    location VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    remarks TEXT,
    transporter_remarks TEXT,
    event_time TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    source VARCHAR(50),
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_shipment_tracking_shipment ON shipment_tracking(shipment_id);

-- Transporter Serviceability table
CREATE TABLE IF NOT EXISTS transporter_serviceability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transporter_id UUID REFERENCES transporters(id) ON DELETE CASCADE NOT NULL,
    origin_pincode VARCHAR(10) NOT NULL,
    destination_pincode VARCHAR(10) NOT NULL,
    is_serviceable BOOLEAN DEFAULT TRUE,
    estimated_days INTEGER,
    cod_available BOOLEAN DEFAULT TRUE,
    prepaid_available BOOLEAN DEFAULT TRUE,
    surface_available BOOLEAN DEFAULT TRUE,
    express_available BOOLEAN DEFAULT FALSE,
    rate FLOAT,
    cod_charge FLOAT,
    origin_state VARCHAR(100),
    destination_state VARCHAR(100),
    origin_city VARCHAR(100),
    destination_city VARCHAR(100),
    zone VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_transporter_serviceability UNIQUE (transporter_id, origin_pincode, destination_pincode)
);
CREATE INDEX IF NOT EXISTS idx_transporter_serviceability_transporter ON transporter_serviceability(transporter_id);
CREATE INDEX IF NOT EXISTS idx_transporter_serviceability_origin ON transporter_serviceability(origin_pincode);
CREATE INDEX IF NOT EXISTS idx_transporter_serviceability_dest ON transporter_serviceability(destination_pincode);

-- =====================================================
-- PART 15: PROCUREMENT (PURCHASE ORDERS, GRN)
-- =====================================================

-- Purchase Requisitions table
CREATE TABLE IF NOT EXISTS purchase_requisitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requisition_number VARCHAR(30) UNIQUE NOT NULL,
    status requisition_status DEFAULT 'DRAFT' NOT NULL,
    requesting_department VARCHAR(50),
    requested_by UUID REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
    request_date DATE DEFAULT CURRENT_DATE NOT NULL,
    required_by_date DATE,
    delivery_warehouse_id UUID REFERENCES warehouses(id) ON DELETE RESTRICT NOT NULL,
    priority INTEGER DEFAULT 5,
    estimated_total NUMERIC(14,2) DEFAULT 0,
    reason TEXT,
    notes TEXT,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,
    converted_to_po_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_purchase_requisitions_number ON purchase_requisitions(requisition_number);
CREATE INDEX IF NOT EXISTS idx_purchase_requisitions_status ON purchase_requisitions(status);

-- Purchase Requisition Items table
CREATE TABLE IF NOT EXISTS purchase_requisition_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requisition_id UUID REFERENCES purchase_requisitions(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT NOT NULL,
    variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    product_name VARCHAR(255) NOT NULL,
    sku VARCHAR(50) NOT NULL,
    quantity_requested INTEGER NOT NULL,
    uom VARCHAR(20) DEFAULT 'PCS',
    estimated_unit_price NUMERIC(12,2) DEFAULT 0,
    estimated_total NUMERIC(12,2) DEFAULT 0,
    preferred_vendor_id UUID REFERENCES vendors(id) ON DELETE SET NULL,
    notes TEXT,
    monthly_quantities JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_purchase_requisition_items_req ON purchase_requisition_items(requisition_id);

-- Purchase Orders table
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number VARCHAR(30) UNIQUE NOT NULL,
    po_date DATE NOT NULL,
    status po_status DEFAULT 'DRAFT' NOT NULL,
    vendor_id UUID REFERENCES vendors(id) ON DELETE RESTRICT NOT NULL,
    requisition_id UUID REFERENCES purchase_requisitions(id) ON DELETE SET NULL,
    delivery_warehouse_id UUID REFERENCES warehouses(id) ON DELETE RESTRICT NOT NULL,
    expected_delivery_date DATE,
    delivery_address JSONB,
    vendor_name VARCHAR(200) NOT NULL,
    vendor_gstin VARCHAR(15),
    vendor_address JSONB,
    bill_to JSONB,
    ship_to JSONB,
    subtotal NUMERIC(14,2) NOT NULL,
    discount_amount NUMERIC(12,2) DEFAULT 0,
    taxable_amount NUMERIC(14,2) NOT NULL,
    cgst_amount NUMERIC(12,2) DEFAULT 0,
    sgst_amount NUMERIC(12,2) DEFAULT 0,
    igst_amount NUMERIC(12,2) DEFAULT 0,
    cess_amount NUMERIC(12,2) DEFAULT 0,
    total_tax NUMERIC(12,2) DEFAULT 0,
    freight_charges NUMERIC(12,2) DEFAULT 0,
    packing_charges NUMERIC(12,2) DEFAULT 0,
    other_charges NUMERIC(12,2) DEFAULT 0,
    grand_total NUMERIC(14,2) NOT NULL,
    total_received_value NUMERIC(14,2) DEFAULT 0,
    payment_terms VARCHAR(100),
    credit_days INTEGER DEFAULT 30,
    advance_required NUMERIC(12,2) DEFAULT 0,
    advance_paid NUMERIC(12,2) DEFAULT 0,
    quotation_reference VARCHAR(50),
    quotation_date DATE,
    terms_and_conditions TEXT,
    special_instructions TEXT,
    sent_to_vendor_at TIMESTAMPTZ,
    vendor_acknowledged_at TIMESTAMPTZ,
    po_pdf_url VARCHAR(500),
    created_by UUID REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    approval_request_id UUID REFERENCES approval_requests(id) ON DELETE SET NULL,
    approval_level VARCHAR(20),
    submitted_for_approval_at TIMESTAMPTZ,
    rejection_reason TEXT,
    internal_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    closed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_number ON purchase_orders(po_number);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_vendor ON purchase_orders(vendor_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_date ON purchase_orders(po_date);

-- Purchase Order Items table
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID REFERENCES purchase_orders(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT,
    variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    product_name VARCHAR(255) NOT NULL,
    sku VARCHAR(50) NOT NULL,
    part_code VARCHAR(20),
    hsn_code VARCHAR(10),
    line_number INTEGER DEFAULT 1,
    quantity_ordered INTEGER NOT NULL,
    quantity_received INTEGER DEFAULT 0,
    quantity_accepted INTEGER DEFAULT 0,
    quantity_rejected INTEGER DEFAULT 0,
    quantity_pending INTEGER DEFAULT 0,
    uom VARCHAR(20) DEFAULT 'PCS',
    unit_price NUMERIC(12,2) NOT NULL,
    discount_percentage NUMERIC(5,2) DEFAULT 0,
    discount_amount NUMERIC(12,2) DEFAULT 0,
    taxable_amount NUMERIC(12,2) NOT NULL,
    gst_rate NUMERIC(5,2) DEFAULT 18,
    cgst_rate NUMERIC(5,2) DEFAULT 0,
    sgst_rate NUMERIC(5,2) DEFAULT 0,
    igst_rate NUMERIC(5,2) DEFAULT 0,
    cgst_amount NUMERIC(12,2) DEFAULT 0,
    sgst_amount NUMERIC(12,2) DEFAULT 0,
    igst_amount NUMERIC(12,2) DEFAULT 0,
    cess_amount NUMERIC(12,2) DEFAULT 0,
    total_amount NUMERIC(12,2) NOT NULL,
    expected_date DATE,
    monthly_quantities JSONB,
    is_closed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_purchase_order_items_po ON purchase_order_items(purchase_order_id);

-- Goods Receipt Notes table
CREATE TABLE IF NOT EXISTS goods_receipt_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grn_number VARCHAR(30) UNIQUE NOT NULL,
    grn_date DATE NOT NULL,
    status grn_status DEFAULT 'DRAFT' NOT NULL,
    purchase_order_id UUID REFERENCES purchase_orders(id) ON DELETE RESTRICT NOT NULL,
    vendor_id UUID REFERENCES vendors(id) ON DELETE RESTRICT NOT NULL,
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE RESTRICT NOT NULL,
    vendor_challan_number VARCHAR(50),
    vendor_challan_date DATE,
    transporter_name VARCHAR(100),
    vehicle_number VARCHAR(20),
    lr_number VARCHAR(50),
    e_way_bill_number VARCHAR(20),
    total_items INTEGER DEFAULT 0,
    total_quantity_received INTEGER DEFAULT 0,
    total_quantity_accepted INTEGER DEFAULT 0,
    total_quantity_rejected INTEGER DEFAULT 0,
    total_value NUMERIC(14,2) DEFAULT 0,
    qc_required BOOLEAN DEFAULT TRUE,
    qc_status quality_check_result,
    qc_done_by UUID REFERENCES users(id) ON DELETE SET NULL,
    qc_done_at TIMESTAMPTZ,
    qc_remarks TEXT,
    received_by UUID REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
    receiving_remarks TEXT,
    put_away_complete BOOLEAN DEFAULT FALSE,
    put_away_at TIMESTAMPTZ,
    grn_pdf_url VARCHAR(500),
    photos_urls JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_grn_number ON goods_receipt_notes(grn_number);
CREATE INDEX IF NOT EXISTS idx_grn_po ON goods_receipt_notes(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_grn_status ON goods_receipt_notes(status);

-- GRN Items table
CREATE TABLE IF NOT EXISTS grn_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grn_id UUID REFERENCES goods_receipt_notes(id) ON DELETE CASCADE NOT NULL,
    po_item_id UUID REFERENCES purchase_order_items(id) ON DELETE RESTRICT NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT NOT NULL,
    variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    product_name VARCHAR(255) NOT NULL,
    sku VARCHAR(50) NOT NULL,
    part_code VARCHAR(20),
    hsn_code VARCHAR(10),
    quantity_expected INTEGER,
    quantity_received INTEGER NOT NULL,
    quantity_accepted INTEGER DEFAULT 0,
    quantity_rejected INTEGER DEFAULT 0,
    uom VARCHAR(20) DEFAULT 'PCS',
    unit_price NUMERIC(12,2) NOT NULL,
    accepted_value NUMERIC(12,2) DEFAULT 0,
    batch_number VARCHAR(50),
    manufacturing_date DATE,
    expiry_date DATE,
    serial_numbers JSONB,
    bin_id UUID REFERENCES warehouse_bins(id) ON DELETE SET NULL,
    bin_location VARCHAR(50),
    qc_result quality_check_result,
    rejection_reason TEXT,
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_grn_items_grn ON grn_items(grn_id);

-- PO Delivery Schedules table
CREATE TABLE IF NOT EXISTS po_delivery_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID REFERENCES purchase_orders(id) ON DELETE CASCADE NOT NULL,
    lot_number INTEGER NOT NULL,
    lot_name VARCHAR(50) NOT NULL,
    month_code VARCHAR(7),
    expected_delivery_date DATE NOT NULL,
    delivery_window_start DATE,
    delivery_window_end DATE,
    actual_delivery_date DATE,
    total_quantity INTEGER NOT NULL,
    quantity_received INTEGER DEFAULT 0,
    lot_value NUMERIC(14,2) NOT NULL,
    lot_tax NUMERIC(12,2) NOT NULL,
    lot_total NUMERIC(14,2) NOT NULL,
    advance_percentage NUMERIC(5,2) DEFAULT 25,
    advance_amount NUMERIC(12,2) NOT NULL,
    balance_amount NUMERIC(12,2) NOT NULL,
    balance_due_days INTEGER DEFAULT 45,
    advance_paid NUMERIC(12,2) DEFAULT 0,
    advance_paid_date DATE,
    advance_payment_ref VARCHAR(100),
    balance_paid NUMERIC(12,2) DEFAULT 0,
    balance_paid_date DATE,
    balance_payment_ref VARCHAR(100),
    balance_due_date DATE,
    status delivery_lot_status DEFAULT 'pending' NOT NULL,
    grn_id UUID REFERENCES goods_receipt_notes(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_po_delivery_schedules_po ON po_delivery_schedules(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_po_delivery_schedules_date ON po_delivery_schedules(expected_delivery_date);
CREATE INDEX IF NOT EXISTS idx_po_delivery_schedules_status ON po_delivery_schedules(status);

-- Vendor Invoices table
CREATE TABLE IF NOT EXISTS vendor_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(50) NOT NULL,
    invoice_date DATE NOT NULL,
    our_reference VARCHAR(30) UNIQUE NOT NULL,
    status vendor_invoice_status DEFAULT 'RECEIVED' NOT NULL,
    vendor_id UUID REFERENCES vendors(id) ON DELETE RESTRICT NOT NULL,
    purchase_order_id UUID REFERENCES purchase_orders(id) ON DELETE SET NULL,
    grn_id UUID REFERENCES goods_receipt_notes(id) ON DELETE SET NULL,
    subtotal NUMERIC(14,2) NOT NULL,
    discount_amount NUMERIC(12,2) DEFAULT 0,
    taxable_amount NUMERIC(14,2) NOT NULL,
    cgst_amount NUMERIC(12,2) DEFAULT 0,
    sgst_amount NUMERIC(12,2) DEFAULT 0,
    igst_amount NUMERIC(12,2) DEFAULT 0,
    cess_amount NUMERIC(12,2) DEFAULT 0,
    total_tax NUMERIC(12,2) DEFAULT 0,
    freight_charges NUMERIC(12,2) DEFAULT 0,
    other_charges NUMERIC(12,2) DEFAULT 0,
    round_off NUMERIC(8,2) DEFAULT 0,
    grand_total NUMERIC(14,2) NOT NULL,
    due_date DATE NOT NULL,
    amount_paid NUMERIC(14,2) DEFAULT 0,
    balance_due NUMERIC(14,2) NOT NULL,
    tds_applicable BOOLEAN DEFAULT TRUE,
    tds_section VARCHAR(10),
    tds_rate NUMERIC(5,2) DEFAULT 0,
    tds_amount NUMERIC(12,2) DEFAULT 0,
    net_payable NUMERIC(14,2),
    po_matched BOOLEAN DEFAULT FALSE,
    grn_matched BOOLEAN DEFAULT FALSE,
    is_fully_matched BOOLEAN DEFAULT FALSE,
    matching_variance NUMERIC(12,2) DEFAULT 0,
    variance_reason TEXT,
    vendor_irn VARCHAR(64),
    vendor_ack_number VARCHAR(20),
    invoice_pdf_url VARCHAR(500),
    received_by UUID REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
    received_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    verified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    verified_at TIMESTAMPTZ,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    internal_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_vendor_invoice UNIQUE (vendor_id, invoice_number)
);
CREATE INDEX IF NOT EXISTS idx_vendor_invoices_reference ON vendor_invoices(our_reference);
CREATE INDEX IF NOT EXISTS idx_vendor_invoices_vendor ON vendor_invoices(vendor_id);
CREATE INDEX IF NOT EXISTS idx_vendor_invoices_status ON vendor_invoices(status);

-- =====================================================
-- PART 16: CALL CENTER AND LEADS
-- =====================================================

-- Calls table
CREATE TABLE IF NOT EXISTS calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id VARCHAR(50) UNIQUE NOT NULL,
    call_type call_type NOT NULL,
    category call_category,
    status call_status DEFAULT 'RINGING' NOT NULL,
    priority call_priority DEFAULT 'NORMAL',
    phone_number VARCHAR(20) NOT NULL,
    caller_name VARCHAR(200),
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    agent_id UUID REFERENCES users(id) ON DELETE SET NULL,
    queue_name VARCHAR(100),
    ivr_path VARCHAR(500),
    call_start_time TIMESTAMPTZ NOT NULL,
    call_answer_time TIMESTAMPTZ,
    call_end_time TIMESTAMPTZ,
    ring_duration_seconds INTEGER DEFAULT 0,
    talk_duration_seconds INTEGER DEFAULT 0,
    hold_duration_seconds INTEGER DEFAULT 0,
    total_duration_seconds INTEGER DEFAULT 0,
    outcome call_outcome,
    disposition_id UUID REFERENCES call_dispositions(id) ON DELETE SET NULL,
    sentiment customer_sentiment,
    recording_url VARCHAR(500),
    transcription TEXT,
    notes TEXT,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    service_request_id UUID REFERENCES service_requests(id) ON DELETE SET NULL,
    lead_id UUID,
    transfer_count INTEGER DEFAULT 0,
    transferred_to UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_calls_call_id ON calls(call_id);
CREATE INDEX IF NOT EXISTS idx_calls_phone ON calls(phone_number);
CREATE INDEX IF NOT EXISTS idx_calls_customer ON calls(customer_id);
CREATE INDEX IF NOT EXISTS idx_calls_agent ON calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);

-- Callback Schedules table
CREATE TABLE IF NOT EXISTS callback_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id) ON DELETE SET NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    phone_number VARCHAR(20) NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    assigned_agent_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status callback_status DEFAULT 'PENDING' NOT NULL,
    priority call_priority DEFAULT 'NORMAL',
    reason TEXT,
    notes TEXT,
    attempt_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    completed_call_id UUID REFERENCES calls(id) ON DELETE SET NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_callback_schedules_time ON callback_schedules(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_callback_schedules_status ON callback_schedules(status);

-- Call QA Reviews table
CREATE TABLE IF NOT EXISTS call_qa_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE NOT NULL,
    reviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status qa_status DEFAULT 'PENDING' NOT NULL,
    overall_score INTEGER,
    greeting_score INTEGER,
    product_knowledge_score INTEGER,
    problem_solving_score INTEGER,
    communication_score INTEGER,
    compliance_score INTEGER,
    closing_score INTEGER,
    strengths TEXT,
    improvements TEXT,
    coaching_notes TEXT,
    reviewed_at TIMESTAMPTZ,
    agent_acknowledged BOOLEAN DEFAULT FALSE,
    agent_acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_call_qa_reviews_call ON call_qa_reviews(call_id);

-- Leads table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_number VARCHAR(30) UNIQUE NOT NULL,
    lead_type lead_type DEFAULT 'INDIVIDUAL',
    source lead_source NOT NULL,
    source_details VARCHAR(200),
    campaign_id UUID,
    referral_code VARCHAR(50),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20) NOT NULL,
    alternate_phone VARCHAR(20),
    whatsapp_number VARCHAR(20),
    company_name VARCHAR(200),
    designation VARCHAR(100),
    industry VARCHAR(100),
    employee_count VARCHAR(50),
    gst_number VARCHAR(20),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    country VARCHAR(50) DEFAULT 'India',
    interest lead_interest DEFAULT 'NEW_PURCHASE',
    interested_products JSONB,
    interested_category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    budget_min NUMERIC(12,2),
    budget_max NUMERIC(12,2),
    quantity_required INTEGER DEFAULT 1,
    expected_purchase_date DATE,
    status lead_status DEFAULT 'NEW',
    priority lead_priority DEFAULT 'MEDIUM',
    score INTEGER DEFAULT 0,
    score_breakdown JSONB,
    is_qualified BOOLEAN DEFAULT FALSE,
    qualification_date TIMESTAMPTZ,
    qualified_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_to_id UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ,
    assigned_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    team_id UUID,
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    next_follow_up_date TIMESTAMPTZ,
    next_follow_up_notes TEXT,
    last_contacted_at TIMESTAMPTZ,
    contact_attempts INTEGER DEFAULT 0,
    converted_at TIMESTAMPTZ,
    converted_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    converted_customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    converted_order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    lost_reason lost_reason,
    lost_reason_details TEXT,
    lost_to_competitor VARCHAR(100),
    lost_at TIMESTAMPTZ,
    description TEXT,
    internal_notes TEXT,
    special_requirements TEXT,
    tags JSONB,
    source_call_id UUID REFERENCES calls(id) ON DELETE SET NULL,
    dealer_id UUID REFERENCES dealers(id) ON DELETE SET NULL,
    estimated_value NUMERIC(12,2),
    actual_value NUMERIC(12,2),
    created_by_id UUID REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leads_number ON leads(lead_number);
CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_assigned ON leads(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_leads_follow_up ON leads(next_follow_up_date);
CREATE INDEX IF NOT EXISTS idx_leads_city ON leads(city);
CREATE INDEX IF NOT EXISTS idx_leads_pincode ON leads(pincode);

-- Update calls table with lead FK
ALTER TABLE calls ADD CONSTRAINT fk_calls_lead
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL;

-- Lead Activities table
CREATE TABLE IF NOT EXISTS lead_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE NOT NULL,
    activity_type activity_type NOT NULL,
    subject VARCHAR(200) NOT NULL,
    description TEXT,
    outcome VARCHAR(100),
    activity_date TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    duration_minutes INTEGER,
    old_status lead_status,
    new_status lead_status,
    old_assignee_id UUID,
    new_assignee_id UUID,
    call_id UUID REFERENCES calls(id) ON DELETE SET NULL,
    follow_up_date TIMESTAMPTZ,
    follow_up_notes TEXT,
    created_by_id UUID REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lead_activities_lead ON lead_activities(lead_id);

-- Lead Assignment Rules table
CREATE TABLE IF NOT EXISTS lead_assignment_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    source lead_source,
    lead_type lead_type,
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    pincode_pattern VARCHAR(50),
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    min_score INTEGER,
    max_score INTEGER,
    assign_to_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    assign_to_team_id UUID,
    round_robin BOOLEAN DEFAULT FALSE,
    round_robin_users JSONB,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- PART 17: FINAL CLEANUP AND COMPLETION
-- =====================================================

-- Add any missing indexes
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_orders_date_status ON orders(created_at, status);
CREATE INDEX IF NOT EXISTS idx_service_requests_date ON service_requests(created_at);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'All ENUM types created.';
    RAISE NOTICE 'All tables created with proper foreign key relationships.';
    RAISE NOTICE 'All indexes created.';
END $$;

