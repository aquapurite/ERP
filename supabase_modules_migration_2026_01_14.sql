-- ============================================================
-- SUPABASE MIGRATION SCRIPT - 2026-01-14
-- New Modules: HR, Performance, Fixed Assets, Notifications
-- Run this in Supabase SQL Editor
-- ============================================================

-- ============================================================
-- PART 1: ENUM TYPES
-- ============================================================

-- HR Enums
DO $$ BEGIN
    CREATE TYPE employmenttype AS ENUM ('FULL_TIME', 'PART_TIME', 'CONTRACT', 'INTERN', 'CONSULTANT');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE employeestatus AS ENUM ('ACTIVE', 'ON_NOTICE', 'ON_LEAVE', 'SUSPENDED', 'RESIGNED', 'TERMINATED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE leavetype AS ENUM ('CASUAL', 'SICK', 'EARNED', 'MATERNITY', 'PATERNITY', 'COMPENSATORY', 'UNPAID');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE leavestatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE attendancestatus AS ENUM ('PRESENT', 'ABSENT', 'HALF_DAY', 'ON_LEAVE', 'HOLIDAY', 'WEEKEND');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE payrollstatus AS ENUM ('DRAFT', 'PROCESSING', 'PROCESSED', 'APPROVED', 'PAID');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE gender AS ENUM ('MALE', 'FEMALE', 'OTHER');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE maritalstatus AS ENUM ('SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Performance Enums
DO $$ BEGIN
    CREATE TYPE appraisalcyclestatus AS ENUM ('DRAFT', 'ACTIVE', 'CLOSED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE goalstatus AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE appraisalstatus AS ENUM ('NOT_STARTED', 'SELF_REVIEW', 'MANAGER_REVIEW', 'HR_REVIEW', 'COMPLETED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Fixed Assets Enums
DO $$ BEGIN
    CREATE TYPE depreciationmethod AS ENUM ('SLM', 'WDV');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE assetstatus AS ENUM ('ACTIVE', 'UNDER_MAINTENANCE', 'DISPOSED', 'WRITTEN_OFF', 'TRANSFERRED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE assettransferstatus AS ENUM ('PENDING', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE maintenancestatus AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Notification Enums
DO $$ BEGIN
    CREATE TYPE notificationtype AS ENUM (
        'SYSTEM', 'ALERT', 'ANNOUNCEMENT',
        'ORDER_CREATED', 'ORDER_CONFIRMED', 'ORDER_SHIPPED', 'ORDER_DELIVERED', 'ORDER_CANCELLED',
        'LOW_STOCK', 'OUT_OF_STOCK', 'STOCK_RECEIVED',
        'APPROVAL_PENDING', 'APPROVAL_APPROVED', 'APPROVAL_REJECTED',
        'LEAVE_REQUEST', 'LEAVE_APPROVED', 'LEAVE_REJECTED', 'PAYSLIP_GENERATED', 'APPRAISAL_DUE',
        'PAYMENT_RECEIVED', 'PAYMENT_DUE', 'INVOICE_GENERATED',
        'SERVICE_ASSIGNED', 'SERVICE_COMPLETED', 'WARRANTY_EXPIRING',
        'ASSET_MAINTENANCE_DUE', 'ASSET_TRANSFER_PENDING',
        'TASK_ASSIGNED', 'REMINDER', 'MENTION'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE notificationpriority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'URGENT');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE notificationchannel AS ENUM ('IN_APP', 'EMAIL', 'SMS', 'PUSH', 'WEBHOOK');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ============================================================
-- PART 2: HR TABLES
-- ============================================================

-- Departments table
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    head_id UUID REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code);
CREATE INDEX IF NOT EXISTS idx_departments_parent ON departments(parent_id);

-- Employees table
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_code VARCHAR(20) UNIQUE NOT NULL,
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Personal Info
    date_of_birth DATE,
    gender gender,
    blood_group VARCHAR(5),
    marital_status maritalstatus,
    nationality VARCHAR(50) DEFAULT 'Indian',

    -- Personal Contact
    personal_email VARCHAR(255),
    personal_phone VARCHAR(20),

    -- Emergency Contact
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relation VARCHAR(50),

    -- Address
    current_address JSONB,
    permanent_address JSONB,

    -- Employment Details
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    designation VARCHAR(100),
    employment_type employmenttype DEFAULT 'FULL_TIME',
    status employeestatus DEFAULT 'ACTIVE',

    -- Employment Dates
    joining_date DATE NOT NULL,
    confirmation_date DATE,
    resignation_date DATE,
    last_working_date DATE,

    -- Reporting
    reporting_manager_id UUID REFERENCES employees(id) ON DELETE SET NULL,

    -- Indian Compliance Documents
    pan_number VARCHAR(10),
    aadhaar_number VARCHAR(12),
    uan_number VARCHAR(12),
    esic_number VARCHAR(17),

    -- Bank Details
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(20),
    bank_ifsc_code VARCHAR(11),

    -- Other
    profile_photo_url VARCHAR(500),
    documents JSONB,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_employees_code ON employees(employee_code);
CREATE INDEX IF NOT EXISTS idx_employees_user ON employees(user_id);
CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_employees_status ON employees(status);
CREATE INDEX IF NOT EXISTS idx_employees_manager ON employees(reporting_manager_id);

-- Salary Structures table
CREATE TABLE IF NOT EXISTS salary_structures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID UNIQUE NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    effective_from DATE NOT NULL,

    -- CTC Breakdown (Monthly)
    basic_salary DECIMAL(12,2) NOT NULL,
    hra DECIMAL(12,2) DEFAULT 0,
    conveyance DECIMAL(12,2) DEFAULT 0,
    medical_allowance DECIMAL(12,2) DEFAULT 0,
    special_allowance DECIMAL(12,2) DEFAULT 0,
    other_allowances DECIMAL(12,2) DEFAULT 0,
    gross_salary DECIMAL(12,2) NOT NULL,

    -- Employer Contributions
    employer_pf DECIMAL(12,2) DEFAULT 0,
    employer_esic DECIMAL(12,2) DEFAULT 0,

    -- CTC
    annual_ctc DECIMAL(14,2) NOT NULL,
    monthly_ctc DECIMAL(12,2) NOT NULL,

    -- Statutory Applicability
    pf_applicable BOOLEAN DEFAULT TRUE,
    esic_applicable BOOLEAN DEFAULT FALSE,
    pt_applicable BOOLEAN DEFAULT TRUE,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_salary_structures_employee ON salary_structures(employee_id);

-- Attendance table
CREATE TABLE IF NOT EXISTS attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,

    check_in TIMESTAMP,
    check_out TIMESTAMP,
    work_hours DECIMAL(4,2),

    status attendancestatus NOT NULL,

    is_late BOOLEAN DEFAULT FALSE,
    late_minutes INTEGER DEFAULT 0,
    is_early_out BOOLEAN DEFAULT FALSE,
    early_out_minutes INTEGER DEFAULT 0,

    location_in JSONB,
    location_out JSONB,

    remarks TEXT,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(employee_id, attendance_date)
);

CREATE INDEX IF NOT EXISTS idx_attendance_employee ON attendance(employee_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status);

-- Leave Balances table
CREATE TABLE IF NOT EXISTS leave_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    leave_type leavetype NOT NULL,
    financial_year VARCHAR(10) NOT NULL,

    opening_balance DECIMAL(4,1) DEFAULT 0,
    accrued DECIMAL(4,1) DEFAULT 0,
    taken DECIMAL(4,1) DEFAULT 0,
    adjusted DECIMAL(4,1) DEFAULT 0,
    closing_balance DECIMAL(4,1) DEFAULT 0,
    carry_forward_limit DECIMAL(4,1) DEFAULT 0,

    UNIQUE(employee_id, leave_type, financial_year)
);

