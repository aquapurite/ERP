-- ============================================================
-- SUPABASE MIGRATION SCRIPT v2 - 2026-01-12
-- Handles PostgreSQL ENUM types correctly
-- Run this in Supabase SQL Editor
-- ============================================================

-- ============================================================
-- PART 1: UUID TYPE CONVERSIONS (franchisee_audits table)
-- ============================================================

-- Convert VARCHAR(36) columns to UUID in franchisee_audits (if columns exist as varchar)
DO $$
BEGIN
    -- Only alter if the column is varchar type
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'franchisee_audits'
        AND column_name = 'id'
        AND data_type = 'character varying'
    ) THEN
        ALTER TABLE franchisee_audits ALTER COLUMN id TYPE UUID USING id::uuid;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'franchisee_audits'
        AND column_name = 'franchisee_id'
        AND data_type = 'character varying'
    ) THEN
        ALTER TABLE franchisee_audits ALTER COLUMN franchisee_id TYPE UUID USING franchisee_id::uuid;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'franchisee_audits'
        AND column_name = 'auditor_id'
        AND data_type = 'character varying'
    ) THEN
        ALTER TABLE franchisee_audits ALTER COLUMN auditor_id TYPE UUID USING auditor_id::uuid;
    END IF;
END $$;


-- ============================================================
-- PART 2: ENUM CASE FIXES (Recreate ENUMs with UPPERCASE)
-- ============================================================

-- Helper function to check if enum value exists
CREATE OR REPLACE FUNCTION enum_value_exists(enum_name text, value_name text)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = enum_name AND e.enumlabel = value_name
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 2.1 ServiceType Enum
-- ============================================================
DO $$
BEGIN
    -- Add uppercase values if they don't exist
    IF NOT enum_value_exists('servicetype', 'INSTALLATION') THEN
        ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'INSTALLATION';
    END IF;
    IF NOT enum_value_exists('servicetype', 'WARRANTY_REPAIR') THEN
        ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'WARRANTY_REPAIR';
    END IF;
    IF NOT enum_value_exists('servicetype', 'PAID_REPAIR') THEN
        ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'PAID_REPAIR';
    END IF;
    IF NOT enum_value_exists('servicetype', 'AMC_SERVICE') THEN
        ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'AMC_SERVICE';
    END IF;
    IF NOT enum_value_exists('servicetype', 'DEMO') THEN
        ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'DEMO';
    END IF;
    IF NOT enum_value_exists('servicetype', 'PREVENTIVE_MAINTENANCE') THEN
        ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'PREVENTIVE_MAINTENANCE';
    END IF;
    IF NOT enum_value_exists('servicetype', 'COMPLAINT') THEN
        ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'COMPLAINT';
    END IF;
    IF NOT enum_value_exists('servicetype', 'FILTER_CHANGE') THEN
        ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'FILTER_CHANGE';
    END IF;
    IF NOT enum_value_exists('servicetype', 'INSPECTION') THEN
        ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'INSPECTION';
    END IF;
    IF NOT enum_value_exists('servicetype', 'UNINSTALLATION') THEN
        ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'UNINSTALLATION';
    END IF;
