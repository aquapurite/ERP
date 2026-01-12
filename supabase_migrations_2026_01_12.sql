-- ============================================================
-- SUPABASE MIGRATION SCRIPT - 2026-01-12
-- Run this in Supabase SQL Editor
-- ============================================================
-- This script includes:
-- 1. UUID column type fixes (String(36) -> UUID)
-- 2. Enum value case fixes (lowercase -> UPPERCASE)
-- 3. Float to Numeric conversion for money fields
-- ============================================================

-- ============================================================
-- PART 1: UUID TYPE CONVERSIONS (franchisee_audits table)
-- ============================================================

-- Convert VARCHAR(36) columns to UUID in franchisee_audits
ALTER TABLE franchisee_audits
    ALTER COLUMN id TYPE UUID USING id::uuid;

ALTER TABLE franchisee_audits
    ALTER COLUMN franchisee_id TYPE UUID USING franchisee_id::uuid;

ALTER TABLE franchisee_audits
    ALTER COLUMN auditor_id TYPE UUID USING auditor_id::uuid;


-- ============================================================
-- PART 2: ENUM CASE FIXES (lowercase -> UPPERCASE)
-- ============================================================

-- service_requests table
UPDATE service_requests SET service_type = UPPER(service_type)
WHERE service_type IS NOT NULL AND service_type != UPPER(service_type);

UPDATE service_requests SET priority = UPPER(priority)
WHERE priority IS NOT NULL AND priority != UPPER(priority);

UPDATE service_requests SET status = UPPER(status)
WHERE status IS NOT NULL AND status != UPPER(status);

UPDATE service_requests SET source = UPPER(source)
WHERE source IS NOT NULL AND source != UPPER(source);

-- warehouses table
UPDATE warehouses SET warehouse_type = UPPER(warehouse_type)
WHERE warehouse_type IS NOT NULL AND warehouse_type != UPPER(warehouse_type);

-- stock_items table
UPDATE stock_items SET status = UPPER(status)
WHERE status IS NOT NULL AND status != UPPER(status);

-- stock_movements table
UPDATE stock_movements SET movement_type = UPPER(movement_type)
WHERE movement_type IS NOT NULL AND movement_type != UPPER(movement_type);

-- po_delivery_schedules table
UPDATE po_delivery_schedules SET status = UPPER(status)
WHERE status IS NOT NULL AND status != UPPER(status);

-- po_serials table
UPDATE po_serials SET status = UPPER(status)
WHERE status IS NOT NULL AND status != UPPER(status);

-- installations table
UPDATE installations SET status = UPPER(status)
WHERE status IS NOT NULL AND status != UPPER(status);

-- amc_contracts table
UPDATE amc_contracts SET amc_type = UPPER(amc_type)
WHERE amc_type IS NOT NULL AND amc_type != UPPER(amc_type);

UPDATE amc_contracts SET status = UPPER(status)
WHERE status IS NOT NULL AND status != UPPER(status);

-- amc_templates table (if exists)
UPDATE amc_templates SET amc_type = UPPER(amc_type)
WHERE amc_type IS NOT NULL AND amc_type != UPPER(amc_type);

-- stock_transfers table
UPDATE stock_transfers SET status = UPPER(status)
WHERE status IS NOT NULL AND status != UPPER(status);

UPDATE stock_transfers SET transfer_type = UPPER(transfer_type)
WHERE transfer_type IS NOT NULL AND transfer_type != UPPER(transfer_type);

-- stock_adjustments table
UPDATE stock_adjustments SET adjustment_type = UPPER(adjustment_type)
WHERE adjustment_type IS NOT NULL AND adjustment_type != UPPER(adjustment_type);

UPDATE stock_adjustments SET status = UPPER(status)
WHERE status IS NOT NULL AND status != UPPER(status);

-- technicians table
UPDATE technicians SET status = UPPER(status)
WHERE status IS NOT NULL AND status != UPPER(status);

UPDATE technicians SET technician_type = UPPER(technician_type)
WHERE technician_type IS NOT NULL AND technician_type != UPPER(technician_type);

UPDATE technicians SET skill_level = UPPER(skill_level)
WHERE skill_level IS NOT NULL AND skill_level != UPPER(skill_level);


-- ============================================================
-- PART 3: FLOAT TO NUMERIC CONVERSIONS (Money Fields)
-- ============================================================

-- stock_items table
ALTER TABLE stock_items
    ALTER COLUMN purchase_price TYPE NUMERIC(12,2) USING purchase_price::numeric(12,2);
ALTER TABLE stock_items
    ALTER COLUMN landed_cost TYPE NUMERIC(12,2) USING landed_cost::numeric(12,2);

