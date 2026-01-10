-- =====================================================
-- FIX MISSING TABLES - Safe incremental migration
-- Run this in Supabase SQL Editor
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- ENUM TYPES (only create if not exists)
-- =====================================================

DO $$
BEGIN
    -- Approval Enums
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approvalentitytype') THEN
        CREATE TYPE approvalentitytype AS ENUM (
            'PURCHASE_ORDER', 'PURCHASE_REQUISITION', 'STOCK_TRANSFER',
            'STOCK_ADJUSTMENT', 'VENDOR_ONBOARDING', 'VENDOR_DELETION',
            'DEALER_ONBOARDING', 'FRANCHISEE_CONTRACT', 'JOURNAL_ENTRY',
            'CREDIT_NOTE', 'DEBIT_NOTE'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approvallevel') THEN
        CREATE TYPE approvallevel AS ENUM ('LEVEL_1', 'LEVEL_2', 'LEVEL_3');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approvalstatus') THEN
        CREATE TYPE approvalstatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'ESCALATED');
    END IF;
END $$;

-- =====================================================
-- USER_ROLES TABLE (if not exists)
-- =====================================================

CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    role_id UUID NOT NULL,
    assigned_by UUID,
    assigned_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_user_role UNIQUE (user_id, role_id)
);

-- Add foreign keys only if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'user_roles_user_id_fkey') THEN
        ALTER TABLE user_roles ADD CONSTRAINT user_roles_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'user_roles_role_id_fkey') THEN
        ALTER TABLE user_roles ADD CONSTRAINT user_roles_role_id_fkey
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;
    END IF;
EXCEPTION WHEN OTHERS THEN
    NULL; -- Ignore errors
END $$;

CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);

-- =====================================================
-- APPROVAL_REQUESTS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_number VARCHAR(30) UNIQUE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_number VARCHAR(50) NOT NULL,
    amount NUMERIC(14, 2) NOT NULL,
    approval_level VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    priority INTEGER DEFAULT 5,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    requested_by UUID NOT NULL,
    requested_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    current_approver_id UUID,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    approval_comments TEXT,
    rejected_by UUID,
    rejected_at TIMESTAMPTZ,
    rejection_reason TEXT,
    due_date TIMESTAMPTZ,
    is_overdue BOOLEAN DEFAULT FALSE,
    escalated_at TIMESTAMPTZ,
    escalated_to UUID,
    escalation_reason TEXT,
    extra_info JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_approval_entity ON approval_requests(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_approval_status_level ON approval_requests(status, approval_level);
CREATE INDEX IF NOT EXISTS idx_approval_request_number ON approval_requests(request_number);

-- =====================================================
-- APPROVAL_HISTORY TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS approval_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_request_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    performed_by UUID NOT NULL,
    comments TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Add foreign key only if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'approval_history_request_fkey') THEN
        ALTER TABLE approval_history ADD CONSTRAINT approval_history_request_fkey
            FOREIGN KEY (approval_request_id) REFERENCES approval_requests(id) ON DELETE CASCADE;
    END IF;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_approval_history_request ON approval_history(approval_request_id);

-- =====================================================
-- AUDIT_LOGS TABLE (commonly needed)
-- =====================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- =====================================================
-- Re-assign admin role if needed
-- =====================================================

-- Make sure admin has SUPER_ADMIN role
INSERT INTO user_roles (id, user_id, role_id, assigned_at, is_primary)
SELECT
    gen_random_uuid(),
    u.id,
    r.id,
    NOW(),
    TRUE
FROM users u, roles r
WHERE u.email = 'admin@aquapurite.com'
AND r.code = 'SUPER_ADMIN'
AND NOT EXISTS (
    SELECT 1 FROM user_roles ur
    WHERE ur.user_id = u.id AND ur.role_id = r.id
);

-- =====================================================
-- SUCCESS
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully!';
END $$;
