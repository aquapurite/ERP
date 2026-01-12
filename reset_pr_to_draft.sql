-- Reset Purchase Requisitions to DRAFT status for testing
-- Run this in Supabase SQL Editor

-- First, let's see what PRs exist and their current status
SELECT
    id,
    requisition_number,
    status,
    requesting_department,
    request_date,
    created_at
FROM purchase_requisitions
ORDER BY created_at DESC;

-- Update PR0001 and PR0002 (or similar patterns) to DRAFT status
-- This will allow you to re-approve and create POs against them

UPDATE purchase_requisitions
SET
    status = 'DRAFT',
    approved_by = NULL,
    approved_at = NULL,
    rejection_reason = NULL
WHERE requisition_number LIKE 'PR-%-0001'
   OR requisition_number LIKE 'PR-%-0002'
   OR requisition_number = 'PR0001'
   OR requisition_number = 'PR0002'
   OR requisition_number = 'PR-0001'
   OR requisition_number = 'PR-0002';

-- If the above doesn't match, try updating all PRs that are not DRAFT
-- Uncomment the following if needed:
-- UPDATE purchase_requisitions
-- SET
--     status = 'DRAFT',
--     approved_by = NULL,
--     approved_at = NULL,
--     rejection_reason = NULL
-- WHERE status != 'DRAFT';

-- Verify the changes
SELECT
    id,
    requisition_number,
    status,
    requesting_department,
    request_date
FROM purchase_requisitions
ORDER BY created_at DESC;
