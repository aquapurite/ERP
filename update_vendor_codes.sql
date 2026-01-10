-- ============================================================================
-- UPDATE VENDOR CODES TO NEW FORMAT
-- Format: VND-{TYPE}-{GLOBAL_SEQUENCE}
-- Run this in Supabase SQL Editor
-- ============================================================================

-- First, let's see what vendors exist
-- SELECT id, vendor_code, name, vendor_type, phone, email, gstin FROM vendors;

-- Update Fastrack Filtration to VND-MFR-00001 (Manufacturer)
UPDATE vendors
SET vendor_code = 'VND-MFR-00001'
WHERE name ILIKE '%Fastrack%' OR name ILIKE '%FASTTRACK%'
  AND vendor_type = 'MANUFACTURER';

-- Update STOS Industrial to VND-SPR-00002 (Spare Parts)
UPDATE vendors
SET vendor_code = 'VND-SPR-00002'
WHERE name ILIKE '%STOS%'
  AND vendor_type = 'SPARE_PARTS';

-- If there's an old "FASTTRACK" with MFR-00001, update it too
UPDATE vendors
SET vendor_code = 'VND-MFR-00001'
WHERE vendor_code = 'MFR-00001';

-- Update any VND-00001 to VND-MFR-00001 (assuming it's Fastrack)
UPDATE vendors
SET vendor_code = 'VND-MFR-00001'
WHERE vendor_code = 'VND-00001';

-- Update any VND-00002 to VND-SPR-00002 (assuming it's STOS)
UPDATE vendors
SET vendor_code = 'VND-SPR-00002'
WHERE vendor_code = 'VND-00002';

-- Delete duplicate vendors (keep only one Fastrack)
-- First identify duplicates
-- SELECT vendor_code, name, COUNT(*) FROM vendors GROUP BY vendor_code, name HAVING COUNT(*) > 1;

-- Delete the PENDING_APPROVAL duplicate if exists
DELETE FROM vendors
WHERE name ILIKE '%FASTTRACK%'
  AND status = 'PENDING_APPROVAL'
  AND vendor_code = 'MFR-00001';

-- Verify the updates
SELECT
    id,
    vendor_code,
    name,
    vendor_type,
    status,
    grade,
    phone,
    email,
    contact_person,
    gstin,
    city,
    state
FROM vendors
ORDER BY vendor_code;