EXCEPTION WHEN others THEN
    RAISE NOTICE 'ServiceType enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.2 ServicePriority Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE servicepriority ADD VALUE IF NOT EXISTS 'LOW';
    ALTER TYPE servicepriority ADD VALUE IF NOT EXISTS 'NORMAL';
    ALTER TYPE servicepriority ADD VALUE IF NOT EXISTS 'HIGH';
    ALTER TYPE servicepriority ADD VALUE IF NOT EXISTS 'URGENT';
    ALTER TYPE servicepriority ADD VALUE IF NOT EXISTS 'CRITICAL';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'ServicePriority enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.3 ServiceStatus Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'DRAFT';
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'PENDING';
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'ASSIGNED';
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'SCHEDULED';
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'EN_ROUTE';
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'IN_PROGRESS';
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'PARTS_REQUIRED';
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'ON_HOLD';
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'COMPLETED';
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'CLOSED';
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'CANCELLED';
    ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'REOPENED';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'ServiceStatus enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.4 ServiceSource Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE servicesource ADD VALUE IF NOT EXISTS 'CALL_CENTER';
    ALTER TYPE servicesource ADD VALUE IF NOT EXISTS 'WEBSITE';
    ALTER TYPE servicesource ADD VALUE IF NOT EXISTS 'MOBILE_APP';
    ALTER TYPE servicesource ADD VALUE IF NOT EXISTS 'WALK_IN';
    ALTER TYPE servicesource ADD VALUE IF NOT EXISTS 'EMAIL';
    ALTER TYPE servicesource ADD VALUE IF NOT EXISTS 'WHATSAPP';
    ALTER TYPE servicesource ADD VALUE IF NOT EXISTS 'AUTO_AMC';
    ALTER TYPE servicesource ADD VALUE IF NOT EXISTS 'REFERRAL';
    ALTER TYPE servicesource ADD VALUE IF NOT EXISTS 'SYSTEM';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'ServiceSource enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.5 WarehouseType Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE warehousetype ADD VALUE IF NOT EXISTS 'MAIN';
    ALTER TYPE warehousetype ADD VALUE IF NOT EXISTS 'REGIONAL';
    ALTER TYPE warehousetype ADD VALUE IF NOT EXISTS 'SERVICE_CENTER';
    ALTER TYPE warehousetype ADD VALUE IF NOT EXISTS 'DEALER';
    ALTER TYPE warehousetype ADD VALUE IF NOT EXISTS 'VIRTUAL';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'WarehouseType enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.6 StockItemStatus Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'AVAILABLE';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'RESERVED';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'ALLOCATED';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'PICKED';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'PACKED';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'IN_TRANSIT';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'SHIPPED';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'DAMAGED';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'DEFECTIVE';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'SOLD';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'RETURNED';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'QUARANTINE';
    ALTER TYPE stockitemstatus ADD VALUE IF NOT EXISTS 'SCRAPPED';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'StockItemStatus enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.7 StockMovementType Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE stockmovementtype ADD VALUE IF NOT EXISTS 'RECEIPT';
    ALTER TYPE stockmovementtype ADD VALUE IF NOT EXISTS 'ISSUE';
    ALTER TYPE stockmovementtype ADD VALUE IF NOT EXISTS 'TRANSFER_IN';
    ALTER TYPE stockmovementtype ADD VALUE IF NOT EXISTS 'TRANSFER_OUT';
    ALTER TYPE stockmovementtype ADD VALUE IF NOT EXISTS 'RETURN_IN';
    ALTER TYPE stockmovementtype ADD VALUE IF NOT EXISTS 'RETURN_OUT';
    ALTER TYPE stockmovementtype ADD VALUE IF NOT EXISTS 'ADJUSTMENT_PLUS';
    ALTER TYPE stockmovementtype ADD VALUE IF NOT EXISTS 'ADJUSTMENT_MINUS';
    ALTER TYPE stockmovementtype ADD VALUE IF NOT EXISTS 'DAMAGE';
    ALTER TYPE stockmovementtype ADD VALUE IF NOT EXISTS 'SCRAP';
    ALTER TYPE stockmovementtype ADD VALUE IF NOT EXISTS 'CYCLE_COUNT';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'StockMovementType enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.8 DeliveryLotStatus Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE deliverylotstatus ADD VALUE IF NOT EXISTS 'PENDING';
    ALTER TYPE deliverylotstatus ADD VALUE IF NOT EXISTS 'ADVANCE_PENDING';
    ALTER TYPE deliverylotstatus ADD VALUE IF NOT EXISTS 'ADVANCE_PAID';
    ALTER TYPE deliverylotstatus ADD VALUE IF NOT EXISTS 'DELIVERED';
    ALTER TYPE deliverylotstatus ADD VALUE IF NOT EXISTS 'PAYMENT_PENDING';
    ALTER TYPE deliverylotstatus ADD VALUE IF NOT EXISTS 'COMPLETED';
    ALTER TYPE deliverylotstatus ADD VALUE IF NOT EXISTS 'CANCELLED';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'DeliveryLotStatus enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.9 SerialStatus Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE serialstatus ADD VALUE IF NOT EXISTS 'GENERATED';
    ALTER TYPE serialstatus ADD VALUE IF NOT EXISTS 'PRINTED';
    ALTER TYPE serialstatus ADD VALUE IF NOT EXISTS 'SENT_TO_VENDOR';
    ALTER TYPE serialstatus ADD VALUE IF NOT EXISTS 'RECEIVED';
    ALTER TYPE serialstatus ADD VALUE IF NOT EXISTS 'ASSIGNED';
    ALTER TYPE serialstatus ADD VALUE IF NOT EXISTS 'SOLD';
    ALTER TYPE serialstatus ADD VALUE IF NOT EXISTS 'RETURNED';
    ALTER TYPE serialstatus ADD VALUE IF NOT EXISTS 'DAMAGED';
    ALTER TYPE serialstatus ADD VALUE IF NOT EXISTS 'CANCELLED';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'SerialStatus enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.10 InstallationStatus Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE installationstatus ADD VALUE IF NOT EXISTS 'PENDING';
    ALTER TYPE installationstatus ADD VALUE IF NOT EXISTS 'SCHEDULED';
    ALTER TYPE installationstatus ADD VALUE IF NOT EXISTS 'IN_PROGRESS';
    ALTER TYPE installationstatus ADD VALUE IF NOT EXISTS 'COMPLETED';
    ALTER TYPE installationstatus ADD VALUE IF NOT EXISTS 'CANCELLED';
    ALTER TYPE installationstatus ADD VALUE IF NOT EXISTS 'FAILED';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'InstallationStatus enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.11 AMCType Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE amctype ADD VALUE IF NOT EXISTS 'STANDARD';
    ALTER TYPE amctype ADD VALUE IF NOT EXISTS 'COMPREHENSIVE';
    ALTER TYPE amctype ADD VALUE IF NOT EXISTS 'EXTENDED_WARRANTY';
    ALTER TYPE amctype ADD VALUE IF NOT EXISTS 'PLATINUM';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'AMCType enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.12 AMCStatus Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE amcstatus ADD VALUE IF NOT EXISTS 'DRAFT';
    ALTER TYPE amcstatus ADD VALUE IF NOT EXISTS 'PENDING_PAYMENT';
    ALTER TYPE amcstatus ADD VALUE IF NOT EXISTS 'ACTIVE';
    ALTER TYPE amcstatus ADD VALUE IF NOT EXISTS 'EXPIRED';
    ALTER TYPE amcstatus ADD VALUE IF NOT EXISTS 'CANCELLED';
    ALTER TYPE amcstatus ADD VALUE IF NOT EXISTS 'RENEWED';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'AMCStatus enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.13 TransferStatus Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE transferstatus ADD VALUE IF NOT EXISTS 'DRAFT';
    ALTER TYPE transferstatus ADD VALUE IF NOT EXISTS 'PENDING_APPROVAL';
    ALTER TYPE transferstatus ADD VALUE IF NOT EXISTS 'APPROVED';
    ALTER TYPE transferstatus ADD VALUE IF NOT EXISTS 'REJECTED';
    ALTER TYPE transferstatus ADD VALUE IF NOT EXISTS 'IN_TRANSIT';
    ALTER TYPE transferstatus ADD VALUE IF NOT EXISTS 'PARTIALLY_RECEIVED';
    ALTER TYPE transferstatus ADD VALUE IF NOT EXISTS 'RECEIVED';
    ALTER TYPE transferstatus ADD VALUE IF NOT EXISTS 'CANCELLED';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'TransferStatus enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.14 TransferType Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE transfertype ADD VALUE IF NOT EXISTS 'STOCK_TRANSFER';
    ALTER TYPE transfertype ADD VALUE IF NOT EXISTS 'REPLENISHMENT';
    ALTER TYPE transfertype ADD VALUE IF NOT EXISTS 'RETURN_TO_MAIN';
    ALTER TYPE transfertype ADD VALUE IF NOT EXISTS 'INTER_REGION';
    ALTER TYPE transfertype ADD VALUE IF NOT EXISTS 'DEALER_SUPPLY';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'TransferType enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.15 AdjustmentType Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE adjustmenttype ADD VALUE IF NOT EXISTS 'CYCLE_COUNT';
    ALTER TYPE adjustmenttype ADD VALUE IF NOT EXISTS 'DAMAGE';
    ALTER TYPE adjustmenttype ADD VALUE IF NOT EXISTS 'THEFT';
    ALTER TYPE adjustmenttype ADD VALUE IF NOT EXISTS 'EXPIRY';
    ALTER TYPE adjustmenttype ADD VALUE IF NOT EXISTS 'QUALITY_ISSUE';
    ALTER TYPE adjustmenttype ADD VALUE IF NOT EXISTS 'CORRECTION';
    ALTER TYPE adjustmenttype ADD VALUE IF NOT EXISTS 'WRITE_OFF';
    ALTER TYPE adjustmenttype ADD VALUE IF NOT EXISTS 'FOUND';
    ALTER TYPE adjustmenttype ADD VALUE IF NOT EXISTS 'OPENING_STOCK';
    ALTER TYPE adjustmenttype ADD VALUE IF NOT EXISTS 'OTHER';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'AdjustmentType enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.16 AdjustmentStatus Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE adjustmentstatus ADD VALUE IF NOT EXISTS 'DRAFT';
    ALTER TYPE adjustmentstatus ADD VALUE IF NOT EXISTS 'PENDING_APPROVAL';
    ALTER TYPE adjustmentstatus ADD VALUE IF NOT EXISTS 'APPROVED';
    ALTER TYPE adjustmentstatus ADD VALUE IF NOT EXISTS 'REJECTED';
    ALTER TYPE adjustmentstatus ADD VALUE IF NOT EXISTS 'COMPLETED';
    ALTER TYPE adjustmentstatus ADD VALUE IF NOT EXISTS 'CANCELLED';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'AdjustmentStatus enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.17 TechnicianStatus Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE technicianstatus ADD VALUE IF NOT EXISTS 'ACTIVE';
    ALTER TYPE technicianstatus ADD VALUE IF NOT EXISTS 'INACTIVE';
    ALTER TYPE technicianstatus ADD VALUE IF NOT EXISTS 'ON_LEAVE';
    ALTER TYPE technicianstatus ADD VALUE IF NOT EXISTS 'TRAINING';
    ALTER TYPE technicianstatus ADD VALUE IF NOT EXISTS 'RESIGNED';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'TechnicianStatus enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.18 TechnicianType Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE techniciantype ADD VALUE IF NOT EXISTS 'INTERNAL';
    ALTER TYPE techniciantype ADD VALUE IF NOT EXISTS 'EXTERNAL';
    ALTER TYPE techniciantype ADD VALUE IF NOT EXISTS 'FREELANCE';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'TechnicianType enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- 2.19 SkillLevel Enum
