-- ============================================================================
-- ADD SPARE PARTS FROM PO/APL/ST/25-26/002 (STOS INDUSTRIAL)
-- TWO Categories: Economical and Premium
-- Run this in Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- Step 1: Create TWO Spare Parts Categories
-- ============================================================================
DELETE FROM categories WHERE slug IN ('spare-parts-economical', 'spare-parts-premium');

-- Category 1: Economical Spare Parts
INSERT INTO categories (
    id, name, slug, description,
    is_active, is_featured, sort_order,
    created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'Spare Parts - Economical',
    'spare-parts-economical',
    'Budget-friendly replacement parts and consumables for water purifiers - standard quality filters, membranes, cartridges',
    TRUE,
    FALSE,
    3,
    NOW(),
    NOW()
);

-- Category 2: Premium Spare Parts
INSERT INTO categories (
    id, name, slug, description,
    is_active, is_featured, sort_order,
    created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'Spare Parts - Premium',
    'spare-parts-premium',
    'Premium quality replacement parts and consumables for water purifiers - superior quality filters, membranes, cartridges',
    TRUE,
    TRUE,
    4,
    NOW(),
    NOW()
);

-- ============================================================================
-- Step 2: Create Spare Part Products
-- SKU Format:
--   Economical: SPEC + ModelCode + Serial (e.g., SPECSDF001)
--   Premium:    SPPR + ModelCode + Serial (e.g., SPPRSDF001)
-- ============================================================================
DO $$
DECLARE
    v_category_economical_id UUID;
    v_category_premium_id UUID;
    v_brand_id UUID;
BEGIN
    -- Get category IDs
    SELECT id INTO v_category_economical_id FROM categories WHERE slug = 'spare-parts-economical';
    SELECT id INTO v_category_premium_id FROM categories WHERE slug = 'spare-parts-premium';

    -- Get brand ID (Aquapurite)
    SELECT id INTO v_brand_id FROM brands WHERE slug = 'aquapurite';

    IF v_category_economical_id IS NULL THEN
        RAISE EXCEPTION 'Category "spare-parts-economical" not found!';
    END IF;

    IF v_category_premium_id IS NULL THEN
        RAISE EXCEPTION 'Category "spare-parts-premium" not found!';
    END IF;

    IF v_brand_id IS NULL THEN
        RAISE EXCEPTION 'Brand "aquapurite" not found!';
    END IF;

    -- Delete existing spare parts for clean re-run
    DELETE FROM products WHERE sku LIKE 'SPEC%' OR sku LIKE 'SPPR%';

    -- ========================================================================
    -- ECONOMICAL SPARE PARTS (SPEC prefix)
    -- ========================================================================

    -- ========================================================================
    -- EC-1: Sediment Filter (Spun Filter) 10" - ECONOMICAL
    -- Cost: Rs.76 | Qty on PO: 500
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Sediment Filter (Spun) 10" - Economical',
        'sediment-filter-spun-10-economical',
        'SPECSDF001',
        'SDF-EC-SP',
        'SPECSDF001',
        'SDF',
        'SP',
        'Economical Spun Polypropylene Sediment Filter 10 inch',
        'Budget-friendly Spun PP Sediment Filter for pre-filtration. Cost-effective option for regular maintenance.',
        '• Spun PP Construction
• 10 inch standard size
• 5 Micron filtration
• Budget-friendly option
• 3-6 months lifespan',
        v_category_economical_id,
        v_brand_id,
        199.00,
        149.00,
        100.00,
        76.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        100,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- EC-2: Pre Carbon Block (Regular) 10" - ECONOMICAL
    -- Cost: Rs.111 | Qty on PO: 500
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Pre Carbon Block (Regular) 10" - Economical',
        'pre-carbon-block-regular-10-economical',
        'SPECPCB001',
        'PCB-EC-RG',
        'SPECPCB001',
        'PCB',
        'SP',
        'Economical Standard Activated Carbon Block for chlorine removal',
        'Standard grade Activated Carbon Block filter for effective chlorine and odor removal. Cost-effective pre-RO filtration.',
        '• Standard Activated Carbon
