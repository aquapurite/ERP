-- Migration: Add Product Serial Sequence Table
-- Purpose: Enable product-level serialization (each model has its own continuous serial range)
-- Supports BOTH Finished Goods (FG) and Spare Parts (SP) with separate sequences

-- Create the product_serial_sequences table
CREATE TABLE IF NOT EXISTS product_serial_sequences (
    id VARCHAR(36) PRIMARY KEY,

    -- Product identification - unique per (model_code + item_type) combination
    -- Note: product_id stored as string for compatibility with existing models
    product_id VARCHAR(36),
    model_code VARCHAR(10) NOT NULL,
    item_type VARCHAR(20) NOT NULL DEFAULT 'FG',  -- 'FG' for Finished Goods, 'SP' for Spare Parts

    -- Product info (denormalized for quick access)
    product_name VARCHAR(255),
    product_sku VARCHAR(50),

    -- Sequence tracking - continuous across all time
    last_serial INTEGER DEFAULT 0 NOT NULL,
    total_generated INTEGER DEFAULT 0,
    max_serial INTEGER DEFAULT 99999999,  -- Default ~1 crore

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint: Same model_code can exist for FG and SP separately
    CONSTRAINT uq_model_code_item_type UNIQUE (model_code, item_type)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_product_serial_sequences_model_code ON product_serial_sequences(model_code);
CREATE INDEX IF NOT EXISTS idx_product_serial_sequences_item_type ON product_serial_sequences(item_type);
CREATE INDEX IF NOT EXISTS idx_product_serial_sequences_product_id ON product_serial_sequences(product_id);

-- Migrate existing data from model_code_references to product_serial_sequences
-- This initializes sequences for existing products with their model codes
-- Handles both FG and SP separately
INSERT INTO product_serial_sequences (id, product_id, model_code, item_type, product_name, product_sku, last_serial, total_generated, max_serial)
SELECT
    REPLACE(gen_random_uuid()::text, '-', ''),
    mcr.product_id,
    mcr.model_code,
    COALESCE(mcr.item_type::text, 'FG'),
    (SELECT name FROM products WHERE id::text = mcr.product_id LIMIT 1),
    mcr.product_sku,
    COALESCE(
        (SELECT MAX(serial_number) FROM po_serials
         WHERE model_code = mcr.model_code
         AND item_type::text = COALESCE(mcr.item_type::text, 'FG')),
        0
    ),
    COALESCE(
        (SELECT COUNT(*)::INTEGER FROM po_serials
         WHERE model_code = mcr.model_code
         AND item_type::text = COALESCE(mcr.item_type::text, 'FG')),
        0
    ),
    99999999
FROM model_code_references mcr
WHERE mcr.is_active = true
ON CONFLICT (model_code, item_type) DO UPDATE SET
    last_serial = GREATEST(product_serial_sequences.last_serial, EXCLUDED.last_serial),
    total_generated = GREATEST(product_serial_sequences.total_generated, EXCLUDED.total_generated),
    updated_at = CURRENT_TIMESTAMP;

-- Output the current state grouped by item type
SELECT
    item_type,
    model_code,
    product_name,
    last_serial,
    total_generated,
    max_serial,
    (max_serial - last_serial) as available_serials
FROM product_serial_sequences
ORDER BY item_type, model_code;

-- Summary by item type
SELECT
    item_type,
    COUNT(*) as total_models,
    SUM(last_serial) as total_serials_used,
    SUM(total_generated) as total_generated
FROM product_serial_sequences
GROUP BY item_type;
