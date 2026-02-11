-- ============================================================
-- FIX: Convert product_id columns from VARCHAR to UUID
-- Run this in Supabase SQL Editor
-- ============================================================

-- Step 1: Check current column types (verify before running)
SELECT
    table_name,
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE column_name = 'product_id'
  AND table_name IN ('model_code_references', 'product_serial_sequences')
ORDER BY table_name;

-- Step 2: Fix model_code_references.product_id
-- Drop the foreign key constraint first
ALTER TABLE model_code_references
    DROP CONSTRAINT IF EXISTS model_code_references_product_id_fkey;

-- Convert VARCHAR to UUID
ALTER TABLE model_code_references
    ALTER COLUMN product_id TYPE UUID USING product_id::uuid;

-- Re-add the foreign key constraint
ALTER TABLE model_code_references
    ADD CONSTRAINT model_code_references_product_id_fkey
    FOREIGN KEY (product_id) REFERENCES products(id);

-- Step 3: Fix product_serial_sequences.product_id
-- Drop the foreign key constraint first
ALTER TABLE product_serial_sequences
    DROP CONSTRAINT IF EXISTS product_serial_sequences_product_id_fkey;

-- Convert VARCHAR to UUID
ALTER TABLE product_serial_sequences
    ALTER COLUMN product_id TYPE UUID USING product_id::uuid;

-- Re-add the foreign key constraint
ALTER TABLE product_serial_sequences
    ADD CONSTRAINT product_serial_sequences_product_id_fkey
    FOREIGN KEY (product_id) REFERENCES products(id);

-- Step 4: Verify the fix
SELECT
    table_name,
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE column_name = 'product_id'
  AND table_name IN ('model_code_references', 'product_serial_sequences')
ORDER BY table_name;

-- Expected output after fix:
-- model_code_references | product_id | uuid | uuid
-- product_serial_sequences | product_id | uuid | uuid
