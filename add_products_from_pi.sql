-- ============================================================================
-- ADD PRODUCTS FROM PI NO./FF/25-26/005 (FASTRACK FILTRATION)
-- Run this in Supabase SQL Editor
-- ============================================================================

-- Step 1: Create Category (Water Purifiers)
-- ============================================================================
INSERT INTO categories (
    id,
    name,
    slug,
    description,
    is_active,
    is_featured,
    sort_order,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'Water Purifiers',
    'water-purifiers',
    'RO, UV, and UF water purification systems for home and commercial use',
    TRUE,
    TRUE,
    1,
    NOW(),
    NOW()
)
ON CONFLICT (slug) DO NOTHING;

-- Step 2: Create Brand (Aquapurite)
-- ============================================================================
INSERT INTO brands (
    id,
    name,
    slug,
    description,
    website,
    is_active,
    is_featured,
    sort_order,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'Aquapurite',
    'aquapurite',
    'Premium water purification solutions - Pure Water, Pure Life',
    'https://aquapurite.com',
    TRUE,
    TRUE,
    1,
    NOW(),
    NOW()
)
ON CONFLICT (slug) DO NOTHING;

-- Step 3: Get Category and Brand IDs for product insertion
-- ============================================================================
DO $$
DECLARE
    v_category_id UUID;
    v_brand_id UUID;
BEGIN
    -- Get category ID
    SELECT id INTO v_category_id FROM categories WHERE slug = 'water-purifiers';

    -- Get brand ID
    SELECT id INTO v_brand_id FROM brands WHERE slug = 'aquapurite';

    IF v_category_id IS NULL OR v_brand_id IS NULL THEN
        RAISE EXCEPTION 'Category or Brand not found. Please check the inserts above.';
    END IF;

    -- ========================================================================
    -- PRODUCT 1: AQUAPURITE BLITZ
    -- Entry-level RO water purifier
    -- Cost: Rs.2,304 | Qty on PI: 150
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, part_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        extra_data, created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Aquapurite Blitz',
        'aquapurite-blitz',
        'AP-BLITZ-001',
        'BLITZ',
        'WPRABL001',      -- FG Code: WP=Water Purifier, RA=RO+Alkaline?, BL=Blitz
        'BLZ',            -- Model code for barcode
        NULL,             -- Vendor part code (if any)
        'FG',             -- Finished Goods
        'Entry-level RO water purifier with 7-stage purification',
        'Aquapurite Blitz is an affordable RO water purifier designed for Indian households. Features 7-stage purification with RO+UV technology.',
        '• 7-Stage Purification
• RO + UV Technology
• 8 Liters Storage Tank
• TDS Controller
• Smart LED Indicators
• Food-grade ABS Plastic Body',
        v_category_id,
        v_brand_id,
        4999.00,          -- MRP
        4499.00,          -- Selling price
        2800.00,          -- Dealer price
        2304.00,          -- Cost price (from PI)
        '842121',         -- HSN Code
        18.00,            -- GST Rate
        18,               -- Warranty months (from PI)
        '18 months warranty on electronic parts, 1 year service warranty. RO Membrane & Housing, Pre & Post Carbon, Sediment Spun provided by buyer.',
        50,               -- Min stock level
        'ACTIVE',
        TRUE,
        TRUE,
        '{"notes": "Buyer provides: RO Membrane & Housing, Pre & Post Carbon, Sediment Spun, UV LED"}'::jsonb,
        NOW(),
        NOW()
    )
    ON CONFLICT (sku) DO UPDATE SET
        cost_price = EXCLUDED.cost_price,
        warranty_months = EXCLUDED.warranty_months,
        warranty_terms = EXCLUDED.warranty_terms,
        updated_at = NOW();

    -- ========================================================================
    -- PRODUCT 2: AQUAPURITE NEURA
    -- Mid-range Alkaline RO water purifier
    -- Cost: Rs.2,509 | Qty on PI: 150
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, part_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        extra_data, created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Aquapurite Neura',
        'aquapurite-neura',
        'AP-NEURA-001',
        'NEURA',
        'WPRANR001',      -- FG Code: WP=Water Purifier, RA=RO+Alkaline, NR=Neura
        'NRA',            -- Model code for barcode
        NULL,
        'FG',
        'Alkaline RO water purifier with mineral enhancement',
        'Aquapurite Neura features advanced Alkaline 4" technology for pH-balanced, mineral-rich drinking water. Perfect for health-conscious families.',
        '• Alkaline 4" Technology