-- ============================================================
DO $$
BEGIN
    ALTER TYPE skilllevel ADD VALUE IF NOT EXISTS 'TRAINEE';
    ALTER TYPE skilllevel ADD VALUE IF NOT EXISTS 'JUNIOR';
    ALTER TYPE skilllevel ADD VALUE IF NOT EXISTS 'SENIOR';
    ALTER TYPE skilllevel ADD VALUE IF NOT EXISTS 'EXPERT';
    ALTER TYPE skilllevel ADD VALUE IF NOT EXISTS 'MASTER';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'SkillLevel enum handling: %', SQLERRM;
END $$;

-- ============================================================
-- NOW UPDATE THE DATA: Convert lowercase to UPPERCASE values
-- ============================================================

-- Update service_requests table
UPDATE service_requests
SET service_type = 'INSTALLATION'::servicetype WHERE service_type::text = 'installation';
UPDATE service_requests
SET service_type = 'WARRANTY_REPAIR'::servicetype WHERE service_type::text = 'warranty_repair';
UPDATE service_requests
SET service_type = 'PAID_REPAIR'::servicetype WHERE service_type::text = 'paid_repair';
UPDATE service_requests
SET service_type = 'AMC_SERVICE'::servicetype WHERE service_type::text = 'amc_service';
UPDATE service_requests
SET service_type = 'DEMO'::servicetype WHERE service_type::text = 'demo';
UPDATE service_requests
SET service_type = 'PREVENTIVE_MAINTENANCE'::servicetype WHERE service_type::text = 'preventive_maintenance';
UPDATE service_requests
SET service_type = 'COMPLAINT'::servicetype WHERE service_type::text = 'complaint';
UPDATE service_requests
SET service_type = 'FILTER_CHANGE'::servicetype WHERE service_type::text = 'filter_change';
UPDATE service_requests
SET service_type = 'INSPECTION'::servicetype WHERE service_type::text = 'inspection';
UPDATE service_requests
SET service_type = 'UNINSTALLATION'::servicetype WHERE service_type::text = 'uninstallation';

