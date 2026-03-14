-- Add sub_item_code column to products, purchase_requisition_items, purchase_order_items, and grn_items
-- This field is optional and only used for Spare Parts (item_type = 'SP')

-- 1. Products table
ALTER TABLE products ADD COLUMN IF NOT EXISTS sub_item_code VARCHAR(50) DEFAULT NULL;
COMMENT ON COLUMN products.sub_item_code IS 'Sub item code for spare parts only';

-- 2. Purchase Requisition Items table
ALTER TABLE purchase_requisition_items ADD COLUMN IF NOT EXISTS sub_item_code VARCHAR(50) DEFAULT NULL;
COMMENT ON COLUMN purchase_requisition_items.sub_item_code IS 'Sub item code for spare parts only';

-- 3. Purchase Order Items table
ALTER TABLE purchase_order_items ADD COLUMN IF NOT EXISTS sub_item_code VARCHAR(50) DEFAULT NULL;
COMMENT ON COLUMN purchase_order_items.sub_item_code IS 'Sub item code for spare parts only';

-- 4. GRN Items table
ALTER TABLE grn_items ADD COLUMN IF NOT EXISTS sub_item_code VARCHAR(50) DEFAULT NULL;
COMMENT ON COLUMN grn_items.sub_item_code IS 'Sub item code for spare parts only';
