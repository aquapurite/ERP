-- ============================================================================
-- SYNC EXISTING PENDING ITEMS TO APPROVAL_REQUESTS TABLE
-- Run this in Supabase SQL Editor to create approval entries for existing items
-- ============================================================================

-- First, let's check what pending items exist

-- 1. Check pending Purchase Requisitions
SELECT 'Purchase Requisitions' as type, id, requisition_number, status, estimated_total, created_by
FROM purchase_requisitions
WHERE status = 'SUBMITTED';

-- 2. Check pending Purchase Orders
SELECT 'Purchase Orders' as type, id, po_number, status, grand_total, created_by
FROM purchase_orders
WHERE status = 'PENDING_APPROVAL';

-- 3. Check pending Vendors
SELECT 'Vendors' as type, id, code, name, status, opening_balance
FROM vendors
WHERE status = 'PENDING_APPROVAL';

-- 4. Check pending Sales Channels
SELECT 'Sales Channels' as type, id, code, name, status
FROM sales_channels
WHERE status = 'PENDING_SETUP' OR status = 'INACTIVE';

-- ============================================================================
-- INSERT PENDING ITEMS INTO APPROVAL_REQUESTS
-- ============================================================================

-- Get a user ID for the requested_by field (first admin or any user)
DO $$
DECLARE
    default_user_id UUID;
    pr_record RECORD;
    po_record RECORD;
    vendor_record RECORD;
    seq_num INTEGER := 1;
    today_prefix TEXT;
    approval_level TEXT;