-- service_requests table
ALTER TABLE service_requests
    ALTER COLUMN total_parts_cost TYPE NUMERIC(12,2) USING total_parts_cost::numeric(12,2);
ALTER TABLE service_requests
    ALTER COLUMN labor_charges TYPE NUMERIC(12,2) USING labor_charges::numeric(12,2);
ALTER TABLE service_requests
    ALTER COLUMN service_charges TYPE NUMERIC(12,2) USING service_charges::numeric(12,2);
ALTER TABLE service_requests
    ALTER COLUMN travel_charges TYPE NUMERIC(12,2) USING travel_charges::numeric(12,2);
ALTER TABLE service_requests
    ALTER COLUMN total_charges TYPE NUMERIC(12,2) USING total_charges::numeric(12,2);
ALTER TABLE service_requests
    ALTER COLUMN payment_collected TYPE NUMERIC(12,2) USING payment_collected::numeric(12,2);

-- warranty_claims table
ALTER TABLE warranty_claims
    ALTER COLUMN refund_amount TYPE NUMERIC(12,2) USING refund_amount::numeric(12,2);
ALTER TABLE warranty_claims
    ALTER COLUMN parts_cost TYPE NUMERIC(12,2) USING parts_cost::numeric(12,2);
ALTER TABLE warranty_claims
    ALTER COLUMN labor_cost TYPE NUMERIC(12,2) USING labor_cost::numeric(12,2);
ALTER TABLE warranty_claims
    ALTER COLUMN total_cost TYPE NUMERIC(12,2) USING total_cost::numeric(12,2);

-- stock_adjustments table
ALTER TABLE stock_adjustments
    ALTER COLUMN total_value_impact TYPE NUMERIC(14,2) USING total_value_impact::numeric(14,2);

-- stock_adjustment_items table
ALTER TABLE stock_adjustment_items
    ALTER COLUMN unit_cost TYPE NUMERIC(12,2) USING unit_cost::numeric(12,2);
ALTER TABLE stock_adjustment_items
    ALTER COLUMN value_impact TYPE NUMERIC(14,2) USING value_impact::numeric(14,2);

-- cycle_counts table (if exists)
ALTER TABLE cycle_counts
    ALTER COLUMN total_variance_value TYPE NUMERIC(14,2) USING total_variance_value::numeric(14,2);

-- amc_contracts table
ALTER TABLE amc_contracts
    ALTER COLUMN base_price TYPE NUMERIC(12,2) USING base_price::numeric(12,2);
ALTER TABLE amc_contracts
    ALTER COLUMN tax_amount TYPE NUMERIC(12,2) USING tax_amount::numeric(12,2);
ALTER TABLE amc_contracts
    ALTER COLUMN discount_amount TYPE NUMERIC(12,2) USING discount_amount::numeric(12,2);
ALTER TABLE amc_contracts
    ALTER COLUMN total_amount TYPE NUMERIC(12,2) USING total_amount::numeric(12,2);
ALTER TABLE amc_contracts
    ALTER COLUMN discount_on_parts TYPE NUMERIC(5,2) USING discount_on_parts::numeric(5,2);

-- amc_templates table (if exists)
ALTER TABLE amc_templates
    ALTER COLUMN base_price TYPE NUMERIC(12,2) USING base_price::numeric(12,2);
ALTER TABLE amc_templates
    ALTER COLUMN tax_rate TYPE NUMERIC(5,2) USING tax_rate::numeric(5,2);
ALTER TABLE amc_templates
    ALTER COLUMN discount_on_parts TYPE NUMERIC(5,2) USING discount_on_parts::numeric(5,2);

-- stock_transfers table
ALTER TABLE stock_transfers
    ALTER COLUMN total_value TYPE NUMERIC(14,2) USING total_value::numeric(14,2);

-- stock_transfer_items table
ALTER TABLE stock_transfer_items
    ALTER COLUMN unit_cost TYPE NUMERIC(12,2) USING unit_cost::numeric(12,2);
ALTER TABLE stock_transfer_items
    ALTER COLUMN total_cost TYPE NUMERIC(14,2) USING total_cost::numeric(14,2);


-- ============================================================
-- VERIFICATION QUERIES (Run these to verify changes)
-- ============================================================

-- Check enum values are UPPERCASE
-- SELECT DISTINCT status FROM service_requests LIMIT 10;
-- SELECT DISTINCT warehouse_type FROM warehouses LIMIT 10;
-- SELECT DISTINCT status FROM stock_items LIMIT 10;

-- Check column types
-- SELECT column_name, data_type, numeric_precision, numeric_scale
-- FROM information_schema.columns
-- WHERE table_name = 'stock_items' AND column_name IN ('purchase_price', 'landed_cost');

-- ============================================================
-- END OF MIGRATION SCRIPT
-- ============================================================
