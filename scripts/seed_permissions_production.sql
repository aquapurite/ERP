-- Seed Modules and Permissions for Production
-- Run this in Supabase SQL Editor

-- ==================== MODULES ====================
INSERT INTO modules (id, name, code, description, icon, sort_order, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'Dashboard', 'dashboard', 'Main dashboard and analytics overview', 'dashboard', 1, true, NOW(), NOW()),
    (gen_random_uuid(), 'Products', 'products', 'Product catalog management', 'inventory', 2, true, NOW(), NOW()),
    (gen_random_uuid(), 'Orders', 'orders', 'Order management and processing', 'shopping_cart', 3, true, NOW(), NOW()),
    (gen_random_uuid(), 'Inventory', 'inventory', 'Inventory and warehouse management', 'warehouse', 4, true, NOW(), NOW()),
    (gen_random_uuid(), 'Service', 'service', 'Service requests and AMC management', 'build', 5, true, NOW(), NOW()),
    (gen_random_uuid(), 'CRM', 'crm', 'Customer relationship management', 'people', 6, true, NOW(), NOW()),
    (gen_random_uuid(), 'Complaints', 'complaints', 'Customer complaints and tickets', 'report_problem', 7, true, NOW(), NOW()),
    (gen_random_uuid(), 'Vendors', 'vendors', 'Vendor and supplier management', 'store', 8, true, NOW(), NOW()),
    (gen_random_uuid(), 'Logistics', 'logistics', 'Delivery and logistics management', 'local_shipping', 9, true, NOW(), NOW()),
    (gen_random_uuid(), 'Procurement', 'procurement', 'Purchase orders and procurement', 'receipt', 10, true, NOW(), NOW()),
    (gen_random_uuid(), 'Finance', 'finance', 'Financial management and accounting', 'account_balance', 11, true, NOW(), NOW()),
    (gen_random_uuid(), 'HR', 'hr', 'Human resources management', 'badge', 12, true, NOW(), NOW()),
    (gen_random_uuid(), 'Marketing', 'marketing', 'Marketing campaigns and promotions', 'campaign', 13, true, NOW(), NOW()),
    (gen_random_uuid(), 'Reports', 'reports', 'Reports and analytics', 'assessment', 14, true, NOW(), NOW()),
    (gen_random_uuid(), 'Notifications', 'notifications', 'System notifications', 'notifications', 15, true, NOW(), NOW()),
    (gen_random_uuid(), 'Settings', 'settings', 'System configuration', 'settings', 16, true, NOW(), NOW()),
    (gen_random_uuid(), 'Access Control', 'access_control', 'User roles and permissions', 'security', 17, true, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ==================== PERMISSIONS ====================
-- Insert permissions linked to modules

-- Dashboard
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Dashboard', 'dashboard:view', 'View dashboard and analytics', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'dashboard'
ON CONFLICT (code) DO NOTHING;

-- Products
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Products', 'products:view', 'View product catalog', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'products'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Create Products', 'products:create', 'Add new products', 'create', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'products'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Update Products', 'products:update', 'Modify product details', 'update', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'products'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Delete Products', 'products:delete', 'Remove products', 'delete', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'products'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Read Products', 'products:read', 'Read product details', 'read', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'products'
ON CONFLICT (code) DO NOTHING;

-- Orders
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Orders', 'orders:view', 'View order list', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'orders'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Create Orders', 'orders:create', 'Create new orders', 'create', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'orders'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Update Orders', 'orders:update', 'Modify order details', 'update', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'orders'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Cancel Orders', 'orders:cancel', 'Cancel orders', 'cancel', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'orders'
ON CONFLICT (code) DO NOTHING;

-- Inventory
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Inventory', 'inventory:view', 'View inventory levels', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'inventory'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Create Inventory', 'inventory:create', 'Add inventory entries', 'create', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'inventory'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Update Inventory', 'inventory:update', 'Modify inventory', 'update', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'inventory'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Approve Inventory', 'inventory:approve', 'Approve inventory changes', 'approve', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'inventory'
ON CONFLICT (code) DO NOTHING;

-- Service
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Service', 'service:view', 'View service requests', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'service'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Create Service', 'service:create', 'Create service requests', 'create', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'service'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Update Service', 'service:update', 'Update service requests', 'update', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'service'
ON CONFLICT (code) DO NOTHING;

-- CRM
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Customers', 'crm:view', 'View customer data', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'crm'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Create Customers', 'crm:create', 'Add new customers', 'create', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'crm'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Update Customers', 'crm:update', 'Modify customer info', 'update', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'crm'
ON CONFLICT (code) DO NOTHING;

-- Vendors
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Vendors', 'vendors:view', 'View vendor list', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'vendors'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Create Vendors', 'vendors:create', 'Add new vendors', 'create', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'vendors'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Update Vendors', 'vendors:update', 'Modify vendor details', 'update', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'vendors'
ON CONFLICT (code) DO NOTHING;

-- Procurement
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Procurement', 'procurement:view', 'View purchase orders', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'procurement'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Create Procurement', 'procurement:create', 'Create purchase orders', 'create', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'procurement'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Update Procurement', 'procurement:update', 'Update purchase orders', 'update', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'procurement'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Approve Procurement', 'procurement:approve', 'Approve purchase orders', 'approve', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'procurement'
ON CONFLICT (code) DO NOTHING;

-- Finance
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Finance', 'finance:view', 'View financial data', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'finance'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Create Finance', 'finance:create', 'Create financial transactions', 'create', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'finance'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Update Finance', 'finance:update', 'Update financial records', 'update', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'finance'
ON CONFLICT (code) DO NOTHING;

-- HR
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View HR', 'hr:view', 'View employee data', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'hr'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Create HR', 'hr:create', 'Add new employees', 'create', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'hr'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Update HR', 'hr:update', 'Update employee info', 'update', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'hr'
ON CONFLICT (code) DO NOTHING;

-- Access Control
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Access Control', 'access_control:view', 'View roles and permissions', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'access_control'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Create Access Control', 'access_control:create', 'Create roles', 'create', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'access_control'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Update Access Control', 'access_control:update', 'Update roles and permissions', 'update', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'access_control'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Delete Access Control', 'access_control:delete', 'Delete roles', 'delete', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'access_control'
ON CONFLICT (code) DO NOTHING;

-- Reports
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Reports', 'reports:view', 'View reports', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'reports'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Export Reports', 'reports:export', 'Export reports', 'export', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'reports'
ON CONFLICT (code) DO NOTHING;

-- Settings
INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'View Settings', 'settings:view', 'View system settings', 'view', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'settings'
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (id, name, code, description, action, module_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), 'Update Settings', 'settings:update', 'Update system settings', 'update', m.id, true, NOW(), NOW()
FROM modules m WHERE m.code = 'settings'
ON CONFLICT (code) DO NOTHING;

-- Verify results
SELECT 'Modules created:' as info, COUNT(*) as count FROM modules;
SELECT 'Permissions created:' as info, COUNT(*) as count FROM permissions;
