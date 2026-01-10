-- =====================================================
-- FIX MISSING TABLES v2 - Safe incremental migration
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Add missing column to user_roles if needed
-- =====================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'user_roles' AND column_name = 'is_primary') THEN
        ALTER TABLE user_roles ADD COLUMN is_primary BOOLEAN DEFAULT FALSE;
    END IF;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

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

-- =====================================================
-- APPROVAL_HISTORY TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS approval_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_request_id UUID REFERENCES approval_requests(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    performed_by UUID NOT NULL,
    comments TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_approval_history_request ON approval_history(approval_request_id);

-- =====================================================
-- AUDIT_LOGS TABLE
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

-- =====================================================
-- Ensure admin has SUPER_ADMIN role (simple version)
-- =====================================================

INSERT INTO user_roles (id, user_id, role_id, assigned_at)
SELECT
    gen_random_uuid(),
    u.id,
    r.id,
    NOW()
FROM users u, roles r
WHERE u.email = 'admin@aquapurite.com'
AND r.code = 'SUPER_ADMIN'
AND NOT EXISTS (
    SELECT 1 FROM user_roles ur
    WHERE ur.user_id = u.id AND ur.role_id = r.id
);

-- Done
SELECT 'Migration completed successfully!' as result;
