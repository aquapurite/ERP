-- ============================================================================
-- DELETE TEST PURCHASE REQUISITIONS
-- Run this in Supabase SQL Editor to remove test PRs
-- ============================================================================

-- First, delete PR items (child records)
DELETE FROM purchase_requisition_items
WHERE requisition_id IN (
    SELECT id FROM purchase_requisitions
    WHERE requisition_number LIKE 'PR-%'
);

-- Then, delete the PRs themselves
DELETE FROM purchase_requisitions
WHERE requisition_number LIKE 'PR-%';

-- Verify deletion
SELECT requisition_number, status, created_at FROM purchase_requisitions ORDER BY created_at;

-- The next PR created will automatically get the next number based on the date
-- Format: PR-YYYYMMDD-0001