• 10 inch standard size
• Removes chlorine & odor
• Cost-effective option
• 6-12 months lifespan',
        v_category_economical_id,
        v_brand_id,
        279.00,
        229.00,
        150.00,
        111.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        100,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- EC-3: Alkaline Mineral Block - ECONOMICAL
    -- Cost: Rs.61 | Qty on PO: 500
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Alkaline Mineral Block - Economical',
        'alkaline-mineral-block-economical',
        'SPECALK001',
        'ALK-EC-01',
        'SPECALK001',
        'ALK',
        'SP',
        'Economical Alkaline filter for pH balance and mineral enhancement',
        'Budget-friendly Alkaline Mineral Block increases water pH and adds essential minerals. Standard quality for regular use.',
        '• Increases pH to 8-9
• Adds essential minerals
• Standard quality
• Budget-friendly
• 6-12 months lifespan',
        v_category_economical_id,
        v_brand_id,
        199.00,
        149.00,
        90.00,
        61.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        100,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- EC-4: Post Carbon with Copper - ECONOMICAL
    -- Cost: Rs.58 | Qty on PO: 500
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Post Carbon with Copper - Economical',
        'post-carbon-copper-economical',
        'SPECPOC001',
        'POC-EC-CU',
        'SPECPOC001',
        'POC',
        'SP',
        'Economical Post carbon filter with copper infusion',
        'Budget-friendly Post Carbon filter with copper. Standard quality for taste enhancement and copper benefits.',
        '• Activated Carbon Polishing
• Copper Infusion
• Standard quality
• Budget-friendly
• 6-12 months lifespan',
        v_category_economical_id,
        v_brand_id,
        179.00,
        139.00,
        85.00,
        58.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        100,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- EC-5: RO Membrane (Regular) 80 GPD - ECONOMICAL
    -- Cost: Rs.375 | Qty on PO: 200
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'RO Membrane (Regular) 80 GPD - Economical',
        'ro-membrane-regular-80gpd-economical',
        'SPECMBF001',
        'MBF-EC-80',
        'SPECMBF001',
        'MBF',
        'SP',
        'Economical Standard 80 GPD RO membrane for medium TDS water',
        'Standard grade RO Membrane with 80 GPD capacity. Suitable for TDS up to 1500 ppm. Cost-effective replacement option.',
        '• 80 GPD Capacity
• Standard Grade
• Up to 1500 TDS handling
• 90%+ rejection rate
• 12-18 months lifespan',
        v_category_economical_id,
        v_brand_id,
        899.00,
        699.00,
        500.00,
        375.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        50,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- EC-6: Prefilter with Spun Filter - ECONOMICAL
    -- Cost: Rs.225 | Qty on PO: 200
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Prefilter with Spun Filter - Economical',
        'prefilter-with-spun-economical',
        'SPECPFS001',
        'PFS-EC-SP',
        'SPECPFS001',
        'PFS',
        'SP',
        'Economical Complete prefilter assembly with housing and spun filter',
        'Budget-friendly Pre-filter assembly with housing and spun filter cartridge. Economical option for new installations.',
        '• Complete Assembly
• Housing included
• Spun filter cartridge
• Economical option
• 3-6 months filter life',
        v_category_economical_id,
        v_brand_id,
        549.00,
        449.00,
        310.00,
        225.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        50,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- EC-7: Plastic PRV (Pressure Reducing Valve) - ECONOMICAL
    -- Cost: Rs.180 | Qty on PO: 200
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Plastic PRV (Pressure Reducing Valve) - Economical',
        'plastic-prv-economical',
        'SPECPRV001',
        'PRV-EC-PL',
        'SPECPRV001',
        'PRV',
        'SP',
        'Economical Plastic Pressure reducing valve for RO system',
        'Budget-friendly Plastic PRV protects RO membranes from high inlet pressure. Economical option for standard installations.',
        '• Pressure Regulation