-- Update priority
UPDATE service_requests SET priority = 'LOW'::servicepriority WHERE priority::text = 'low';
UPDATE service_requests SET priority = 'NORMAL'::servicepriority WHERE priority::text = 'normal';
UPDATE service_requests SET priority = 'HIGH'::servicepriority WHERE priority::text = 'high';
UPDATE service_requests SET priority = 'URGENT'::servicepriority WHERE priority::text = 'urgent';
UPDATE service_requests SET priority = 'CRITICAL'::servicepriority WHERE priority::text = 'critical';

-- Update status
UPDATE service_requests SET status = 'DRAFT'::servicestatus WHERE status::text = 'draft';
UPDATE service_requests SET status = 'PENDING'::servicestatus WHERE status::text = 'pending';
UPDATE service_requests SET status = 'ASSIGNED'::servicestatus WHERE status::text = 'assigned';
UPDATE service_requests SET status = 'SCHEDULED'::servicestatus WHERE status::text = 'scheduled';
UPDATE service_requests SET status = 'EN_ROUTE'::servicestatus WHERE status::text = 'en_route';
UPDATE service_requests SET status = 'IN_PROGRESS'::servicestatus WHERE status::text = 'in_progress';
UPDATE service_requests SET status = 'PARTS_REQUIRED'::servicestatus WHERE status::text = 'parts_required';
UPDATE service_requests SET status = 'ON_HOLD'::servicestatus WHERE status::text = 'on_hold';
UPDATE service_requests SET status = 'COMPLETED'::servicestatus WHERE status::text = 'completed';
UPDATE service_requests SET status = 'CLOSED'::servicestatus WHERE status::text = 'closed';
UPDATE service_requests SET status = 'CANCELLED'::servicestatus WHERE status::text = 'cancelled';
UPDATE service_requests SET status = 'REOPENED'::servicestatus WHERE status::text = 'reopened';

