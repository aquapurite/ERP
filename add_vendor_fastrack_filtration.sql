-- ============================================================================
-- ADD VENDOR: FASTRACK FILTRATION PVT. LTD.
-- First vendor in the database - extracted from PI NO./FF/25-26/005
-- Run this in Supabase SQL Editor
-- ============================================================================

-- First, ensure unique constraint exists on vendor_code (if not already)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'vendors_vendor_code_key'
    ) THEN
        ALTER TABLE vendors ADD CONSTRAINT vendors_vendor_code_key UNIQUE (vendor_code);
    END IF;
EXCEPTION WHEN others THEN
    -- Constraint might already exist or column might have duplicates
    RAISE NOTICE 'Could not add unique constraint: %', SQLERRM;
END $$;

-- Delete existing vendor if exists (for clean re-run)
DELETE FROM vendors WHERE vendor_code = 'VND-FTFL-001';

-- Insert vendor
INSERT INTO vendors (
    id,
    vendor_code,
    name,
    legal_name,
    trade_name,
    vendor_type,
    status,
    grade,

    -- Address
    address_line1,
    city,
    state,
    state_code,
    pincode,
    country,
    gst_state_code,

    -- Contact
    contact_person,
    phone,
    email,

    -- GST Compliance
    gst_registered,
    gstin,
    pan,

    -- Bank Details
    bank_name,
    bank_branch,
    bank_account_number,
    bank_ifsc,
    bank_account_type,
    beneficiary_name,

    -- Payment Terms
    payment_terms,
    credit_days,
    credit_limit,
    advance_percentage,

    -- Products Info
    primary_products,
    default_lead_days,

    -- Opening Balance
    opening_balance,
    current_balance,
    advance_balance,

    -- Performance
    total_po_count,
    total_po_value,

    -- Notes
    internal_notes,

    -- Timestamps
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'VND-FTFL-001',
    'Fastrack Filtration',
    'FASTRACK FILTRATION PVT. LTD.',
    'Fastrack Filtration',
    'MANUFACTURER',
    'PENDING_APPROVAL',
    'B',

    -- Address (placeholder)
    'Peeragarhi Area',
    'New Delhi',
    'Delhi',
    '07',
    '110087',
    'India',
    '07',

    -- Contact (to be collected)
    NULL,
    NULL,
    NULL,

    -- GST Compliance
    TRUE,
    NULL,  -- GSTIN (TO BE COLLECTED)
    NULL,  -- PAN (TO BE COLLECTED)

    -- Bank Details (from PI)
    'HDFC BANK',
    'PEERAGARHI, DELHI',
    '50200076691896',
    'HDFC0001127',
    'CURRENT',
    'FASTRACK FILTRATION PVT. LTD.',

    -- Payment Terms
    'PARTIAL_ADVANCE',
    30,
    2000000.00,
    25.00,

    -- Products Info
    'Water Purifiers (RO Systems): AQUAPURITE BLITZ, NEURA, PREMIO, ELITZ. HSN: 842121. Warranty: 18 months electronics, 1 year SV.',
    30,

    -- Opening Balance
    0.00,
    0.00,
    0.00,

    -- Performance
    0,
    0.00,

    -- Notes
    'First vendor. Payment: 25% Adv, 25% Dispatch, 50% PDC. Notes from PI: Neura - Alkaline 4", RO Membrane & Housing by Buyer; Blitz - RO Membrane, Pre/Post Carbon, Sediment by Buyer; ALL - UV LED by Buyer.',

    -- Timestamps
    NOW(),
    NOW()
);

-- ============================================================================
-- VERIFY
-- ============================================================================
SELECT
    vendor_code,
    name,
    legal_name,
    vendor_type,
    status,
    payment_terms,
    advance_percentage,
    bank_name,
    bank_account_number,
    bank_ifsc,
    created_at
FROM vendors
WHERE vendor_code = 'VND-FTFL-001';

-- ============================================================================
-- IMPORTANT: Collect from vendor for GST compliance:
-- 1. GSTIN (mandatory for ITC)
-- 2. PAN Number
-- 3. Complete registered address
-- 4. Contact person, phone, email
-- ============================================================================