• Protects RO membrane
• Plastic construction
• 1/4" connections
• Economical option',
        v_category_economical_id,
        v_brand_id,
        449.00,
        349.00,
        240.00,
        180.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        50,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- PREMIUM SPARE PARTS (SPPR prefix)
    -- ========================================================================

    -- ========================================================================
    -- PR-1: Sediment Filter (PP Yarn Wound) 10" - PREMIUM
    -- Cost: Rs.97 | Qty on PO: 500
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Sediment Filter (PP Yarn Wound) 10" - Premium',
        'sediment-filter-pp-yarn-wound-10-premium',
        'SPPRSDF001',
        'SDF-PR-YW',
        'SPPRSDF001',
        'SDF',
        'SP',
        'Premium PP Yarn Wound Sediment Filter 10 inch for superior pre-filtration',
        'High-quality PP Yarn Wound Sediment Filter removes sand, silt, rust and sediments with superior efficiency. Premium quality for best results.',
        '• PP Yarn Wound Construction
• 10 inch standard size
• 5 Micron filtration
• Superior sediment removal
• 3-6 months lifespan',
        v_category_premium_id,
        v_brand_id,
        249.00,
        199.00,
        130.00,
        97.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        100,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- PR-2: Pre Carbon Block (Premium) 10" - PREMIUM
    -- Cost: Rs.114 | Qty on PO: 500
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Pre Carbon Block (Premium) 10" - Premium',
        'pre-carbon-block-premium-10-premium',
        'SPPRPCB001',
        'PCB-PR-PR',
        'SPPRPCB001',
        'PCB',
        'SP',
        'Premium Activated Carbon Block for superior chlorine and odor removal',
        'Premium grade Activated Carbon Block filter removes chlorine, bad taste, odor and organic compounds with superior efficiency.',
        '• Premium Activated Carbon
• 10 inch standard size
• Superior chlorine removal
• Reduces organic compounds
• 6-12 months lifespan',
        v_category_premium_id,
        v_brand_id,
        299.00,
        249.00,
        160.00,
        114.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        100,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- PR-3: RO Membrane (Premium) 80 GPD - PREMIUM
    -- Cost: Rs.398 | Qty on PO: 200
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'RO Membrane (Premium) 80 GPD - Premium',
        'ro-membrane-premium-80gpd-premium',
        'SPPRMBF001',
        'MBF-PR-80',
        'SPPRMBF001',
        'MBF',
        'SP',
        'Premium 80 GPD RO membrane for high TDS water',
        'Premium grade RO Membrane with 80 GPD capacity. Handles high TDS water up to 2000 ppm with excellent 95%+ rejection rate.',
        '• 80 GPD Capacity
• Premium Grade
• Up to 2000 TDS handling
• 95%+ rejection rate
• 12-18 months lifespan',
        v_category_premium_id,
        v_brand_id,
        999.00,
        799.00,
        550.00,
        398.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        50,
        'ACTIVE',
        TRUE,
        TRUE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- PR-4: Pre-Filter Multi Layer Candle - PREMIUM
    -- Cost: Rs.245 | Qty on PO: 200
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Pre-Filter Multi Layer Candle - Premium',
        'prefilter-multi-layer-candle-premium',
        'SPPRPFC001',
        'PFC-PR-ML',
        'SPPRPFC001',
        'PFC',
        'SP',
        'Premium Multi-layer pre-filter candle for comprehensive sediment removal',
        'Multi-layer Pre-Filter Candle with graduated filtration layers for comprehensive removal of sediments and larger particles.',
        '• Multi-layer construction
• Graduated filtration
• Superior sediment removal
• Extended lifespan
• 6-9 months lifespan',
        v_category_premium_id,
        v_brand_id,
        599.00,
        499.00,
        340.00,
        245.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        50,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- PR-5: HMR Cartridge - PREMIUM
    -- Cost: Rs.801 | Qty on PO: 100
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'HMR Cartridge - Premium',
        'hmr-cartridge-premium',
        'SPPRHMR001',
        'HMR-PR-CT',
        'SPPRHMR001',
        'HMR',
        'SP',
        'Premium Heavy Metal Remover cartridge for arsenic and lead removal',
        'Premium HMR (Heavy Metal Remover) Cartridge effectively removes heavy metals like arsenic, lead, mercury with KDF media.',
        '• Heavy Metal Removal
