-- ============================================================================
-- UPDATE COMPANY DETAILS WITH CERTIFICATE DATA
-- Run this in Supabase SQL Editor to update company information
-- ============================================================================

-- Update existing company or insert if not exists
INSERT INTO companies (
    legal_name,
    trade_name,
    code,
    company_type,

    -- Tax Registration
    gstin,
    gst_registration_type,
    state_code,
    pan,
    tan,
    cin,
    msme_registered,
    udyam_number,
    msme_category,

    -- Address
    address_line1,
    address_line2,
    city,
    district,
    state,
    pincode,
    country,

    -- Contact
    email,
    phone,
    mobile,

    -- Invoice Settings
    invoice_prefix,
    po_prefix,

    -- Status
    is_active,
    is_primary,

    -- Timestamps
    created_at,
    updated_at
) VALUES (
    'AQUAPURITE PRIVATE LIMITED',
    'Aquapurite',
    'AQUA',
    'PRIVATE_LIMITED',

    -- Tax Registration (from certificates)
    '07ABDCA6170C1Z0',      -- GSTIN
    'REGULAR',
    '07',                    -- Delhi state code
    'ABDCA6170C',           -- PAN
    'DELA84712F',           -- TAN
    'U32909DL2025PTC454115', -- CIN
    TRUE,                    -- MSME Registered
    'UDYAM-DL-03-0068837',  -- Udyam Number
    'MICRO',                 -- MSME Category

    -- Address
    'PLOT 36-A, KH NO 181, PH-1, SHYAM VIHAR, DINDAPUR EXT',
    'Najafgarh',
    'New Delhi',
    'South West Delhi',
    'Delhi',
    '110043',
    'India',

    -- Contact
    'riaansh97@gmail.com',
    '9013034083',
    '9013034083',

    -- Invoice Settings
    'INV',
    'PO',

    -- Status
    TRUE,
    TRUE,

    -- Timestamps
    NOW(),
    NOW()
)
ON CONFLICT (code) DO UPDATE SET
    legal_name = EXCLUDED.legal_name,
    trade_name = EXCLUDED.trade_name,
    company_type = EXCLUDED.company_type,
    gstin = EXCLUDED.gstin,
    gst_registration_type = EXCLUDED.gst_registration_type,
    state_code = EXCLUDED.state_code,
    pan = EXCLUDED.pan,
    tan = EXCLUDED.tan,
    cin = EXCLUDED.cin,
    msme_registered = EXCLUDED.msme_registered,
    udyam_number = EXCLUDED.udyam_number,
    msme_category = EXCLUDED.msme_category,
    address_line1 = EXCLUDED.address_line1,
    address_line2 = EXCLUDED.address_line2,
    city = EXCLUDED.city,
    district = EXCLUDED.district,
    state = EXCLUDED.state,
    pincode = EXCLUDED.pincode,
    country = EXCLUDED.country,
    email = EXCLUDED.email,
    phone = EXCLUDED.phone,
    mobile = EXCLUDED.mobile,
    is_active = EXCLUDED.is_active,
    is_primary = EXCLUDED.is_primary,
    updated_at = NOW();

-- Verify the update
SELECT
    'Company Details Updated' as status,
    legal_name,
    gstin,
    pan,
    tan,
    cin,
    udyam_number,
    msme_category,
    address_line1 || ', ' || COALESCE(address_line2, '') || ', ' || city || ' - ' || pincode as full_address,
    email,
    phone
FROM companies
WHERE code = 'AQUA';

-- ============================================================================
-- COMPANY DETAILS SUMMARY (from certificates)
-- ============================================================================
-- Legal Name: AQUAPURITE PRIVATE LIMITED
-- Trade Name: Aquapurite
-- CIN: U32909DL2025PTC454115
-- PAN: ABDCA6170C
-- TAN: DELA84712F
-- GSTIN: 07ABDCA6170C1Z0 (Delhi - State Code 07)
-- Udyam Number: UDYAM-DL-03-0068837
-- MSME Category: MICRO ENTERPRISE
--
-- Registered Address:
-- PLOT 36-A, KH NO 181, PH-1, SHYAM VIHAR, DINDAPUR EXT
-- Najafgarh, New Delhi - 110043, Delhi, India
--
-- Contact:
-- Email: riaansh97@gmail.com
-- Phone: 9013034083
--
-- Date of Incorporation: 28/08/2025
-- ============================================================================