-- Update source
UPDATE service_requests SET source = 'CALL_CENTER'::servicesource WHERE source::text = 'call_center';
UPDATE service_requests SET source = 'WEBSITE'::servicesource WHERE source::text = 'website';
UPDATE service_requests SET source = 'MOBILE_APP'::servicesource WHERE source::text = 'mobile_app';
UPDATE service_requests SET source = 'WALK_IN'::servicesource WHERE source::text = 'walk_in';
UPDATE service_requests SET source = 'EMAIL'::servicesource WHERE source::text = 'email';
UPDATE service_requests SET source = 'WHATSAPP'::servicesource WHERE source::text = 'whatsapp';
UPDATE service_requests SET source = 'AUTO_AMC'::servicesource WHERE source::text = 'auto_amc';
UPDATE service_requests SET source = 'REFERRAL'::servicesource WHERE source::text = 'referral';
UPDATE service_requests SET source = 'SYSTEM'::servicesource WHERE source::text = 'system';

-- Update warehouses
UPDATE warehouses SET warehouse_type = 'MAIN'::warehousetype WHERE warehouse_type::text = 'main';
UPDATE warehouses SET warehouse_type = 'REGIONAL'::warehousetype WHERE warehouse_type::text = 'regional';
UPDATE warehouses SET warehouse_type = 'SERVICE_CENTER'::warehousetype WHERE warehouse_type::text = 'service_center';
UPDATE warehouses SET warehouse_type = 'DEALER'::warehousetype WHERE warehouse_type::text = 'dealer';
UPDATE warehouses SET warehouse_type = 'VIRTUAL'::warehousetype WHERE warehouse_type::text = 'virtual';

-- Update stock_items
UPDATE stock_items SET status = 'AVAILABLE'::stockitemstatus WHERE status::text = 'available';
UPDATE stock_items SET status = 'RESERVED'::stockitemstatus WHERE status::text = 'reserved';
UPDATE stock_items SET status = 'ALLOCATED'::stockitemstatus WHERE status::text = 'allocated';
UPDATE stock_items SET status = 'PICKED'::stockitemstatus WHERE status::text = 'picked';
UPDATE stock_items SET status = 'PACKED'::stockitemstatus WHERE status::text = 'packed';
UPDATE stock_items SET status = 'IN_TRANSIT'::stockitemstatus WHERE status::text = 'in_transit';
UPDATE stock_items SET status = 'SHIPPED'::stockitemstatus WHERE status::text = 'shipped';
UPDATE stock_items SET status = 'DAMAGED'::stockitemstatus WHERE status::text = 'damaged';
UPDATE stock_items SET status = 'DEFECTIVE'::stockitemstatus WHERE status::text = 'defective';
UPDATE stock_items SET status = 'SOLD'::stockitemstatus WHERE status::text = 'sold';
UPDATE stock_items SET status = 'RETURNED'::stockitemstatus WHERE status::text = 'returned';
UPDATE stock_items SET status = 'QUARANTINE'::stockitemstatus WHERE status::text = 'quarantine';
UPDATE stock_items SET status = 'SCRAPPED'::stockitemstatus WHERE status::text = 'scrapped';

-- Update stock_movements
UPDATE stock_movements SET movement_type = 'RECEIPT'::stockmovementtype WHERE movement_type::text = 'receipt';
UPDATE stock_movements SET movement_type = 'ISSUE'::stockmovementtype WHERE movement_type::text = 'issue';
UPDATE stock_movements SET movement_type = 'TRANSFER_IN'::stockmovementtype WHERE movement_type::text = 'transfer_in';
UPDATE stock_movements SET movement_type = 'TRANSFER_OUT'::stockmovementtype WHERE movement_type::text = 'transfer_out';
UPDATE stock_movements SET movement_type = 'RETURN_IN'::stockmovementtype WHERE movement_type::text = 'return_in';
UPDATE stock_movements SET movement_type = 'RETURN_OUT'::stockmovementtype WHERE movement_type::text = 'return_out';
UPDATE stock_movements SET movement_type = 'ADJUSTMENT_PLUS'::stockmovementtype WHERE movement_type::text = 'adjustment_plus';
UPDATE stock_movements SET movement_type = 'ADJUSTMENT_MINUS'::stockmovementtype WHERE movement_type::text = 'adjustment_minus';
UPDATE stock_movements SET movement_type = 'DAMAGE'::stockmovementtype WHERE movement_type::text = 'damage';
UPDATE stock_movements SET movement_type = 'SCRAP'::stockmovementtype WHERE movement_type::text = 'scrap';
UPDATE stock_movements SET movement_type = 'CYCLE_COUNT'::stockmovementtype WHERE movement_type::text = 'cycle_count';