• RO + UV + UF Purification
• Mineral Enhancement
• 10 Liters Storage Tank
• TDS Controller with Display
• Smart Auto-flush
• LED Indicators',
        v_category_id,
        v_brand_id,
        6999.00,          -- MRP
        6299.00,          -- Selling price
        3500.00,          -- Dealer price
        2509.00,          -- Cost price (from PI)
        '842121',         -- HSN Code
        18.00,            -- GST Rate
        18,               -- Warranty months
        '18 months warranty on electronic parts, 1 year service warranty. Alkaline 4", RO Membrane & Housing provided by buyer.',
        50,
        'ACTIVE',
        TRUE,
        TRUE,
        '{"notes": "Buyer provides: Alkaline 4\", RO Membrane & Housing, UV LED"}'::jsonb,
        NOW(),
        NOW()
    )
    ON CONFLICT (sku) DO UPDATE SET
        cost_price = EXCLUDED.cost_price,
        warranty_months = EXCLUDED.warranty_months,
        warranty_terms = EXCLUDED.warranty_terms,
        updated_at = NOW();

    -- ========================================================================
    -- PRODUCT 3: AQUAPURITE PREMIO
    -- Premium water purifier
    -- Cost: Rs.12,185 | Qty on PI: 20
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, part_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured, is_bestseller,
        extra_data, created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Aquapurite Premio',
        'aquapurite-premio',
        'AP-PREMIO-001',
        'PREMIO',
        'WPRAPM001',      -- FG Code
        'PMO',            -- Model code for barcode
        NULL,
        'FG',
        'Premium 10-stage water purifier with copper infusion',
        'Aquapurite Premio is our flagship model featuring 10-stage purification with copper infusion technology. Designed for premium households demanding the best.',
        '• 10-Stage Advanced Purification
• RO + UV + UF + Copper Infusion
• Alkaline + Mineral Booster
• 12 Liters Stainless Steel Tank
• Digital TDS Display
• Touch Panel Controls
• Auto-flush & Filter Change Alert
• Premium Design with LED Display',
        v_category_id,
        v_brand_id,
        24999.00,         -- MRP (Premium pricing)
        21999.00,         -- Selling price
        15000.00,         -- Dealer price
        12185.00,         -- Cost price (from PI)
        '842121',         -- HSN Code
        18.00,            -- GST Rate
        18,               -- Warranty months
        '18 months comprehensive warranty on electronic parts, 1 year service warranty.',
        10,               -- Lower min stock (premium product)
        'ACTIVE',
        TRUE,
        TRUE,
        TRUE,             -- Bestseller
        '{"notes": "Buyer provides: UV LED", "premium": true}'::jsonb,
        NOW(),
        NOW()
    )
    ON CONFLICT (sku) DO UPDATE SET
        cost_price = EXCLUDED.cost_price,
        warranty_months = EXCLUDED.warranty_months,
        warranty_terms = EXCLUDED.warranty_terms,
        updated_at = NOW();

    -- ========================================================================
    -- PRODUCT 4: AQUAPURITE ELITZ
    -- Elite series water purifier
    -- Cost: Rs.8,321 | Qty on PI: 25
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, part_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        extra_data, created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Aquapurite Elitz',
        'aquapurite-elitz',
        'AP-ELITZ-001',
        'ELITZ',
        'WPRAEL001',      -- FG Code
        'ELZ',            -- Model code for barcode
        NULL,
        'FG',
        'Elite RO+UV water purifier with 9-stage purification',
        'Aquapurite Elitz combines elegant design with superior performance. 9-stage purification ensures safe and healthy drinking water for your family.',
        '• 9-Stage Purification System
• RO + UV + UF Technology
• Alkaline Water Enhancement
• 10 Liters Storage Tank
• Digital TDS Controller
• Filter Change Indicator
• Smart Auto-flush
• Elegant Compact Design',
        v_category_id,
        v_brand_id,
        16999.00,         -- MRP
        14999.00,         -- Selling price
        10000.00,         -- Dealer price
        8321.00,          -- Cost price (from PI)
        '842121',         -- HSN Code
        18.00,            -- GST Rate
        18,               -- Warranty months
        '18 months warranty on electronic parts, 1 year service warranty.',
        20,
        'ACTIVE',
        TRUE,
        TRUE,
        '{"notes": "Buyer provides: UV LED"}'::jsonb,
        NOW(),
        NOW()
    )
    ON CONFLICT (sku) DO UPDATE SET
        cost_price = EXCLUDED.cost_price,
        warranty_months = EXCLUDED.warranty_months,
        warranty_terms = EXCLUDED.warranty_terms,
        updated_at = NOW();

    RAISE NOTICE 'All 4 products created successfully!';
END $$;

-- ============================================================================
-- VERIFY RESULTS
-- ============================================================================

-- Check Category
SELECT id, name, slug, is_active FROM categories WHERE slug = 'water-purifiers';

-- Check Brand
SELECT id, name, slug, is_active FROM brands WHERE slug = 'aquapurite';

-- Check Products
SELECT
    sku,
    name,
    model_number,
    fg_code,
    model_code,
    cost_price,
    dealer_price,
    selling_price,
    mrp,
    hsn_code,
    warranty_months,
    status
FROM products
WHERE sku IN ('AP-BLITZ-001', 'AP-NEURA-001', 'AP-PREMIO-001', 'AP-ELITZ-001')
ORDER BY cost_price;

-- ============================================================================
-- PRICE SUMMARY (from PI NO./FF/25-26/005)
-- ============================================================================
-- | Product | Cost (PI) | Dealer | Selling | MRP     | Margin % |
-- |---------|-----------|--------|---------|---------|----------|
-- | BLITZ   | 2,304     | 2,800  | 4,499   | 4,999   | ~95%     |
-- | NEURA   | 2,509     | 3,500  | 6,299   | 6,999   | ~151%    |
-- | ELITZ   | 8,321     | 10,000 | 14,999  | 16,999  | ~80%     |
-- | PREMIO  | 12,185    | 15,000 | 21,999  | 24,999  | ~80%     |
-- ============================================================================