• Arsenic & Lead removal
• Mercury filtration
• Premium KDF media
• 12 months lifespan',
        v_category_premium_id,
        v_brand_id,
        1999.00,
        1599.00,
        1100.00,
        801.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        25,
        'ACTIVE',
        TRUE,
        TRUE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- PR-6: Prefilter with Multilayer Candle (Housing) - PREMIUM
    -- Cost: Rs.280 | Qty on PO: 200
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Prefilter with Multilayer Candle (Housing) - Premium',
        'prefilter-multilayer-housing-premium',
        'SPPRPFC002',
        'PFC-PR-HS',
        'SPPRPFC002',
        'PFC',
        'SP',
        'Premium Complete prefilter assembly with housing and multilayer candle',
        'Premium Pre-filter assembly includes housing and multilayer candle. Ready to install unit with superior filtration.',
        '• Complete Assembly
• Housing included
• Multilayer candle
• Premium quality
• 6-9 months filter life',
        v_category_premium_id,
        v_brand_id,
        699.00,
        549.00,
        380.00,
        280.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        50,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- PR-7: Heavy Metal Remover (Inline) - PREMIUM
    -- Cost: Rs.850 | Qty on PO: 100
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Heavy Metal Remover (Inline) - Premium',
        'hmr-inline-premium',
        'SPPRHMR002',
        'HMR-PR-IL',
        'SPPRHMR002',
        'HMR',
        'SP',
        'Premium Inline Heavy Metal Remover for post-RO installation',
        'Premium Inline HMR filter for post-RO installation. Compact design with superior heavy metal removal capability.',
        '• Inline design
• Post-RO installation
• Compact size
• Premium quality
• 12 months lifespan',
        v_category_premium_id,
        v_brand_id,
        2199.00,
        1799.00,
        1200.00,
        850.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        25,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    -- ========================================================================
    -- PR-8: Brass Diverter Valve - PREMIUM
    -- Cost: Rs.150 | Qty on PO: 200
    -- ========================================================================
    INSERT INTO products (
        id, name, slug, sku, model_number, fg_code, model_code, item_type,
        short_description, description, features,
        category_id, brand_id,
        mrp, selling_price, dealer_price, cost_price,
        hsn_code, gst_rate,
        warranty_months, warranty_terms,
        min_stock_level, status, is_active, is_featured,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(),
        'Brass Diverter Valve - Premium',
        'brass-diverter-valve-premium',
        'SPPRBDV001',
        'BDV-PR-BR',
        'SPPRBDV001',
        'BDV',
        'SP',
        'Premium Brass diverter valve for kitchen faucet connection',
        'High-quality Brass Diverter Valve for connecting RO system to kitchen faucet. Durable brass construction with leak-proof design.',
        '• Brass construction
• Kitchen faucet mount
• Leak-proof design
• 1/4" RO connection
• Premium quality',
        v_category_premium_id,
        v_brand_id,
        399.00,
        299.00,
        200.00,
        150.00,
        '84212190',
        18.00,
        6,
        '6 months warranty against manufacturing defects',
        50,
        'ACTIVE',
        TRUE,
        FALSE,
        NOW(),
        NOW()
    );

    RAISE NOTICE 'All 15 spare parts created successfully! (7 Economical + 8 Premium)';
END $$;

-- ============================================================================
-- Step 3: Create Model Code References for Serialization
-- ============================================================================
DELETE FROM model_code_references WHERE fg_code LIKE 'SPEC%' OR fg_code LIKE 'SPPR%';

-- Economical Model Codes
INSERT INTO model_code_references (id, fg_code, model_code, item_type, description, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid()::text, 'SPECSDF001', 'SDF', 'SPARE_PART', 'Sediment Filter - Economical', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPECPCB001', 'PCB', 'SPARE_PART', 'Pre Carbon Block - Economical', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPECALK001', 'ALK', 'SPARE_PART', 'Alkaline Mineral - Economical', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPECPOC001', 'POC', 'SPARE_PART', 'Post Carbon - Economical', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPECMBF001', 'MBF', 'SPARE_PART', 'RO Membrane - Economical', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPECPFS001', 'PFS', 'SPARE_PART', 'Prefilter with Spun - Economical', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPECPRV001', 'PRV', 'SPARE_PART', 'Pressure Reducing Valve - Economical', TRUE, NOW(), NOW());

