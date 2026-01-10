-- ============================================================================
-- UPDATE FASTRACK FILTRATION VENDOR DETAILS
-- Extracted from PI NO./FF/25-26/005 dated 19.11.2025
-- Run this in Supabase SQL Editor
-- ============================================================================

UPDATE vendors
SET
    -- Company Details
    name = 'Fastrack Filtration',
    legal_name = 'FASTRACK FILTRATION PVT. LTD.',
    trade_name = 'Fastrack Filtration',
    vendor_type = 'MANUFACTURER',

    -- Bank Details (from PI document)
    bank_name = 'HDFC BANK',
    bank_account_number = '50200076691896',
    bank_branch = 'PEERAGARHI, DELHI',
    bank_ifsc = 'HDFC0001127',
    bank_account_type = 'CURRENT',
    beneficiary_name = 'FASTRACK FILTRATION PVT. LTD.',

    -- Payment Terms (from PI)
    payment_terms = 'CUSTOM',
    credit_days = 30,
    advance_percentage = 25,

    -- Lead Time (from PI - 30 days delivery)
    default_lead_days = 30,

    -- Products
    primary_products = ARRAY['Water Purifiers', 'AQUAPURITE BLITZ', 'AQUAPURITE NEURA', 'AQUAPURITE PREMIO', 'AQUAPURITE ELITZ'],

    -- Notes
    internal_notes = 'Payment Terms: 25% Advance, 25% at Dispatch, 50% PDC. Warranty: 18 months electronic, 1 year SV. Delivery: 30 days from advance payment.',

    -- Status
    status = 'ACTIVE',
    grade = 'B',

    -- Updated timestamp
    updated_at = NOW()

WHERE vendor_code = 'VND-MFR-00001';

-- Verify the update
SELECT
    vendor_code,
    name,
    legal_name,
    vendor_type,
    status,
    grade,
    bank_name,
    bank_account_number,
    bank_ifsc,
    payment_terms,
    advance_percentage,
    default_lead_days,
    primary_products,
    internal_notes
FROM vendors
WHERE vendor_code = 'VND-MFR-00001';
