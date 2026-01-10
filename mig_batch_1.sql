-- Migration Batch 1

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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	UNIQUE (code)
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
	UNIQUE (code)
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
	CONSTRAINT uq_channel_commission_category UNIQUE (plan_id, category_id)
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
	CONSTRAINT uq_plan_category_rate UNIQUE (plan_id, category_id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	UNIQUE (code)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	CONSTRAINT uq_transporter_serviceability UNIQUE (transporter_id, origin_pincode, destination_pincode)
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
	UNIQUE (employee_code)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
)

;

