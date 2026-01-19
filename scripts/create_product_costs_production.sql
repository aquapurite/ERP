-- Product Costs Table for COGS Auto-Calculation
-- Run this SQL in Supabase SQL Editor to create the table in production

-- Check if table exists, create only if not
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'product_costs') THEN
        CREATE TABLE product_costs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Product Reference
            product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            variant_id UUID REFERENCES product_variants(id) ON DELETE CASCADE,

            -- Warehouse (NULL = company-wide aggregate)
            warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,

            -- Valuation Method: WEIGHTED_AVG, FIFO, SPECIFIC_ID
            valuation_method VARCHAR(20) NOT NULL DEFAULT 'WEIGHTED_AVG',

            -- Cost Fields - Auto-calculated from GRN
            average_cost NUMERIC(12, 2) NOT NULL DEFAULT 0,
            last_purchase_cost NUMERIC(12, 2),
            standard_cost NUMERIC(12, 2),

            -- Inventory Position
            quantity_on_hand INTEGER NOT NULL DEFAULT 0,
            total_value NUMERIC(14, 2) NOT NULL DEFAULT 0,

            -- Tracking
            last_grn_id UUID REFERENCES goods_receipt_notes(id) ON DELETE SET NULL,
            last_calculated_at TIMESTAMPTZ,

            -- Cost History (JSONB array of cost movements)
            cost_history JSONB DEFAULT '[]'::jsonb,

            -- Timestamps
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        -- Create indexes for fast lookups
        CREATE INDEX idx_product_costs_product ON product_costs(product_id);
        CREATE INDEX idx_product_costs_warehouse ON product_costs(warehouse_id);
        CREATE INDEX idx_product_costs_variant ON product_costs(variant_id);

        -- Unique constraint: one cost record per product+variant+warehouse
        CREATE UNIQUE INDEX uq_product_cost ON product_costs(product_id, COALESCE(variant_id, '00000000-0000-0000-0000-000000000000'::uuid), COALESCE(warehouse_id, '00000000-0000-0000-0000-000000000000'::uuid));

        RAISE NOTICE 'Created product_costs table successfully';
    ELSE
        RAISE NOTICE 'Table product_costs already exists, skipping';
    END IF;
END $$;

-- Verify table was created
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'product_costs'
ORDER BY ordinal_position;
