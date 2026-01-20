-- Fix missing device_fingerprint column in abandoned_carts table
-- Run this in Supabase SQL Editor

-- Add the missing column
ALTER TABLE abandoned_carts
ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(100);

-- Add comment for documentation
COMMENT ON COLUMN abandoned_carts.device_fingerprint IS 'Device fingerprint for cross-session tracking';

-- Verify the column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'abandoned_carts'
  AND column_name = 'device_fingerprint';
