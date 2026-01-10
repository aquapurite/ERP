-- Migration Batch 2

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
	CONSTRAINT uq_plan_product_rate UNIQUE (plan_id, product_id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	UNIQUE (period_name)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	UNIQUE (product_id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id)
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
	PRIMARY KEY (id)
)

;


-- Table: user_roles

CREATE TABLE IF NOT EXISTS user_roles (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	role_id UUID NOT NULL, 
	assigned_by UUID, 
	assigned_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	CONSTRAINT uq_company_branch_code UNIQUE (company_id, code)
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
	CONSTRAINT uq_tier_product_pricing UNIQUE (tier, product_id, variant_id)
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
	UNIQUE (user_id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
)

;

