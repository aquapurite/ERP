-- ============================================================================
-- ADD VENDOR: FASTRACK FILTRATION PVT. LTD.
-- First vendor in the database - extracted from PI NO./FF/25-26/005
-- Run this in Supabase SQL Editor
-- ============================================================================

-- Insert vendor
INSERT INTO vendors (
    id,
    vendor_code,
    name,                                     -- Required display name
    legal_name,
    trade_name,
    vendor_type,
    status,
    grade,

    -- Address (placeholder - update when actual address available)
    address_line1,
    city,
    state,
    state_code,
    pincode,
    country,
    gst_state_code,

    -- Contact (Update when available)
    contact_person,
    phone,
    email,

    -- GST Compliance
    gst_registered,
    gstin,
    pan,

    -- Bank Details (from PI)
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
    'VND-FTFL-001',                                -- Vendor code
    'Fastrack Filtration',                         -- Display name (required)
    'FASTRACK FILTRATION PVT. LTD.',               -- Legal name
    'Fastrack Filtration',                         -- Trade name
    'MANUFACTURER',                                 -- Vendor type
    'PENDING_APPROVAL',                             -- Status
    'B',                                            -- Grade (default - will improve based on performance)

    -- Address (placeholder - update when actual address is available)
    'Peeragarhi Area',                             -- Address line 1
    'New Delhi',                                   -- City
    'Delhi',                                       -- State
    '07',                                          -- State code (Delhi)
    '110087',                                      -- Pincode
    'India',                                       -- Country
    '07',                                          -- GST State Code (Delhi)

    -- Contact (update when available)
    NULL,                                          -- Contact person (TO BE COLLECTED)
    NULL,                                          -- Phone (TO BE COLLECTED)
    NULL,                                          -- Email (TO BE COLLECTED)

    -- GST Compliance
    TRUE,                                          -- GST registered (assumed)
    NULL,                                          -- GSTIN (TO BE COLLECTED - IMPORTANT!)
    NULL,                                          -- PAN (TO BE COLLECTED)

    -- Bank Details (from PI)
    'HDFC BANK',                                   -- Bank name
    'PEERAGARHI, DELHI',                           -- Bank branch
    '50200076691896',                              -- Account number
    'HDFC0001127',                                 -- IFSC code
    'CURRENT',                                     -- Account type
    'FASTRACK FILTRATION PVT. LTD.',               -- Beneficiary name

    -- Payment Terms (from PI: 25% advance, 25% dispatch, 50% PDC)
    'PARTIAL_ADVANCE',                             -- Payment terms enum
    30,                                            -- Credit days (50% PDC implies ~30 days)
    2000000.00,                                    -- Credit limit (based on PI value)
    25.00,                                         -- Advance percentage (25%)

    -- Products Info
    'Water Purifiers (RO Systems): AQUAPURITE BLITZ, NEURA, PREMIO, ELITZ. HSN: 842121. Warranty: 18 months electronics, 1 year SV.',
    30,                                            -- Lead days (from PI terms)

    -- Opening Balance
    0.00,                                          -- Opening balance
    0.00,                                          -- Current balance
    0.00,                                          -- Advance balance

    -- Performance
    0,                                             -- Total PO count
    0.00,                                          -- Total PO value

    -- Notes
    'First vendor. Payment: 25% Adv, 25% Dispatch, 50% PDC. Notes from PI: Neura - Alkaline 4", RO Membrane & Housing by Buyer; Blitz - RO Membrane, Pre/Post Carbon, Sediment by Buyer; ALL - UV LED by Buyer.',

    -- Timestamps
    NOW(),
    NOW()
)
ON CONFLICT (vendor_code) DO UPDATE SET
    name = EXCLUDED.name,
    legal_name = EXCLUDED.legal_name,
    bank_name = EXCLUDED.bank_name,
    bank_branch = EXCLUDED.bank_branch,
    bank_account_number = EXCLUDED.bank_account_number,
    bank_ifsc = EXCLUDED.bank_ifsc,
    beneficiary_name = EXCLUDED.beneficiary_name,
    payment_terms = EXCLUDED.payment_terms,
    advance_percentage = EXCLUDED.advance_percentage,
    primary_products = EXCLUDED.primary_products,
    default_lead_days = EXCLUDED.default_lead_days,
    internal_notes = EXCLUDED.internal_notes,
    updated_at = NOW();

-- ============================================================================
-- IMPORTANT: Collect the following from vendor for GST compliance:
-- 1. GSTIN (mandatory for claiming ITC)
-- 2. PAN Number
-- 3. Complete registered address
-- 4. Contact person name, phone, email
-- ============================================================================

-- Verify the vendor was added
SELECT
    vendor_code,
    name,
    legal_name,
    vendor_type,
    status,
    grade,
    payment_terms,
    advance_percentage,
    credit_days,
    bank_name,
    bank_account_number,
    bank_ifsc,
    default_lead_days,
    primary_products,
    created_at
FROM vendors
WHERE vendor_code = 'VND-FTFL-001';

-- ============================================================================
-- PRODUCTS FROM PI NO./FF/25-26/005 (dated 19.11.2025)
-- ============================================================================
-- | Product           | HSN    | Qty  | Rate     | Total      |
-- |-------------------|--------|------|----------|------------|
-- | AQUAPURITE BLITZ  | 842121 | 150  | 2,304.00 | 3,45,600   |
-- | AQUAPURITE NEURA  | 842121 | 150  | 2,509.00 | 3,76,350   |
-- | AQUAPURITE PREMIO | 842121 |  20  | 12,185.00| 2,43,700   |
-- | AQUAPURITE ELITZ  | 842121 |  25  | 8,321.00 | 2,08,025   |
-- ============================================================================
-- Subtotal:     Rs. 11,73,675.00
-- CGST 9%:      Rs. 1,05,631.00
-- SGST 9%:      Rs. 1,05,631.00
-- GRAND TOTAL:  Rs. 13,84,937.00
-- ============================================================================
--
-- PAYMENT TERMS:
-- - 25% Advance against PI:    Rs. 3,46,234
-- - 25% At dispatch:           Rs. 3,46,234
-- - 50% PDC from dispatch:     Rs. 6,92,469
--
-- WARRANTY:
-- - 18 months on electronic parts
-- - 1 year SV warranty
--
-- DELIVERY:
-- - Within 30 days from receipt of advance payment
-- - Packing material design from buyer required
--
-- BUYER-PROVIDED COMPONENTS:
-- - Neura Model: Alkaline 4", RO Membrane & Housing
-- - Blitz Model: RO Membrane & Housing, Pre & Post Carbon, Sediment Spun
-- - ALL Models: UV LED
-- ============================================================================
