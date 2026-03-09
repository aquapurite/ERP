-- Migration: Add expense_voucher_lines table for multi-line expense vouchers
-- Each line captures a separate expense category, amount, and GST rate

CREATE TABLE IF NOT EXISTS expense_voucher_lines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  voucher_id UUID NOT NULL REFERENCES expense_vouchers(id) ON DELETE CASCADE,
  line_number INT NOT NULL DEFAULT 1,
  expense_category_id UUID REFERENCES expense_categories(id),
  description TEXT,
  amount DECIMAL(18,2) NOT NULL,
  gst_rate DECIMAL(5,2) DEFAULT 0,
  gst_amount DECIMAL(18,2) DEFAULT 0,
  cost_center_id UUID REFERENCES cost_centers(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evl_voucher ON expense_voucher_lines(voucher_id);
CREATE INDEX IF NOT EXISTS idx_evl_category ON expense_voucher_lines(expense_category_id);
