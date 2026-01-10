-- Add missing enum values to channeltype
-- Run this in Supabase SQL Editor

-- Add simplified channel type values
ALTER TYPE channeltype ADD VALUE IF NOT EXISTS 'D2C';
ALTER TYPE channeltype ADD VALUE IF NOT EXISTS 'MARKETPLACE';
ALTER TYPE channeltype ADD VALUE IF NOT EXISTS 'B2B';
ALTER TYPE channeltype ADD VALUE IF NOT EXISTS 'OFFLINE';
ALTER TYPE channeltype ADD VALUE IF NOT EXISTS 'DEALER';

-- Verify the enum values
SELECT enumlabel FROM pg_enum
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'channeltype')
ORDER BY enumsortorder;
