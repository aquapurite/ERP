-- =====================================================
-- Chart of Accounts Cleanup Script
-- Fix GST account codes and restore correct structure
-- =====================================================
--
-- ISSUE: The COA has GST accounts at wrong codes.
--
-- Current State (WRONG):
-- - 1200: "GST Input Credit" (should be Inventory)
-- - 1510: "CGST Input" (should be Land & Building)
-- - 1520: "SGST Input" (should be Plant & Machinery)
-- - 1530: "IGST Input" (should be Furniture & Fixtures)
-- - 2310: "CGST Payable" (should not exist)
-- - 2320: "SGST Payable" (should not exist)
--
-- Correct Structure:
-- Assets:
--   1200: Inventory
--   1400: GST Input Credit (parent)
--     1410: CGST Input Credit
--     1420: SGST Input Credit
--     1430: IGST Input Credit
--   1500: Fixed Assets (parent)
--     1510: Land & Building
--     1520: Plant & Machinery
--     1530: Furniture & Fixtures
--
-- Liabilities:
--   2200: GST Output Liability (parent)
--     2210: CGST Output Liability
--     2220: SGST Output Liability
--     2230: IGST Output Liability
--   2300: TDS Payable (separate from GST)
-- =====================================================

-- STEP 1: Check current state (run this first to see what we have)
SELECT account_code, account_name, account_type, parent_id, current_balance
FROM chart_of_accounts
WHERE account_code IN ('1200', '1400', '1410', '1420', '1430',
                        '1500', '1510', '1520', '1530',
                        '2200', '2210', '2220', '2230',
                        '2300', '2310', '2320', '2330')
ORDER BY account_code;

-- STEP 2: Get parent account IDs for reference
-- You'll need these UUIDs for the parent_id relationships

-- Get Assets parent (1000)
SELECT id, account_code, account_name FROM chart_of_accounts WHERE account_code = '1000';

-- Get Fixed Assets parent (1500)
SELECT id, account_code, account_name FROM chart_of_accounts WHERE account_code = '1500';

-- Get GST Liabilities parent (2200)
SELECT id, account_code, account_name FROM chart_of_accounts WHERE account_code = '2200';

-- =====================================================
-- STEP 3: Fix existing wrong entries
-- =====================================================

-- 3a. Fix 1200 from "GST Input Credit" to "Inventory"
UPDATE chart_of_accounts
SET account_name = 'Inventory',
    account_sub_type = 'INVENTORY'
WHERE account_code = '1200' AND account_name LIKE '%GST%';

-- 3b. Fix 1510 from "CGST Input" to "Land & Building"
UPDATE chart_of_accounts
SET account_name = 'Land & Building',
    account_sub_type = 'FIXED_ASSET'
WHERE account_code = '1510' AND account_name LIKE '%GST%';

-- 3c. Fix 1520 from "SGST Input" to "Plant & Machinery"
UPDATE chart_of_accounts
SET account_name = 'Plant & Machinery',
    account_sub_type = 'FIXED_ASSET'
WHERE account_code = '1520' AND account_name LIKE '%GST%';

-- 3d. Fix 1530 from "IGST Input" to "Furniture & Fixtures"
UPDATE chart_of_accounts
SET account_name = 'Furniture & Fixtures',
    account_sub_type = 'FIXED_ASSET'
WHERE account_code = '1530' AND account_name LIKE '%GST%';

-- =====================================================
-- STEP 4: Create missing GST Input Credit accounts
-- (Replace 'PARENT_ID' with actual UUID from Step 2)
-- =====================================================

-- First check if 1400 exists as parent
-- If not, create it:
INSERT INTO chart_of_accounts (
    id, account_code, account_name, account_type, account_sub_type,
    is_active, is_group, allow_direct_posting, current_balance,
    created_at, updated_at
)
SELECT
    gen_random_uuid(), '1400', 'GST Input Credit', 'ASSET', 'CURRENT_ASSET',
    true, true, false, 0,
    now(), now()
WHERE NOT EXISTS (SELECT 1 FROM chart_of_accounts WHERE account_code = '1400');

-- Create CGST Input Credit (1410)
INSERT INTO chart_of_accounts (
    id, account_code, account_name, account_type, account_sub_type,
    parent_id, is_active, is_group, allow_direct_posting, current_balance,
    created_at, updated_at
)
SELECT
    gen_random_uuid(), '1410', 'CGST Input Credit', 'ASSET', 'CURRENT_ASSET',
    (SELECT id FROM chart_of_accounts WHERE account_code = '1400'),
    true, false, true, 0,
    now(), now()
WHERE NOT EXISTS (SELECT 1 FROM chart_of_accounts WHERE account_code = '1410');

-- Create SGST Input Credit (1420)
INSERT INTO chart_of_accounts (
    id, account_code, account_name, account_type, account_sub_type,
    parent_id, is_active, is_group, allow_direct_posting, current_balance,
    created_at, updated_at
)
SELECT
    gen_random_uuid(), '1420', 'SGST Input Credit', 'ASSET', 'CURRENT_ASSET',
    (SELECT id FROM chart_of_accounts WHERE account_code = '1400'),
    true, false, true, 0,
    now(), now()