CREATE INDEX IF NOT EXISTS idx_leave_balances_employee ON leave_balances(employee_id);

-- Leave Requests table
CREATE TABLE IF NOT EXISTS leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    leave_type leavetype NOT NULL,

    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    days DECIMAL(4,1) NOT NULL,
    is_half_day BOOLEAN DEFAULT FALSE,
    half_day_type VARCHAR(15),

    reason TEXT,
    status leavestatus DEFAULT 'PENDING',

    applied_on TIMESTAMP DEFAULT NOW(),
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_on TIMESTAMP,
    rejection_reason TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leave_requests_employee ON leave_requests(employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status);

-- Payrolls table
CREATE TABLE IF NOT EXISTS payrolls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_month DATE NOT NULL,
    financial_year VARCHAR(10) NOT NULL,

    status payrollstatus DEFAULT 'DRAFT',

    total_employees INTEGER DEFAULT 0,
    total_gross DECIMAL(14,2) DEFAULT 0,
    total_deductions DECIMAL(14,2) DEFAULT 0,
    total_net DECIMAL(14,2) DEFAULT 0,

    processed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    processed_at TIMESTAMP,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payrolls_month ON payrolls(payroll_month);
CREATE INDEX IF NOT EXISTS idx_payrolls_status ON payrolls(status);

