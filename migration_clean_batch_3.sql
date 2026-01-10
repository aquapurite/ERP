-- Clean Migration Batch 3
-- Tables without foreign keys

-- Table: inventory_summary

CREATE TABLE IF NOT EXISTS inventory_summary (
	id UUID NOT NULL, 
	warehouse_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	total_quantity INTEGER, 
	available_quantity INTEGER, 
	reserved_quantity INTEGER, 
	allocated_quantity INTEGER, 
	damaged_quantity INTEGER, 
	in_transit_quantity INTEGER, 
	reorder_level INTEGER, 
	minimum_stock INTEGER, 
	maximum_stock INTEGER, 
	average_cost FLOAT, 
	total_value FLOAT, 
	last_stock_in_date TIMESTAMP WITHOUT TIME ZONE, 
	last_stock_out_date TIMESTAMP WITHOUT TIME ZONE, 
	last_audit_date TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_inventory_summary UNIQUE (warehouse_id, product_id, variant_id)
)

;


-- Table: invoice_number_sequences

CREATE TABLE IF NOT EXISTS invoice_number_sequences (
	id UUID NOT NULL, 
	series_code VARCHAR(20) NOT NULL, 
	series_name VARCHAR(100) NOT NULL, 
	financial_year VARCHAR(10) NOT NULL, 
	prefix VARCHAR(20) NOT NULL, 
	suffix VARCHAR(20), 
	current_number INTEGER NOT NULL, 
	padding_length INTEGER NOT NULL, 
	warehouse_id UUID, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_invoice_sequence UNIQUE (series_code, financial_year)
)

;


-- Table: manifests

CREATE TABLE IF NOT EXISTS manifests (
	id UUID NOT NULL, 
	manifest_number VARCHAR(30) NOT NULL, 
	warehouse_id UUID NOT NULL, 
	transporter_id UUID NOT NULL, 
	status manifeststatus NOT NULL, 
	business_type businesstype NOT NULL, 
	manifest_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	total_shipments INTEGER NOT NULL, 
	scanned_shipments INTEGER NOT NULL, 
	total_weight_kg FLOAT NOT NULL, 
	total_boxes INTEGER NOT NULL, 
	vehicle_number VARCHAR(50), 
	driver_name VARCHAR(200), 
	driver_phone VARCHAR(20), 
	remarks TEXT, 
	created_by UUID, 
	confirmed_by UUID, 
	confirmed_at TIMESTAMP WITHOUT TIME ZONE, 
	handover_at TIMESTAMP WITHOUT TIME ZONE, 
	handover_by UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	cancelled_at TIMESTAMP WITHOUT TIME ZONE, 
	cancellation_reason TEXT, 
	PRIMARY KEY (id)
)

;


-- Table: picklists

CREATE TABLE IF NOT EXISTS picklists (
	id UUID NOT NULL, 
	picklist_number VARCHAR(30) NOT NULL, 
	warehouse_id UUID NOT NULL, 
	status pickliststatus NOT NULL, 
	picklist_type picklisttype NOT NULL, 
	priority INTEGER NOT NULL, 
	total_orders INTEGER NOT NULL, 
	total_items INTEGER NOT NULL, 
	total_quantity INTEGER NOT NULL, 
	picked_quantity INTEGER NOT NULL, 
	assigned_to UUID, 
	assigned_at TIMESTAMP WITHOUT TIME ZONE, 
	created_by UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	cancelled_at TIMESTAMP WITHOUT TIME ZONE, 
	notes TEXT, 
	cancellation_reason TEXT, 
	PRIMARY KEY (id)
)

;


-- Table: purchase_requisitions

