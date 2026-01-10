-- ============================================================================
-- ADD VENDOR 02: STOS INDUSTRIAL CORPORATION PVT. LTD.
-- Spare Parts Vendor - extracted from PO/APL/ST/25-26/002
-- Run this in Supabase SQL Editor
-- ============================================================================

-- Delete existing vendor if exists (for clean re-run)
DELETE FROM vendors WHERE vendor_code = 'VND-SPR-00002';

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
    'VND-SPR-00002',
    'STOS Industrial',
    'STOS INDUSTRIAL CORPORATION PRIVATE LIMITED',
    'STOS Industrial',
    'SPARE_PARTS',
    'ACTIVE',
    'A',

    -- GST Compliance
    '09AACCO4091J1Z6',
    TRUE,
    '09',  -- Uttar Pradesh
    'AACCO4091J',
    NULL,

    -- MSME (TO BE COLLECTED)
    FALSE,
    NULL,
    NULL,

    -- Contact
    'Saurabh Garg',
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,

    -- Address
    'E-180, Sector-17, Kavi Nagar Industrial Area',
    NULL,
    'Ghaziabad',
    'Uttar Pradesh',
    '09',
    '201002',
    'India',

    -- Bank Details
    'ICICI BANK',
    'Ghaziabad',
    '125605002916',
    'ICIC0001256',
    'CURRENT',
    'STOS INDUSTRIAL CORPORATION PRIVATE LIMITED',

    -- Payment Terms (25% Advance, 75% in 45 days)
    'PARTIAL_ADVANCE',
    45,
    500000.00,
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
    'Spare Parts for Water Purifiers: Sediment Filters, Carbon Blocks, Alkaline, Membranes, Pre-filters, HMR, PRV, Valves. HSN: 84212190. Warranty: 6 months.',
    15,
    25000.00,

    -- Performance
    1,
    0.00,

    -- Verification
    FALSE,

    -- Notes
    'Spare parts vendor. Payment: 25% Advance, 75% in 45 days. All items 6 months warranty. Contact: Saurabh Garg. Supplies both Economical and Premium spare parts.',

    -- Timestamps
    NOW(),
    NOW()
);

-- ============================================================================
-- ADD SUPPLIER CODE FOR SERIALIZATION
-- ST = STOS (first 2 letters of supplier name)
-- ============================================================================
DELETE FROM supplier_codes WHERE code = 'ST';

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
    (SELECT id::text FROM vendors WHERE vendor_code = 'VND-SPR-00002'),
    'ST',
    'STOS Industrial',
    'STOS Industrial Corporation Pvt. Ltd. - Spare Parts Supplier',
    TRUE,
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
    grade,
    gstin,
    gst_state_code,
    payment_terms,
    advance_percentage,
    bank_name,
    bank_account_number,
    bank_ifsc,
    contact_person,
    created_at
FROM vendors
WHERE vendor_code = 'VND-SPR-00002';

-- Verify supplier code
SELECT * FROM supplier_codes WHERE code = 'ST';

-- ============================================================================
-- VENDOR SUMMARY
-- ============================================================================
-- | Field          | Fastrack (VND-00001)     | STOS (VND-SPR-00002)         |
-- |----------------|--------------------------|--------------------------|
-- | Type           | MANUFACTURER             | SPARE_PARTS              |
-- | Products       | Water Purifiers (FG)     | Spare Parts (SP)         |
-- | State          | Delhi (07)               | Uttar Pradesh (09)       |
-- | GSTIN          | TO BE COLLECTED          | 09AACCO4091J1Z6          |
-- | Bank           | HDFC                     | ICICI                    |
-- | Payment        | 25% Adv, 50% PDC         | 25% Adv, 75% in 45 days  |
-- | Warranty       | 18 months                | 6 months                 |
-- | Supplier Code  | FS                       | ST                       |
-- ============================================================================