BEGIN
    -- Get default user
    SELECT id INTO default_user_id FROM users LIMIT 1;

    IF default_user_id IS NULL THEN
        RAISE EXCEPTION 'No users found in the system';
    END IF;

    today_prefix := 'APR-' || TO_CHAR(NOW(), 'YYYYMMDD');

    -- Get next sequence number
    SELECT COALESCE(MAX(CAST(SPLIT_PART(request_number, '-', 3) AS INTEGER)), 0) + 1
    INTO seq_num
    FROM approval_requests
    WHERE request_number LIKE today_prefix || '%';

    -- Insert pending Purchase Requisitions
    FOR pr_record IN
        SELECT id, requisition_number, estimated_total, created_by, reason, created_at
        FROM purchase_requisitions
        WHERE status = 'SUBMITTED'
        AND id NOT IN (SELECT entity_id FROM approval_requests WHERE entity_type = 'PURCHASE_REQUISITION')
    LOOP
        -- Determine approval level based on amount
        IF COALESCE(pr_record.estimated_total, 0) <= 50000 THEN
            approval_level := 'LEVEL_1';
        ELSIF pr_record.estimated_total <= 500000 THEN
            approval_level := 'LEVEL_2';
        ELSE
            approval_level := 'LEVEL_3';
        END IF;

        INSERT INTO approval_requests (
            id, request_number, entity_type, entity_id, entity_number,
            amount, approval_level, status, priority, title, description,
            requested_by, requested_at, due_date, is_overdue, created_at, updated_at
        ) VALUES (
            gen_random_uuid(),
            today_prefix || '-' || LPAD(seq_num::TEXT, 4, '0'),
            'PURCHASE_REQUISITION',
            pr_record.id,
            pr_record.requisition_number,
            COALESCE(pr_record.estimated_total, 0),
            approval_level,
            'PENDING',
            5,
            'Purchase Requisition: ' || pr_record.requisition_number,
            pr_record.reason,
            COALESCE(pr_record.created_by, default_user_id),
            COALESCE(pr_record.created_at, NOW()),
            NOW() + INTERVAL '3 days',
            FALSE,
            NOW(),
            NOW()
        );

        seq_num := seq_num + 1;
        RAISE NOTICE 'Created approval for PR: %', pr_record.requisition_number;
    END LOOP;

    -- Insert pending Purchase Orders
    FOR po_record IN
        SELECT id, po_number, grand_total, created_by, terms_and_conditions, created_at, vendor_name
        FROM purchase_orders
        WHERE status = 'PENDING_APPROVAL'
        AND id NOT IN (SELECT entity_id FROM approval_requests WHERE entity_type = 'PURCHASE_ORDER')
    LOOP
        -- Determine approval level based on amount
        IF COALESCE(po_record.grand_total, 0) <= 50000 THEN
            approval_level := 'LEVEL_1';
        ELSIF po_record.grand_total <= 500000 THEN
            approval_level := 'LEVEL_2';
        ELSE
            approval_level := 'LEVEL_3';
        END IF;

        INSERT INTO approval_requests (
            id, request_number, entity_type, entity_id, entity_number,
            amount, approval_level, status, priority, title, description,
            requested_by, requested_at, due_date, is_overdue,
            extra_info, created_at, updated_at
        ) VALUES (
            gen_random_uuid(),
            today_prefix || '-' || LPAD(seq_num::TEXT, 4, '0'),
            'PURCHASE_ORDER',
            po_record.id,
            po_record.po_number,
            COALESCE(po_record.grand_total, 0),
            approval_level,
            'PENDING',
            5,
            'PO Approval: ' || po_record.po_number || ' - ' || COALESCE(po_record.vendor_name, 'Unknown Vendor'),
            po_record.terms_and_conditions,
            COALESCE(po_record.created_by, default_user_id),
            COALESCE(po_record.created_at, NOW()),
            NOW() + INTERVAL '3 days',
            FALSE,
            jsonb_build_object('vendor_name', po_record.vendor_name),
            NOW(),
            NOW()
        );

        seq_num := seq_num + 1;
        RAISE NOTICE 'Created approval for PO: %', po_record.po_number;
    END LOOP;

    -- Insert pending Vendors
    FOR vendor_record IN
        SELECT id, code, name, opening_balance, created_at
        FROM vendors
        WHERE status = 'PENDING_APPROVAL'
        AND id NOT IN (SELECT entity_id FROM approval_requests WHERE entity_type = 'VENDOR_ONBOARDING')
    LOOP
        -- Determine approval level based on opening balance
        IF COALESCE(vendor_record.opening_balance, 0) <= 50000 THEN
            approval_level := 'LEVEL_1';
        ELSIF vendor_record.opening_balance <= 500000 THEN
            approval_level := 'LEVEL_2';
        ELSE
            approval_level := 'LEVEL_3';
        END IF;

        INSERT INTO approval_requests (
            id, request_number, entity_type, entity_id, entity_number,
            amount, approval_level, status, priority, title, description,
            requested_by, requested_at, due_date, is_overdue, created_at, updated_at
        ) VALUES (
            gen_random_uuid(),
            today_prefix || '-' || LPAD(seq_num::TEXT, 4, '0'),
            'VENDOR_ONBOARDING',
            vendor_record.id,
            vendor_record.code,
            COALESCE(vendor_record.opening_balance, 0),
            approval_level,
            'PENDING',
            5,
            'Vendor Onboarding: ' || vendor_record.name,
            'New vendor registration',
            default_user_id,
            COALESCE(vendor_record.created_at, NOW()),
            NOW() + INTERVAL '3 days',
            FALSE,
            NOW(),
            NOW()
        );

        seq_num := seq_num + 1;
        RAISE NOTICE 'Created approval for Vendor: %', vendor_record.name;
    END LOOP;

    -- Insert pending Sales Channels
    FOR vendor_record IN
        SELECT id, code, name, created_at
        FROM sales_channels
        WHERE status IN ('PENDING_SETUP', 'INACTIVE')
        AND id NOT IN (SELECT entity_id FROM approval_requests WHERE entity_type = 'SALES_CHANNEL')
    LOOP
        INSERT INTO approval_requests (
            id, request_number, entity_type, entity_id, entity_number,
            amount, approval_level, status, priority, title, description,
            requested_by, requested_at, due_date, is_overdue, created_at, updated_at
        ) VALUES (
            gen_random_uuid(),
            today_prefix || '-' || LPAD(seq_num::TEXT, 4, '0'),
            'SALES_CHANNEL',
            vendor_record.id,
            vendor_record.code,
            0,  -- No amount for channels
            'LEVEL_1',  -- Default to Level 1
            'PENDING',
            5,
            'Sales Channel Setup: ' || vendor_record.name,
            'New sales channel setup approval',
            default_user_id,
            COALESCE(vendor_record.created_at, NOW()),
            NOW() + INTERVAL '3 days',
            FALSE,
            NOW(),
            NOW()
        );

        seq_num := seq_num + 1;
        RAISE NOTICE 'Created approval for Sales Channel: %', vendor_record.name;
    END LOOP;

    RAISE NOTICE 'Sync completed. Total approvals created: %', seq_num - 1;
END $$;

-- Verify the results
SELECT
    request_number,
    entity_type,
    entity_number,
    title,
    amount,
    approval_level,
    status,
    requested_at
FROM approval_requests
WHERE status = 'PENDING'
ORDER BY created_at DESC;