-- Premium Model Codes
INSERT INTO model_code_references (id, fg_code, model_code, item_type, description, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid()::text, 'SPPRSDF001', 'SDF', 'SPARE_PART', 'Sediment Filter - Premium', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPPRPCB001', 'PCB', 'SPARE_PART', 'Pre Carbon Block - Premium', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPPRMBF001', 'MBF', 'SPARE_PART', 'RO Membrane - Premium', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPPRPFC001', 'PFC', 'SPARE_PART', 'Pre-Filter Candle - Premium', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPPRPFC002', 'PFC', 'SPARE_PART', 'Pre-Filter Housing - Premium', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPPRHMR001', 'HMR', 'SPARE_PART', 'HMR Cartridge - Premium', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPPRHMR002', 'HMR', 'SPARE_PART', 'HMR Inline - Premium', TRUE, NOW(), NOW()),
    (gen_random_uuid()::text, 'SPPRBDV001', 'BDV', 'SPARE_PART', 'Brass Diverter Valve - Premium', TRUE, NOW(), NOW());

-- ============================================================================
-- VERIFY RESULTS
-- ============================================================================

-- Check Categories
SELECT id, name, slug, is_active, sort_order FROM categories WHERE slug LIKE 'spare-parts%';

-- Check Spare Parts Count by Category
SELECT
    c.name as category,
    COUNT(p.id) as product_count
FROM products p
JOIN categories c ON p.category_id = c.id
WHERE c.slug LIKE 'spare-parts%'
GROUP BY c.name;

-- Check Economical Products
SELECT sku, name, cost_price, selling_price, mrp
FROM products
WHERE sku LIKE 'SPEC%'
ORDER BY sku;

-- Check Premium Products
SELECT sku, name, cost_price, selling_price, mrp
FROM products
WHERE sku LIKE 'SPPR%'
ORDER BY sku;

-- Check Model Code References
SELECT fg_code, model_code, item_type, description
FROM model_code_references
WHERE fg_code LIKE 'SPEC%' OR fg_code LIKE 'SPPR%'
ORDER BY fg_code;

-- ============================================================================
-- SPARE PARTS SUMMARY
-- ============================================================================
--
-- ECONOMICAL (7 products) - SPEC prefix:
-- | SKU        | Description                  | Cost  | Selling | MRP   |
-- |------------|------------------------------|-------|---------|-------|
-- | SPECSDF001 | Sediment Filter (Spun)       | 76    | 149     | 199   |
-- | SPECPCB001 | Pre Carbon Block (Regular)   | 111   | 229     | 279   |
-- | SPECALK001 | Alkaline Mineral Block       | 61    | 149     | 199   |
-- | SPECPOC001 | Post Carbon with Copper      | 58    | 139     | 179   |
-- | SPECMBF001 | RO Membrane (Regular)        | 375   | 699     | 899   |
-- | SPECPFS001 | Prefilter with Spun          | 225   | 449     | 549   |
-- | SPECPRV001 | Plastic PRV                  | 180   | 349     | 449   |
--
-- PREMIUM (8 products) - SPPR prefix:
-- | SKU        | Description                  | Cost  | Selling | MRP   |
-- |------------|------------------------------|-------|---------|-------|
-- | SPPRSDF001 | Sediment Filter (Yarn Wound) | 97    | 199     | 249   |
-- | SPPRPCB001 | Pre Carbon Block (Premium)   | 114   | 249     | 299   |
-- | SPPRMBF001 | RO Membrane (Premium)        | 398   | 799     | 999   |
-- | SPPRPFC001 | Pre-Filter Multi Layer       | 245   | 499     | 599   |
-- | SPPRPFC002 | Prefilter w/ Housing         | 280   | 549     | 699   |
-- | SPPRHMR001 | HMR Cartridge                | 801   | 1599    | 1999  |
-- | SPPRHMR002 | HMR Inline                   | 850   | 1799    | 2199  |
-- | SPPRBDV001 | Brass Diverter Valve         | 150   | 299     | 399   |
--
-- ============================================================================
