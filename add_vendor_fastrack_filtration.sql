-- ============================================================================
-- ADD VENDOR 01: FASTRACK FILTRATION PVT. LTD.
-- Water Purifier Manufacturer - extracted from PI NO./FF/25-26/005
-- Run this in Supabase SQL Editor
-- ============================================================================

-- Delete existing vendor if exists (for clean re-run)
DELETE FROM vendors WHERE vendor_code IN ('VND-MFR-00001', 'VND-MFR-00001', 'MFR-00001');

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

    -- GST Compliance
    gstin,
    gst_registered,
    gst_state_code,
    pan,
    tan,

    -- MSME
    msme_registered,
    msme_number,
    msme_category,

    -- Contact Details
    contact_person,
    designation,
    email,
    phone,
    mobile,
    website,

    -- Address
    address_line1,
    address_line2,
    city,
    state,
    state_code,
    pincode,
    country,

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

    -- TDS
    tds_applicable,
    tds_section,
    tds_rate,
    lower_tds_certificate,

    -- Outstanding
    opening_balance,
    current_balance,
    advance_balance,

    -- Products Info
    primary_products,
    default_lead_days,
    min_order_value,

    -- Performance
    total_po_count,
    total_po_value,

    -- Verification
    is_verified,

    -- Notes
    internal_notes,

    -- Timestamps
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'VND-MFR-00001',
    'Fastrack Filtration',
    'FASTRACK FILTRATION PVT. LTD.',
    'Fastrack Filtration',
    'MANUFACTURER',
    'ACTIVE',
    'B',

    -- GST Compliance (TO BE COLLECTED)
    NULL,  -- GSTIN - TO BE COLLECTED
    TRUE,
    '07',  -- Delhi
    NULL,  -- PAN - TO BE COLLECTED
    NULL,  -- TAN

    -- MSME (TO BE COLLECTED)
    FALSE,
    NULL,
    NULL,

    -- Contact (TO BE COLLECTED)
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,

    -- Address (placeholder - to be updated)
    'Peeragarhi Area',
    NULL,
    'New Delhi',
    'Delhi',
    '07',
    '110087',
    'India',

    -- Bank Details (from PI)
    'HDFC BANK',
    'PEERAGARHI, DELHI',
    '50200076691896',
    'HDFC0001127',
    'CURRENT',
    'FASTRACK FILTRATION PVT. LTD.',

    -- Payment Terms (25% Adv, 25% Dispatch, 50% PDC)
    'PARTIAL_ADVANCE',
    30,
    2000000.00,
    25.00,

    -- TDS
    TRUE,
    '194C',
    2.00,
    FALSE,  -- lower_tds_certificate

    -- Outstanding
    0.00,
    0.00,
    0.00,

    -- Products Info
    'Water Purifiers (RO Systems): AQUAPURITE BLITZ, NEURA, PREMIO, ELITZ. HSN: 842121. Warranty: 18 months electronics, 1 year SV.',
    30,
    50000.00,

    -- Performance
    0,
    0.00,

    -- Verification
    FALSE,

    -- Notes
    'First vendor - Water Purifier Manufacturer. Payment: 25% Adv, 25% Dispatch, 50% PDC. Notes from PI: Neura - Alkaline 4", RO Membrane & Housing by Buyer; Blitz - RO Membrane, Pre/Post Carbon, Sediment by Buyer; ALL - UV LED by Buyer.',

    -- Timestamps
    NOW(),
    NOW()
);

-- ============================================================================
-- ADD SUPPLIER CODE FOR SERIALIZATION
-- FS = Fastrack (first 2 letters of supplier name)
-- ============================================================================
DELETE FROM supplier_codes WHERE code = 'FS';

INSERT INTO supplier_codes (
    id,
    vendor_id,
    code,
    name,
    description,
    is_active,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid()::text,
    (SELECT id::text FROM vendors WHERE vendor_code = 'VND-MFR-00001'),
    'FS',
    'Fastrack Filtration',
    'Fastrack Filtration Pvt. Ltd. - Water Purifier Manufacturer',
    TRUE,
    NOW(),
    NOW()
);

-- ============================================================================
-- ADD MODEL CODE REFERENCES FOR FINISHED GOODS (Water Purifiers)
-- ============================================================================
DELETE FROM model_code_references WHERE fg_code IN ('WPRABL001', 'WPRANR001', 'WPRAEL001', 'WPRAPM001');

INSERT INTO model_code_references (id, fg_code, model_code, item_type, description, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid()::text, 'WPRABL001', 'BLZ', 'FINISHED_GOODS', 'Aquapurite Blitz - Entry Level RO', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'WPRANR001', 'NRA', 'FINISHED_GOODS', 'Aquapurite Neura - Alkaline RO', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'WPRAEL001', 'ELZ', 'FINISHED_GOODS', 'Aquapurite Elitz - Elite RO', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'WPRAPM001', 'PMO', 'FINISHED_GOODS', 'Aquapurite Premio - Premium RO', TRUE, NOW(), NOW());

-- ============================================================================
-- VERIFY
-- ============================================================================
SELECT
    vendor_code,
    name,
    legal_name,
    vendor_type,
    status,
    grade,
    gst_state_code,
    payment_terms,
    advance_percentage,
    bank_name,
    bank_account_number,
    bank_ifsc,
    tds_applicable,
    tds_section,
    tds_rate,
    created_at
FROM vendors
WHERE vendor_code = 'VND-MFR-00001';

-- Verify supplier code
SELECT * FROM supplier_codes WHERE code = 'FS';

-- Verify model codes for FG
SELECT fg_code, model_code, item_type, description FROM model_code_references WHERE fg_code LIKE 'WPRA%';

-- ============================================================================
-- IMPORTANT: Collect from vendor for GST compliance:
-- 1. GSTIN (mandatory for ITC) - 15 digit
-- 2. PAN Number - 10 char
-- 3. Complete registered address
-- 4. Contact person, phone, email
-- 5. MSME/Udyam registration (if applicable)
-- ============================================================================
