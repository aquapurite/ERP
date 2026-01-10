-- Clean Migration Batch 5
-- Tables without foreign keys

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
	PRIMARY KEY (id)
	UNIQUE (irn)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
	UNIQUE (warranty_card_number)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	CONSTRAINT uq_vendor_invoice UNIQUE (vendor_id, invoice_number)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
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
	PRIMARY KEY (id)
)

;