-- Update po_delivery_schedules
UPDATE po_delivery_schedules SET status = 'PENDING'::deliverylotstatus WHERE status::text = 'pending';
UPDATE po_delivery_schedules SET status = 'ADVANCE_PENDING'::deliverylotstatus WHERE status::text = 'advance_pending';
UPDATE po_delivery_schedules SET status = 'ADVANCE_PAID'::deliverylotstatus WHERE status::text = 'advance_paid';
UPDATE po_delivery_schedules SET status = 'DELIVERED'::deliverylotstatus WHERE status::text = 'delivered';
UPDATE po_delivery_schedules SET status = 'PAYMENT_PENDING'::deliverylotstatus WHERE status::text = 'payment_pending';
UPDATE po_delivery_schedules SET status = 'COMPLETED'::deliverylotstatus WHERE status::text = 'completed';
UPDATE po_delivery_schedules SET status = 'CANCELLED'::deliverylotstatus WHERE status::text = 'cancelled';

-- Update po_serials
UPDATE po_serials SET status = 'GENERATED'::serialstatus WHERE status::text = 'generated';
UPDATE po_serials SET status = 'PRINTED'::serialstatus WHERE status::text = 'printed';
UPDATE po_serials SET status = 'SENT_TO_VENDOR'::serialstatus WHERE status::text = 'sent_to_vendor';
UPDATE po_serials SET status = 'RECEIVED'::serialstatus WHERE status::text = 'received';
UPDATE po_serials SET status = 'ASSIGNED'::serialstatus WHERE status::text = 'assigned';
UPDATE po_serials SET status = 'SOLD'::serialstatus WHERE status::text = 'sold';
UPDATE po_serials SET status = 'RETURNED'::serialstatus WHERE status::text = 'returned';
UPDATE po_serials SET status = 'DAMAGED'::serialstatus WHERE status::text = 'damaged';
UPDATE po_serials SET status = 'CANCELLED'::serialstatus WHERE status::text = 'cancelled';

-- Update installations
UPDATE installations SET status = 'PENDING'::installationstatus WHERE status::text = 'pending';
UPDATE installations SET status = 'SCHEDULED'::installationstatus WHERE status::text = 'scheduled';
UPDATE installations SET status = 'IN_PROGRESS'::installationstatus WHERE status::text = 'in_progress';
UPDATE installations SET status = 'COMPLETED'::installationstatus WHERE status::text = 'completed';
UPDATE installations SET status = 'CANCELLED'::installationstatus WHERE status::text = 'cancelled';
UPDATE installations SET status = 'FAILED'::installationstatus WHERE status::text = 'failed';

-- Update amc_contracts
UPDATE amc_contracts SET amc_type = 'STANDARD'::amctype WHERE amc_type::text = 'standard';
UPDATE amc_contracts SET amc_type = 'COMPREHENSIVE'::amctype WHERE amc_type::text = 'comprehensive';
UPDATE amc_contracts SET amc_type = 'EXTENDED_WARRANTY'::amctype WHERE amc_type::text = 'extended_warranty';
UPDATE amc_contracts SET amc_type = 'PLATINUM'::amctype WHERE amc_type::text = 'platinum';

UPDATE amc_contracts SET status = 'DRAFT'::amcstatus WHERE status::text = 'draft';
UPDATE amc_contracts SET status = 'PENDING_PAYMENT'::amcstatus WHERE status::text = 'pending_payment';
UPDATE amc_contracts SET status = 'ACTIVE'::amcstatus WHERE status::text = 'active';
UPDATE amc_contracts SET status = 'EXPIRED'::amcstatus WHERE status::text = 'expired';
UPDATE amc_contracts SET status = 'CANCELLED'::amcstatus WHERE status::text = 'cancelled';
UPDATE amc_contracts SET status = 'RENEWED'::amcstatus WHERE status::text = 'renewed';

