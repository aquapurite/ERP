-- Customer Identity Management Fixes
-- Run in Supabase SQL Editor

-- ============================================================
-- Fix #3: Phone Uniqueness Constraint
-- ============================================================
-- Verified 0 duplicate phones exist in production (4 customers)

ALTER TABLE customers
ADD CONSTRAINT uq_customers_phone UNIQUE (phone);

-- ============================================================
-- Fix #2: CRM Customer Linkage to Billing Tables
-- ============================================================
-- Add crm_customer_id (FK to customers.id) to billing tables
-- Nullable, non-breaking, backward-compatible

-- Tax Invoices
ALTER TABLE tax_invoices
ADD COLUMN crm_customer_id UUID REFERENCES customers(id) ON DELETE SET NULL;

CREATE INDEX ix_tax_invoices_crm_customer_id ON tax_invoices(crm_customer_id);

-- Credit/Debit Notes
ALTER TABLE credit_debit_notes
ADD COLUMN crm_customer_id UUID REFERENCES customers(id) ON DELETE SET NULL;

CREATE INDEX ix_credit_debit_notes_crm_customer_id ON credit_debit_notes(crm_customer_id);

-- Payment Receipts
ALTER TABLE payment_receipts
ADD COLUMN crm_customer_id UUID REFERENCES customers(id) ON DELETE SET NULL;

CREATE INDEX ix_payment_receipts_crm_customer_id ON payment_receipts(crm_customer_id);

-- ============================================================
-- Backfill crm_customer_id from orders.customer_id
-- ============================================================
-- For invoices that have an order_id, trace back to the CRM customer

UPDATE tax_invoices ti
SET crm_customer_id = o.customer_id
FROM orders o
WHERE ti.order_id = o.id
  AND o.customer_id IS NOT NULL
  AND ti.crm_customer_id IS NULL;

UPDATE payment_receipts pr
SET crm_customer_id = o.customer_id
FROM tax_invoices ti
JOIN orders o ON ti.order_id = o.id
WHERE pr.invoice_id = ti.id
  AND o.customer_id IS NOT NULL
  AND pr.crm_customer_id IS NULL;
