-- Complete Supabase Schema Fix for Aquapurite ERP
-- Run this in Supabase SQL Editor

-- Step 1: Drop existing tables (in correct order due to foreign keys)
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS user_roles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS regions CASCADE;

-- Step 2: Create ENUM types
DROP TYPE IF EXISTS rolelevel CASCADE;
CREATE TYPE rolelevel AS ENUM ('SUPER_ADMIN', 'DIRECTOR', 'HEAD', 'MANAGER', 'EXECUTIVE');

DROP TYPE IF EXISTS regiontype CASCADE;
CREATE TYPE regiontype AS ENUM ('COUNTRY', 'ZONE', 'STATE', 'DISTRICT', 'CITY', 'AREA');

-- Step 3: Create regions table
CREATE TABLE regions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    type regiontype NOT NULL DEFAULT 'STATE',
    parent_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Step 4: Create roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    level rolelevel NOT NULL DEFAULT 'EXECUTIVE',
    department VARCHAR(50),
    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Step 5: Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),
    employee_code VARCHAR(50) UNIQUE,
    department VARCHAR(100),
    designation VARCHAR(100),
    region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP
);

-- Step 6: Create user_roles table
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, role_id)
);

-- Step 7: Create audit_logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    old_values TEXT,
    new_values TEXT,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Step 8: Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- Step 9: Insert super_admin role
INSERT INTO roles (name, code, description, level, is_system, is_active)
VALUES ('Super Admin', 'super_admin', 'Full system access', 'SUPER_ADMIN', TRUE, TRUE);

-- Step 10: Insert admin user
-- Password: Admin@123 (argon2 hash)
INSERT INTO users (email, phone, password_hash, first_name, last_name, employee_code, department, designation, is_active, is_verified)
VALUES (
    'admin@aquapurite.com',
    '+919999999999',
    '$argon2id$v=19$m=65536,t=3,p=4$P+e8N8Y4p3QuBaD0/v9fqw$JJgpoDj/OaHms6FQEPdwuHb/zTiAILgDALsm53q4LsI',
    'Super',
    'Admin',
    'EMP001',
    'Administration',
    'System Administrator',
    TRUE,
    TRUE
);

-- Step 11: Assign super_admin role to admin user
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.email = 'admin@aquapurite.com' AND r.code = 'super_admin';

-- Verify setup
SELECT 'Setup complete!' AS status;
SELECT 'Users:' AS info, COUNT(*) AS count FROM users;
SELECT 'Roles:' AS info, COUNT(*) AS count FROM roles;
SELECT 'User Roles:' AS info, COUNT(*) AS count FROM user_roles;
