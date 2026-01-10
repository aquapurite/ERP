-- Complete Supabase Migration
-- Run this in Supabase SQL Editor
-- Generated from SQLAlchemy models

-- Table: brands

CREATE TABLE IF NOT EXISTS brands (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	slug VARCHAR(120) NOT NULL, 
	description TEXT, 
	logo_url VARCHAR(500), 
	banner_url VARCHAR(500), 
	website VARCHAR(255), 
	contact_email VARCHAR(255), 
	contact_phone VARCHAR(20), 
	sort_order INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	is_featured BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;

-- Table: call_dispositions

CREATE TABLE IF NOT EXISTS call_dispositions (
	id UUID NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description TEXT, 
	category callcategory NOT NULL, 
	requires_callback BOOLEAN NOT NULL, 
	auto_create_ticket BOOLEAN NOT NULL, 
	auto_create_lead BOOLEAN NOT NULL, 
	requires_escalation BOOLEAN NOT NULL, 
	is_resolution BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;

-- Table: categories

CREATE TABLE IF NOT EXISTS categories (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	slug VARCHAR(120) NOT NULL, 
	description TEXT, 
	parent_id UUID, 
	image_url VARCHAR(500), 
	icon VARCHAR(50), 
	sort_order INTEGER NOT NULL, 
	meta_title VARCHAR(200), 
	meta_description VARCHAR(500), 
	is_active BOOLEAN NOT NULL, 
	is_featured BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES categories (id) ON DELETE SET NULL
)

;

-- Table: channel_commission_plans

CREATE TABLE IF NOT EXISTS channel_commission_plans (
	id UUID NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	channel_code VARCHAR(30) NOT NULL, 
	beneficiary_type commissionbeneficiary NOT NULL, 
	effective_from DATE NOT NULL, 
	effective_to DATE, 
	is_active BOOLEAN NOT NULL, 
	commission_type VARCHAR(30) NOT NULL, 
	base_rate NUMERIC(5, 2) NOT NULL, 
	fixed_amount NUMERIC(10, 2), 
	rate_slabs JSON, 
	calculate_on VARCHAR(30) NOT NULL, 
	exclude_tax BOOLEAN NOT NULL, 
	exclude_shipping BOOLEAN NOT NULL, 
	exclude_discounts BOOLEAN NOT NULL, 
	min_order_value NUMERIC(12, 2), 
	applicable_categories JSON, 
	applicable_products JSON, 
	excluded_products JSON, 
	payout_frequency VARCHAR(20) NOT NULL, 
	payout_after_days INTEGER NOT NULL, 
	min_payout_amount NUMERIC(10, 2) NOT NULL, 
	clawback_days INTEGER NOT NULL, 
	tds_applicable BOOLEAN NOT NULL, 
	tds_rate NUMERIC(5, 2) NOT NULL, 
	tds_section VARCHAR(20), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_channel_commission_plan UNIQUE (channel_code, beneficiary_type, name)
)

;

-- Table: chart_of_accounts

CREATE TABLE IF NOT EXISTS chart_of_accounts (
	id UUID NOT NULL, 
	account_code VARCHAR(20) NOT NULL, 
	account_name VARCHAR(200) NOT NULL, 
	description TEXT, 
	account_type accounttype NOT NULL, 
	account_sub_type accountsubtype, 
	parent_id UUID, 
	level INTEGER NOT NULL, 
	is_group BOOLEAN NOT NULL, 
	opening_balance NUMERIC(15, 2) NOT NULL, 
	current_balance NUMERIC(15, 2) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	is_system BOOLEAN NOT NULL, 
	allow_direct_posting BOOLEAN NOT NULL, 
	bank_account_number VARCHAR(50), 
	bank_name VARCHAR(200), 
	bank_ifsc VARCHAR(20), 
	gst_type VARCHAR(20), 
	sort_order INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES chart_of_accounts (id) ON DELETE RESTRICT
)

;

-- Table: commission_plans

CREATE TABLE IF NOT EXISTS commission_plans (
	id UUID NOT NULL, 
	plan_code VARCHAR(30) NOT NULL, 
	plan_name VARCHAR(200) NOT NULL, 
	description TEXT, 
	commission_type commissiontype NOT NULL, 
	calculation_basis calculationbasis NOT NULL, 
	effective_from DATE NOT NULL, 
	effective_to DATE, 
	is_active BOOLEAN NOT NULL, 
	default_rate NUMERIC(5, 2) NOT NULL, 
	min_rate NUMERIC(5, 2), 
	max_rate NUMERIC(5, 2), 
	rate_slabs JSON, 
	min_order_value NUMERIC(12, 2), 
	applicable_products JSON, 
	applicable_categories JSON, 
	excluded_products JSON, 
	payout_after_days INTEGER NOT NULL, 
	requires_full_payment BOOLEAN NOT NULL, 
	clawback_period_days INTEGER NOT NULL, 
	tds_applicable BOOLEAN NOT NULL, 
	tds_rate NUMERIC(5, 2) NOT NULL, 
	tds_section VARCHAR(20), 
	terms_and_conditions TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;

-- Table: companies

CREATE TABLE IF NOT EXISTS companies (
	id UUID NOT NULL, 
	legal_name VARCHAR(300) NOT NULL, 
	trade_name VARCHAR(300), 
	code VARCHAR(20) NOT NULL, 
	company_type companytype NOT NULL, 
	gstin VARCHAR(15) NOT NULL, 
	gst_registration_type gstregistrationtype NOT NULL, 
	state_code VARCHAR(2) NOT NULL, 
	pan VARCHAR(10) NOT NULL, 
	tan VARCHAR(10), 
	cin VARCHAR(21), 
	llpin VARCHAR(10), 
	msme_registered BOOLEAN NOT NULL, 
	udyam_number VARCHAR(30), 
	msme_category VARCHAR(20), 
	address_line1 VARCHAR(255) NOT NULL, 
	address_line2 VARCHAR(255), 
	city VARCHAR(100) NOT NULL, 
	district VARCHAR(100), 
	state VARCHAR(100) NOT NULL, 
	pincode VARCHAR(10) NOT NULL, 
	country VARCHAR(50) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20) NOT NULL, 
	mobile VARCHAR(20), 
	fax VARCHAR(20), 
	website VARCHAR(255), 
	bank_name VARCHAR(200), 
	bank_branch VARCHAR(200), 
	bank_account_number VARCHAR(30), 
	bank_ifsc VARCHAR(11), 
	bank_account_type VARCHAR(20), 
	bank_account_name VARCHAR(200), 
	logo_url VARCHAR(500), 
	logo_small_url VARCHAR(500), 
	favicon_url VARCHAR(500), 
	signature_url VARCHAR(500), 
	einvoice_enabled BOOLEAN NOT NULL, 
	einvoice_username VARCHAR(100), 
	einvoice_password_encrypted VARCHAR(500), 
	einvoice_api_mode VARCHAR(20) NOT NULL, 
	ewb_enabled BOOLEAN NOT NULL, 
	ewb_username VARCHAR(100), 
	ewb_password_encrypted VARCHAR(500), 
	ewb_api_mode VARCHAR(20) NOT NULL, 
	invoice_prefix VARCHAR(20) NOT NULL, 
	invoice_suffix VARCHAR(20), 
	financial_year_start_month INTEGER NOT NULL, 
	invoice_terms TEXT, 
	invoice_notes TEXT, 
	invoice_footer TEXT, 
	po_prefix VARCHAR(20) NOT NULL, 
	po_terms TEXT, 
	currency_code VARCHAR(3) NOT NULL, 
	currency_symbol VARCHAR(5) NOT NULL, 
	default_cgst_rate NUMERIC(5, 2) NOT NULL, 
	default_sgst_rate NUMERIC(5, 2) NOT NULL, 
	default_igst_rate NUMERIC(5, 2) NOT NULL, 
	tds_deductor BOOLEAN NOT NULL, 
	default_tds_rate NUMERIC(5, 2) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	is_primary BOOLEAN NOT NULL, 
	extra_data JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;

-- Table: lead_score_rules

CREATE TABLE IF NOT EXISTS lead_score_rules (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description TEXT, 
	field VARCHAR(50) NOT NULL, 
	operator VARCHAR(20) NOT NULL, 
	value VARCHAR(255) NOT NULL, 
	score_points INTEGER NOT NULL, 
	priority INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;

-- Table: loyalty_programs

CREATE TABLE IF NOT EXISTS loyalty_programs (
	id UUID NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	applicable_channels JSON, 
	points_per_rupee NUMERIC(5, 2) NOT NULL, 
	point_value NUMERIC(5, 2) NOT NULL, 
	min_points_redeem INTEGER NOT NULL, 
	max_points_per_order INTEGER, 
	max_discount_percentage NUMERIC(5, 2), 
	points_expiry_months INTEGER NOT NULL, 
	tier_config JSON, 
	is_active BOOLEAN NOT NULL, 
	effective_from DATE NOT NULL, 
	effective_to DATE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;

-- Table: modules

CREATE TABLE IF NOT EXISTS modules (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	description TEXT, 
	icon VARCHAR(50), 
	sort_order INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
)

;

-- Table: referral_programs

CREATE TABLE IF NOT EXISTS referral_programs (
	id UUID NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	applicable_channels JSON, 
	referrer_reward_type VARCHAR(30) NOT NULL, 
	referrer_reward_value NUMERIC(10, 2) NOT NULL, 
	referrer_max_reward NUMERIC(10, 2), 
	referee_reward_type VARCHAR(30) NOT NULL, 
	referee_reward_value NUMERIC(10, 2) NOT NULL, 
	referee_max_reward NUMERIC(10, 2), 
	min_order_value NUMERIC(12, 2), 
	max_referrals_per_user INTEGER, 
	reward_after_delivery BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	effective_from DATE NOT NULL, 
	effective_to DATE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;

-- Table: regions

CREATE TABLE IF NOT EXISTS regions (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	type regiontype NOT NULL, 
	parent_id UUID, 
	description TEXT, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code), 
	FOREIGN KEY(parent_id) REFERENCES regions (id) ON DELETE SET NULL
)

;

-- Table: roles

CREATE TABLE IF NOT EXISTS roles (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	description TEXT, 
	level rolelevel NOT NULL, 
	department VARCHAR(50), 
	is_system BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
)

;

-- Table: tax_configurations

CREATE TABLE IF NOT EXISTS tax_configurations (
	id UUID NOT NULL, 
	hsn_code VARCHAR(10) NOT NULL, 
	description VARCHAR(500) NOT NULL, 
	state_code VARCHAR(5), 
	cgst_rate NUMERIC(5, 2) NOT NULL, 
	sgst_rate NUMERIC(5, 2) NOT NULL, 
	igst_rate NUMERIC(5, 2) NOT NULL, 
	cess_rate NUMERIC(5, 2) NOT NULL, 
	is_rcm_applicable BOOLEAN NOT NULL, 
	is_exempt BOOLEAN NOT NULL, 
	exemption_reason VARCHAR(500), 
	effective_from DATE NOT NULL, 
	effective_to DATE, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_tax_hsn_state UNIQUE (hsn_code, state_code)
)

;

-- Table: transporters

CREATE TABLE IF NOT EXISTS transporters (
	id UUID NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	transporter_type transportertype NOT NULL, 
	api_endpoint VARCHAR(500), 
	api_key VARCHAR(255), 
	api_secret VARCHAR(255), 
	webhook_url VARCHAR(500), 
	is_active BOOLEAN NOT NULL, 
	supports_cod BOOLEAN NOT NULL, 
	supports_prepaid BOOLEAN NOT NULL, 
	supports_reverse_pickup BOOLEAN NOT NULL, 
	supports_surface BOOLEAN NOT NULL, 
	supports_express BOOLEAN NOT NULL, 
	max_weight_kg FLOAT, 
	min_weight_kg FLOAT, 
	base_rate FLOAT, 
	rate_per_kg FLOAT, 
	cod_charges FLOAT, 
	cod_percentage FLOAT, 
	contact_name VARCHAR(200), 
	contact_phone VARCHAR(20), 
	contact_email VARCHAR(255), 
	address TEXT, 
	tracking_url_template VARCHAR(500), 
	awb_prefix VARCHAR(20), 
	awb_sequence_start INTEGER NOT NULL, 
	awb_sequence_current INTEGER NOT NULL, 
	priority INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;

-- Table: amc_plans

CREATE TABLE IF NOT EXISTS amc_plans (
	id UUID NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	amc_type amctype, 
	category_id UUID, 
	product_ids JSON, 
	duration_months INTEGER, 
	base_price FLOAT, 
	tax_rate FLOAT, 
	services_included INTEGER, 
	parts_covered BOOLEAN, 
	labor_covered BOOLEAN, 
	emergency_support BOOLEAN, 
	priority_service BOOLEAN, 
	discount_on_parts FLOAT, 
	terms_and_conditions TEXT, 
	description TEXT, 
	is_active BOOLEAN, 
	sort_order INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (code), 
	FOREIGN KEY(category_id) REFERENCES categories (id)
)

;

-- Table: channel_commission_category_rates

CREATE TABLE IF NOT EXISTS channel_commission_category_rates (
	id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	category_id UUID NOT NULL, 
	commission_rate NUMERIC(5, 2) NOT NULL, 
	fixed_amount NUMERIC(10, 2), 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_channel_commission_category UNIQUE (plan_id, category_id), 
	FOREIGN KEY(plan_id) REFERENCES channel_commission_plans (id) ON DELETE CASCADE, 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE CASCADE
)

;

-- Table: commission_category_rates

CREATE TABLE IF NOT EXISTS commission_category_rates (
	id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	category_id UUID NOT NULL, 
	commission_rate NUMERIC(5, 2) NOT NULL, 
	rate_slabs JSON, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_plan_category_rate UNIQUE (plan_id, category_id), 
	FOREIGN KEY(plan_id) REFERENCES commission_plans (id) ON DELETE CASCADE, 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE CASCADE
)

;

-- Table: company_bank_accounts

CREATE TABLE IF NOT EXISTS company_bank_accounts (
	id UUID NOT NULL, 
	company_id UUID NOT NULL, 
	bank_name VARCHAR(200) NOT NULL, 
	branch_name VARCHAR(200) NOT NULL, 
	account_number VARCHAR(30) NOT NULL, 
	ifsc_code VARCHAR(11) NOT NULL, 
	account_type VARCHAR(20) NOT NULL, 
	account_name VARCHAR(200) NOT NULL, 
	upi_id VARCHAR(100), 
	swift_code VARCHAR(15), 
	purpose VARCHAR(50) NOT NULL, 
	is_primary BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	show_on_invoice BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE
)

;

-- Table: customers

CREATE TABLE IF NOT EXISTS customers (
	id UUID NOT NULL, 
	customer_code VARCHAR(20) NOT NULL, 
	first_name VARCHAR(100) NOT NULL, 
	last_name VARCHAR(100), 
	email VARCHAR(255), 
	phone VARCHAR(20) NOT NULL, 
	alternate_phone VARCHAR(20), 
	customer_type customertype NOT NULL, 
	source customersource NOT NULL, 
	company_name VARCHAR(200), 
	gst_number VARCHAR(20), 
	date_of_birth DATE, 
	anniversary_date DATE, 
	region_id UUID, 
	is_active BOOLEAN NOT NULL, 
	is_verified BOOLEAN NOT NULL, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(region_id) REFERENCES regions (id) ON DELETE SET NULL
)

;

-- Table: permissions

CREATE TABLE IF NOT EXISTS permissions (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	code VARCHAR(100) NOT NULL, 
	description TEXT, 
	module_id UUID NOT NULL, 
	action VARCHAR(50) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_module_action UNIQUE (module_id, action), 
	UNIQUE (code), 
	FOREIGN KEY(module_id) REFERENCES modules (id) ON DELETE CASCADE
)

;

-- Table: products

CREATE TABLE IF NOT EXISTS products (
	id UUID NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	slug VARCHAR(280) NOT NULL, 
	sku VARCHAR(50) NOT NULL, 
	model_number VARCHAR(100), 
	fg_code VARCHAR(20), 
	model_code VARCHAR(10), 
	part_code VARCHAR(20), 
	item_type VARCHAR(2) NOT NULL, 
	short_description VARCHAR(500), 
	description TEXT, 
	features TEXT, 
	category_id UUID NOT NULL, 
	brand_id UUID NOT NULL, 
	mrp NUMERIC(12, 2) NOT NULL, 
	selling_price NUMERIC(12, 2) NOT NULL, 
	dealer_price NUMERIC(12, 2), 
	cost_price NUMERIC(12, 2), 
	hsn_code VARCHAR(20), 
	gst_rate NUMERIC(5, 2), 
	warranty_months INTEGER NOT NULL, 
	extended_warranty_available BOOLEAN NOT NULL, 
	warranty_terms TEXT, 
	dead_weight_kg NUMERIC(8, 3), 
	length_cm NUMERIC(8, 2), 
	width_cm NUMERIC(8, 2), 
	height_cm NUMERIC(8, 2), 
	min_stock_level INTEGER NOT NULL, 
	max_stock_level INTEGER, 
	status productstatus NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	is_featured BOOLEAN NOT NULL, 
	is_bestseller BOOLEAN NOT NULL, 
	is_new_arrival BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	meta_title VARCHAR(200), 
	meta_description VARCHAR(500), 
	meta_keywords VARCHAR(255), 
	extra_data JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	published_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE RESTRICT, 
	FOREIGN KEY(brand_id) REFERENCES brands (id) ON DELETE RESTRICT
)

;

-- Table: sla_configurations

CREATE TABLE IF NOT EXISTS sla_configurations (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description TEXT, 
	source_type escalationsource NOT NULL, 
	priority escalationpriority NOT NULL, 
	category_id UUID, 
	response_time_minutes INTEGER NOT NULL, 
	resolution_time_minutes INTEGER NOT NULL, 
	business_hours_only BOOLEAN NOT NULL, 
	business_start_hour INTEGER NOT NULL, 
	business_end_hour INTEGER NOT NULL, 
	exclude_weekends BOOLEAN NOT NULL, 
	exclude_holidays BOOLEAN NOT NULL, 
	penalty_percentage NUMERIC(5, 2), 
	impact_score INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL
)

;

-- Table: transporter_serviceability

CREATE TABLE IF NOT EXISTS transporter_serviceability (
	id UUID NOT NULL, 
	transporter_id UUID NOT NULL, 
	origin_pincode VARCHAR(10) NOT NULL, 
	destination_pincode VARCHAR(10) NOT NULL, 
	is_serviceable BOOLEAN NOT NULL, 
	estimated_days INTEGER, 
	cod_available BOOLEAN NOT NULL, 
	prepaid_available BOOLEAN NOT NULL, 
	surface_available BOOLEAN NOT NULL, 
	express_available BOOLEAN NOT NULL, 
	rate FLOAT, 
	cod_charge FLOAT, 
	origin_state VARCHAR(100), 
	destination_state VARCHAR(100), 
	origin_city VARCHAR(100), 
	destination_city VARCHAR(100), 
	zone VARCHAR(20), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_transporter_serviceability UNIQUE (transporter_id, origin_pincode, destination_pincode), 
	FOREIGN KEY(transporter_id) REFERENCES transporters (id) ON DELETE CASCADE
)

;

-- Table: users

CREATE TABLE IF NOT EXISTS users (
	id UUID NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20), 
	password_hash VARCHAR(255) NOT NULL, 
	first_name VARCHAR(100) NOT NULL, 
	last_name VARCHAR(100), 
	avatar_url VARCHAR(500), 
	employee_code VARCHAR(50), 
	department VARCHAR(100), 
	designation VARCHAR(100), 
	region_id UUID, 
	is_active BOOLEAN NOT NULL, 
	is_verified BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	last_login_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (employee_code), 
	FOREIGN KEY(region_id) REFERENCES regions (id) ON DELETE SET NULL
)

;

-- Table: approval_requests

CREATE TABLE IF NOT EXISTS approval_requests (
	id UUID NOT NULL, 
	request_number VARCHAR(30) NOT NULL, 
	entity_type approvalentitytype NOT NULL, 
	entity_id UUID NOT NULL, 
	entity_number VARCHAR(50) NOT NULL, 
	amount NUMERIC(14, 2) NOT NULL, 
	approval_level approvallevel NOT NULL, 
	status approvalstatus NOT NULL, 
	priority INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	requested_by UUID NOT NULL, 
	requested_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	current_approver_id UUID, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	approval_comments TEXT, 
	rejected_by UUID, 
	rejected_at TIMESTAMP WITHOUT TIME ZONE, 
	rejection_reason TEXT, 
	due_date TIMESTAMP WITHOUT TIME ZONE, 
	is_overdue BOOLEAN NOT NULL, 
	escalated_at TIMESTAMP WITHOUT TIME ZONE, 
	escalated_to UUID, 
	escalation_reason TEXT, 
	extra_info JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(requested_by) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(current_approver_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(rejected_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(escalated_to) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: audience_segments

CREATE TABLE IF NOT EXISTS audience_segments (
	id UUID NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	segment_type audiencetype NOT NULL, 
	conditions JSON, 
	condition_logic VARCHAR(10) NOT NULL, 
	customer_ids JSON, 
	estimated_size INTEGER NOT NULL, 
	last_calculated_at TIMESTAMP WITHOUT TIME ZONE, 
	is_active BOOLEAN NOT NULL, 
	created_by_id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

-- Table: audit_logs

CREATE TABLE IF NOT EXISTS audit_logs (
	id UUID NOT NULL, 
	user_id UUID, 
	action VARCHAR(50) NOT NULL, 
	entity_type VARCHAR(50) NOT NULL, 
	entity_id UUID, 
	old_values JSON, 
	new_values JSON, 
	description TEXT, 
	ip_address VARCHAR(50), 
	user_agent VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: campaign_templates

CREATE TABLE IF NOT EXISTS campaign_templates (
	id UUID NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	campaign_type campaigntype NOT NULL, 
	category campaigncategory NOT NULL, 
	subject VARCHAR(500), 
	content TEXT NOT NULL, 
	html_content TEXT, 
	variables JSON, 
	media_urls JSON, 
	is_active BOOLEAN NOT NULL, 
	is_system BOOLEAN NOT NULL, 
	created_by_id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

-- Table: commission_payouts

CREATE TABLE IF NOT EXISTS commission_payouts (
	id UUID NOT NULL, 
	payout_number VARCHAR(30) NOT NULL, 
	period_start DATE NOT NULL, 
	period_end DATE NOT NULL, 
	payout_date DATE NOT NULL, 
	status payoutstatus NOT NULL, 
	total_gross NUMERIC(14, 2) NOT NULL, 
	total_tds NUMERIC(12, 2) NOT NULL, 
	total_deductions NUMERIC(12, 2) NOT NULL, 
	total_net NUMERIC(14, 2) NOT NULL, 
	transaction_count INTEGER NOT NULL, 
	earner_count INTEGER NOT NULL, 
	payment_mode VARCHAR(30), 
	payment_reference VARCHAR(100), 
	payment_date DATE, 
	remarks TEXT, 
	created_by UUID, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	processed_by UUID, 
	processed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: commission_product_rates

CREATE TABLE IF NOT EXISTS commission_product_rates (
	id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	commission_rate NUMERIC(5, 2) NOT NULL, 
	fixed_amount NUMERIC(10, 2), 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_plan_product_rate UNIQUE (plan_id, product_id), 
	FOREIGN KEY(plan_id) REFERENCES commission_plans (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)

;

-- Table: cost_centers

CREATE TABLE IF NOT EXISTS cost_centers (
	id UUID NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	parent_id UUID, 
	cost_center_type VARCHAR(50) NOT NULL, 
	annual_budget NUMERIC(15, 2) NOT NULL, 
	current_spend NUMERIC(15, 2) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	manager_id UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES cost_centers (id) ON DELETE RESTRICT, 
	FOREIGN KEY(manager_id) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: customer_addresses

CREATE TABLE IF NOT EXISTS customer_addresses (
	id UUID NOT NULL, 
	customer_id UUID NOT NULL, 
	address_type addresstype NOT NULL, 
	contact_name VARCHAR(100), 
	contact_phone VARCHAR(20), 
	address_line1 VARCHAR(255) NOT NULL, 
	address_line2 VARCHAR(255), 
	landmark VARCHAR(200), 
	city VARCHAR(100) NOT NULL, 
	state VARCHAR(100) NOT NULL, 
	pincode VARCHAR(10) NOT NULL, 
	country VARCHAR(100) NOT NULL, 
	latitude FLOAT, 
	longitude FLOAT, 
	is_default BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE
)

;

-- Table: dealer_schemes

CREATE TABLE IF NOT EXISTS dealer_schemes (
	id UUID NOT NULL, 
	scheme_code VARCHAR(30) NOT NULL, 
	scheme_name VARCHAR(200) NOT NULL, 
	description TEXT, 
	scheme_type schemetype NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	applicable_dealer_types JSON, 
	applicable_tiers JSON, 
	applicable_regions JSON, 
	applicable_products JSON, 
	applicable_categories JSON, 
	rules JSON NOT NULL, 
	total_budget NUMERIC(14, 2), 
	utilized_budget NUMERIC(14, 2) NOT NULL, 
	terms_and_conditions TEXT, 
	can_combine BOOLEAN NOT NULL, 
	created_by UUID, 
	approved_by UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: escalation_matrix

CREATE TABLE IF NOT EXISTS escalation_matrix (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description TEXT, 
	source_type escalationsource NOT NULL, 
	category_id UUID, 
	priority escalationpriority, 
	region_id UUID, 
	level escalationlevel NOT NULL, 
	trigger_after_minutes INTEGER NOT NULL, 
	response_sla_minutes INTEGER NOT NULL, 
	resolution_sla_minutes INTEGER NOT NULL, 
	notify_user_id UUID, 
	notify_role_id UUID, 
	assign_to_user_id UUID, 
	assign_to_role_id UUID, 
	additional_notify_emails JSON, 
	notification_channels JSON, 
	notification_template_id UUID, 
	auto_escalate BOOLEAN NOT NULL, 
	auto_assign BOOLEAN NOT NULL, 
	require_acknowledgment BOOLEAN NOT NULL, 
	acknowledgment_sla_minutes INTEGER, 
	is_active BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL, 
	FOREIGN KEY(region_id) REFERENCES regions (id) ON DELETE SET NULL, 
	FOREIGN KEY(notify_user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(notify_role_id) REFERENCES roles (id) ON DELETE SET NULL, 
	FOREIGN KEY(assign_to_user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(assign_to_role_id) REFERENCES roles (id) ON DELETE SET NULL
)

;

-- Table: financial_periods

CREATE TABLE IF NOT EXISTS financial_periods (
	id UUID NOT NULL, 
	period_name VARCHAR(50) NOT NULL, 
	period_code VARCHAR(20), 
	financial_year VARCHAR(10), 
	period_type VARCHAR(20) NOT NULL, 
	is_year_end BOOLEAN NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	status financialperiodstatus NOT NULL, 
	is_current BOOLEAN NOT NULL, 
	is_adjustment_period BOOLEAN NOT NULL, 
	closed_by UUID, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (period_name), 
	FOREIGN KEY(closed_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: franchisees

CREATE TABLE IF NOT EXISTS franchisees (
	id VARCHAR(36) NOT NULL, 
	franchisee_code VARCHAR(50) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	legal_name VARCHAR(300), 
	franchisee_type franchiseetype NOT NULL, 
	status franchiseestatus NOT NULL, 
	tier franchiseetier NOT NULL, 
	contact_person VARCHAR(200) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20) NOT NULL, 
	alternate_phone VARCHAR(20), 
	website VARCHAR(500), 
	address_line1 VARCHAR(500) NOT NULL, 
	address_line2 VARCHAR(500), 
	city VARCHAR(100) NOT NULL, 
	state VARCHAR(100) NOT NULL, 
	pincode VARCHAR(10) NOT NULL, 
	country VARCHAR(100) NOT NULL, 
	latitude NUMERIC(10, 7), 
	longitude NUMERIC(10, 7), 
	gst_number VARCHAR(20), 
	pan_number VARCHAR(20), 
	cin_number VARCHAR(30), 
	bank_name VARCHAR(200), 
	bank_account_number VARCHAR(50), 
	bank_ifsc VARCHAR(20), 
	parent_franchisee_id VARCHAR(36), 
	region_id VARCHAR(36), 
	credit_limit NUMERIC(15, 2) NOT NULL, 
	current_outstanding NUMERIC(15, 2) NOT NULL, 
	payment_terms_days INTEGER NOT NULL, 
	commission_rate NUMERIC(5, 2) NOT NULL, 
	security_deposit NUMERIC(15, 2) NOT NULL, 
	total_orders INTEGER NOT NULL, 
	total_revenue NUMERIC(18, 2) NOT NULL, 
	avg_monthly_revenue NUMERIC(15, 2) NOT NULL, 
	customer_rating NUMERIC(3, 2) NOT NULL, 
	compliance_score NUMERIC(5, 2) NOT NULL, 
	application_date DATE, 
	approval_date DATE, 
	activation_date DATE, 
	termination_date DATE, 
	last_order_date DATE, 
	last_audit_date DATE, 
	documents JSON, 
	notes TEXT, 
	created_by_id VARCHAR(36), 
	approved_by_id VARCHAR(36), 
	account_manager_id VARCHAR(36), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_franchisee_id) REFERENCES franchisees (id), 
	FOREIGN KEY(region_id) REFERENCES regions (id), 
	FOREIGN KEY(created_by_id) REFERENCES users (id), 
	FOREIGN KEY(approved_by_id) REFERENCES users (id), 
	FOREIGN KEY(account_manager_id) REFERENCES users (id)
)

;

-- Table: lead_assignment_rules

CREATE TABLE IF NOT EXISTS lead_assignment_rules (
	id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description TEXT, 
	source leadsource, 
	lead_type leadtype, 
	region_id UUID, 
	pincode_pattern VARCHAR(50), 
	category_id UUID, 
	min_score INTEGER, 
	max_score INTEGER, 
	assign_to_user_id UUID, 
	assign_to_team_id UUID, 
	round_robin BOOLEAN NOT NULL, 
	round_robin_users JSON, 
	priority INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(region_id) REFERENCES regions (id) ON DELETE SET NULL, 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL, 
	FOREIGN KEY(assign_to_user_id) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: model_code_references

CREATE TABLE IF NOT EXISTS model_code_references (
	id VARCHAR(36) NOT NULL, 
	product_id VARCHAR(36), 
	product_sku VARCHAR(50), 
	fg_code VARCHAR(20), 
	model_code VARCHAR(10) NOT NULL, 
	item_type itemtype, 
	description VARCHAR(255), 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (product_id), 
	FOREIGN KEY(product_id) REFERENCES products (id)
)

;

-- Table: product_documents

CREATE TABLE IF NOT EXISTS product_documents (
	id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	document_type documenttype NOT NULL, 
	file_url VARCHAR(500) NOT NULL, 
	file_size_bytes INTEGER, 
	mime_type VARCHAR(100), 
	sort_order INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)

;

-- Table: product_images

CREATE TABLE IF NOT EXISTS product_images (
	id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	image_url VARCHAR(500) NOT NULL, 
	thumbnail_url VARCHAR(500), 
	alt_text VARCHAR(255), 
	is_primary BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)

;

-- Table: product_specifications

CREATE TABLE IF NOT EXISTS product_specifications (
	id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	group_name VARCHAR(100) NOT NULL, 
	key VARCHAR(100) NOT NULL, 
	value VARCHAR(500) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)

;

-- Table: product_variants

CREATE TABLE IF NOT EXISTS product_variants (
	id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	sku VARCHAR(50) NOT NULL, 
	attributes JSON, 
	mrp NUMERIC(12, 2), 
	selling_price NUMERIC(12, 2), 
	stock_quantity INTEGER NOT NULL, 
	image_url VARCHAR(500), 
	is_active BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)

;

-- Table: promotions

CREATE TABLE IF NOT EXISTS promotions (
	id UUID NOT NULL, 
	promo_code VARCHAR(30) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	short_description VARCHAR(500), 
	promotion_type promotiontype NOT NULL, 
	promotion_scope promotionscope NOT NULL, 
	discount_application discountapplication NOT NULL, 
	status promotionstatus NOT NULL, 
	start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	end_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	is_recurring BOOLEAN NOT NULL, 
	recurring_schedule JSON, 
	applicable_channels JSON, 
	excluded_channels JSON, 
	is_d2c BOOLEAN NOT NULL, 
	is_marketplace BOOLEAN NOT NULL, 
	is_dealer BOOLEAN NOT NULL, 
	is_retail BOOLEAN NOT NULL, 
	is_corporate BOOLEAN NOT NULL, 
	discount_percentage NUMERIC(5, 2), 
	max_discount_amount NUMERIC(12, 2), 
	discount_amount NUMERIC(12, 2), 
	cashback_percentage NUMERIC(5, 2), 
	cashback_amount NUMERIC(12, 2), 
	max_cashback NUMERIC(12, 2), 
	buy_quantity INTEGER, 
	get_quantity INTEGER, 
	get_discount_percentage NUMERIC(5, 2), 
	min_order_value NUMERIC(12, 2), 
	min_quantity INTEGER, 
	applicable_products JSON, 
	applicable_categories JSON, 
	applicable_brands JSON, 
	excluded_products JSON, 
	excluded_categories JSON, 
	customer_segments JSON, 
	applicable_regions JSON, 
	applicable_pincodes JSON, 
	applicable_dealer_types JSON, 
	applicable_dealer_tiers JSON, 
	applicable_dealers JSON, 
	applicable_payment_methods JSON, 
	applicable_banks JSON, 
	applicable_card_types JSON, 
	total_usage_limit INTEGER, 
	per_customer_limit INTEGER NOT NULL, 
	per_order_limit INTEGER NOT NULL, 
	current_usage_count INTEGER NOT NULL, 
	total_budget NUMERIC(14, 2), 
	utilized_budget NUMERIC(14, 2) NOT NULL, 
	display_priority INTEGER NOT NULL, 
	is_featured BOOLEAN NOT NULL, 
	is_stackable BOOLEAN NOT NULL, 
	show_on_product_page BOOLEAN NOT NULL, 
	show_on_checkout BOOLEAN NOT NULL, 
	requires_coupon_code BOOLEAN NOT NULL, 
	coupon_code VARCHAR(30), 
	banner_image_url VARCHAR(500), 
	terms_and_conditions TEXT, 
	created_by UUID, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: role_permissions

CREATE TABLE IF NOT EXISTS role_permissions (
	id UUID NOT NULL, 
	role_id UUID NOT NULL, 
	permission_id UUID NOT NULL, 
	granted_by UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id), 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE, 
	FOREIGN KEY(permission_id) REFERENCES permissions (id) ON DELETE CASCADE, 
	FOREIGN KEY(granted_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: serial_sequences

CREATE TABLE IF NOT EXISTS serial_sequences (
	id VARCHAR(36) NOT NULL, 
	product_id VARCHAR(36), 
	model_code VARCHAR(10) NOT NULL, 
	item_type itemtype, 
	supplier_code VARCHAR(2) NOT NULL, 
	year_code VARCHAR(2) NOT NULL, 
	month_code VARCHAR(1) NOT NULL, 
	last_serial INTEGER NOT NULL, 
	total_generated INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES products (id)
)

;

-- Table: user_roles

CREATE TABLE IF NOT EXISTS user_roles (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	role_id UUID NOT NULL, 
	assigned_by UUID, 
	assigned_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE, 
	FOREIGN KEY(assigned_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: warehouses

CREATE TABLE IF NOT EXISTS warehouses (
	id UUID NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	warehouse_type warehousetype, 
	address_line1 VARCHAR(255) NOT NULL, 
	address_line2 VARCHAR(255), 
	city VARCHAR(100) NOT NULL, 
	state VARCHAR(100) NOT NULL, 
	pincode VARCHAR(10) NOT NULL, 
	country VARCHAR(100), 
	latitude FLOAT, 
	longitude FLOAT, 
	contact_name VARCHAR(100), 
	contact_phone VARCHAR(20), 
	contact_email VARCHAR(100), 
	region_id UUID, 
	manager_id UUID, 
	total_capacity FLOAT, 
	current_utilization FLOAT, 
	is_active BOOLEAN, 
	is_default BOOLEAN, 
	can_fulfill_orders BOOLEAN, 
	can_receive_transfers BOOLEAN, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(region_id) REFERENCES regions (id), 
	FOREIGN KEY(manager_id) REFERENCES users (id)
)

;

-- Table: approval_history

CREATE TABLE IF NOT EXISTS approval_history (
	id UUID NOT NULL, 
	approval_request_id UUID NOT NULL, 
	action VARCHAR(50) NOT NULL, 
	from_status VARCHAR(20), 
	to_status VARCHAR(20) NOT NULL, 
	performed_by UUID NOT NULL, 
	comments TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(approval_request_id) REFERENCES approval_requests (id) ON DELETE CASCADE, 
	FOREIGN KEY(performed_by) REFERENCES users (id) ON DELETE RESTRICT
)

;

-- Table: campaign_automations

CREATE TABLE IF NOT EXISTS campaign_automations (
	id UUID NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	trigger_type VARCHAR(50) NOT NULL, 
	trigger_conditions JSON, 
	delay_minutes INTEGER NOT NULL, 
	template_id UUID NOT NULL, 
	campaign_type campaigntype NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	max_per_customer INTEGER NOT NULL, 
	cooldown_days INTEGER NOT NULL, 
	total_triggered INTEGER NOT NULL, 
	total_sent INTEGER NOT NULL, 
	created_by_id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(template_id) REFERENCES campaign_templates (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

-- Table: campaigns

CREATE TABLE IF NOT EXISTS campaigns (
	id UUID NOT NULL, 
	campaign_code VARCHAR(30) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	campaign_type campaigntype NOT NULL, 
	category campaigncategory NOT NULL, 
	status campaignstatus NOT NULL, 
	template_id UUID, 
	subject VARCHAR(500), 
	content TEXT NOT NULL, 
	html_content TEXT, 
	media_urls JSON, 
	cta_text VARCHAR(100), 
	cta_url VARCHAR(500), 
	audience_type audiencetype NOT NULL, 
	segment_id UUID, 
	target_count INTEGER NOT NULL, 
	scheduled_at TIMESTAMP WITHOUT TIME ZONE, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	is_recurring BOOLEAN NOT NULL, 
	recurrence_pattern VARCHAR(50), 
	recurrence_config JSON, 
	sender_name VARCHAR(100), 
	sender_email VARCHAR(255), 
	sender_phone VARCHAR(20), 
	reply_to VARCHAR(255), 
	is_ab_test BOOLEAN NOT NULL, 
	ab_test_config JSON, 
	budget_amount NUMERIC(12, 2), 
	daily_limit INTEGER, 
	hourly_limit INTEGER, 
	total_sent INTEGER NOT NULL, 
	total_delivered INTEGER NOT NULL, 
	total_opened INTEGER NOT NULL, 
	total_clicked INTEGER NOT NULL, 
	total_bounced INTEGER NOT NULL, 
	total_unsubscribed INTEGER NOT NULL, 
	total_failed INTEGER NOT NULL, 
	total_cost NUMERIC(12, 2) NOT NULL, 
	tags JSON, 
	created_by_id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(template_id) REFERENCES campaign_templates (id) ON DELETE SET NULL, 
	FOREIGN KEY(segment_id) REFERENCES audience_segments (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

-- Table: company_branches

CREATE TABLE IF NOT EXISTS company_branches (
	id UUID NOT NULL, 
	company_id UUID NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	branch_type VARCHAR(50) NOT NULL, 
	gstin VARCHAR(15), 
	state_code VARCHAR(2) NOT NULL, 
	address_line1 VARCHAR(255) NOT NULL, 
	address_line2 VARCHAR(255), 
	city VARCHAR(100) NOT NULL, 
	state VARCHAR(100) NOT NULL, 
	pincode VARCHAR(10) NOT NULL, 
	email VARCHAR(255), 
	phone VARCHAR(20), 
	contact_person VARCHAR(100), 
	warehouse_id UUID, 
	is_active BOOLEAN NOT NULL, 
	is_billing_address BOOLEAN NOT NULL, 
	is_shipping_address BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_company_branch_code UNIQUE (company_id, code), 
	FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE, 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL
)

;

-- Table: dealer_tier_pricing

CREATE TABLE IF NOT EXISTS dealer_tier_pricing (
	id UUID NOT NULL, 
	tier dealertier NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	discount_percentage NUMERIC(5, 2) NOT NULL, 
	fixed_price NUMERIC(12, 2), 
	is_active BOOLEAN NOT NULL, 
	effective_from DATE NOT NULL, 
	effective_to DATE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_tier_product_pricing UNIQUE (tier, product_id, variant_id), 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id) ON DELETE CASCADE
)

;

-- Table: dealers

CREATE TABLE IF NOT EXISTS dealers (
	id UUID NOT NULL, 
	dealer_code VARCHAR(30) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	legal_name VARCHAR(200) NOT NULL, 
	display_name VARCHAR(200), 
	dealer_type dealertype NOT NULL, 
	status dealerstatus NOT NULL, 
	tier dealertier NOT NULL, 
	parent_dealer_id UUID, 
	user_id UUID, 
	gstin VARCHAR(15) NOT NULL, 
	pan VARCHAR(10) NOT NULL, 
	tan VARCHAR(10), 
	gst_registration_type VARCHAR(30) NOT NULL, 
	is_msme BOOLEAN NOT NULL, 
	msme_number VARCHAR(30), 
	contact_person VARCHAR(200) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20) NOT NULL, 
	alternate_phone VARCHAR(20), 
	whatsapp VARCHAR(20), 
	registered_address_line1 VARCHAR(255) NOT NULL, 
	registered_address_line2 VARCHAR(255), 
	registered_city VARCHAR(100) NOT NULL, 
	registered_district VARCHAR(100) NOT NULL, 
	registered_state VARCHAR(100) NOT NULL, 
	registered_state_code VARCHAR(2) NOT NULL, 
	registered_pincode VARCHAR(10) NOT NULL, 
	shipping_address_line1 VARCHAR(255), 
	shipping_address_line2 VARCHAR(255), 
	shipping_city VARCHAR(100), 
	shipping_state VARCHAR(100), 
	shipping_pincode VARCHAR(10), 
	region VARCHAR(50) NOT NULL, 
	state VARCHAR(100) NOT NULL, 
	territory VARCHAR(100), 
	assigned_pincodes JSON, 
	business_type VARCHAR(50) NOT NULL, 
	establishment_year INTEGER, 
	annual_turnover NUMERIC(14, 2), 
	shop_area_sqft INTEGER, 
	no_of_employees INTEGER, 
	existing_brands JSON, 
	bank_name VARCHAR(200), 
	bank_branch VARCHAR(200), 
	bank_account_number VARCHAR(30), 
	bank_ifsc VARCHAR(11), 
	bank_account_name VARCHAR(200), 
	credit_limit NUMERIC(14, 2) NOT NULL, 
	credit_days INTEGER NOT NULL, 
	credit_status creditstatus NOT NULL, 
	outstanding_amount NUMERIC(14, 2) NOT NULL, 
	overdue_amount NUMERIC(14, 2) NOT NULL, 
	security_deposit NUMERIC(14, 2) NOT NULL, 
	security_deposit_paid BOOLEAN NOT NULL, 
	default_warehouse_id UUID, 
	sales_rep_id UUID, 
	area_sales_manager_id UUID, 
	agreement_start_date DATE, 
	agreement_end_date DATE, 
	agreement_document_url VARCHAR(500), 
	gst_certificate_url VARCHAR(500), 
	pan_card_url VARCHAR(500), 
	shop_photo_url VARCHAR(500), 
	cancelled_cheque_url VARCHAR(500), 
	kyc_verified BOOLEAN NOT NULL, 
	kyc_verified_at TIMESTAMP WITHOUT TIME ZONE, 
	kyc_verified_by UUID, 
	total_orders INTEGER NOT NULL, 
	total_revenue NUMERIC(14, 2) NOT NULL, 
	last_order_date TIMESTAMP WITHOUT TIME ZONE, 
	average_order_value NUMERIC(12, 2), 
	dealer_rating NUMERIC(3, 2), 
	payment_rating NUMERIC(3, 2), 
	can_place_orders BOOLEAN NOT NULL, 
	receive_promotions BOOLEAN NOT NULL, 
	portal_access BOOLEAN NOT NULL, 
	internal_notes TEXT, 
	onboarded_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_dealer_id) REFERENCES dealers (id) ON DELETE SET NULL, 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(default_warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL, 
	FOREIGN KEY(sales_rep_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(area_sales_manager_id) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: franchisee_audits

CREATE TABLE IF NOT EXISTS franchisee_audits (
	id VARCHAR(36) NOT NULL, 
	franchisee_id VARCHAR(36) NOT NULL, 
	audit_number VARCHAR(50) NOT NULL, 
	audit_type audittype NOT NULL, 
	status auditstatus NOT NULL, 
	scheduled_date DATE NOT NULL, 
	actual_date DATE, 
	auditor_id VARCHAR(36), 
	auditor_name VARCHAR(200) NOT NULL, 
	checklist JSON, 
	findings TEXT, 
	observations JSON, 
	non_conformities JSON, 
	overall_score NUMERIC(5, 2), 
	compliance_score NUMERIC(5, 2), 
	quality_score NUMERIC(5, 2), 
	result auditresult, 
	corrective_actions JSON, 
	follow_up_required BOOLEAN NOT NULL, 
	follow_up_date DATE, 
	report_url VARCHAR(500), 
	evidence_urls JSON, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(franchisee_id) REFERENCES franchisees (id), 
	FOREIGN KEY(auditor_id) REFERENCES users (id)
)

;

-- Table: franchisee_contracts

CREATE TABLE IF NOT EXISTS franchisee_contracts (
	id VARCHAR(36) NOT NULL, 
	franchisee_id VARCHAR(36) NOT NULL, 
	contract_number VARCHAR(50) NOT NULL, 
	contract_type VARCHAR(50) NOT NULL, 
	status contractstatus NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	auto_renewal BOOLEAN NOT NULL, 
	renewal_terms_days INTEGER NOT NULL, 
	notice_period_days INTEGER NOT NULL, 
	franchise_fee NUMERIC(15, 2) NOT NULL, 
	royalty_percentage NUMERIC(5, 2) NOT NULL, 
	marketing_fee_percentage NUMERIC(5, 2) NOT NULL, 
	minimum_purchase_commitment NUMERIC(15, 2) NOT NULL, 
	territory_exclusive BOOLEAN NOT NULL, 
	territory_description TEXT, 
	document_url VARCHAR(500), 
	signed_document_url VARCHAR(500), 
	approved_by_id VARCHAR(36), 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	terminated_by_id VARCHAR(36), 
	termination_reason TEXT, 
	terminated_at TIMESTAMP WITHOUT TIME ZONE, 
	notes TEXT, 
	created_by_id VARCHAR(36), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(franchisee_id) REFERENCES franchisees (id), 
	FOREIGN KEY(approved_by_id) REFERENCES users (id), 
	FOREIGN KEY(terminated_by_id) REFERENCES users (id), 
	FOREIGN KEY(created_by_id) REFERENCES users (id)
)

;

-- Table: franchisee_performance

CREATE TABLE IF NOT EXISTS franchisee_performance (
	id VARCHAR(36) NOT NULL, 
	franchisee_id VARCHAR(36) NOT NULL, 
	period_type VARCHAR(20) NOT NULL, 
	period_start DATE NOT NULL, 
	period_end DATE NOT NULL, 
	total_orders INTEGER NOT NULL, 
	total_units_sold INTEGER NOT NULL, 
	gross_revenue NUMERIC(18, 2) NOT NULL, 
	net_revenue NUMERIC(18, 2) NOT NULL, 
	returns_value NUMERIC(15, 2) NOT NULL, 
	target_revenue NUMERIC(18, 2) NOT NULL, 
	target_orders INTEGER NOT NULL, 
	target_achievement_percentage NUMERIC(5, 2) NOT NULL, 
	new_customers INTEGER NOT NULL, 
	repeat_customers INTEGER NOT NULL, 
	customer_complaints INTEGER NOT NULL, 
	avg_customer_rating NUMERIC(3, 2) NOT NULL, 
	installations_completed INTEGER NOT NULL, 
	service_calls_handled INTEGER NOT NULL, 
	avg_response_time_hours NUMERIC(6, 2) NOT NULL, 
	first_time_fix_rate NUMERIC(5, 2) NOT NULL, 
	commission_earned NUMERIC(15, 2) NOT NULL, 
	incentives_earned NUMERIC(15, 2) NOT NULL, 
	penalties_applied NUMERIC(15, 2) NOT NULL, 
	overall_score NUMERIC(5, 2) NOT NULL, 
	sales_score NUMERIC(5, 2) NOT NULL, 
	service_score NUMERIC(5, 2) NOT NULL, 
	compliance_score NUMERIC(5, 2) NOT NULL, 
	rank_in_region INTEGER, 
	rank_overall INTEGER, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(franchisee_id) REFERENCES franchisees (id)
)

;

-- Table: franchisee_support_tickets

CREATE TABLE IF NOT EXISTS franchisee_support_tickets (
	id VARCHAR(36) NOT NULL, 
	franchisee_id VARCHAR(36) NOT NULL, 
	ticket_number VARCHAR(50) NOT NULL, 
	subject VARCHAR(500) NOT NULL, 
	description TEXT NOT NULL, 
	category supportticketcategory NOT NULL, 
	priority supportticketpriority NOT NULL, 
	status supportticketstatus NOT NULL, 
	contact_name VARCHAR(200) NOT NULL, 
	contact_email VARCHAR(255), 
	contact_phone VARCHAR(20), 
	assigned_to_id VARCHAR(36), 
	assigned_at TIMESTAMP WITHOUT TIME ZONE, 
	sla_due_at TIMESTAMP WITHOUT TIME ZONE, 
	sla_breached BOOLEAN NOT NULL, 
	resolution TEXT, 
	resolved_by_id VARCHAR(36), 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	resolution_time_hours NUMERIC(8, 2), 
	satisfaction_rating INTEGER, 
	feedback TEXT, 
	is_escalated BOOLEAN NOT NULL, 
	escalated_to_id VARCHAR(36), 
	escalated_at TIMESTAMP WITHOUT TIME ZONE, 
	escalation_reason TEXT, 
	attachments JSON, 
	first_response_at TIMESTAMP WITHOUT TIME ZONE, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	reopen_count INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(franchisee_id) REFERENCES franchisees (id), 
	FOREIGN KEY(assigned_to_id) REFERENCES users (id), 
	FOREIGN KEY(resolved_by_id) REFERENCES users (id), 
	FOREIGN KEY(escalated_to_id) REFERENCES users (id)
)

;

-- Table: franchisee_territories

CREATE TABLE IF NOT EXISTS franchisee_territories (
	id VARCHAR(36) NOT NULL, 
	franchisee_id VARCHAR(36) NOT NULL, 
	territory_name VARCHAR(200) NOT NULL, 
	territory_type VARCHAR(50) NOT NULL, 
	status territorystatus NOT NULL, 
	is_exclusive BOOLEAN NOT NULL, 
	pincodes JSON, 
	cities JSON, 
	districts JSON, 
	states JSON, 
	geo_boundary JSON, 
	effective_from DATE NOT NULL, 
	effective_to DATE, 
	total_customers INTEGER NOT NULL, 
	total_orders INTEGER NOT NULL, 
	total_revenue NUMERIC(18, 2) NOT NULL, 
	notes TEXT, 
	created_by_id VARCHAR(36), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(franchisee_id) REFERENCES franchisees (id), 
	FOREIGN KEY(created_by_id) REFERENCES users (id)
)

;

-- Table: franchisee_trainings

CREATE TABLE IF NOT EXISTS franchisee_trainings (
	id VARCHAR(36) NOT NULL, 
	franchisee_id VARCHAR(36) NOT NULL, 
	training_code VARCHAR(50) NOT NULL, 
	training_name VARCHAR(200) NOT NULL, 
	training_type trainingtype NOT NULL, 
	status trainingstatus NOT NULL, 
	description TEXT, 
	objectives JSON, 
	scheduled_date DATE NOT NULL, 
	start_time VARCHAR(10), 
	duration_hours NUMERIC(4, 1) NOT NULL, 
	mode VARCHAR(20) NOT NULL, 
	location VARCHAR(500), 
	meeting_link VARCHAR(500), 
	attendee_name VARCHAR(200) NOT NULL, 
	attendee_email VARCHAR(255), 
	attendee_phone VARCHAR(20), 
	attended BOOLEAN NOT NULL, 
	attendance_percentage NUMERIC(5, 2) NOT NULL, 
	has_assessment BOOLEAN NOT NULL, 
	assessment_score NUMERIC(5, 2), 
	passing_score NUMERIC(5, 2) NOT NULL, 
	passed BOOLEAN NOT NULL, 
	attempts INTEGER NOT NULL, 
	certificate_issued BOOLEAN NOT NULL, 
	certificate_number VARCHAR(50), 
	certificate_url VARCHAR(500), 
	certificate_expiry DATE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	feedback TEXT, 
	feedback_rating INTEGER, 
	trainer_name VARCHAR(200), 
	trainer_id VARCHAR(36), 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(franchisee_id) REFERENCES franchisees (id), 
	FOREIGN KEY(trainer_id) REFERENCES users (id)
)

;

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
	CONSTRAINT uq_inventory_summary UNIQUE (warehouse_id, product_id, variant_id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
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
	CONSTRAINT uq_invoice_sequence UNIQUE (series_code, financial_year), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL
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
	PRIMARY KEY (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
	FOREIGN KEY(transporter_id) REFERENCES transporters (id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(confirmed_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(handover_by) REFERENCES users (id) ON DELETE SET NULL
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
	PRIMARY KEY (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
	FOREIGN KEY(assigned_to) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
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
	PRIMARY KEY (id), 
	FOREIGN KEY(requested_by) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(delivery_warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
	FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE SET NULL
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
	PRIMARY KEY (id), 
	FOREIGN KEY(default_warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL
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
	PRIMARY KEY (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id)
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
	PRIMARY KEY (id), 
	FOREIGN KEY(from_warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(to_warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(requested_by) REFERENCES users (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id), 
	FOREIGN KEY(dispatched_by) REFERENCES users (id), 
	FOREIGN KEY(received_by) REFERENCES users (id)
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
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(region_id) REFERENCES regions (id), 
	FOREIGN KEY(assigned_warehouse_id) REFERENCES warehouses (id)
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
	PRIMARY KEY (id), 
	FOREIGN KEY(default_warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL, 
	FOREIGN KEY(verified_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE SET NULL
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
	CONSTRAINT uq_warehouse_serviceability UNIQUE (warehouse_id, pincode), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE CASCADE
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
	CONSTRAINT uq_warehouse_zone_code UNIQUE (warehouse_id, zone_code), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE CASCADE
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
	CONSTRAINT uq_allocation_rule_channel_priority UNIQUE (channel_code, priority), 
	FOREIGN KEY(channel_id) REFERENCES sales_channels (id) ON DELETE SET NULL, 
	FOREIGN KEY(fixed_warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
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
	PRIMARY KEY (id), 
	FOREIGN KEY(campaign_id) REFERENCES campaigns (id) ON DELETE CASCADE, 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE SET NULL
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
	CONSTRAINT uq_channel_inventory UNIQUE (channel_id, warehouse_id, product_id, variant_id), 
	FOREIGN KEY(channel_id) REFERENCES sales_channels (id) ON DELETE CASCADE, 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id) ON DELETE CASCADE
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
	CONSTRAINT uq_channel_product_pricing UNIQUE (channel_id, product_id, variant_id), 
	FOREIGN KEY(channel_id) REFERENCES sales_channels (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id) ON DELETE CASCADE
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
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(dealer_id) REFERENCES dealers (id) ON DELETE CASCADE, 
	FOREIGN KEY(plan_id) REFERENCES commission_plans (id) ON DELETE RESTRICT
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
	PRIMARY KEY (id), 
	FOREIGN KEY(dealer_id) REFERENCES dealers (id) ON DELETE CASCADE
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
	CONSTRAINT uq_dealer_product_pricing UNIQUE (dealer_id, product_id, variant_id), 
	FOREIGN KEY(dealer_id) REFERENCES dealers (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id) ON DELETE CASCADE
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
	CONSTRAINT uq_dealer_target UNIQUE (dealer_id, target_period, target_year, target_month), 
	FOREIGN KEY(dealer_id) REFERENCES dealers (id) ON DELETE CASCADE, 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE SET NULL
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
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE SET NULL, 
	FOREIGN KEY(assigned_to_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(assigned_by_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(acknowledged_by_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(resolved_by_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(matrix_id) REFERENCES escalation_matrix (id) ON DELETE SET NULL, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE SET NULL, 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL, 
	FOREIGN KEY(region_id) REFERENCES regions (id) ON DELETE SET NULL, 
	FOREIGN KEY(dealer_id) REFERENCES dealers (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE RESTRICT
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
	PRIMARY KEY (id), 
	FOREIGN KEY(franchisee_id) REFERENCES franchisees (id), 
	FOREIGN KEY(territory_id) REFERENCES franchisee_territories (id)
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
	PRIMARY KEY (id), 
	FOREIGN KEY(ticket_id) REFERENCES franchisee_support_tickets (id), 
	FOREIGN KEY(author_id) REFERENCES users (id)
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
	PRIMARY KEY (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id), 
	FOREIGN KEY(assigned_to) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(adjustment_id) REFERENCES stock_adjustments (id)
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
	PRIMARY KEY (id), 
	FOREIGN KEY(period_id) REFERENCES financial_periods (id) ON DELETE RESTRICT, 
	FOREIGN KEY(channel_id) REFERENCES sales_channels (id) ON DELETE SET NULL, 
	FOREIGN KEY(reversal_of_id) REFERENCES journal_entries (id) ON DELETE SET NULL, 
	FOREIGN KEY(reversed_by_id) REFERENCES journal_entries (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(submitted_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(posted_by) REFERENCES users (id) ON DELETE SET NULL
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
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE RESTRICT, 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL, 
	FOREIGN KEY(dealer_id) REFERENCES dealers (id) ON DELETE SET NULL, 
	FOREIGN KEY(region_id) REFERENCES regions (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
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
	PRIMARY KEY (id), 
	FOREIGN KEY(vendor_id) REFERENCES vendors (id) ON DELETE RESTRICT, 
	FOREIGN KEY(requisition_id) REFERENCES purchase_requisitions (id) ON DELETE SET NULL, 
	FOREIGN KEY(delivery_warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(approval_request_id) REFERENCES approval_requests (id) ON DELETE SET NULL
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
	PRIMARY KEY (id), 
	FOREIGN KEY(requisition_id) REFERENCES purchase_requisitions (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id) ON DELETE SET NULL, 
	FOREIGN KEY(preferred_vendor_id) REFERENCES vendors (id) ON DELETE SET NULL
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
	CONSTRAINT uq_putaway_rule UNIQUE (warehouse_id, category_id, priority), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE CASCADE, 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE SET NULL, 
	FOREIGN KEY(brand_id) REFERENCES brands (id) ON DELETE SET NULL, 
	FOREIGN KEY(target_zone_id) REFERENCES warehouse_zones (id) ON DELETE CASCADE
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
	PRIMARY KEY (id), 
	FOREIGN KEY(transfer_id) REFERENCES stock_transfers (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
)

;

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

-- Table: credit_debit_notes

CREATE TABLE IF NOT EXISTS credit_debit_notes (
	id UUID NOT NULL, 
	note_number VARCHAR(50) NOT NULL, 
	document_type documenttype NOT NULL, 
	invoice_id UUID NOT NULL, 
	original_invoice_number VARCHAR(50) NOT NULL, 
	original_invoice_date DATE NOT NULL, 
	note_date DATE NOT NULL, 
	reason notereason NOT NULL, 
	reason_description VARCHAR(500), 
	status invoicestatus NOT NULL, 
	customer_id UUID, 
	customer_name VARCHAR(200) NOT NULL, 
	customer_gstin VARCHAR(15), 
	place_of_supply VARCHAR(100) NOT NULL, 
	place_of_supply_code VARCHAR(2) NOT NULL, 
	is_interstate BOOLEAN NOT NULL, 
	taxable_amount NUMERIC(14, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	cess_amount NUMERIC(12, 2) NOT NULL, 
	total_tax NUMERIC(12, 2) NOT NULL, 
	grand_total NUMERIC(14, 2) NOT NULL, 
	irn VARCHAR(64), 
	ack_number VARCHAR(50), 
	ack_date TIMESTAMP WITHOUT TIME ZONE, 
	pre_gst BOOLEAN NOT NULL, 
	pdf_url VARCHAR(500), 
	created_by UUID, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES tax_invoices (id) ON DELETE RESTRICT, 
	FOREIGN KEY(customer_id) REFERENCES users (id) ON DELETE SET NULL, 
	UNIQUE (irn), 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: eway_bills

CREATE TABLE IF NOT EXISTS eway_bills (
	id UUID NOT NULL, 
	eway_bill_number VARCHAR(20), 
	invoice_id UUID NOT NULL, 
	status ewaybillstatus NOT NULL, 
	document_type VARCHAR(20) NOT NULL, 
	document_number VARCHAR(50) NOT NULL, 
	document_date DATE NOT NULL, 
	supply_type VARCHAR(10) NOT NULL, 
	sub_supply_type VARCHAR(10) NOT NULL, 
	transaction_type VARCHAR(10) NOT NULL, 
	from_gstin VARCHAR(15) NOT NULL, 
	from_name VARCHAR(200) NOT NULL, 
	from_address1 VARCHAR(255) NOT NULL, 
	from_address2 VARCHAR(255), 
	from_place VARCHAR(100) NOT NULL, 
	from_pincode VARCHAR(10) NOT NULL, 
	from_state_code VARCHAR(2) NOT NULL, 
	to_gstin VARCHAR(15), 
	to_name VARCHAR(200) NOT NULL, 
	to_address1 VARCHAR(255) NOT NULL, 
	to_address2 VARCHAR(255), 
	to_place VARCHAR(100) NOT NULL, 
	to_pincode VARCHAR(10) NOT NULL, 
	to_state_code VARCHAR(2) NOT NULL, 
	total_value NUMERIC(14, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	cess_amount NUMERIC(12, 2) NOT NULL, 
	transporter_id UUID, 
	transporter_name VARCHAR(200), 
	transporter_gstin VARCHAR(15), 
	transport_mode VARCHAR(10) NOT NULL, 
	vehicle_number VARCHAR(20), 
	vehicle_type VARCHAR(10), 
	transport_doc_number VARCHAR(50), 
	transport_doc_date DATE, 
	distance_km INTEGER NOT NULL, 
	valid_from TIMESTAMP WITHOUT TIME ZONE, 
	valid_until TIMESTAMP WITHOUT TIME ZONE, 
	extension_count INTEGER NOT NULL, 
	extended_until TIMESTAMP WITHOUT TIME ZONE, 
	extension_reason VARCHAR(500), 
	cancelled_at TIMESTAMP WITHOUT TIME ZONE, 
	cancellation_reason VARCHAR(500), 
	generated_at TIMESTAMP WITHOUT TIME ZONE, 
	api_response JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES tax_invoices (id) ON DELETE CASCADE, 
	FOREIGN KEY(transporter_id) REFERENCES transporters (id) ON DELETE SET NULL
)

;

-- Table: general_ledger

CREATE TABLE IF NOT EXISTS general_ledger (
	id UUID NOT NULL, 
	account_id UUID NOT NULL, 
	period_id UUID NOT NULL, 
	transaction_date DATE NOT NULL, 
	journal_entry_id UUID NOT NULL, 
	journal_line_id UUID NOT NULL, 
	debit_amount NUMERIC(15, 2) NOT NULL, 
	credit_amount NUMERIC(15, 2) NOT NULL, 
	running_balance NUMERIC(15, 2) NOT NULL, 
	narration TEXT, 
	cost_center_id UUID, 
	channel_id UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(account_id) REFERENCES chart_of_accounts (id) ON DELETE RESTRICT, 
	FOREIGN KEY(period_id) REFERENCES financial_periods (id) ON DELETE RESTRICT, 
	FOREIGN KEY(journal_entry_id) REFERENCES journal_entries (id) ON DELETE CASCADE, 
	FOREIGN KEY(journal_line_id) REFERENCES journal_entry_lines (id) ON DELETE CASCADE, 
	FOREIGN KEY(cost_center_id) REFERENCES cost_centers (id) ON DELETE SET NULL, 
	FOREIGN KEY(channel_id) REFERENCES sales_channels (id) ON DELETE SET NULL
)

;

-- Table: grn_items

CREATE TABLE IF NOT EXISTS grn_items (
	id UUID NOT NULL, 
	grn_id UUID NOT NULL, 
	po_item_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	product_name VARCHAR(255) NOT NULL, 
	sku VARCHAR(50) NOT NULL, 
	part_code VARCHAR(20), 
	hsn_code VARCHAR(10), 
	quantity_expected INTEGER NOT NULL, 
	quantity_received INTEGER NOT NULL, 
	quantity_accepted INTEGER NOT NULL, 
	quantity_rejected INTEGER NOT NULL, 
	uom VARCHAR(20) NOT NULL, 
	unit_price NUMERIC(12, 2) NOT NULL, 
	accepted_value NUMERIC(12, 2) NOT NULL, 
	batch_number VARCHAR(50), 
	manufacturing_date DATE, 
	expiry_date DATE, 
	serial_numbers JSON, 
	bin_id UUID, 
	bin_location VARCHAR(50), 
	qc_result qualitycheckresult, 
	rejection_reason TEXT, 
	remarks TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(grn_id) REFERENCES goods_receipt_notes (id) ON DELETE CASCADE, 
	FOREIGN KEY(po_item_id) REFERENCES purchase_order_items (id) ON DELETE RESTRICT, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id) ON DELETE SET NULL, 
	FOREIGN KEY(bin_id) REFERENCES warehouse_bins (id) ON DELETE SET NULL
)

;

-- Table: installations

CREATE TABLE IF NOT EXISTS installations (
	id UUID NOT NULL, 
	installation_number VARCHAR(50) NOT NULL, 
	status installationstatus, 
	customer_id UUID NOT NULL, 
	order_id UUID, 
	order_item_id UUID, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	serial_number VARCHAR(100), 
	stock_item_id UUID, 
	address_id UUID, 
	installation_address JSON, 
	installation_pincode VARCHAR(10), 
	installation_city VARCHAR(100), 
	latitude FLOAT, 
	longitude FLOAT, 
	preferred_date DATE, 
	preferred_time_slot VARCHAR(50), 
	scheduled_date DATE, 
	scheduled_time_slot VARCHAR(50), 
	technician_id UUID, 
	franchisee_id UUID, 
	assigned_at TIMESTAMP WITHOUT TIME ZONE, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	installation_date DATE, 
	installation_notes TEXT, 
	pre_installation_checklist JSON, 
	post_installation_checklist JSON, 
	installation_photos JSON, 
	accessories_used JSON, 
	input_tds INTEGER, 
	output_tds INTEGER, 
	warranty_start_date DATE, 
	warranty_end_date DATE, 
	warranty_months INTEGER, 
	extended_warranty_months INTEGER, 
	warranty_card_number VARCHAR(50), 
	warranty_card_url VARCHAR(500), 
	customer_signature_url VARCHAR(500), 
	customer_feedback TEXT, 
	customer_rating INTEGER, 
	demo_given BOOLEAN, 
	demo_notes TEXT, 
	region_id UUID, 
	notes TEXT, 
	internal_notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	created_by UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id), 
	FOREIGN KEY(stock_item_id) REFERENCES stock_items (id), 
	FOREIGN KEY(address_id) REFERENCES customer_addresses (id), 
	FOREIGN KEY(technician_id) REFERENCES technicians (id), 
	FOREIGN KEY(franchisee_id) REFERENCES franchisees (id), 
	UNIQUE (warranty_card_number), 
	FOREIGN KEY(region_id) REFERENCES regions (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)

;

-- Table: invoice_items

CREATE TABLE IF NOT EXISTS invoice_items (
	id UUID NOT NULL, 
	invoice_id UUID NOT NULL, 
	product_id UUID, 
	variant_id UUID, 
	sku VARCHAR(50) NOT NULL, 
	item_name VARCHAR(300) NOT NULL, 
	item_description VARCHAR(500), 
	hsn_code VARCHAR(8) NOT NULL, 
	is_service BOOLEAN NOT NULL, 
	serial_numbers JSON, 
	quantity NUMERIC(10, 3) NOT NULL, 
	uom VARCHAR(10) NOT NULL, 
	unit_price NUMERIC(12, 2) NOT NULL, 
	mrp NUMERIC(12, 2), 
	discount_percentage NUMERIC(5, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	taxable_value NUMERIC(12, 2) NOT NULL, 
	gst_rate NUMERIC(5, 2) NOT NULL, 
	cgst_rate NUMERIC(5, 2) NOT NULL, 
	sgst_rate NUMERIC(5, 2) NOT NULL, 
	igst_rate NUMERIC(5, 2) NOT NULL, 
	cess_rate NUMERIC(5, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	cess_amount NUMERIC(12, 2) NOT NULL, 
	total_tax NUMERIC(12, 2) NOT NULL, 
	line_total NUMERIC(14, 2) NOT NULL, 
	warranty_months INTEGER, 
	warranty_end_date DATE, 
	order_item_id UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES tax_invoices (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE SET NULL, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id) ON DELETE SET NULL
)

;

-- Table: manifest_items

CREATE TABLE IF NOT EXISTS manifest_items (
	id UUID NOT NULL, 
	manifest_id UUID NOT NULL, 
	shipment_id UUID NOT NULL, 
	awb_number VARCHAR(100) NOT NULL, 
	tracking_number VARCHAR(100), 
	order_number VARCHAR(50) NOT NULL, 
	weight_kg FLOAT NOT NULL, 
	no_of_boxes INTEGER NOT NULL, 
	is_scanned BOOLEAN NOT NULL, 
	scanned_at TIMESTAMP WITHOUT TIME ZONE, 
	scanned_by UUID, 
	is_handed_over BOOLEAN NOT NULL, 
	handed_over_at TIMESTAMP WITHOUT TIME ZONE, 
	destination_pincode VARCHAR(10), 
	destination_city VARCHAR(100), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(manifest_id) REFERENCES manifests (id) ON DELETE CASCADE, 
	FOREIGN KEY(shipment_id) REFERENCES shipments (id) ON DELETE RESTRICT, 
	FOREIGN KEY(scanned_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: payment_receipts

CREATE TABLE IF NOT EXISTS payment_receipts (
	id UUID NOT NULL, 
	receipt_number VARCHAR(50) NOT NULL, 
	invoice_id UUID NOT NULL, 
	customer_id UUID, 
	payment_date DATE NOT NULL, 
	payment_mode paymentmode NOT NULL, 
	amount NUMERIC(14, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	bank_name VARCHAR(200), 
	bank_branch VARCHAR(200), 
	cheque_number VARCHAR(20), 
	cheque_date DATE, 
	transaction_reference VARCHAR(100), 
	tds_applicable BOOLEAN NOT NULL, 
	tds_rate NUMERIC(5, 2), 
	tds_amount NUMERIC(12, 2), 
	tds_section VARCHAR(20), 
	net_amount NUMERIC(14, 2) NOT NULL, 
	is_confirmed BOOLEAN NOT NULL, 
	confirmed_at TIMESTAMP WITHOUT TIME ZONE, 
	is_bounced BOOLEAN NOT NULL, 
	bounced_at TIMESTAMP WITHOUT TIME ZONE, 
	bounce_reason VARCHAR(500), 
	remarks VARCHAR(500), 
	created_by UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES tax_invoices (id) ON DELETE CASCADE, 
	FOREIGN KEY(customer_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: picklist_items

CREATE TABLE IF NOT EXISTS picklist_items (
	id UUID NOT NULL, 
	picklist_id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	order_item_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	sku VARCHAR(50) NOT NULL, 
	product_name VARCHAR(255) NOT NULL, 
	variant_name VARCHAR(255), 
	bin_id UUID, 
	bin_location VARCHAR(100), 
	quantity_required INTEGER NOT NULL, 
	quantity_picked INTEGER NOT NULL, 
	quantity_short INTEGER NOT NULL, 
	is_picked BOOLEAN NOT NULL, 
	is_short BOOLEAN NOT NULL, 
	picked_serials TEXT, 
	pick_sequence INTEGER NOT NULL, 
	picked_by UUID, 
	picked_at TIMESTAMP WITHOUT TIME ZONE, 
	notes TEXT, 
	short_reason TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(picklist_id) REFERENCES picklists (id) ON DELETE CASCADE, 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
	FOREIGN KEY(order_item_id) REFERENCES order_items (id) ON DELETE RESTRICT, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id) ON DELETE SET NULL, 
	FOREIGN KEY(bin_id) REFERENCES warehouse_bins (id) ON DELETE SET NULL, 
	FOREIGN KEY(picked_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: po_delivery_schedules

CREATE TABLE IF NOT EXISTS po_delivery_schedules (
	id UUID NOT NULL, 
	purchase_order_id UUID NOT NULL, 
	lot_number INTEGER NOT NULL, 
	lot_name VARCHAR(50) NOT NULL, 
	month_code VARCHAR(7), 
	expected_delivery_date DATE NOT NULL, 
	delivery_window_start DATE, 
	delivery_window_end DATE, 
	actual_delivery_date DATE, 
	total_quantity INTEGER NOT NULL, 
	quantity_received INTEGER NOT NULL, 
	lot_value NUMERIC(14, 2) NOT NULL, 
	lot_tax NUMERIC(12, 2) NOT NULL, 
	lot_total NUMERIC(14, 2) NOT NULL, 
	advance_percentage NUMERIC(5, 2) NOT NULL, 
	advance_amount NUMERIC(12, 2) NOT NULL, 
	balance_amount NUMERIC(12, 2) NOT NULL, 
	balance_due_days INTEGER NOT NULL, 
	advance_paid NUMERIC(12, 2) NOT NULL, 
	advance_paid_date DATE, 
	advance_payment_ref VARCHAR(100), 
	balance_paid NUMERIC(12, 2) NOT NULL, 
	balance_paid_date DATE, 
	balance_payment_ref VARCHAR(100), 
	balance_due_date DATE, 
	status deliverylotstatus NOT NULL, 
	grn_id UUID, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(purchase_order_id) REFERENCES purchase_orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(grn_id) REFERENCES goods_receipt_notes (id) ON DELETE SET NULL
)

;

-- Table: po_serials

CREATE TABLE IF NOT EXISTS po_serials (
	id VARCHAR(36) NOT NULL, 
	po_id VARCHAR(36) NOT NULL, 
	po_item_id VARCHAR(36), 
	product_id VARCHAR(36), 
	product_sku VARCHAR(50), 
	model_code VARCHAR(10) NOT NULL, 
	item_type itemtype, 
	brand_prefix VARCHAR(2), 
	supplier_code VARCHAR(2) NOT NULL, 
	year_code VARCHAR(2) NOT NULL, 
	month_code VARCHAR(1) NOT NULL, 
	serial_number INTEGER NOT NULL, 
	barcode VARCHAR(20) NOT NULL, 
	status serialstatus, 
	grn_id VARCHAR(36), 
	grn_item_id VARCHAR(36), 
	received_at TIMESTAMP WITHOUT TIME ZONE, 
	received_by VARCHAR(36), 
	stock_item_id VARCHAR(36), 
	assigned_at TIMESTAMP WITHOUT TIME ZONE, 
	order_id VARCHAR(36), 
	order_item_id VARCHAR(36), 
	sold_at TIMESTAMP WITHOUT TIME ZONE, 
	customer_id VARCHAR(36), 
	warranty_start_date TIMESTAMP WITHOUT TIME ZONE, 
	warranty_end_date TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(po_id) REFERENCES purchase_orders (id), 
	FOREIGN KEY(po_item_id) REFERENCES purchase_order_items (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(grn_id) REFERENCES goods_receipt_notes (id), 
	FOREIGN KEY(stock_item_id) REFERENCES stock_items (id)
)

;

-- Table: shipment_tracking

CREATE TABLE IF NOT EXISTS shipment_tracking (
	id UUID NOT NULL, 
	shipment_id UUID NOT NULL, 
	status shipmentstatus NOT NULL, 
	status_code VARCHAR(50), 
	location VARCHAR(255), 
	city VARCHAR(100), 
	state VARCHAR(100), 
	pincode VARCHAR(10), 
	remarks TEXT, 
	transporter_remarks TEXT, 
	event_time TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	source VARCHAR(50), 
	updated_by UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(shipment_id) REFERENCES shipments (id) ON DELETE CASCADE, 
	FOREIGN KEY(updated_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: stock_adjustment_items

CREATE TABLE IF NOT EXISTS stock_adjustment_items (
	id UUID NOT NULL, 
	adjustment_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	stock_item_id UUID, 
	system_quantity INTEGER, 
	physical_quantity INTEGER, 
	adjustment_quantity INTEGER, 
	unit_cost FLOAT, 
	value_impact FLOAT, 
	serial_number VARCHAR(100), 
	reason TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(adjustment_id) REFERENCES stock_adjustments (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id), 
	FOREIGN KEY(stock_item_id) REFERENCES stock_items (id)
)

;

-- Table: stock_movements

CREATE TABLE IF NOT EXISTS stock_movements (
	id UUID NOT NULL, 
	movement_number VARCHAR(50) NOT NULL, 
	movement_type stockmovementtype NOT NULL, 
	movement_date TIMESTAMP WITHOUT TIME ZONE, 
	warehouse_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	variant_id UUID, 
	stock_item_id UUID, 
	quantity INTEGER NOT NULL, 
	balance_before INTEGER, 
	balance_after INTEGER, 
	reference_type VARCHAR(50), 
	reference_id UUID, 
	reference_number VARCHAR(100), 
	unit_cost FLOAT, 
	total_cost FLOAT, 
	created_by UUID, 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id), 
	FOREIGN KEY(stock_item_id) REFERENCES stock_items (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)

;

-- Table: stock_transfer_serials

CREATE TABLE IF NOT EXISTS stock_transfer_serials (
	id UUID NOT NULL, 
	transfer_item_id UUID NOT NULL, 
	stock_item_id UUID NOT NULL, 
	is_dispatched INTEGER, 
	is_received INTEGER, 
	is_damaged INTEGER, 
	received_at TIMESTAMP WITHOUT TIME ZONE, 
	damage_notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(transfer_item_id) REFERENCES stock_transfer_items (id), 
	FOREIGN KEY(stock_item_id) REFERENCES stock_items (id)
)

;

-- Table: vendor_invoices

CREATE TABLE IF NOT EXISTS vendor_invoices (
	id UUID NOT NULL, 
	invoice_number VARCHAR(50) NOT NULL, 
	invoice_date DATE NOT NULL, 
	our_reference VARCHAR(30) NOT NULL, 
	status vendorinvoicestatus NOT NULL, 
	vendor_id UUID NOT NULL, 
	purchase_order_id UUID, 
	grn_id UUID, 
	subtotal NUMERIC(14, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	taxable_amount NUMERIC(14, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	cess_amount NUMERIC(12, 2) NOT NULL, 
	total_tax NUMERIC(12, 2) NOT NULL, 
	freight_charges NUMERIC(12, 2) NOT NULL, 
	other_charges NUMERIC(12, 2) NOT NULL, 
	round_off NUMERIC(8, 2) NOT NULL, 
	grand_total NUMERIC(14, 2) NOT NULL, 
	due_date DATE NOT NULL, 
	amount_paid NUMERIC(14, 2) NOT NULL, 
	balance_due NUMERIC(14, 2) NOT NULL, 
	tds_applicable BOOLEAN NOT NULL, 
	tds_section VARCHAR(10), 
	tds_rate NUMERIC(5, 2) NOT NULL, 
	tds_amount NUMERIC(12, 2) NOT NULL, 
	net_payable NUMERIC(14, 2) NOT NULL, 
	po_matched BOOLEAN NOT NULL, 
	grn_matched BOOLEAN NOT NULL, 
	is_fully_matched BOOLEAN NOT NULL, 
	matching_variance NUMERIC(12, 2) NOT NULL, 
	variance_reason TEXT, 
	vendor_irn VARCHAR(64), 
	vendor_ack_number VARCHAR(20), 
	invoice_pdf_url VARCHAR(500), 
	received_by UUID NOT NULL, 
	received_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	verified_by UUID, 
	verified_at TIMESTAMP WITHOUT TIME ZONE, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	internal_notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_vendor_invoice UNIQUE (vendor_id, invoice_number), 
	FOREIGN KEY(vendor_id) REFERENCES vendors (id) ON DELETE RESTRICT, 
	FOREIGN KEY(purchase_order_id) REFERENCES purchase_orders (id) ON DELETE SET NULL, 
	FOREIGN KEY(grn_id) REFERENCES goods_receipt_notes (id) ON DELETE SET NULL, 
	FOREIGN KEY(received_by) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(verified_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: vendor_proforma_items

CREATE TABLE IF NOT EXISTS vendor_proforma_items (
	id UUID NOT NULL, 
	proforma_id UUID NOT NULL, 
	product_id UUID, 
	part_code VARCHAR(20), 
	description VARCHAR(500) NOT NULL, 
	hsn_code VARCHAR(10), 
	uom VARCHAR(20) NOT NULL, 
	quantity NUMERIC(10, 2) NOT NULL, 
	unit_price NUMERIC(12, 2) NOT NULL, 
	discount_percent NUMERIC(5, 2) NOT NULL, 
	discount_amount NUMERIC(12, 2) NOT NULL, 
	taxable_amount NUMERIC(12, 2) NOT NULL, 
	gst_rate NUMERIC(5, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	total_amount NUMERIC(12, 2) NOT NULL, 
	lead_time_days INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(proforma_id) REFERENCES vendor_proforma_invoices (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE SET NULL
)

;

-- Table: amc_contracts

CREATE TABLE IF NOT EXISTS amc_contracts (
	id UUID NOT NULL, 
	contract_number VARCHAR(50) NOT NULL, 
	amc_type amctype, 
	status amcstatus, 
	customer_id UUID NOT NULL, 
	customer_address_id UUID, 
	product_id UUID NOT NULL, 
	installation_id UUID, 
	serial_number VARCHAR(100) NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	duration_months INTEGER, 
	total_services INTEGER, 
	services_used INTEGER, 
	services_remaining INTEGER, 
	base_price FLOAT, 
	tax_amount FLOAT, 
	discount_amount FLOAT, 
	total_amount FLOAT, 
	payment_status VARCHAR(50), 
	payment_mode VARCHAR(50), 
	payment_reference VARCHAR(100), 
	paid_at TIMESTAMP WITHOUT TIME ZONE, 
	parts_covered BOOLEAN, 
	labor_covered BOOLEAN, 
	emergency_support BOOLEAN, 
	priority_service BOOLEAN, 
	discount_on_parts FLOAT, 
	terms_and_conditions TEXT, 
	is_renewable BOOLEAN, 
	renewal_reminder_sent BOOLEAN, 
	renewed_from_id UUID, 
	renewed_to_id UUID, 
	service_schedule JSON, 
	next_service_due DATE, 
	notes TEXT, 
	internal_notes TEXT, 
	created_by UUID, 
	approved_by UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(customer_address_id) REFERENCES customer_addresses (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(installation_id) REFERENCES installations (id), 
	FOREIGN KEY(renewed_from_id) REFERENCES amc_contracts (id), 
	FOREIGN KEY(renewed_to_id) REFERENCES amc_contracts (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id)
)

;

-- Table: credit_debit_note_items

CREATE TABLE IF NOT EXISTS credit_debit_note_items (
	id UUID NOT NULL, 
	note_id UUID NOT NULL, 
	product_id UUID, 
	sku VARCHAR(50) NOT NULL, 
	item_name VARCHAR(300) NOT NULL, 
	hsn_code VARCHAR(8) NOT NULL, 
	quantity NUMERIC(10, 3) NOT NULL, 
	uom VARCHAR(10) NOT NULL, 
	unit_price NUMERIC(12, 2) NOT NULL, 
	taxable_value NUMERIC(12, 2) NOT NULL, 
	gst_rate NUMERIC(5, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	total_tax NUMERIC(12, 2) NOT NULL, 
	line_total NUMERIC(14, 2) NOT NULL, 
	original_invoice_item_id UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(note_id) REFERENCES credit_debit_notes (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE SET NULL
)

;

-- Table: eway_bill_items

CREATE TABLE IF NOT EXISTS eway_bill_items (
	id UUID NOT NULL, 
	eway_bill_id UUID NOT NULL, 
	product_name VARCHAR(300) NOT NULL, 
	part_code VARCHAR(20), 
	hsn_code VARCHAR(8) NOT NULL, 
	quantity NUMERIC(10, 3) NOT NULL, 
	uom VARCHAR(10) NOT NULL, 
	taxable_value NUMERIC(12, 2) NOT NULL, 
	gst_rate NUMERIC(5, 2) NOT NULL, 
	cgst_amount NUMERIC(12, 2) NOT NULL, 
	sgst_amount NUMERIC(12, 2) NOT NULL, 
	igst_amount NUMERIC(12, 2) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(eway_bill_id) REFERENCES eway_bills (id) ON DELETE CASCADE
)

;

-- Table: service_requests

CREATE TABLE IF NOT EXISTS service_requests (
	id UUID NOT NULL, 
	ticket_number VARCHAR(50) NOT NULL, 
	service_type servicetype NOT NULL, 
	source servicesource, 
	priority servicepriority, 
	status servicestatus, 
	customer_id UUID NOT NULL, 
	customer_address_id UUID, 
	order_id UUID, 
	order_item_id UUID, 
	product_id UUID, 
	serial_number VARCHAR(100), 
	installation_id UUID, 
	amc_id UUID, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	symptoms JSON, 
	customer_reported_issue TEXT, 
	service_address JSON, 
	service_pincode VARCHAR(10), 
	service_city VARCHAR(100), 
	service_state VARCHAR(100), 
	latitude FLOAT, 
	longitude FLOAT, 
	technician_id UUID, 
	franchisee_id UUID, 
	assigned_at TIMESTAMP WITHOUT TIME ZONE, 
	assigned_by UUID, 
	preferred_date DATE, 
	preferred_time_slot VARCHAR(50), 
	scheduled_date DATE, 
	scheduled_time_slot VARCHAR(50), 
	region_id UUID, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	sla_breach_at TIMESTAMP WITHOUT TIME ZONE, 
	is_sla_breached BOOLEAN, 
	resolution_type VARCHAR(50), 
	resolution_notes TEXT, 
	root_cause TEXT, 
	action_taken TEXT, 
	parts_used JSON, 
	total_parts_cost FLOAT, 
	labor_charges FLOAT, 
	service_charges FLOAT, 
	travel_charges FLOAT, 
	total_charges FLOAT, 
	is_chargeable BOOLEAN, 
	payment_status VARCHAR(50), 
	payment_collected FLOAT, 
	payment_mode VARCHAR(50), 
	customer_rating INTEGER, 
	customer_feedback TEXT, 
	feedback_date TIMESTAMP WITHOUT TIME ZONE, 
	images_before JSON, 
	images_after JSON, 
	customer_signature_url VARCHAR(500), 
	internal_notes TEXT, 
	escalation_level INTEGER, 
	escalated_to UUID, 
	escalation_reason TEXT, 
	created_by UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(customer_address_id) REFERENCES customer_addresses (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(installation_id) REFERENCES installations (id), 
	FOREIGN KEY(amc_id) REFERENCES amc_contracts (id), 
	FOREIGN KEY(technician_id) REFERENCES technicians (id), 
	FOREIGN KEY(franchisee_id) REFERENCES franchisees (id), 
	FOREIGN KEY(assigned_by) REFERENCES users (id), 
	FOREIGN KEY(region_id) REFERENCES regions (id), 
	FOREIGN KEY(escalated_to) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)

;

-- Table: calls

CREATE TABLE IF NOT EXISTS calls (
	id UUID NOT NULL, 
	call_id VARCHAR(30) NOT NULL, 
	call_type calltype NOT NULL, 
	category callcategory NOT NULL, 
	sub_category VARCHAR(50), 
	customer_id UUID, 
	customer_name VARCHAR(200), 
	customer_phone VARCHAR(20) NOT NULL, 
	customer_email VARCHAR(255), 
	customer_address TEXT, 
	agent_id UUID NOT NULL, 
	call_start_time TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	call_end_time TIMESTAMP WITHOUT TIME ZONE, 
	duration_seconds INTEGER, 
	hold_time_seconds INTEGER NOT NULL, 
	talk_time_seconds INTEGER, 
	status callstatus NOT NULL, 
	outcome calloutcome, 
	disposition_id UUID, 
	priority callpriority NOT NULL, 
	sentiment customersentiment, 
	urgency_level INTEGER NOT NULL, 
	call_reason TEXT, 
	call_notes TEXT, 
	resolution_notes TEXT, 
	internal_notes TEXT, 
	linked_ticket_id UUID, 
	linked_lead_id UUID, 
	linked_order_id UUID, 
	product_id UUID, 
	serial_number VARCHAR(100), 
	transferred_from_id UUID, 
	transferred_to_id UUID, 
	transfer_reason VARCHAR(200), 
	recording_url VARCHAR(500), 
	recording_duration INTEGER, 
	is_first_contact BOOLEAN NOT NULL, 
	is_resolved_first_call BOOLEAN NOT NULL, 
	follow_up_required BOOLEAN NOT NULL, 
	campaign_id UUID, 
	consent_confirmed BOOLEAN NOT NULL, 
	disclosure_read BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE SET NULL, 
	FOREIGN KEY(agent_id) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(disposition_id) REFERENCES call_dispositions (id) ON DELETE SET NULL, 
	FOREIGN KEY(linked_ticket_id) REFERENCES service_requests (id) ON DELETE SET NULL, 
	FOREIGN KEY(linked_order_id) REFERENCES orders (id) ON DELETE SET NULL, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE SET NULL, 
	FOREIGN KEY(transferred_from_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(transferred_to_id) REFERENCES users (id) ON DELETE SET NULL
)

;

-- Table: parts_requests

CREATE TABLE IF NOT EXISTS parts_requests (
	id UUID NOT NULL, 
	request_number VARCHAR(50) NOT NULL, 
	service_request_id UUID NOT NULL, 
	status VARCHAR(50), 
	items JSON, 
	from_warehouse_id UUID, 
	requested_by UUID, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	dispatched_at TIMESTAMP WITHOUT TIME ZONE, 
	delivered_at TIMESTAMP WITHOUT TIME ZONE, 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(service_request_id) REFERENCES service_requests (id), 
	FOREIGN KEY(from_warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(requested_by) REFERENCES users (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id)
)

;

-- Table: service_status_history

CREATE TABLE IF NOT EXISTS service_status_history (
	id UUID NOT NULL, 
	service_request_id UUID NOT NULL, 
	from_status servicestatus, 
	to_status servicestatus NOT NULL, 
	changed_by UUID, 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(service_request_id) REFERENCES service_requests (id), 
	FOREIGN KEY(changed_by) REFERENCES users (id)
)

;

-- Table: technician_job_history

CREATE TABLE IF NOT EXISTS technician_job_history (
	id UUID NOT NULL, 
	technician_id UUID NOT NULL, 
	service_request_id UUID NOT NULL, 
	assigned_at TIMESTAMP WITHOUT TIME ZONE, 
	assigned_by UUID, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	time_taken_minutes INTEGER, 
	status VARCHAR(50), 
	reassignment_reason TEXT, 
	customer_rating INTEGER, 
	customer_feedback TEXT, 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(technician_id) REFERENCES technicians (id), 
	FOREIGN KEY(service_request_id) REFERENCES service_requests (id), 
	FOREIGN KEY(assigned_by) REFERENCES users (id)
)

;

-- Table: warranty_claims

CREATE TABLE IF NOT EXISTS warranty_claims (
	id UUID NOT NULL, 
	claim_number VARCHAR(50) NOT NULL, 
	installation_id UUID NOT NULL, 
	service_request_id UUID, 
	customer_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	serial_number VARCHAR(100) NOT NULL, 
	claim_type VARCHAR(50), 
	issue_description TEXT NOT NULL, 
	diagnosis TEXT, 
	status VARCHAR(50), 
	is_valid_claim BOOLEAN, 
	rejection_reason TEXT, 
	approved_by UUID, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	resolution_type VARCHAR(50), 
	resolution_notes TEXT, 
	replacement_serial VARCHAR(100), 
	refund_amount FLOAT, 
	parts_cost FLOAT, 
	labor_cost FLOAT, 
	total_cost FLOAT, 
	claim_date DATE, 
	resolved_date DATE, 
	notes TEXT, 
	created_by UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(installation_id) REFERENCES installations (id), 
	FOREIGN KEY(service_request_id) REFERENCES service_requests (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)

;

-- Table: call_qa_reviews

CREATE TABLE IF NOT EXISTS call_qa_reviews (
	id UUID NOT NULL, 
	call_id UUID NOT NULL, 
	reviewer_id UUID NOT NULL, 
	greeting_score INTEGER NOT NULL, 
	communication_score INTEGER NOT NULL, 
	product_knowledge_score INTEGER NOT NULL, 
	problem_solving_score INTEGER NOT NULL, 
	empathy_score INTEGER NOT NULL, 
	compliance_score INTEGER NOT NULL, 
	closing_score INTEGER NOT NULL, 
	overall_score NUMERIC(4, 2) NOT NULL, 
	total_points INTEGER NOT NULL, 
	max_points INTEGER NOT NULL, 
	strengths TEXT, 
	areas_for_improvement TEXT, 
	reviewer_comments TEXT, 
	status qastatus NOT NULL, 
	acknowledged_by_agent BOOLEAN NOT NULL, 
	acknowledged_at TIMESTAMP WITHOUT TIME ZONE, 
	agent_comments TEXT, 
	is_disputed BOOLEAN NOT NULL, 
	dispute_reason TEXT, 
	dispute_resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	dispute_resolution TEXT, 
	reviewed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(call_id) REFERENCES calls (id) ON DELETE CASCADE, 
	FOREIGN KEY(reviewer_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

-- Table: callback_schedules

CREATE TABLE IF NOT EXISTS callback_schedules (
	id UUID NOT NULL, 
	call_id UUID, 
	customer_id UUID, 
	customer_name VARCHAR(200) NOT NULL, 
	customer_phone VARCHAR(20) NOT NULL, 
	assigned_agent_id UUID NOT NULL, 
	created_by_id UUID NOT NULL, 
	scheduled_date DATE NOT NULL, 
	scheduled_time TIME WITHOUT TIME ZONE, 
	scheduled_datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	time_window_start TIME WITHOUT TIME ZONE, 
	time_window_end TIME WITHOUT TIME ZONE, 
	reason VARCHAR(500) NOT NULL, 
	category callcategory NOT NULL, 
	priority callpriority NOT NULL, 
	notes TEXT, 
	status callbackstatus NOT NULL, 
	completed_call_id UUID, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	completion_notes TEXT, 
	attempt_count INTEGER NOT NULL, 
	max_attempts INTEGER NOT NULL, 
	last_attempt_at TIMESTAMP WITHOUT TIME ZONE, 
	rescheduled_from_id UUID, 
	reschedule_count INTEGER NOT NULL, 
	reminder_sent BOOLEAN NOT NULL, 
	reminder_sent_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(call_id) REFERENCES calls (id) ON DELETE SET NULL, 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE SET NULL, 
	FOREIGN KEY(assigned_agent_id) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(rescheduled_from_id) REFERENCES callback_schedules (id) ON DELETE SET NULL
)

;

-- Table: leads

CREATE TABLE IF NOT EXISTS leads (
	id UUID NOT NULL, 
	lead_number VARCHAR(30) NOT NULL, 
	lead_type leadtype NOT NULL, 
	source leadsource NOT NULL, 
	source_details VARCHAR(200), 
	campaign_id UUID, 
	referral_code VARCHAR(50), 
	first_name VARCHAR(100) NOT NULL, 
	last_name VARCHAR(100), 
	email VARCHAR(255), 
	phone VARCHAR(20) NOT NULL, 
	alternate_phone VARCHAR(20), 
	whatsapp_number VARCHAR(20), 
	company_name VARCHAR(200), 
	designation VARCHAR(100), 
	industry VARCHAR(100), 
	employee_count VARCHAR(50), 
	gst_number VARCHAR(20), 
	address_line1 VARCHAR(255), 
	address_line2 VARCHAR(255), 
	city VARCHAR(100), 
	state VARCHAR(100), 
	pincode VARCHAR(10), 
	country VARCHAR(50) NOT NULL, 
	interest leadinterest NOT NULL, 
	interested_products JSON, 
	interested_category_id UUID, 
	budget_min NUMERIC(12, 2), 
	budget_max NUMERIC(12, 2), 
	quantity_required INTEGER NOT NULL, 
	expected_purchase_date DATE, 
	status leadstatus NOT NULL, 
	priority leadpriority NOT NULL, 
	score INTEGER NOT NULL, 
	score_breakdown JSON, 
	is_qualified BOOLEAN NOT NULL, 
	qualification_date TIMESTAMP WITHOUT TIME ZONE, 
	qualified_by_id UUID, 
	assigned_to_id UUID, 
	assigned_at TIMESTAMP WITHOUT TIME ZONE, 
	assigned_by_id UUID, 
	team_id UUID, 
	region_id UUID, 
	next_follow_up_date TIMESTAMP WITHOUT TIME ZONE, 
	next_follow_up_notes TEXT, 
	last_contacted_at TIMESTAMP WITHOUT TIME ZONE, 
	contact_attempts INTEGER NOT NULL, 
	converted_at TIMESTAMP WITHOUT TIME ZONE, 
	converted_by_id UUID, 
	converted_customer_id UUID, 
	converted_order_id UUID, 
	lost_reason lostreason, 
	lost_reason_details TEXT, 
	lost_to_competitor VARCHAR(100), 
	lost_at TIMESTAMP WITHOUT TIME ZONE, 
	description TEXT, 
	internal_notes TEXT, 
	special_requirements TEXT, 
	tags JSON, 
	source_call_id UUID, 
	dealer_id UUID, 
	estimated_value NUMERIC(12, 2), 
	actual_value NUMERIC(12, 2), 
	created_by_id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(interested_category_id) REFERENCES categories (id) ON DELETE SET NULL, 
	FOREIGN KEY(qualified_by_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(assigned_to_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(assigned_by_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(region_id) REFERENCES regions (id) ON DELETE SET NULL, 
	FOREIGN KEY(converted_by_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(converted_customer_id) REFERENCES customers (id) ON DELETE SET NULL, 
	FOREIGN KEY(converted_order_id) REFERENCES orders (id) ON DELETE SET NULL, 
	FOREIGN KEY(source_call_id) REFERENCES calls (id) ON DELETE SET NULL, 
	FOREIGN KEY(dealer_id) REFERENCES dealers (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

-- Table: lead_activities

CREATE TABLE IF NOT EXISTS lead_activities (
	id UUID NOT NULL, 
	lead_id UUID NOT NULL, 
	activity_type activitytype NOT NULL, 
	subject VARCHAR(200) NOT NULL, 
	description TEXT, 
	outcome VARCHAR(100), 
	activity_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	duration_minutes INTEGER, 
	old_status leadstatus, 
	new_status leadstatus, 
	old_assignee_id UUID, 
	new_assignee_id UUID, 
	call_id UUID, 
	follow_up_date TIMESTAMP WITHOUT TIME ZONE, 
	follow_up_notes TEXT, 
	created_by_id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(lead_id) REFERENCES leads (id) ON DELETE CASCADE, 
	FOREIGN KEY(call_id) REFERENCES calls (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