CREATE TABLE IF NOT EXISTS purchase_requisitions (
	id UUID NOT NULL, 
	requisition_number VARCHAR(30) NOT NULL, 
	status requisitionstatus NOT NULL, 
	requesting_department VARCHAR(50), 
	requested_by UUID NOT NULL, 
	request_date DATE NOT NULL, 
	required_by_date DATE, 
	delivery_warehouse_id UUID NOT NULL, 
	priority INTEGER NOT NULL, 
	estimated_total NUMERIC(14, 2) NOT NULL, 
	reason TEXT, 
	notes TEXT, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	rejection_reason TEXT, 
	converted_to_po_id UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


-- Table: sales_channels

CREATE TABLE IF NOT EXISTS sales_channels (
	id UUID NOT NULL, 
	code VARCHAR(30) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	display_name VARCHAR(200) NOT NULL, 
	channel_type channeltype NOT NULL, 
	status channelstatus NOT NULL, 
	seller_id VARCHAR(100), 
	api_endpoint VARCHAR(500), 
	api_key VARCHAR(255), 
	api_secret VARCHAR(255), 
	webhook_url VARCHAR(500), 
	default_warehouse_id UUID, 
	fulfillment_type VARCHAR(50), 
	auto_confirm_orders BOOLEAN NOT NULL, 
	auto_allocate_inventory BOOLEAN NOT NULL, 
	commission_percentage NUMERIC(5, 2), 
	fixed_fee_per_order NUMERIC(10, 2), 
	payment_cycle_days INTEGER NOT NULL, 
	price_markup_percentage NUMERIC(5, 2), 
	price_discount_percentage NUMERIC(5, 2), 
	use_channel_specific_pricing BOOLEAN NOT NULL, 
	return_window_days INTEGER NOT NULL, 
	replacement_window_days INTEGER NOT NULL, 
	supports_return_pickup BOOLEAN NOT NULL, 
	tax_inclusive_pricing BOOLEAN NOT NULL, 
	collect_tcs BOOLEAN NOT NULL, 
	tcs_rate NUMERIC(5, 2), 
	contact_name VARCHAR(200), 
	contact_email VARCHAR(255), 
	contact_phone VARCHAR(20), 
	config JSON, 
	last_sync_at TIMESTAMP WITHOUT TIME ZONE, 
	sync_enabled BOOLEAN NOT NULL, 
	sync_interval_minutes INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


-- Table: stock_adjustments

CREATE TABLE IF NOT EXISTS stock_adjustments (
	id UUID NOT NULL, 
	adjustment_number VARCHAR(50) NOT NULL, 
	adjustment_type adjustmenttype NOT NULL, 
	status adjustmentstatus, 
	warehouse_id UUID NOT NULL, 
	adjustment_date TIMESTAMP WITHOUT TIME ZONE, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_by UUID NOT NULL, 
	approved_by UUID, 
	requires_approval INTEGER, 
	rejection_reason TEXT, 
	total_items INTEGER, 
	total_quantity_adjusted INTEGER, 
	total_value_impact FLOAT, 
	reason TEXT NOT NULL, 
	reference_document VARCHAR(100), 
	notes TEXT, 
	PRIMARY KEY (id)
)

;


-- Table: stock_transfers

CREATE TABLE IF NOT EXISTS stock_transfers (
	id UUID NOT NULL, 
	transfer_number VARCHAR(50) NOT NULL, 
	transfer_type transfertype, 
	status transferstatus, 
	from_warehouse_id UUID NOT NULL, 
	to_warehouse_id UUID NOT NULL, 
	request_date TIMESTAMP WITHOUT TIME ZONE, 
	expected_date TIMESTAMP WITHOUT TIME ZONE, 
	dispatch_date TIMESTAMP WITHOUT TIME ZONE, 
	received_date TIMESTAMP WITHOUT TIME ZONE, 
	requested_by UUID, 
	approved_by UUID, 
	dispatched_by UUID, 
	received_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	rejection_reason TEXT, 
	total_items INTEGER, 
	total_quantity INTEGER, 
	total_value FLOAT, 
	received_quantity INTEGER, 
	vehicle_number VARCHAR(50), 
	driver_name VARCHAR(100), 
	driver_phone VARCHAR(20), 
	challan_number VARCHAR(50), 
	eway_bill_number VARCHAR(50), 
	notes TEXT, 
	internal_notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


-- Table: technicians

CREATE TABLE IF NOT EXISTS technicians (
	id UUID NOT NULL, 
	employee_code VARCHAR(20) NOT NULL, 
	first_name VARCHAR(100) NOT NULL, 
	last_name VARCHAR(100), 
	phone VARCHAR(20) NOT NULL, 
	alternate_phone VARCHAR(20), 
	email VARCHAR(100), 
	user_id UUID, 
	technician_type techniciantype, 
	status technicianstatus, 
	date_of_joining DATE, 
	date_of_leaving DATE, 
	skill_level skilllevel, 
	specializations JSON, 
	certifications JSON, 
	region_id UUID, 
	assigned_warehouse_id UUID, 
	service_pincodes JSON, 
	address TEXT, 
	city VARCHAR(100), 
	state VARCHAR(100), 
	pincode VARCHAR(10), 
	aadhaar_number VARCHAR(20), 
	pan_number VARCHAR(20), 
	driving_license VARCHAR(50), 
	id_proof_url VARCHAR(500), 
	photo_url VARCHAR(500), 
	bank_name VARCHAR(100), 
	bank_account_number VARCHAR(50), 
	ifsc_code VARCHAR(20), 
	total_jobs_completed INTEGER, 
	average_rating FLOAT, 
	total_ratings INTEGER, 
	current_month_jobs INTEGER, 
	is_available BOOLEAN, 
	last_job_date TIMESTAMP WITHOUT TIME ZONE, 
	current_location_lat FLOAT, 
	current_location_lng FLOAT, 
	location_updated_at TIMESTAMP WITHOUT TIME ZONE, 
	notes TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (user_id)
)

;


-- Table: vendors

CREATE TABLE IF NOT EXISTS vendors (
	id UUID NOT NULL, 
	vendor_code VARCHAR(30) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	legal_name VARCHAR(200) NOT NULL, 
	trade_name VARCHAR(200), 
	vendor_type vendortype NOT NULL, 
	status vendorstatus NOT NULL, 
	grade vendorgrade NOT NULL, 
	gstin VARCHAR(15), 
	gst_registered BOOLEAN NOT NULL, 
	gst_state_code VARCHAR(2), 
	pan VARCHAR(10), 
	tan VARCHAR(10), 
	msme_registered BOOLEAN NOT NULL, 
	msme_number VARCHAR(30), 
	msme_category VARCHAR(20), 
	contact_person VARCHAR(100), 
	designation VARCHAR(100), 
	email VARCHAR(100), 
	phone VARCHAR(20), 
	mobile VARCHAR(20), 
	website VARCHAR(200), 
	address_line1 VARCHAR(255) NOT NULL, 
	address_line2 VARCHAR(255), 
	city VARCHAR(100) NOT NULL, 
	state VARCHAR(100) NOT NULL, 
	state_code VARCHAR(2), 
	pincode VARCHAR(10) NOT NULL, 
	country VARCHAR(50) NOT NULL, 
	warehouse_address JSON, 
	bank_name VARCHAR(100), 
	bank_branch VARCHAR(100), 
	bank_account_number VARCHAR(30), 
	bank_ifsc VARCHAR(11), 
	bank_account_type VARCHAR(20), 
	beneficiary_name VARCHAR(100), 
	payment_terms paymentterms NOT NULL, 
	credit_days INTEGER NOT NULL, 
	credit_limit NUMERIC(14, 2) NOT NULL, 
	advance_percentage NUMERIC(5, 2) NOT NULL, 
	tds_applicable BOOLEAN NOT NULL, 
	tds_section VARCHAR(10), 
	tds_rate NUMERIC(5, 2) NOT NULL, 
	lower_tds_certificate BOOLEAN NOT NULL, 
	lower_tds_rate NUMERIC(5, 2), 
	lower_tds_valid_till DATE, 
	opening_balance NUMERIC(14, 2) NOT NULL, 
	current_balance NUMERIC(14, 2) NOT NULL, 
	advance_balance NUMERIC(14, 2) NOT NULL, 
	product_categories JSON, 
	primary_products TEXT, 
	default_lead_days INTEGER NOT NULL, 
	min_order_value NUMERIC(12, 2), 
	min_order_quantity INTEGER, 
	default_warehouse_id UUID, 
	gst_certificate_url VARCHAR(500), 
	pan_card_url VARCHAR(500), 
	msme_certificate_url VARCHAR(500), 
	cancelled_cheque_url VARCHAR(500), 
	agreement_url VARCHAR(500), 
	is_verified BOOLEAN NOT NULL, 
	verified_at TIMESTAMP WITHOUT TIME ZONE, 
	verified_by UUID, 
	total_po_count INTEGER NOT NULL, 
	total_po_value NUMERIC(14, 2) NOT NULL, 
	on_time_delivery_rate NUMERIC(5, 2), 
	quality_rejection_rate NUMERIC(5, 2), 
	last_po_date TIMESTAMP WITHOUT TIME ZONE, 
	last_payment_date TIMESTAMP WITHOUT TIME ZONE, 
	internal_notes TEXT, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


-- Table: warehouse_serviceability

CREATE TABLE IF NOT EXISTS warehouse_serviceability (
	id UUID NOT NULL, 
	warehouse_id UUID NOT NULL, 
	pincode VARCHAR(10) NOT NULL, 
	is_serviceable BOOLEAN NOT NULL, 
	cod_available BOOLEAN NOT NULL, 
	prepaid_available BOOLEAN NOT NULL, 
	estimated_days INTEGER, 
	priority INTEGER NOT NULL, 
	shipping_cost FLOAT, 
	city VARCHAR(100), 
	state VARCHAR(100), 
	zone VARCHAR(20), 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_warehouse_serviceability UNIQUE (warehouse_id, pincode)
)

;


-- Table: warehouse_zones

CREATE TABLE IF NOT EXISTS warehouse_zones (
	id UUID NOT NULL, 
	warehouse_id UUID NOT NULL, 
	zone_code VARCHAR(20) NOT NULL, 
	zone_name VARCHAR(200) NOT NULL, 
	description TEXT, 
	zone_type zonetype NOT NULL, 
	floor_number INTEGER, 
	area_sqft FLOAT, 
	max_capacity INTEGER, 
	current_capacity INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	is_pickable BOOLEAN NOT NULL, 
	is_receivable BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_warehouse_zone_code UNIQUE (warehouse_id, zone_code)
)

;


-- Table: allocation_rules

CREATE TABLE IF NOT EXISTS allocation_rules (
	id UUID NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	channel_code channelcode NOT NULL, 
	channel_id UUID, 
	priority INTEGER NOT NULL, 
	allocation_type allocationtype NOT NULL, 
	fixed_warehouse_id UUID, 
	priority_factors VARCHAR(200), 
	min_order_value FLOAT, 
	max_order_value FLOAT, 
	payment_mode VARCHAR(20), 
	allow_split BOOLEAN NOT NULL, 
	max_splits INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by UUID, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_allocation_rule_channel_priority UNIQUE (channel_code, priority)
)

;


-- Table: campaign_recipients

CREATE TABLE IF NOT EXISTS campaign_recipients (
	id UUID NOT NULL, 
	campaign_id UUID NOT NULL, 
	customer_id UUID, 
	email VARCHAR(255), 
	phone VARCHAR(20), 
	name VARCHAR(200), 
	personalization_data JSON, 
	status deliverystatus NOT NULL, 
	sent_at TIMESTAMP WITHOUT TIME ZONE, 
	delivered_at TIMESTAMP WITHOUT TIME ZONE, 
	opened_at TIMESTAMP WITHOUT TIME ZONE, 
	clicked_at TIMESTAMP WITHOUT TIME ZONE, 
	bounced_at TIMESTAMP WITHOUT TIME ZONE, 
	unsubscribed_at TIMESTAMP WITHOUT TIME ZONE, 
	failed_at TIMESTAMP WITHOUT TIME ZONE, 
	open_count INTEGER NOT NULL, 
	click_count INTEGER NOT NULL, 
	failure_reason TEXT, 
	external_message_id VARCHAR(100), 
	ab_variant VARCHAR(10), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


-- Table: channel_inventory

CREATE TABLE IF NOT EXISTS channel_inventory (
	id UUID NOT NULL, 
	channel_id UUID NOT NULL, 
	warehouse_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	allocated_quantity INTEGER NOT NULL, 
	buffer_quantity INTEGER NOT NULL, 
	reserved_quantity INTEGER NOT NULL, 
	marketplace_quantity INTEGER NOT NULL, 
	last_synced_at TIMESTAMP WITHOUT TIME ZONE, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_channel_inventory UNIQUE (channel_id, warehouse_id, product_id, variant_id)
)

;


-- Table: channel_pricing

CREATE TABLE IF NOT EXISTS channel_pricing (
	id UUID NOT NULL, 
	channel_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	mrp NUMERIC(12, 2) NOT NULL, 
	selling_price NUMERIC(12, 2) NOT NULL, 
	transfer_price NUMERIC(12, 2), 
	discount_percentage NUMERIC(5, 2), 
	max_discount_percentage NUMERIC(5, 2), 
	is_active BOOLEAN NOT NULL, 
	is_listed BOOLEAN NOT NULL, 
	effective_from TIMESTAMP WITHOUT TIME ZONE, 
	effective_to TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_channel_product_pricing UNIQUE (channel_id, product_id, variant_id)
)

;


-- Table: commission_earners

CREATE TABLE IF NOT EXISTS commission_earners (
	id UUID NOT NULL, 
	earner_type commissiontype NOT NULL, 
	user_id UUID, 
	dealer_id UUID, 
	earner_name VARCHAR(200) NOT NULL, 
	earner_email VARCHAR(255), 
	earner_phone VARCHAR(20), 
	referral_code VARCHAR(30), 
	plan_id UUID NOT NULL, 
	custom_rate NUMERIC(5, 2), 
	bank_name VARCHAR(200), 
	bank_account_number VARCHAR(30), 
	bank_ifsc VARCHAR(11), 
	bank_account_name VARCHAR(200), 
	upi_id VARCHAR(100), 
	pan_number VARCHAR(10), 
	tds_rate_override NUMERIC(5, 2), 
	is_active BOOLEAN NOT NULL, 
	is_verified BOOLEAN NOT NULL, 
	verified_at TIMESTAMP WITHOUT TIME ZONE, 
	total_earnings NUMERIC(14, 2) NOT NULL, 
	total_paid NUMERIC(14, 2) NOT NULL, 
	pending_payout NUMERIC(14, 2) NOT NULL, 
	total_orders INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


-- Table: dealer_credit_ledger

CREATE TABLE IF NOT EXISTS dealer_credit_ledger (
	id UUID NOT NULL, 
	dealer_id UUID NOT NULL, 
	transaction_type transactiontype NOT NULL, 
	transaction_date DATE NOT NULL, 
	due_date DATE, 
	reference_type VARCHAR(50) NOT NULL, 
	reference_number VARCHAR(50) NOT NULL, 
	reference_id UUID, 
	debit_amount NUMERIC(14, 2) NOT NULL, 
	credit_amount NUMERIC(14, 2) NOT NULL, 
	balance NUMERIC(14, 2) NOT NULL, 
	payment_mode VARCHAR(30), 
	cheque_number VARCHAR(20), 
	transaction_reference VARCHAR(100), 
	is_settled BOOLEAN NOT NULL, 
	settled_date DATE, 
	days_overdue INTEGER NOT NULL, 
	remarks VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


-- Table: dealer_pricing

CREATE TABLE IF NOT EXISTS dealer_pricing (
	id UUID NOT NULL, 
	dealer_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	mrp NUMERIC(12, 2) NOT NULL, 
	dealer_price NUMERIC(12, 2) NOT NULL, 
	special_price NUMERIC(12, 2), 
	margin_percentage NUMERIC(5, 2), 
	minimum_margin NUMERIC(5, 2), 
	moq INTEGER NOT NULL, 
	effective_from DATE NOT NULL, 
	effective_to DATE, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_dealer_product_pricing UNIQUE (dealer_id, product_id, variant_id)
)

;


-- Table: dealer_targets

CREATE TABLE IF NOT EXISTS dealer_targets (
	id UUID NOT NULL, 
	dealer_id UUID NOT NULL, 
	target_period VARCHAR(20) NOT NULL, 
	target_year INTEGER NOT NULL, 
	target_month INTEGER, 
	target_quarter INTEGER, 
	target_type VARCHAR(30) NOT NULL, 
	category_id UUID, 
	product_id UUID, 
	revenue_target NUMERIC(14, 2) NOT NULL, 
	quantity_target INTEGER NOT NULL, 
	revenue_achieved NUMERIC(14, 2) NOT NULL, 
	quantity_achieved INTEGER NOT NULL, 
	incentive_percentage NUMERIC(5, 2), 
	incentive_earned NUMERIC(12, 2) NOT NULL, 
	is_incentive_paid BOOLEAN NOT NULL, 
	is_finalized BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_dealer_target UNIQUE (dealer_id, target_period, target_year, target_month)
)

;


-- Table: escalations

CREATE TABLE IF NOT EXISTS escalations (
	id UUID NOT NULL, 
	escalation_number VARCHAR(30) NOT NULL, 
	source_type escalationsource NOT NULL, 
	source_id UUID, 
	source_reference VARCHAR(50), 
	customer_id UUID, 
	customer_name VARCHAR(200) NOT NULL, 
	customer_phone VARCHAR(20) NOT NULL, 
	customer_email VARCHAR(255), 
	subject VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	current_level escalationlevel NOT NULL, 
	priority escalationpriority NOT NULL, 
	reason escalationreason NOT NULL, 
	reason_details TEXT, 
	status escalationstatus NOT NULL, 
	assigned_to_id UUID, 
	assigned_at TIMESTAMP WITHOUT TIME ZONE, 
	assigned_by_id UUID, 
	response_due_at TIMESTAMP WITHOUT TIME ZONE, 
	resolution_due_at TIMESTAMP WITHOUT TIME ZONE, 
	first_response_at TIMESTAMP WITHOUT TIME ZONE, 
	is_response_sla_breached BOOLEAN NOT NULL, 
	is_resolution_sla_breached BOOLEAN NOT NULL, 
	acknowledged_at TIMESTAMP WITHOUT TIME ZONE, 
	acknowledged_by_id UUID, 
	acknowledgment_notes TEXT, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	resolved_by_id UUID, 
	resolution_notes TEXT, 
	resolution_type VARCHAR(50), 
	customer_satisfied BOOLEAN, 
	satisfaction_rating INTEGER, 
	customer_feedback TEXT, 
	reopen_count INTEGER NOT NULL, 
	last_reopened_at TIMESTAMP WITHOUT TIME ZONE, 
	reopen_reason TEXT, 
	matrix_id UUID, 
	product_id UUID, 
	category_id UUID, 
	region_id UUID, 
	dealer_id UUID, 
	internal_notes TEXT, 
	tags JSON, 
	created_by_id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


-- Table: franchisee_serviceability

CREATE TABLE IF NOT EXISTS franchisee_serviceability (
	id VARCHAR(36) NOT NULL, 
	franchisee_id VARCHAR(36) NOT NULL, 
	territory_id VARCHAR(36), 
	pincode VARCHAR(10) NOT NULL, 
	city VARCHAR(100), 
	district VARCHAR(100), 
	state VARCHAR(100), 
	service_types JSON NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	priority INTEGER NOT NULL, 
	max_daily_capacity INTEGER NOT NULL, 
	current_load INTEGER NOT NULL, 
	expected_response_hours INTEGER NOT NULL, 
	expected_completion_hours INTEGER NOT NULL, 
	total_jobs_completed INTEGER NOT NULL, 
	avg_rating FLOAT, 
	on_time_completion_rate FLOAT NOT NULL, 
	effective_from DATE NOT NULL, 
	effective_to DATE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


-- Table: franchisee_support_comments

CREATE TABLE IF NOT EXISTS franchisee_support_comments (
	id VARCHAR(36) NOT NULL, 
	ticket_id VARCHAR(36) NOT NULL, 
	comment TEXT NOT NULL, 
	is_internal BOOLEAN NOT NULL, 
	author_id VARCHAR(36), 
	author_type VARCHAR(20) NOT NULL, 
	author_name VARCHAR(200) NOT NULL, 
	attachments JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


-- Table: inventory_audits

CREATE TABLE IF NOT EXISTS inventory_audits (
	id UUID NOT NULL, 
	audit_number VARCHAR(50) NOT NULL, 
	audit_name VARCHAR(200), 
	warehouse_id UUID NOT NULL, 
	category_id UUID, 
	scheduled_date TIMESTAMP WITHOUT TIME ZONE, 
	start_date TIMESTAMP WITHOUT TIME ZONE, 
	end_date TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(50), 
	assigned_to UUID, 
	created_by UUID, 
	total_items_counted INTEGER, 
	variance_items INTEGER, 
	total_variance_value FLOAT, 
	adjustment_id UUID, 
	notes TEXT, 
	PRIMARY KEY (id)
)

;


-- Table: journal_entries

CREATE TABLE IF NOT EXISTS journal_entries (
	id UUID NOT NULL, 
	entry_number VARCHAR(30) NOT NULL, 
	entry_date DATE NOT NULL, 
	period_id UUID NOT NULL, 
	entry_type VARCHAR(50) NOT NULL, 
	source_type VARCHAR(50), 
	source_id UUID, 
	source_number VARCHAR(50), 
	narration TEXT NOT NULL, 
	channel_id UUID, 
	total_debit NUMERIC(15, 2) NOT NULL, 
	total_credit NUMERIC(15, 2) NOT NULL, 
	status journalentrystatus NOT NULL, 
	is_reversed BOOLEAN NOT NULL, 
	reversal_of_id UUID, 
	reversed_by_id UUID, 
	created_by UUID NOT NULL, 
	submitted_by UUID, 
	submitted_at TIMESTAMP WITHOUT TIME ZONE, 
	approval_level VARCHAR(20), 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	rejection_reason TEXT, 
	posted_by UUID, 
	posted_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


-- Table: orders

CREATE TABLE IF NOT EXISTS orders (
	id UUID NOT NULL, 
	order_number VARCHAR(30) NOT NULL, 
	customer_id UUID NOT NULL, 
	status orderstatus NOT NULL, 
	source ordersource NOT NULL, 
	warehouse_id UUID, 
	dealer_id UUID, 
	subtotal NUMERIC(12, 2) NOT NULL, 
	tax_amount NUMERIC(12, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	shipping_amount NUMERIC(12, 2) NOT NULL, 
	total_amount NUMERIC(12, 2) NOT NULL, 
	discount_code VARCHAR(50), 
	discount_type VARCHAR(20), 
	payment_method paymentmethod NOT NULL, 
	payment_status paymentstatus NOT NULL, 
	amount_paid NUMERIC(12, 2) NOT NULL, 
	shipping_address JSON NOT NULL, 
	billing_address JSON, 
	expected_delivery_date TIMESTAMP WITHOUT TIME ZONE, 
	delivered_at TIMESTAMP WITHOUT TIME ZONE, 
	region_id UUID, 
	customer_notes TEXT, 
	internal_notes TEXT, 
	created_by UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	confirmed_at TIMESTAMP WITHOUT TIME ZONE, 
	cancelled_at TIMESTAMP WITHOUT TIME ZONE, 
	allocated_at TIMESTAMP WITHOUT TIME ZONE, 
	picked_at TIMESTAMP WITHOUT TIME ZONE, 
	packed_at TIMESTAMP WITHOUT TIME ZONE, 
	shipped_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


-- Table: purchase_orders

CREATE TABLE IF NOT EXISTS purchase_orders (
	id UUID NOT NULL, 
	po_number VARCHAR(30) NOT NULL, 
	po_date DATE NOT NULL, 
	status postatus NOT NULL, 
	vendor_id UUID NOT NULL, 
	requisition_id UUID, 
	delivery_warehouse_id UUID NOT NULL, 
	expected_delivery_date DATE, 
	delivery_address JSON, 
	vendor_name VARCHAR(200) NOT NULL, 
	vendor_gstin VARCHAR(15), 
	vendor_address JSON, 
	bill_to JSON, 
	ship_to JSON, 
	subtotal NUMERIC(14, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	taxable_amount NUMERIC(14, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	cess_amount NUMERIC(12, 2) NOT NULL, 
	total_tax NUMERIC(12, 2) NOT NULL, 
	freight_charges NUMERIC(12, 2) NOT NULL, 
	packing_charges NUMERIC(12, 2) NOT NULL, 
	other_charges NUMERIC(12, 2) NOT NULL, 
	grand_total NUMERIC(14, 2) NOT NULL, 
	total_received_value NUMERIC(14, 2) NOT NULL, 
	payment_terms VARCHAR(100), 
	credit_days INTEGER NOT NULL, 
	advance_required NUMERIC(12, 2) NOT NULL, 
	advance_paid NUMERIC(12, 2) NOT NULL, 
	quotation_reference VARCHAR(50), 
	quotation_date DATE, 
	terms_and_conditions TEXT, 
	special_instructions TEXT, 
	sent_to_vendor_at TIMESTAMP WITHOUT TIME ZONE, 
	vendor_acknowledged_at TIMESTAMP WITHOUT TIME ZONE, 
	po_pdf_url VARCHAR(500), 
	created_by UUID NOT NULL, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	approval_request_id UUID, 
	approval_level VARCHAR(20), 
	submitted_for_approval_at TIMESTAMP WITHOUT TIME ZONE, 
	rejection_reason TEXT, 
	internal_notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;


-- Table: purchase_requisition_items

CREATE TABLE IF NOT EXISTS purchase_requisition_items (
	id UUID NOT NULL, 
	requisition_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	product_name VARCHAR(255) NOT NULL, 
	sku VARCHAR(50) NOT NULL, 
	quantity_requested INTEGER NOT NULL, 
	uom VARCHAR(20) NOT NULL, 
	estimated_unit_price NUMERIC(12, 2) NOT NULL, 
	estimated_total NUMERIC(12, 2) NOT NULL, 
	preferred_vendor_id UUID, 
	notes TEXT, 
	monthly_quantities JSON, 
	PRIMARY KEY (id)
)

;


-- Table: putaway_rules

CREATE TABLE IF NOT EXISTS putaway_rules (
	id UUID NOT NULL, 
	warehouse_id UUID NOT NULL, 
	rule_name VARCHAR(200) NOT NULL, 
	description TEXT, 
	category_id UUID, 
	product_id UUID, 
	brand_id UUID, 
	target_zone_id UUID NOT NULL, 
	target_bin_pattern VARCHAR(100), 
	priority INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_putaway_rule UNIQUE (warehouse_id, category_id, priority)
)

;


-- Table: stock_transfer_items

CREATE TABLE IF NOT EXISTS stock_transfer_items (
	id UUID NOT NULL, 
	transfer_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	requested_quantity INTEGER NOT NULL, 
	approved_quantity INTEGER, 
	dispatched_quantity INTEGER, 
	received_quantity INTEGER, 
	damaged_quantity INTEGER, 
	unit_cost FLOAT, 
	total_cost FLOAT, 
	notes TEXT, 
	PRIMARY KEY (id)
)

;