WHERE NOT EXISTS (SELECT 1 FROM chart_of_accounts WHERE account_code = '1420');

-- Create IGST Input Credit (1430)
INSERT INTO chart_of_accounts (
    id, account_code, account_name, account_type, account_sub_type,
    parent_id, is_active, is_group, allow_direct_posting, current_balance,
    created_at, updated_at
)
SELECT
    gen_random_uuid(), '1430', 'IGST Input Credit', 'ASSET', 'CURRENT_ASSET',
    (SELECT id FROM chart_of_accounts WHERE account_code = '1400'),
    true, false, true, 0,
    now(), now()
WHERE NOT EXISTS (SELECT 1 FROM chart_of_accounts WHERE account_code = '1430');

-- =====================================================
-- STEP 5: Create missing GST Output Liability accounts
-- =====================================================

-- Create CGST Output Liability (2210)
INSERT INTO chart_of_accounts (
    id, account_code, account_name, account_type, account_sub_type,
    parent_id, is_active, is_group, allow_direct_posting, current_balance,
    created_at, updated_at
)
SELECT
    gen_random_uuid(), '2210', 'CGST Output Liability', 'LIABILITY', 'TAX_PAYABLE',
    (SELECT id FROM chart_of_accounts WHERE account_code = '2200'),
    true, false, true, 0,
    now(), now()
WHERE NOT EXISTS (SELECT 1 FROM chart_of_accounts WHERE account_code = '2210');

-- Create SGST Output Liability (2220)
INSERT INTO chart_of_accounts (
    id, account_code, account_name, account_type, account_sub_type,
    parent_id, is_active, is_group, allow_direct_posting, current_balance,
    created_at, updated_at
)
SELECT
    gen_random_uuid(), '2220', 'SGST Output Liability', 'LIABILITY', 'TAX_PAYABLE',
    (SELECT id FROM chart_of_accounts WHERE account_code = '2200'),
    true, false, true, 0,
    now(), now()
WHERE NOT EXISTS (SELECT 1 FROM chart_of_accounts WHERE account_code = '2220');

-- Create IGST Output Liability (2230)
INSERT INTO chart_of_accounts (
    id, account_code, account_name, account_type, account_sub_type,
    parent_id, is_active, is_group, allow_direct_posting, current_balance,
    created_at, updated_at
)
SELECT
    gen_random_uuid(), '2230', 'IGST Output Liability', 'LIABILITY', 'TAX_PAYABLE',
    (SELECT id FROM chart_of_accounts WHERE account_code = '2200'),
    true, false, true, 0,
    now(), now()
WHERE NOT EXISTS (SELECT 1 FROM chart_of_accounts WHERE account_code = '2230');

-- =====================================================
-- STEP 6: Fix wrong GST accounts at 2310, 2320
-- Delete or rename these accounts
-- =====================================================

-- Option A: Delete if no transactions
DELETE FROM chart_of_accounts
WHERE account_code IN ('2310', '2320')
  AND account_name LIKE '%GST%'
  AND current_balance = 0
  AND NOT EXISTS (
      SELECT 1 FROM journal_entry_lines jel
      WHERE jel.account_id = chart_of_accounts.id
  );

-- Option B: If transactions exist, rename to indicate legacy
-- UPDATE chart_of_accounts
-- SET account_name = account_name || ' (LEGACY - DO NOT USE)'
-- WHERE account_code IN ('2310', '2320') AND account_name LIKE '%GST%';

-- =====================================================
-- STEP 7: Verify final state
-- =====================================================
SELECT account_code, account_name, account_type, account_sub_type, current_balance
FROM chart_of_accounts
WHERE account_code IN ('1200', '1400', '1410', '1420', '1430',
                        '1500', '1510', '1520', '1530',
                        '2200', '2210', '2220', '2230',
                        '2300', '2310', '2320', '2330')
ORDER BY account_code;

-- =====================================================
-- Expected Final Result:
-- =====================================================
-- 1200: Inventory (ASSET/INVENTORY)
-- 1400: GST Input Credit (ASSET/CURRENT_ASSET) - parent
-- 1410: CGST Input Credit (ASSET/CURRENT_ASSET)
-- 1420: SGST Input Credit (ASSET/CURRENT_ASSET)
-- 1430: IGST Input Credit (ASSET/CURRENT_ASSET)
-- 1500: Fixed Assets (ASSET/FIXED_ASSET) - parent
-- 1510: Land & Building (ASSET/FIXED_ASSET)
-- 1520: Plant & Machinery (ASSET/FIXED_ASSET)
-- 1530: Furniture & Fixtures (ASSET/FIXED_ASSET)
-- 2200: GST Liabilities (LIABILITY/TAX_PAYABLE) - parent
-- 2210: CGST Output Liability (LIABILITY/TAX_PAYABLE)
-- 2220: SGST Output Liability (LIABILITY/TAX_PAYABLE)
-- 2230: IGST Output Liability (LIABILITY/TAX_PAYABLE)
-- 2300: TDS Payable (LIABILITY/TAX_PAYABLE)