-- Payslips table
CREATE TABLE IF NOT EXISTS payslips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_id UUID NOT NULL REFERENCES payrolls(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    payslip_number VARCHAR(30) UNIQUE NOT NULL,

    -- Attendance Summary
    working_days INTEGER NOT NULL,
    days_present DECIMAL(4,1) NOT NULL,
    days_absent DECIMAL(4,1) DEFAULT 0,
    leaves_taken DECIMAL(4,1) DEFAULT 0,

    -- Earnings
    basic_earned DECIMAL(12,2) DEFAULT 0,
    hra_earned DECIMAL(12,2) DEFAULT 0,
    conveyance_earned DECIMAL(12,2) DEFAULT 0,
    medical_earned DECIMAL(12,2) DEFAULT 0,
    special_earned DECIMAL(12,2) DEFAULT 0,
    other_earned DECIMAL(12,2) DEFAULT 0,
    overtime_amount DECIMAL(12,2) DEFAULT 0,
    arrears DECIMAL(12,2) DEFAULT 0,
    bonus DECIMAL(12,2) DEFAULT 0,
    gross_earnings DECIMAL(12,2) NOT NULL,

    -- Deductions - Statutory
    employee_pf DECIMAL(12,2) DEFAULT 0,
    employer_pf DECIMAL(12,2) DEFAULT 0,
    employee_esic DECIMAL(12,2) DEFAULT 0,
    employer_esic DECIMAL(12,2) DEFAULT 0,
    professional_tax DECIMAL(12,2) DEFAULT 0,
    tds DECIMAL(12,2) DEFAULT 0,

    -- Deductions - Other
    loan_deduction DECIMAL(12,2) DEFAULT 0,
    advance_deduction DECIMAL(12,2) DEFAULT 0,
    other_deductions DECIMAL(12,2) DEFAULT 0,
    total_deductions DECIMAL(12,2) NOT NULL,

    -- Net Pay
    net_salary DECIMAL(12,2) NOT NULL,

    -- Payment
    payment_mode VARCHAR(20),
    payment_date DATE,
    payment_reference VARCHAR(50),
    payslip_pdf_url VARCHAR(500),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payslips_payroll ON payslips(payroll_id);
CREATE INDEX IF NOT EXISTS idx_payslips_employee ON payslips(employee_id);


-- ============================================================
-- PART 3: PERFORMANCE MANAGEMENT TABLES
-- ============================================================

-- Appraisal Cycles table
CREATE TABLE IF NOT EXISTS appraisal_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    financial_year VARCHAR(10) NOT NULL,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    review_start_date DATE,
    review_end_date DATE,

    status appraisalcyclestatus DEFAULT 'DRAFT',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_appraisal_cycles_year ON appraisal_cycles(financial_year);
CREATE INDEX IF NOT EXISTS idx_appraisal_cycles_status ON appraisal_cycles(status);

-- KPIs table
CREATE TABLE IF NOT EXISTS kpis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,

    unit_of_measure VARCHAR(50) NOT NULL,
    target_value DECIMAL(12,2),
    weightage DECIMAL(5,2) DEFAULT 0,

    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    designation VARCHAR(100),

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kpis_category ON kpis(category);
CREATE INDEX IF NOT EXISTS idx_kpis_department ON kpis(department_id);

-- Goals table
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    cycle_id UUID NOT NULL REFERENCES appraisal_cycles(id) ON DELETE CASCADE,

    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,

    kpi_id UUID REFERENCES kpis(id) ON DELETE SET NULL,

    target_value DECIMAL(12,2),
    achieved_value DECIMAL(12,2),
    unit_of_measure VARCHAR(50),
    weightage DECIMAL(5,2) DEFAULT 0,

    start_date DATE NOT NULL,
    due_date DATE NOT NULL,
    completed_date DATE,

    status goalstatus DEFAULT 'PENDING',
    completion_percentage INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_goals_employee ON goals(employee_id);
CREATE INDEX IF NOT EXISTS idx_goals_cycle ON goals(cycle_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);

-- Appraisals table
CREATE TABLE IF NOT EXISTS appraisals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    cycle_id UUID NOT NULL REFERENCES appraisal_cycles(id) ON DELETE CASCADE,

    status appraisalstatus DEFAULT 'NOT_STARTED',

    -- Self Review
    self_rating DECIMAL(3,1),
    self_comments TEXT,
    self_review_date TIMESTAMP,

    -- Manager Review
    manager_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    manager_rating DECIMAL(3,1),
    manager_comments TEXT,
    manager_review_date TIMESTAMP,

    -- Final Rating
    final_rating DECIMAL(3,1),
    performance_band VARCHAR(20),

    -- Goals Achievement
    goals_achieved INTEGER DEFAULT 0,
    goals_total INTEGER DEFAULT 0,
    overall_goal_score DECIMAL(5,2),

    -- Development
    strengths TEXT,
    areas_of_improvement TEXT,
    development_plan TEXT,

    -- Recommendations
    recommended_for_promotion BOOLEAN DEFAULT FALSE,
    recommended_increment_percentage DECIMAL(5,2),

    -- HR Review
    hr_reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    hr_review_date TIMESTAMP,
    hr_comments TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(employee_id, cycle_id)
);