-- Update stock_transfers
UPDATE stock_transfers SET status = 'DRAFT'::transferstatus WHERE status::text = 'draft';
UPDATE stock_transfers SET status = 'PENDING_APPROVAL'::transferstatus WHERE status::text = 'pending_approval';
UPDATE stock_transfers SET status = 'APPROVED'::transferstatus WHERE status::text = 'approved';
UPDATE stock_transfers SET status = 'REJECTED'::transferstatus WHERE status::text = 'rejected';
UPDATE stock_transfers SET status = 'IN_TRANSIT'::transferstatus WHERE status::text = 'in_transit';
UPDATE stock_transfers SET status = 'PARTIALLY_RECEIVED'::transferstatus WHERE status::text = 'partially_received';
UPDATE stock_transfers SET status = 'RECEIVED'::transferstatus WHERE status::text = 'received';
UPDATE stock_transfers SET status = 'CANCELLED'::transferstatus WHERE status::text = 'cancelled';

UPDATE stock_transfers SET transfer_type = 'STOCK_TRANSFER'::transfertype WHERE transfer_type::text = 'stock_transfer';
UPDATE stock_transfers SET transfer_type = 'REPLENISHMENT'::transfertype WHERE transfer_type::text = 'replenishment';
UPDATE stock_transfers SET transfer_type = 'RETURN_TO_MAIN'::transfertype WHERE transfer_type::text = 'return_to_main';
UPDATE stock_transfers SET transfer_type = 'INTER_REGION'::transfertype WHERE transfer_type::text = 'inter_region';
UPDATE stock_transfers SET transfer_type = 'DEALER_SUPPLY'::transfertype WHERE transfer_type::text = 'dealer_supply';

-- Update stock_adjustments
UPDATE stock_adjustments SET adjustment_type = 'CYCLE_COUNT'::adjustmenttype WHERE adjustment_type::text = 'cycle_count';
UPDATE stock_adjustments SET adjustment_type = 'DAMAGE'::adjustmenttype WHERE adjustment_type::text = 'damage';
UPDATE stock_adjustments SET adjustment_type = 'THEFT'::adjustmenttype WHERE adjustment_type::text = 'theft';
UPDATE stock_adjustments SET adjustment_type = 'EXPIRY'::adjustmenttype WHERE adjustment_type::text = 'expiry';
UPDATE stock_adjustments SET adjustment_type = 'QUALITY_ISSUE'::adjustmenttype WHERE adjustment_type::text = 'quality_issue';
UPDATE stock_adjustments SET adjustment_type = 'CORRECTION'::adjustmenttype WHERE adjustment_type::text = 'correction';
UPDATE stock_adjustments SET adjustment_type = 'WRITE_OFF'::adjustmenttype WHERE adjustment_type::text = 'write_off';
UPDATE stock_adjustments SET adjustment_type = 'FOUND'::adjustmenttype WHERE adjustment_type::text = 'found';
UPDATE stock_adjustments SET adjustment_type = 'OPENING_STOCK'::adjustmenttype WHERE adjustment_type::text = 'opening_stock';
UPDATE stock_adjustments SET adjustment_type = 'OTHER'::adjustmenttype WHERE adjustment_type::text = 'other';

UPDATE stock_adjustments SET status = 'DRAFT'::adjustmentstatus WHERE status::text = 'draft';
UPDATE stock_adjustments SET status = 'PENDING_APPROVAL'::adjustmentstatus WHERE status::text = 'pending_approval';
UPDATE stock_adjustments SET status = 'APPROVED'::adjustmentstatus WHERE status::text = 'approved';
UPDATE stock_adjustments SET status = 'REJECTED'::adjustmentstatus WHERE status::text = 'rejected';
UPDATE stock_adjustments SET status = 'COMPLETED'::adjustmentstatus WHERE status::text = 'completed';
UPDATE stock_adjustments SET status = 'CANCELLED'::adjustmentstatus WHERE status::text = 'cancelled';

-- Update technicians
UPDATE technicians SET status = 'ACTIVE'::technicianstatus WHERE status::text = 'active';
UPDATE technicians SET status = 'INACTIVE'::technicianstatus WHERE status::text = 'inactive';
UPDATE technicians SET status = 'ON_LEAVE'::technicianstatus WHERE status::text = 'on_leave';
UPDATE technicians SET status = 'TRAINING'::technicianstatus WHERE status::text = 'training';
UPDATE technicians SET status = 'RESIGNED'::technicianstatus WHERE status::text = 'resigned';

