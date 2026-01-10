-- Create Company Tables for Supabase
-- Run this in Supabase SQL Editor

-- Create ENUM types first
DO $$ BEGIN
    CREATE TYPE company_type AS ENUM (
        'PRIVATE_LIMITED', 'PUBLIC_LIMITED', 'LLP', 'PARTNERSHIP',
        'PROPRIETORSHIP', 'OPC', 'TRUST', 'SOCIETY', 'HUF', 'GOVERNMENT'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE gst_registration_type AS ENUM (
        'REGULAR', 'COMPOSITION', 'CASUAL', 'SEZ_UNIT', 'SEZ_DEVELOPER',
        'ISD', 'TDS_DEDUCTOR', 'TCS_COLLECTOR', 'NON_RESIDENT', 'UNREGISTERED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Create companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic Information
    legal_name VARCHAR(300) NOT NULL,
    trade_name VARCHAR(300),
    code VARCHAR(20) UNIQUE NOT NULL,
    company_type company_type DEFAULT 'PRIVATE_LIMITED' NOT NULL,

    -- Tax Registration
    gstin VARCHAR(15) NOT NULL,
    gst_registration_type gst_registration_type DEFAULT 'REGULAR' NOT NULL,
    state_code VARCHAR(2) NOT NULL,
    pan VARCHAR(10) NOT NULL,
    tan VARCHAR(10),
    cin VARCHAR(21),
    llpin VARCHAR(10),
    msme_registered BOOLEAN DEFAULT FALSE,
    udyam_number VARCHAR(30),
    msme_category VARCHAR(20),

    -- Address
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    district VARCHAR(100),
    state VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    country VARCHAR(50) DEFAULT 'India',

    -- Contact
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    mobile VARCHAR(20),
    fax VARCHAR(20),
    website VARCHAR(255),

    -- Bank Details
    bank_name VARCHAR(200),
    bank_branch VARCHAR(200),
    bank_account_number VARCHAR(30),
    bank_ifsc VARCHAR(11),
    bank_account_type VARCHAR(20),
    bank_account_name VARCHAR(200),

    -- Branding
    logo_url VARCHAR(500),
    logo_small_url VARCHAR(500),
    favicon_url VARCHAR(500),
    signature_url VARCHAR(500),

    -- E-Invoice
    einvoice_enabled BOOLEAN DEFAULT FALSE,
    einvoice_username VARCHAR(100),
    einvoice_password_encrypted VARCHAR(500),
    einvoice_api_mode VARCHAR(20) DEFAULT 'SANDBOX',

    -- E-Way Bill
    ewb_enabled BOOLEAN DEFAULT FALSE,
    ewb_username VARCHAR(100),
    ewb_password_encrypted VARCHAR(500),
    ewb_api_mode VARCHAR(20) DEFAULT 'SANDBOX',

    -- Invoice Settings
    invoice_prefix VARCHAR(20) DEFAULT 'INV',
    invoice_suffix VARCHAR(20),
    financial_year_start_month INTEGER DEFAULT 4,
    invoice_terms TEXT,
    invoice_notes TEXT,
    invoice_footer TEXT,

    -- PO Settings
    po_prefix VARCHAR(20) DEFAULT 'PO',
    po_terms TEXT,

    -- Currency & Tax
    currency_code VARCHAR(3) DEFAULT 'INR',
    currency_symbol VARCHAR(5) DEFAULT '₹',
    default_cgst_rate NUMERIC(5,2) DEFAULT 9.00,
    default_sgst_rate NUMERIC(5,2) DEFAULT 9.00,
    default_igst_rate NUMERIC(5,2) DEFAULT 18.00,
    tds_deductor BOOLEAN DEFAULT TRUE,
    default_tds_rate NUMERIC(5,2) DEFAULT 10.00,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    extra_data JSONB,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Create index on GSTIN
CREATE INDEX IF NOT EXISTS ix_companies_gstin ON companies(gstin);
CREATE INDEX IF NOT EXISTS ix_companies_code ON companies(code);

-- Create company_branches table
CREATE TABLE IF NOT EXISTS company_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    code VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    branch_type VARCHAR(50) DEFAULT 'OFFICE',

    gstin VARCHAR(15),
    state_code VARCHAR(2) NOT NULL,

    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,

    email VARCHAR(255),
    phone VARCHAR(20),
    contact_person VARCHAR(100),

    warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,

    is_active BOOLEAN DEFAULT TRUE,
    is_billing_address BOOLEAN DEFAULT FALSE,
    is_shipping_address BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(company_id, code)
);

CREATE INDEX IF NOT EXISTS ix_company_branches_company_id ON company_branches(company_id);
CREATE INDEX IF NOT EXISTS ix_company_branches_gstin ON company_branches(gstin);

-- Create company_bank_accounts table
CREATE TABLE IF NOT EXISTS company_bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    bank_name VARCHAR(200) NOT NULL,
    branch_name VARCHAR(200) NOT NULL,
    account_number VARCHAR(30) NOT NULL,
    ifsc_code VARCHAR(11) NOT NULL,
    account_type VARCHAR(20) DEFAULT 'CURRENT',
    account_name VARCHAR(200) NOT NULL,

    upi_id VARCHAR(100),
    swift_code VARCHAR(15),

    purpose VARCHAR(50) DEFAULT 'GENERAL',
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    show_on_invoice BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_company_bank_accounts_company_id ON company_bank_accounts(company_id);

-- Insert default company (Aquapurite)
INSERT INTO companies (
    legal_name, trade_name, code, company_type, gstin, state_code, pan,
    address_line1, city, state, pincode, email, phone, is_primary
) VALUES (
    'Aquapurite Private Limited',
    'Aquapurite',
    'AQUA',
    'PRIVATE_LIMITED',
    '27AAAAA0000A1Z5',  -- Replace with actual GSTIN
    '27',  -- Maharashtra
    'AAAAA0000A',  -- Replace with actual PAN
    '123 Business Park',
    'Mumbai',
    'Maharashtra',
    '400001',
    'info@aquapurite.com',
    '+919999999999',
    TRUE
) ON CONFLICT (code) DO NOTHING;

-- Verify
SELECT 'Companies table created successfully' as status;
SELECT COUNT(*) as company_count FROM companies;
