-- Migration Batch 4
-- Tables 91 to 120

-- Table: supplier_codes

CREATE TABLE IF NOT EXISTS supplier_codes (
	id VARCHAR(36) NOT NULL, 
	vendor_id VARCHAR(36), 
	code VARCHAR(2) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description VARCHAR(255), 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (vendor_id), 
	FOREIGN KEY(vendor_id) REFERENCES vendors (id)
)

;

-- Table: technician_leaves

CREATE TABLE IF NOT EXISTS technician_leaves (
	id UUID NOT NULL, 
	technician_id UUID NOT NULL, 
	leave_type VARCHAR(50), 
	from_date DATE NOT NULL, 
	to_date DATE NOT NULL, 
	reason TEXT, 
	status VARCHAR(50), 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	rejection_reason TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(technician_id) REFERENCES technicians (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id)
)

;

-- Table: unsubscribe_list

CREATE TABLE IF NOT EXISTS unsubscribe_list (
	id UUID NOT NULL, 
	customer_id UUID, 
	email VARCHAR(255), 
	phone VARCHAR(20), 
	channel campaigntype NOT NULL, 
	reason TEXT, 
	source_campaign_id UUID, 
	unsubscribed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE SET NULL, 
	FOREIGN KEY(source_campaign_id) REFERENCES campaigns (id) ON DELETE SET NULL
)

;

-- Table: vendor_contacts

CREATE TABLE IF NOT EXISTS vendor_contacts (
	id UUID NOT NULL, 
	vendor_id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	designation VARCHAR(100), 
	department VARCHAR(50), 
	email VARCHAR(100), 
	phone VARCHAR(20), 
	mobile VARCHAR(20), 
	is_primary BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(vendor_id) REFERENCES vendors (id) ON DELETE CASCADE
)

;

-- Table: vendor_ledger