UPDATE technicians SET technician_type = 'INTERNAL'::techniciantype WHERE technician_type::text = 'internal';
UPDATE technicians SET technician_type = 'EXTERNAL'::techniciantype WHERE technician_type::text = 'external';
UPDATE technicians SET technician_type = 'FREELANCE'::techniciantype WHERE technician_type::text = 'freelance';

UPDATE technicians SET skill_level = 'TRAINEE'::skilllevel WHERE skill_level::text = 'trainee';
UPDATE technicians SET skill_level = 'JUNIOR'::skilllevel WHERE skill_level::text = 'junior';
UPDATE technicians SET skill_level = 'SENIOR'::skilllevel WHERE skill_level::text = 'senior';
UPDATE technicians SET skill_level = 'EXPERT'::skilllevel WHERE skill_level::text = 'expert';
UPDATE technicians SET skill_level = 'MASTER'::skilllevel WHERE skill_level::text = 'master';


-- ============================================================
-- PART 3: FLOAT TO NUMERIC CONVERSIONS (Money Fields)
-- Only runs if columns exist and are float type
-- ============================================================

-- stock_items table
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'stock_items' AND column_name = 'purchase_price' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE stock_items ALTER COLUMN purchase_price TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'stock_items' AND column_name = 'landed_cost' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE stock_items ALTER COLUMN landed_cost TYPE NUMERIC(12,2);
    END IF;
END $$;

-- service_requests table
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'service_requests' AND column_name = 'total_parts_cost' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE service_requests ALTER COLUMN total_parts_cost TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'service_requests' AND column_name = 'labor_charges' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE service_requests ALTER COLUMN labor_charges TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'service_requests' AND column_name = 'service_charges' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE service_requests ALTER COLUMN service_charges TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'service_requests' AND column_name = 'travel_charges' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE service_requests ALTER COLUMN travel_charges TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'service_requests' AND column_name = 'total_charges' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE service_requests ALTER COLUMN total_charges TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'service_requests' AND column_name = 'payment_collected' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE service_requests ALTER COLUMN payment_collected TYPE NUMERIC(12,2);
    END IF;
END $$;

-- warranty_claims table
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'warranty_claims' AND column_name = 'refund_amount' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE warranty_claims ALTER COLUMN refund_amount TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'warranty_claims' AND column_name = 'parts_cost' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE warranty_claims ALTER COLUMN parts_cost TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'warranty_claims' AND column_name = 'labor_cost' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE warranty_claims ALTER COLUMN labor_cost TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'warranty_claims' AND column_name = 'total_cost' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE warranty_claims ALTER COLUMN total_cost TYPE NUMERIC(12,2);
    END IF;
END $$;

-- stock_adjustments table
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'stock_adjustments' AND column_name = 'total_value_impact' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE stock_adjustments ALTER COLUMN total_value_impact TYPE NUMERIC(14,2);
    END IF;
END $$;

-- stock_adjustment_items table
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'stock_adjustment_items' AND column_name = 'unit_cost' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE stock_adjustment_items ALTER COLUMN unit_cost TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'stock_adjustment_items' AND column_name = 'value_impact' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE stock_adjustment_items ALTER COLUMN value_impact TYPE NUMERIC(14,2);
    END IF;
END $$;

-- amc_contracts table
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'amc_contracts' AND column_name = 'base_price' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE amc_contracts ALTER COLUMN base_price TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'amc_contracts' AND column_name = 'tax_amount' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE amc_contracts ALTER COLUMN tax_amount TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'amc_contracts' AND column_name = 'discount_amount' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE amc_contracts ALTER COLUMN discount_amount TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'amc_contracts' AND column_name = 'total_amount' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE amc_contracts ALTER COLUMN total_amount TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'amc_contracts' AND column_name = 'discount_on_parts' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE amc_contracts ALTER COLUMN discount_on_parts TYPE NUMERIC(5,2);
    END IF;
END $$;

-- stock_transfers table
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'stock_transfers' AND column_name = 'total_value' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE stock_transfers ALTER COLUMN total_value TYPE NUMERIC(14,2);
    END IF;
END $$;

-- stock_transfer_items table
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'stock_transfer_items' AND column_name = 'unit_cost' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE stock_transfer_items ALTER COLUMN unit_cost TYPE NUMERIC(12,2);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'stock_transfer_items' AND column_name = 'total_cost' AND data_type IN ('real', 'double precision')) THEN
        ALTER TABLE stock_transfer_items ALTER COLUMN total_cost TYPE NUMERIC(14,2);
    END IF;
END $$;

-- Clean up helper function
DROP FUNCTION IF EXISTS enum_value_exists(text, text);

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
SELECT 'Migration completed successfully!' AS result;
