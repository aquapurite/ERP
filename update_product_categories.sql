-- ============================================================================
-- UPDATE PRODUCT CATEGORIES
-- Maps products to correct categories based on item_type
-- Run this in Supabase SQL Editor
-- ============================================================================

-- First, let's see what categories exist
SELECT id, name, slug FROM categories ORDER BY name;

-- Let's see the current state of products and their categories
SELECT
    p.name as product_name,
    p.sku,
    p.item_type,
    p.category_id,
    c.name as current_category
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
ORDER BY p.item_type, p.name;

-- ============================================================================
-- STEP 1: Find category IDs (run this first to get the UUIDs)
-- ============================================================================
-- Copy the category IDs from the result above, then use them below

-- ============================================================================
-- STEP 2: Update products based on item_type
-- Replace 'YOUR_FINISHED_GOODS_CATEGORY_ID' and 'YOUR_SPARE_PARTS_CATEGORY_ID'
-- with actual UUIDs from Step 1
-- ============================================================================

-- Example (update with actual category IDs):
/*
-- Update Finished Goods products
UPDATE products
SET category_id = 'YOUR_FINISHED_GOODS_CATEGORY_ID'
WHERE item_type = 'FINISHED_GOODS';

-- Update Spare Parts products
UPDATE products
SET category_id = 'YOUR_SPARE_PARTS_CATEGORY_ID'
WHERE item_type = 'SPARE_PARTS';

-- Update Consumables (if you have a consumables category)
UPDATE products
SET category_id = 'YOUR_CONSUMABLES_CATEGORY_ID'
WHERE item_type = 'CONSUMABLES';

-- Update Components
UPDATE products
SET category_id = 'YOUR_COMPONENTS_CATEGORY_ID'
WHERE item_type = 'COMPONENTS';

-- Update Accessories
UPDATE products
SET category_id = 'YOUR_ACCESSORIES_CATEGORY_ID'
WHERE item_type = 'ACCESSORIES';
*/

-- ============================================================================
-- STEP 3: Verify the update
-- ============================================================================
SELECT
    c.name as category,
    COUNT(*) as product_count
FROM products p
JOIN categories c ON p.category_id = c.id
GROUP BY c.name
ORDER BY c.name;

-- ============================================================================
-- ALTERNATIVE: If categories don't exist, create them first
-- ============================================================================
/*
-- Create Finished Goods category if not exists
INSERT INTO categories (name, slug, description, is_active, sort_order)
VALUES ('Finished Goods', 'finished-goods', 'Complete water purifier products', true, 1)
ON CONFLICT (slug) DO NOTHING;

-- Create Spare Parts category if not exists
INSERT INTO categories (name, slug, description, is_active, sort_order)
VALUES ('Spare Parts', 'spare-parts', 'Replacement parts and components', true, 2)
ON CONFLICT (slug) DO NOTHING;

-- Create Consumables category if not exists
INSERT INTO categories (name, slug, description, is_active, sort_order)
VALUES ('Consumables', 'consumables', 'Filters, membranes, and other consumables', true, 3)
ON CONFLICT (slug) DO NOTHING;
*/