CREATE TABLE IF NOT EXISTS vendor_ledger (
	id UUID NOT NULL, 
	vendor_id UUID NOT NULL, 
	transaction_type vendortransactiontype NOT NULL, 
	transaction_date DATE NOT NULL, 
	due_date DATE, 
	reference_type VARCHAR(50) NOT NULL, 
	reference_number VARCHAR(50) NOT NULL, 
	reference_id UUID, 
	vendor_invoice_number VARCHAR(50), 
	vendor_invoice_date DATE, 
	debit_amount NUMERIC(14, 2) NOT NULL, 
	credit_amount NUMERIC(14, 2) NOT NULL, 
	running_balance NUMERIC(14, 2) NOT NULL, 
	tds_amount NUMERIC(12, 2) NOT NULL, 
	tds_section VARCHAR(10), 
	payment_mode VARCHAR(20), 
	payment_reference VARCHAR(100), 
	bank_name VARCHAR(100), 
	cheque_number VARCHAR(20), 
	cheque_date DATE, 
	is_settled BOOLEAN NOT NULL, 
	settled_date DATE, 
	days_overdue INTEGER NOT NULL, 
	narration TEXT, 
	created_by UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(vendor_id) REFERENCES vendors (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: warehouse_bins

CREATE TABLE IF NOT EXISTS warehouse_bins (
	id UUID NOT NULL, 
	warehouse_id UUID NOT NULL, 
	zone_id UUID, 
	bin_code VARCHAR(50) NOT NULL, 
	bin_name VARCHAR(200), 
	barcode VARCHAR(100), 
	aisle VARCHAR(10), 
	rack VARCHAR(10), 
	shelf VARCHAR(10), 
	position VARCHAR(10), 
	bin_type bintype NOT NULL, 
	length FLOAT, 
	width FLOAT, 
	height FLOAT, 
	max_capacity INTEGER, 
	max_weight_kg FLOAT, 
	current_items INTEGER NOT NULL, 
	current_weight_kg FLOAT NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	is_reserved BOOLEAN NOT NULL, 
	is_pickable BOOLEAN NOT NULL, 
	is_receivable BOOLEAN NOT NULL, 
	reserved_product_id UUID, 
	pick_sequence INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	last_activity_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_warehouse_bin_code UNIQUE (warehouse_id, bin_code), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE CASCADE, 
	FOREIGN KEY(zone_id) REFERENCES warehouse_zones (id) ON DELETE SET NULL, 
	FOREIGN KEY(reserved_product_id) REFERENCES products (id) ON DELETE SET NULL
)

;

-- Table: affiliate_referrals

CREATE TABLE IF NOT EXISTS affiliate_referrals (
	id UUID NOT NULL, 
	earner_id UUID NOT NULL, 
	referral_code VARCHAR(30) NOT NULL, 
	customer_id UUID, 
	customer_email VARCHAR(255), 
	customer_phone VARCHAR(20), 
	order_id UUID, 
	click_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	source_url VARCHAR(500), 
	landing_page VARCHAR(500), 
	utm_source VARCHAR(100), 
	utm_medium VARCHAR(100), 
	utm_campaign VARCHAR(100), 
	ip_address VARCHAR(50), 
	user_agent VARCHAR(500), 
	device_type VARCHAR(30), 
	is_converted BOOLEAN NOT NULL, 
	converted_at TIMESTAMP WITHOUT TIME ZONE, 
	conversion_value NUMERIC(14, 2), 
	attribution_window_days INTEGER NOT NULL, 
	is_first_order BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(earner_id) REFERENCES commission_earners (id) ON DELETE CASCADE, 
	FOREIGN KEY(customer_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE SET NULL
)

;

-- Table: allocation_logs

CREATE TABLE IF NOT EXISTS allocation_logs (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	rule_id UUID, 
	warehouse_id UUID, 
	customer_pincode VARCHAR(10) NOT NULL, 
	is_successful BOOLEAN NOT NULL, 
	failure_reason VARCHAR(500), 
	decision_factors TEXT, 
	candidates_considered TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(rule_id) REFERENCES allocation_rules (id) ON DELETE SET NULL, 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL
)

;

-- Table: campaign_automation_logs

CREATE TABLE IF NOT EXISTS campaign_automation_logs (
	id UUID NOT NULL, 
	automation_id UUID NOT NULL, 
	customer_id UUID NOT NULL, 
	trigger_entity_type VARCHAR(50), 
	trigger_entity_id UUID, 
	status VARCHAR(20) NOT NULL, 
	skip_reason TEXT, 
	recipient_id UUID, 
	triggered_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	sent_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(automation_id) REFERENCES campaign_automations (id) ON DELETE CASCADE, 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE, 
	FOREIGN KEY(recipient_id) REFERENCES campaign_recipients (id) ON DELETE SET NULL
)

;

-- Table: channel_commission_earnings

CREATE TABLE IF NOT EXISTS channel_commission_earnings (
	id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	channel_code VARCHAR(30) NOT NULL, 
	beneficiary_type commissionbeneficiary NOT NULL, 
	beneficiary_id UUID NOT NULL, 
	beneficiary_name VARCHAR(200) NOT NULL, 
	order_id UUID, 
	order_number VARCHAR(50) NOT NULL, 
	order_date DATE NOT NULL, 
	earning_date DATE NOT NULL, 
	order_value NUMERIC(14, 2) NOT NULL, 
	commission_base NUMERIC(14, 2) NOT NULL, 
	commission_rate NUMERIC(5, 2) NOT NULL, 
	commission_amount NUMERIC(12, 2) NOT NULL, 
	tds_rate NUMERIC(5, 2) NOT NULL, 
	tds_amount NUMERIC(10, 2) NOT NULL, 
	other_deductions NUMERIC(10, 2) NOT NULL, 
	net_amount NUMERIC(12, 2) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	eligible_date DATE, 
	is_paid BOOLEAN NOT NULL, 
	paid_at TIMESTAMP WITHOUT TIME ZONE, 
	payout_reference VARCHAR(50), 
	is_clawed_back BOOLEAN NOT NULL, 
	clawback_date DATE, 
	clawback_reason VARCHAR(500), 
	clawback_amount NUMERIC(12, 2) NOT NULL, 
	parent_earning_id UUID, 
	level INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(plan_id) REFERENCES channel_commission_plans (id) ON DELETE RESTRICT, 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE SET NULL, 
	FOREIGN KEY(parent_earning_id) REFERENCES channel_commission_earnings (id) ON DELETE SET NULL
)

;

-- Table: channel_orders

CREATE TABLE IF NOT EXISTS channel_orders (
	id UUID NOT NULL, 
	channel_id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	channel_order_id VARCHAR(100) NOT NULL, 
	channel_order_item_id VARCHAR(100), 
	channel_selling_price NUMERIC(12, 2) NOT NULL, 
	channel_shipping_fee NUMERIC(10, 2) NOT NULL, 
	channel_commission NUMERIC(10, 2) NOT NULL, 
	channel_tcs NUMERIC(10, 2) NOT NULL, 
	net_receivable NUMERIC(12, 2) NOT NULL, 
	channel_status VARCHAR(100), 
	raw_order_data JSON, 
	synced_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	last_status_sync_at TIMESTAMP WITHOUT TIME ZONE, 
	settlement_id VARCHAR(100), 
	settlement_date TIMESTAMP WITHOUT TIME ZONE, 
	is_settled BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_channel_order UNIQUE (channel_id, channel_order_id), 
	FOREIGN KEY(channel_id) REFERENCES sales_channels (id) ON DELETE RESTRICT, 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE
)

;

-- Table: commission_payout_lines

CREATE TABLE IF NOT EXISTS commission_payout_lines (
	id UUID NOT NULL, 
	payout_id UUID NOT NULL, 
	earner_id UUID NOT NULL, 
	gross_amount NUMERIC(12, 2) NOT NULL, 
	tds_amount NUMERIC(10, 2) NOT NULL, 
	other_deductions NUMERIC(10, 2) NOT NULL, 
	net_amount NUMERIC(12, 2) NOT NULL, 
	transaction_count INTEGER NOT NULL, 
	payment_mode VARCHAR(30) NOT NULL, 
	bank_name VARCHAR(200), 
	account_number VARCHAR(30), 
	ifsc_code VARCHAR(11), 
	upi_id VARCHAR(100), 
	payment_status VARCHAR(20) NOT NULL, 
	payment_reference VARCHAR(100), 
	payment_date TIMESTAMP WITHOUT TIME ZONE, 
	failure_reason VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_payout_earner UNIQUE (payout_id, earner_id), 
	FOREIGN KEY(payout_id) REFERENCES commission_payouts (id) ON DELETE CASCADE, 
	FOREIGN KEY(earner_id) REFERENCES commission_earners (id) ON DELETE CASCADE
)

;

-- Table: commission_transactions

CREATE TABLE IF NOT EXISTS commission_transactions (
	id UUID NOT NULL, 
	earner_id UUID NOT NULL, 
	order_id UUID, 
	service_request_id UUID, 
	transaction_date DATE NOT NULL, 
	transaction_reference VARCHAR(50) NOT NULL, 
	order_value NUMERIC(14, 2) NOT NULL, 
	commission_base NUMERIC(14, 2) NOT NULL, 
	commission_rate NUMERIC(5, 2) NOT NULL, 
	commission_amount NUMERIC(12, 2) NOT NULL, 
	tds_rate NUMERIC(5, 2) NOT NULL, 
	tds_amount NUMERIC(10, 2) NOT NULL, 
	other_deductions NUMERIC(10, 2) NOT NULL, 
	deduction_remarks VARCHAR(500), 
	net_amount NUMERIC(12, 2) NOT NULL, 
	status commissionstatus NOT NULL, 
	status_reason VARCHAR(500), 
	eligible_date DATE, 
	is_eligible BOOLEAN NOT NULL, 
	payout_id UUID, 
	paid_at TIMESTAMP WITHOUT TIME ZONE, 
	is_clawed_back BOOLEAN NOT NULL, 
	clawback_date DATE, 
	clawback_reason VARCHAR(500), 
	parent_transaction_id UUID, 
	level INTEGER NOT NULL, 
	remarks VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(earner_id) REFERENCES commission_earners (id) ON DELETE CASCADE, 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE SET NULL, 
	FOREIGN KEY(payout_id) REFERENCES commission_payouts (id) ON DELETE SET NULL, 
	FOREIGN KEY(parent_transaction_id) REFERENCES commission_transactions (id) ON DELETE SET NULL
)

;

-- Table: customer_referrals

CREATE TABLE IF NOT EXISTS customer_referrals (
	id UUID NOT NULL, 
	program_id UUID NOT NULL, 
	referrer_id UUID NOT NULL, 
	referral_code VARCHAR(20) NOT NULL, 
	referee_id UUID, 
	referee_email VARCHAR(255), 
	referee_phone VARCHAR(20), 
	channel_code VARCHAR(30), 
	order_id UUID, 
	order_value NUMERIC(14, 2), 
	status VARCHAR(30) NOT NULL, 
	referrer_reward NUMERIC(10, 2) NOT NULL, 
	referrer_rewarded_at TIMESTAMP WITHOUT TIME ZONE, 
	referee_reward NUMERIC(10, 2) NOT NULL, 
	referee_rewarded_at TIMESTAMP WITHOUT TIME ZONE, 
	referred_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	registered_at TIMESTAMP WITHOUT TIME ZONE, 
	ordered_at TIMESTAMP WITHOUT TIME ZONE, 
	delivered_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(program_id) REFERENCES referral_programs (id) ON DELETE RESTRICT, 
	FOREIGN KEY(referrer_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(referee_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE SET NULL
)

;

-- Table: dealer_scheme_applications

CREATE TABLE IF NOT EXISTS dealer_scheme_applications (
	id UUID NOT NULL, 
	scheme_id UUID NOT NULL, 
	dealer_id UUID NOT NULL, 
	order_id UUID, 
	application_date DATE NOT NULL, 
	order_value NUMERIC(14, 2) NOT NULL, 
	discount_calculated NUMERIC(12, 2) NOT NULL, 
	is_approved BOOLEAN NOT NULL, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(scheme_id) REFERENCES dealer_schemes (id) ON DELETE CASCADE, 
	FOREIGN KEY(dealer_id) REFERENCES dealers (id) ON DELETE CASCADE, 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE SET NULL
)

;

-- Table: escalation_comments

CREATE TABLE IF NOT EXISTS escalation_comments (
	id UUID NOT NULL, 
	escalation_id UUID NOT NULL, 
	comment TEXT NOT NULL, 
	is_internal BOOLEAN NOT NULL, 
	is_system BOOLEAN NOT NULL, 
	attachments JSON, 
	created_by_id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(escalation_id) REFERENCES escalations (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

-- Table: escalation_history

CREATE TABLE IF NOT EXISTS escalation_history (
	id UUID NOT NULL, 
	escalation_id UUID NOT NULL, 
	from_level escalationlevel, 
	to_level escalationlevel NOT NULL, 
	from_status escalationstatus, 
	to_status escalationstatus NOT NULL, 
	from_assignee_id UUID, 
	to_assignee_id UUID, 
	action VARCHAR(50) NOT NULL, 
	reason TEXT, 
	notes TEXT, 
	is_auto BOOLEAN NOT NULL, 
	trigger_type VARCHAR(50), 
	changed_by_id UUID NOT NULL, 
	changed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(escalation_id) REFERENCES escalations (id) ON DELETE CASCADE, 
	FOREIGN KEY(changed_by_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

-- Table: escalation_notifications

CREATE TABLE IF NOT EXISTS escalation_notifications (
	id UUID NOT NULL, 
	escalation_id UUID NOT NULL, 
	channel notificationchannel NOT NULL, 
	recipient_type VARCHAR(20) NOT NULL, 
	recipient_id UUID, 
	recipient_email VARCHAR(255), 
	recipient_phone VARCHAR(20), 
	subject VARCHAR(255), 
	message TEXT NOT NULL, 
	sent_at TIMESTAMP WITHOUT TIME ZONE, 
	delivered_at TIMESTAMP WITHOUT TIME ZONE, 
	read_at TIMESTAMP WITHOUT TIME ZONE, 
	failed_at TIMESTAMP WITHOUT TIME ZONE, 
	failure_reason TEXT, 
	retry_count INTEGER NOT NULL, 
	max_retries INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(escalation_id) REFERENCES escalations (id) ON DELETE CASCADE
)

;

-- Table: goods_receipt_notes

CREATE TABLE IF NOT EXISTS goods_receipt_notes (
	id UUID NOT NULL, 
	grn_number VARCHAR(30) NOT NULL, 
	grn_date DATE NOT NULL, 
	status grnstatus NOT NULL, 
	purchase_order_id UUID NOT NULL, 
	vendor_id UUID NOT NULL, 
	warehouse_id UUID NOT NULL, 
	vendor_challan_number VARCHAR(50), 
	vendor_challan_date DATE, 
	transporter_name VARCHAR(100), 
	vehicle_number VARCHAR(20), 
	lr_number VARCHAR(50), 
	e_way_bill_number VARCHAR(20), 
	total_items INTEGER NOT NULL, 
	total_quantity_received INTEGER NOT NULL, 
	total_quantity_accepted INTEGER NOT NULL, 
	total_quantity_rejected INTEGER NOT NULL, 
	total_value NUMERIC(14, 2) NOT NULL, 
	qc_required BOOLEAN NOT NULL, 
	qc_status qualitycheckresult, 
	qc_done_by UUID, 
	qc_done_at TIMESTAMP WITHOUT TIME ZONE, 
	qc_remarks TEXT, 
	received_by UUID NOT NULL, 
	receiving_remarks TEXT, 
	put_away_complete BOOLEAN NOT NULL, 
	put_away_at TIMESTAMP WITHOUT TIME ZONE, 
	grn_pdf_url VARCHAR(500), 
	photos_urls JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(purchase_order_id) REFERENCES purchase_orders (id) ON DELETE RESTRICT, 
	FOREIGN KEY(vendor_id) REFERENCES vendors (id) ON DELETE RESTRICT, 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
	FOREIGN KEY(qc_done_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(received_by) REFERENCES users (id) ON DELETE RESTRICT
)

;

-- Table: invoices

CREATE TABLE IF NOT EXISTS invoices (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	invoice_number VARCHAR(30) NOT NULL, 
	subtotal NUMERIC(12, 2) NOT NULL, 
	tax_amount NUMERIC(12, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	total_amount NUMERIC(12, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	pdf_url VARCHAR(500), 
	invoice_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	due_date TIMESTAMP WITHOUT TIME ZONE, 
	is_cancelled BOOLEAN NOT NULL, 
	cancelled_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (order_id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE
)

;

-- Table: journal_entry_lines

CREATE TABLE IF NOT EXISTS journal_entry_lines (
	id UUID NOT NULL, 
	journal_entry_id UUID NOT NULL, 
	account_id UUID NOT NULL, 
	debit_amount NUMERIC(15, 2) NOT NULL, 
	credit_amount NUMERIC(15, 2) NOT NULL, 
	cost_center_id UUID, 
	description TEXT, 
	line_number INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(journal_entry_id) REFERENCES journal_entries (id) ON DELETE CASCADE, 
	FOREIGN KEY(account_id) REFERENCES chart_of_accounts (id) ON DELETE RESTRICT, 
	FOREIGN KEY(cost_center_id) REFERENCES cost_centers (id) ON DELETE SET NULL
)

;

-- Table: order_items

CREATE TABLE IF NOT EXISTS order_items (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	product_name VARCHAR(255) NOT NULL, 
	product_sku VARCHAR(50) NOT NULL, 
	variant_name VARCHAR(255), 
	quantity INTEGER NOT NULL, 
	unit_price NUMERIC(12, 2) NOT NULL, 
	unit_mrp NUMERIC(12, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	tax_rate NUMERIC(5, 2) NOT NULL, 
	tax_amount NUMERIC(12, 2) NOT NULL, 
	total_amount NUMERIC(12, 2) NOT NULL, 
	hsn_code VARCHAR(20), 
	warranty_months INTEGER NOT NULL, 
	serial_number VARCHAR(100), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id) ON DELETE SET NULL
)

;

-- Table: order_status_history

CREATE TABLE IF NOT EXISTS order_status_history (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	from_status orderstatus, 
	to_status orderstatus NOT NULL, 
	changed_by UUID, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(changed_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: payments

CREATE TABLE IF NOT EXISTS payments (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	amount NUMERIC(12, 2) NOT NULL, 
	method paymentmethod NOT NULL, 
	status paymentstatus NOT NULL, 
	transaction_id VARCHAR(100), 
	gateway VARCHAR(50), 
	gateway_response JSON, 
	reference_number VARCHAR(100), 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE
)

;

-- Table: promotion_usage

CREATE TABLE IF NOT EXISTS promotion_usage (
	id UUID NOT NULL, 
	promotion_id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	customer_id UUID, 
	dealer_id UUID, 
	channel_code VARCHAR(30) NOT NULL, 
	usage_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	order_value NUMERIC(14, 2) NOT NULL, 
	discount_applied NUMERIC(12, 2) NOT NULL, 
	cashback_earned NUMERIC(12, 2) NOT NULL, 
	is_reversed BOOLEAN NOT NULL, 
	reversed_at TIMESTAMP WITHOUT TIME ZONE, 
	reversal_reason VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(promotion_id) REFERENCES promotions (id) ON DELETE CASCADE, 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(customer_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(dealer_id) REFERENCES dealers (id) ON DELETE SET NULL
)

;

-- Table: purchase_order_items

CREATE TABLE IF NOT EXISTS purchase_order_items (
	id UUID NOT NULL, 
	purchase_order_id UUID NOT NULL, 
	product_id UUID, 
	variant_id UUID, 
	product_name VARCHAR(255) NOT NULL, 
	sku VARCHAR(50) NOT NULL, 
	part_code VARCHAR(20), 
	hsn_code VARCHAR(10), 
	line_number INTEGER NOT NULL, 
	quantity_ordered INTEGER NOT NULL, 
	quantity_received INTEGER NOT NULL, 
	quantity_accepted INTEGER NOT NULL, 
	quantity_rejected INTEGER NOT NULL, 
	quantity_pending INTEGER NOT NULL, 
	uom VARCHAR(20) NOT NULL, 
	unit_price NUMERIC(12, 2) NOT NULL, 
	discount_percentage NUMERIC(5, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	taxable_amount NUMERIC(12, 2) NOT NULL, 
	gst_rate NUMERIC(5, 2) NOT NULL, 
	cgst_rate NUMERIC(5, 2) NOT NULL, 
	sgst_rate NUMERIC(5, 2) NOT NULL, 
	igst_rate NUMERIC(5, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	cess_amount NUMERIC(12, 2) NOT NULL, 
	total_amount NUMERIC(12, 2) NOT NULL, 
	expected_date DATE, 
	monthly_quantities JSON, 
	is_closed BOOLEAN NOT NULL, 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(purchase_order_id) REFERENCES purchase_orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id) ON DELETE SET NULL
)

;

-- Table: shipments

CREATE TABLE IF NOT EXISTS shipments (
	id UUID NOT NULL, 
	shipment_number VARCHAR(30) NOT NULL, 
	order_id UUID NOT NULL, 
	warehouse_id UUID NOT NULL, 
	transporter_id UUID, 
	manifest_id UUID, 
	awb_number VARCHAR(100), 
	tracking_number VARCHAR(100), 
	status shipmentstatus NOT NULL, 
	payment_mode paymentmode NOT NULL, 
	cod_amount FLOAT, 
	cod_collected BOOLEAN NOT NULL, 
	cod_collected_at TIMESTAMP WITHOUT TIME ZONE, 
	packaging_type packagingtype NOT NULL, 
	no_of_boxes INTEGER NOT NULL, 
	weight_kg FLOAT NOT NULL, 
	volumetric_weight_kg FLOAT, 
	chargeable_weight_kg FLOAT, 
	length_cm FLOAT, 
	breadth_cm FLOAT, 
	height_cm FLOAT, 
	ship_to_name VARCHAR(200) NOT NULL, 
	ship_to_phone VARCHAR(20) NOT NULL, 
	ship_to_email VARCHAR(255), 
	ship_to_address JSON NOT NULL, 
	ship_to_pincode VARCHAR(10) NOT NULL, 
	ship_to_city VARCHAR(100), 
	ship_to_state VARCHAR(100), 
	expected_delivery_date DATE, 
	promised_delivery_date DATE, 
	actual_delivery_date DATE, 
	delivery_attempts INTEGER NOT NULL, 
	max_delivery_attempts INTEGER NOT NULL, 
	delivered_to VARCHAR(200), 
	delivery_relation VARCHAR(100), 
	delivery_remarks TEXT, 
	pod_image_url VARCHAR(500), 
	pod_signature_url VARCHAR(500), 
	pod_latitude FLOAT, 
	pod_longitude FLOAT, 
	shipping_label_url VARCHAR(500), 
	invoice_url VARCHAR(500), 
	rto_reason TEXT, 
	rto_initiated_at TIMESTAMP WITHOUT TIME ZONE, 
	rto_delivered_at TIMESTAMP WITHOUT TIME ZONE, 
	shipping_charge FLOAT NOT NULL, 
	cod_charge FLOAT NOT NULL, 
	insurance_charge FLOAT NOT NULL, 
	total_shipping_cost FLOAT NOT NULL, 
	created_by UUID, 
	packed_by UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	packed_at TIMESTAMP WITHOUT TIME ZONE, 
	shipped_at TIMESTAMP WITHOUT TIME ZONE, 
	delivered_at TIMESTAMP WITHOUT TIME ZONE, 
	cancelled_at TIMESTAMP WITHOUT TIME ZONE, 
	cancellation_reason TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
	FOREIGN KEY(transporter_id) REFERENCES transporters (id) ON DELETE SET NULL, 
	FOREIGN KEY(manifest_id) REFERENCES manifests (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(packed_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: stock_items

CREATE TABLE IF NOT EXISTS stock_items (
	id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	warehouse_id UUID NOT NULL, 
	serial_number VARCHAR(100), 
	batch_number VARCHAR(50), 
	barcode VARCHAR(100), 
	status stockitemstatus, 
	purchase_order_id UUID, 
	grn_number VARCHAR(50), 
	vendor_id UUID, 
	purchase_price FLOAT, 
	landed_cost FLOAT, 
	manufacturing_date DATE, 
	expiry_date DATE, 
	warranty_start_date DATE, 
	warranty_end_date DATE, 
	received_date TIMESTAMP WITHOUT TIME ZONE, 
	order_id UUID, 
	order_item_id UUID, 
	allocated_at TIMESTAMP WITHOUT TIME ZONE, 
	bin_id UUID, 
	rack_location VARCHAR(50), 
	bin_number VARCHAR(50), 
	quality_grade VARCHAR(20), 
	inspection_status VARCHAR(50), 
	inspection_notes TEXT, 
	last_movement_date TIMESTAMP WITHOUT TIME ZONE, 
	last_counted_date TIMESTAMP WITHOUT TIME ZONE, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_stock_item_serial UNIQUE (serial_number), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(bin_id) REFERENCES warehouse_bins (id)
)

;

-- Table: tax_invoices

CREATE TABLE IF NOT EXISTS tax_invoices (
	id UUID NOT NULL, 
	invoice_number VARCHAR(50) NOT NULL, 
	invoice_series VARCHAR(20), 
	invoice_type invoicetype NOT NULL, 
	status invoicestatus NOT NULL, 
	invoice_date DATE NOT NULL, 
	due_date DATE, 
	supply_date DATE, 
	order_id UUID, 
	warehouse_id UUID, 
	customer_id UUID, 
	customer_name VARCHAR(200) NOT NULL, 
	customer_gstin VARCHAR(15), 
	customer_pan VARCHAR(10), 
	billing_address_line1 VARCHAR(255) NOT NULL, 
	billing_address_line2 VARCHAR(255), 
	billing_city VARCHAR(100) NOT NULL, 
	billing_state VARCHAR(100) NOT NULL, 
	billing_state_code VARCHAR(2) NOT NULL, 
	billing_pincode VARCHAR(10) NOT NULL, 
	billing_country VARCHAR(100) NOT NULL, 
	shipping_address_line1 VARCHAR(255), 
	shipping_address_line2 VARCHAR(255), 
	shipping_city VARCHAR(100), 
	shipping_state VARCHAR(100), 
	shipping_state_code VARCHAR(2), 
	shipping_pincode VARCHAR(10), 
	shipping_country VARCHAR(100), 
	seller_gstin VARCHAR(15) NOT NULL, 
	seller_name VARCHAR(200) NOT NULL, 
	seller_address VARCHAR(500) NOT NULL, 
	seller_state_code VARCHAR(2) NOT NULL, 
	place_of_supply VARCHAR(100) NOT NULL, 
	place_of_supply_code VARCHAR(2) NOT NULL, 
	is_interstate BOOLEAN NOT NULL, 
	is_reverse_charge BOOLEAN NOT NULL, 
	subtotal NUMERIC(14, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	taxable_amount NUMERIC(14, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	cess_amount NUMERIC(12, 2) NOT NULL, 
	total_tax NUMERIC(12, 2) NOT NULL, 
	shipping_charges NUMERIC(10, 2) NOT NULL, 
	packaging_charges NUMERIC(10, 2) NOT NULL, 
	installation_charges NUMERIC(10, 2) NOT NULL, 
	other_charges NUMERIC(10, 2) NOT NULL, 
	grand_total NUMERIC(14, 2) NOT NULL, 
	amount_in_words VARCHAR(500), 
	currency VARCHAR(3) NOT NULL, 
	round_off NUMERIC(10, 2) NOT NULL, 
	amount_paid NUMERIC(14, 2) NOT NULL, 
	amount_due NUMERIC(14, 2) NOT NULL, 
	payment_terms VARCHAR(200), 
	payment_due_days INTEGER NOT NULL, 
	irn VARCHAR(64), 
	irn_generated_at TIMESTAMP WITHOUT TIME ZONE, 
	ack_number VARCHAR(50), 
	ack_date TIMESTAMP WITHOUT TIME ZONE, 
	signed_invoice TEXT, 
	signed_qr_code TEXT, 
	einvoice_status VARCHAR(50), 
	einvoice_error TEXT, 
	eway_bill_number VARCHAR(20), 
	pdf_url VARCHAR(500), 
	original_copy_url VARCHAR(500), 
	duplicate_copy_url VARCHAR(500), 
	terms_and_conditions TEXT, 
	internal_notes TEXT, 
	customer_notes TEXT, 
	channel_code VARCHAR(30), 
	channel_invoice_id VARCHAR(100), 
	created_by UUID, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	cancelled_by UUID, 
	cancelled_at TIMESTAMP WITHOUT TIME ZONE, 
	cancellation_reason VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE SET NULL, 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL, 
	FOREIGN KEY(customer_id) REFERENCES users (id) ON DELETE SET NULL, 
	UNIQUE (irn), 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(cancelled_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: vendor_proforma_invoices

CREATE TABLE IF NOT EXISTS vendor_proforma_invoices (
	id UUID NOT NULL, 
	proforma_number VARCHAR(50) NOT NULL, 
	our_reference VARCHAR(30) NOT NULL, 
	status proformastatus NOT NULL, 
	vendor_id UUID NOT NULL, 
	proforma_date DATE NOT NULL, 
	validity_date DATE, 
	requisition_id UUID, 
	purchase_order_id UUID, 
	delivery_warehouse_id UUID, 
	delivery_days INTEGER, 
	delivery_terms VARCHAR(200), 
	bill_to JSON, 
	ship_to JSON, 
	payment_terms VARCHAR(200), 
	credit_days INTEGER NOT NULL, 
	subtotal NUMERIC(14, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	discount_percent NUMERIC(5, 2) NOT NULL, 
	taxable_amount NUMERIC(14, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	total_tax NUMERIC(12, 2) NOT NULL, 
	freight_charges NUMERIC(12, 2) NOT NULL, 
	packing_charges NUMERIC(12, 2) NOT NULL, 
	other_charges NUMERIC(12, 2) NOT NULL, 
	round_off NUMERIC(8, 2) NOT NULL, 
	grand_total NUMERIC(14, 2) NOT NULL, 
	proforma_pdf_url VARCHAR(500), 
	vendor_remarks TEXT, 
	internal_notes TEXT, 
	received_by UUID NOT NULL, 
	received_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	rejection_reason TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_vendor_proforma UNIQUE (vendor_id, proforma_number), 
	FOREIGN KEY(vendor_id) REFERENCES vendors (id) ON DELETE RESTRICT, 
	FOREIGN KEY(requisition_id) REFERENCES purchase_requisitions (id) ON DELETE SET NULL, 
	FOREIGN KEY(purchase_order_id) REFERENCES purchase_orders (id) ON DELETE SET NULL, 
	FOREIGN KEY(delivery_warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL, 
	FOREIGN KEY(received_by) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE SET NULL
)

;