CREATE INDEX IF NOT EXISTS idx_appraisals_employee ON appraisals(employee_id);
CREATE INDEX IF NOT EXISTS idx_appraisals_cycle ON appraisals(cycle_id);
CREATE INDEX IF NOT EXISTS idx_appraisals_status ON appraisals(status);

-- Performance Feedback table
CREATE TABLE IF NOT EXISTS performance_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    given_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    feedback_type VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,

    is_private BOOLEAN DEFAULT FALSE,
    goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_performance_feedback_employee ON performance_feedback(employee_id);


-- ============================================================
-- PART 4: FIXED ASSETS TABLES
-- ============================================================

-- Asset Categories table
CREATE TABLE IF NOT EXISTS asset_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,

    depreciation_method depreciationmethod DEFAULT 'SLM',
    depreciation_rate DECIMAL(5,2) NOT NULL,
    useful_life_years INTEGER NOT NULL,

    asset_account_id UUID,
    depreciation_account_id UUID,
    expense_account_id UUID,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_asset_categories_code ON asset_categories(code);

-- Assets table
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id UUID NOT NULL REFERENCES asset_categories(id) ON DELETE RESTRICT,

    -- Serial/Model Info
    serial_number VARCHAR(100),
    model_number VARCHAR(100),
    manufacturer VARCHAR(100),

    -- Location
    warehouse_id UUID,
    location_details VARCHAR(200),
    custodian_employee_id UUID,
    department_id UUID,

    -- Purchase Details
    purchase_date DATE NOT NULL,
    purchase_price DECIMAL(14,2) NOT NULL,
    purchase_invoice_no VARCHAR(50),
    vendor_id UUID,
    po_number VARCHAR(50),

    -- Capitalization
    capitalization_date DATE NOT NULL,
    installation_cost DECIMAL(12,2) DEFAULT 0,
    other_costs DECIMAL(12,2) DEFAULT 0,
    capitalized_value DECIMAL(14,2) NOT NULL,

    -- Depreciation (overrides)
    depreciation_method depreciationmethod,
    depreciation_rate DECIMAL(5,2),
    useful_life_years INTEGER,
    salvage_value DECIMAL(12,2) DEFAULT 0,

    -- Current Values
    accumulated_depreciation DECIMAL(14,2) DEFAULT 0,
    current_book_value DECIMAL(14,2) NOT NULL,
    last_depreciation_date DATE,

    -- Warranty
    warranty_start_date DATE,
    warranty_end_date DATE,
    warranty_details TEXT,

    -- Insurance
    insured BOOLEAN DEFAULT FALSE,
    insurance_policy_no VARCHAR(50),
    insurance_value DECIMAL(14,2),
    insurance_expiry DATE,

    -- Status
    status assetstatus DEFAULT 'ACTIVE',

    -- Disposal
    disposal_date DATE,
    disposal_price DECIMAL(14,2),
    disposal_reason TEXT,
    gain_loss_on_disposal DECIMAL(14,2),

    -- Documents
    documents JSONB,
    images JSONB,
    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assets_code ON assets(asset_code);
CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category_id);
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
CREATE INDEX IF NOT EXISTS idx_assets_warehouse ON assets(warehouse_id);

-- Depreciation Entries table
CREATE TABLE IF NOT EXISTS depreciation_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,

    period_date DATE NOT NULL,
    financial_year VARCHAR(10) NOT NULL,

    opening_book_value DECIMAL(14,2) NOT NULL,
    depreciation_method depreciationmethod NOT NULL,
    depreciation_rate DECIMAL(5,2) NOT NULL,
    depreciation_amount DECIMAL(12,2) NOT NULL,
    closing_book_value DECIMAL(14,2) NOT NULL,
    accumulated_depreciation DECIMAL(14,2) NOT NULL,

    journal_entry_id UUID,
    is_posted BOOLEAN DEFAULT FALSE,

    processed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    processed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(asset_id, period_date)
);

CREATE INDEX IF NOT EXISTS idx_depreciation_entries_asset ON depreciation_entries(asset_id);
CREATE INDEX IF NOT EXISTS idx_depreciation_entries_period ON depreciation_entries(period_date);
CREATE INDEX IF NOT EXISTS idx_depreciation_entries_fy ON depreciation_entries(financial_year);

-- Asset Transfers table
CREATE TABLE IF NOT EXISTS asset_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    transfer_number VARCHAR(30) UNIQUE NOT NULL,

    -- From Location
    from_warehouse_id UUID,
    from_department_id UUID,
    from_custodian_id UUID,
    from_location_details VARCHAR(200),

    -- To Location
    to_warehouse_id UUID,
    to_department_id UUID,
    to_custodian_id UUID,
    to_location_details VARCHAR(200),

    transfer_date DATE NOT NULL,
    reason TEXT,

    status assettransferstatus DEFAULT 'PENDING',

    requested_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP,
    completed_at TIMESTAMP,
    received_by UUID REFERENCES users(id) ON DELETE SET NULL,

    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_asset_transfers_asset ON asset_transfers(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_transfers_status ON asset_transfers(status);

-- Asset Maintenance table
CREATE TABLE IF NOT EXISTS asset_maintenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    maintenance_number VARCHAR(30) UNIQUE NOT NULL,

    maintenance_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,

    scheduled_date DATE NOT NULL,
    started_date DATE,
    completed_date DATE,

    estimated_cost DECIMAL(12,2) DEFAULT 0,
    actual_cost DECIMAL(12,2) DEFAULT 0,

    vendor_id UUID,
    vendor_invoice_no VARCHAR(50),

    status maintenancestatus DEFAULT 'SCHEDULED',

    findings TEXT,
    parts_replaced TEXT,
    recommendations TEXT,

    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    documents JSONB,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_asset_maintenance_asset ON asset_maintenance(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_maintenance_status ON asset_maintenance(status);


-- ============================================================
-- PART 5: NOTIFICATIONS TABLES
-- ============================================================

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    notification_type notificationtype NOT NULL,
    priority notificationpriority DEFAULT 'MEDIUM',

    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,

    action_url VARCHAR(500),
    action_label VARCHAR(100),

    entity_type VARCHAR(50),
    entity_id UUID,

    extra_data JSONB DEFAULT '{}',

    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,

    channels JSONB DEFAULT '[]',
    delivered_at JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_user_type ON notifications(user_id, notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);

-- Notification Preferences table
CREATE TABLE IF NOT EXISTS notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    push_enabled BOOLEAN DEFAULT TRUE,
    in_app_enabled BOOLEAN DEFAULT TRUE,

    type_preferences JSONB DEFAULT '{}',

    quiet_hours_enabled BOOLEAN DEFAULT FALSE,
    quiet_hours_start VARCHAR(5),
    quiet_hours_end VARCHAR(5),

    email_digest_enabled BOOLEAN DEFAULT FALSE,
    email_digest_frequency VARCHAR(20) DEFAULT 'DAILY',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_preferences_user ON notification_preferences(user_id);

-- Notification Templates table
CREATE TABLE IF NOT EXISTS notification_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_type notificationtype UNIQUE NOT NULL,

    title_template VARCHAR(200) NOT NULL,
    message_template TEXT NOT NULL,

    email_subject_template VARCHAR(200),
    email_body_template TEXT,
    sms_template VARCHAR(500),

    default_channels JSONB DEFAULT '["IN_APP"]',
    default_priority notificationpriority DEFAULT 'MEDIUM',

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Announcements table
CREATE TABLE IF NOT EXISTS announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,

    announcement_type VARCHAR(20) DEFAULT 'INFO',

    action_url VARCHAR(500),
    action_label VARCHAR(100),

    target_roles JSONB DEFAULT '[]',
    target_departments JSONB DEFAULT '[]',

    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,

    is_dismissible BOOLEAN DEFAULT TRUE,
    show_on_dashboard BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,

    created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_announcements_active ON announcements(is_active);
CREATE INDEX IF NOT EXISTS idx_announcements_dates ON announcements(start_date, end_date);

-- Announcement Dismissals table
CREATE TABLE IF NOT EXISTS announcement_dismissals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    announcement_id UUID NOT NULL REFERENCES announcements(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    dismissed_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(announcement_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_announcement_dismissals_announcement ON announcement_dismissals(announcement_id);
CREATE INDEX IF NOT EXISTS idx_announcement_dismissals_user ON announcement_dismissals(user_id);


-- ============================================================
-- PART 6: INVENTORY SUMMARY TABLE (for stock tracking)
-- ============================================================

-- Create inventory_summary table (matches the model)
CREATE TABLE IF NOT EXISTS inventory_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    product_id UUID NOT NULL REFERENCES products(id),
    variant_id UUID REFERENCES product_variants(id),

    -- Stock levels
    total_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    allocated_quantity INTEGER DEFAULT 0,
    damaged_quantity INTEGER DEFAULT 0,
    in_transit_quantity INTEGER DEFAULT 0,

    -- Thresholds
    reorder_level INTEGER DEFAULT 10,
    minimum_stock INTEGER DEFAULT 5,
    maximum_stock INTEGER DEFAULT 1000,

    -- Valuation
    average_cost FLOAT DEFAULT 0,
    total_value FLOAT DEFAULT 0,

    -- Last activity
    last_stock_in_date TIMESTAMP,
    last_stock_out_date TIMESTAMP,
    last_audit_date TIMESTAMP,

    UNIQUE(warehouse_id, product_id, variant_id)
);

CREATE INDEX IF NOT EXISTS idx_inventory_summary_warehouse ON inventory_summary(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_inventory_summary_product ON inventory_summary(product_id);

-- Create a convenience view named 'inventory' for backward compatibility
CREATE OR REPLACE VIEW inventory AS
SELECT
    product_id,
    (SELECT sku FROM products WHERE id = product_id) as sku,
    available_quantity as quantity_available,
    reserved_quantity,
    warehouse_id,
    TRUE as is_active
FROM inventory_summary;


-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================

SELECT 'Migration completed successfully! Created tables for HR, Performance, Fixed Assets, and Notifications modules.' AS result;
