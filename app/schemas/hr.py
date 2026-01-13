"""Pydantic schemas for HR & Payroll module."""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, EmailStr

from app.models.hr import (
    EmploymentType, EmployeeStatus, LeaveType, LeaveStatus,
    AttendanceStatus, PayrollStatus, Gender, MaritalStatus
)


# ==================== Department Schemas ====================

class DepartmentBase(BaseModel):
    """Base schema for Department."""
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    head_id: Optional[UUID] = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    """Schema for creating Department."""
    pass


class DepartmentUpdate(BaseModel):
    """Schema for updating Department."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    head_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Response schema for Department."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_name: Optional[str] = None
    head_name: Optional[str] = None
    employee_count: int = 0
    created_at: datetime
    updated_at: datetime


class DepartmentListResponse(BaseModel):
    """Response for listing Departments."""
    items: List[DepartmentResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 1


class DepartmentDropdown(BaseModel):
    """Dropdown item for Department selection."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str


# ==================== Employee Schemas ====================

class AddressSchema(BaseModel):
    """Schema for address fields."""
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: str = "India"


class EmployeeBase(BaseModel):
    """Base schema for Employee."""
    # Personal Info
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    blood_group: Optional[str] = Field(None, max_length=5)
    marital_status: Optional[MaritalStatus] = None
    nationality: str = "Indian"

    # Personal Contact
    personal_email: Optional[EmailStr] = None
    personal_phone: Optional[str] = Field(None, max_length=20)

    # Emergency Contact
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)

    # Address
    current_address: Optional[AddressSchema] = None
    permanent_address: Optional[AddressSchema] = None

    # Employment
    department_id: Optional[UUID] = None
    designation: Optional[str] = Field(None, max_length=100)
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    joining_date: date
    confirmation_date: Optional[date] = None
    reporting_manager_id: Optional[UUID] = None

    # Indian Documents
    pan_number: Optional[str] = Field(None, max_length=10)
    aadhaar_number: Optional[str] = Field(None, max_length=12)
    uan_number: Optional[str] = Field(None, max_length=12)
    esic_number: Optional[str] = Field(None, max_length=17)

    # Bank Details
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=20)
    bank_ifsc_code: Optional[str] = Field(None, max_length=11)


class EmployeeCreateWithUser(BaseModel):
    """Schema for creating Employee with new User account."""
    # User account details
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

    # Employee details (extends EmployeeBase)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    blood_group: Optional[str] = Field(None, max_length=5)
    marital_status: Optional[MaritalStatus] = None
    nationality: str = "Indian"

    personal_email: Optional[EmailStr] = None
    personal_phone: Optional[str] = Field(None, max_length=20)

    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)

    current_address: Optional[AddressSchema] = None
    permanent_address: Optional[AddressSchema] = None

    department_id: Optional[UUID] = None
    designation: Optional[str] = Field(None, max_length=100)
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    joining_date: date
    confirmation_date: Optional[date] = None
    reporting_manager_id: Optional[UUID] = None

    pan_number: Optional[str] = Field(None, max_length=10)
    aadhaar_number: Optional[str] = Field(None, max_length=12)
    uan_number: Optional[str] = Field(None, max_length=12)
    esic_number: Optional[str] = Field(None, max_length=17)

    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=20)
    bank_ifsc_code: Optional[str] = Field(None, max_length=11)

    # Role assignment
    role_ids: Optional[List[UUID]] = None


class EmployeeUpdate(BaseModel):
    """Schema for updating Employee."""
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    blood_group: Optional[str] = Field(None, max_length=5)
    marital_status: Optional[MaritalStatus] = None
    nationality: Optional[str] = None

    personal_email: Optional[EmailStr] = None
    personal_phone: Optional[str] = Field(None, max_length=20)

    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)

    current_address: Optional[AddressSchema] = None
    permanent_address: Optional[AddressSchema] = None

    department_id: Optional[UUID] = None
    designation: Optional[str] = Field(None, max_length=100)
    employment_type: Optional[EmploymentType] = None
    status: Optional[EmployeeStatus] = None
    confirmation_date: Optional[date] = None
    resignation_date: Optional[date] = None
    last_working_date: Optional[date] = None
    reporting_manager_id: Optional[UUID] = None

    pan_number: Optional[str] = Field(None, max_length=10)
    aadhaar_number: Optional[str] = Field(None, max_length=12)
    uan_number: Optional[str] = Field(None, max_length=12)
    esic_number: Optional[str] = Field(None, max_length=17)

    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=20)
    bank_ifsc_code: Optional[str] = Field(None, max_length=11)

    profile_photo_url: Optional[str] = None


class EmployeeResponse(BaseModel):
    """Response schema for Employee (list view)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_code: str
    user_id: UUID

    # User details
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    # Employment
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    designation: Optional[str] = None
    employment_type: EmploymentType
    status: EmployeeStatus
    joining_date: date

    # Manager
    reporting_manager_id: Optional[UUID] = None
    reporting_manager_name: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class EmployeeDetailResponse(EmployeeResponse):
    """Detailed response schema for Employee (profile view)."""
    # Personal
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    blood_group: Optional[str] = None
    marital_status: Optional[MaritalStatus] = None
    nationality: Optional[str] = None

    # Contact
    personal_email: Optional[str] = None
    personal_phone: Optional[str] = None

    # Emergency
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    # Address
    current_address: Optional[dict] = None
    permanent_address: Optional[dict] = None

    # Dates
    confirmation_date: Optional[date] = None
    resignation_date: Optional[date] = None
    last_working_date: Optional[date] = None

    # Documents
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    uan_number: Optional[str] = None
    esic_number: Optional[str] = None

    # Bank
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None

    profile_photo_url: Optional[str] = None
    documents: Optional[dict] = None


class EmployeeListResponse(BaseModel):
    """Response for listing Employees."""
    items: List[EmployeeResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 1


class EmployeeDropdown(BaseModel):
    """Dropdown item for Employee selection."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_code: str
    full_name: str
    designation: Optional[str] = None
    department_name: Optional[str] = None


# ==================== Salary Structure Schemas ====================

class SalaryStructureBase(BaseModel):
    """Base schema for Salary Structure."""
    effective_from: date

    # CTC Components
    basic_salary: Decimal = Field(..., ge=0)
    hra: Decimal = Field(Decimal("0"), ge=0)
    conveyance: Decimal = Field(Decimal("0"), ge=0)
    medical_allowance: Decimal = Field(Decimal("0"), ge=0)
    special_allowance: Decimal = Field(Decimal("0"), ge=0)
    other_allowances: Decimal = Field(Decimal("0"), ge=0)

    # Statutory
    pf_applicable: bool = True
    esic_applicable: bool = False
    pt_applicable: bool = True


class SalaryStructureCreate(SalaryStructureBase):
    """Schema for creating Salary Structure."""
    employee_id: UUID


class SalaryStructureUpdate(BaseModel):
    """Schema for updating Salary Structure."""
    effective_from: Optional[date] = None
    basic_salary: Optional[Decimal] = Field(None, ge=0)
    hra: Optional[Decimal] = Field(None, ge=0)
    conveyance: Optional[Decimal] = Field(None, ge=0)
    medical_allowance: Optional[Decimal] = Field(None, ge=0)
    special_allowance: Optional[Decimal] = Field(None, ge=0)
    other_allowances: Optional[Decimal] = Field(None, ge=0)
    pf_applicable: Optional[bool] = None
    esic_applicable: Optional[bool] = None
    pt_applicable: Optional[bool] = None


class SalaryStructureResponse(SalaryStructureBase):
    """Response schema for Salary Structure."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID

    # Computed
    gross_salary: Decimal
    employer_pf: Decimal
    employer_esic: Decimal
    monthly_ctc: Decimal
    annual_ctc: Decimal

    is_active: bool
    created_at: datetime
    updated_at: datetime


# ==================== Attendance Schemas ====================

class AttendanceBase(BaseModel):
    """Base schema for Attendance."""
    employee_id: UUID
    attendance_date: date
    status: AttendanceStatus
    remarks: Optional[str] = None


class AttendanceCheckIn(BaseModel):
    """Schema for check-in."""
    employee_id: Optional[UUID] = None  # Auto from token if not provided
    location: Optional[dict] = None  # {lat, lng, address}
    remarks: Optional[str] = None


class AttendanceCheckOut(BaseModel):
    """Schema for check-out."""
    employee_id: Optional[UUID] = None
    location: Optional[dict] = None
    remarks: Optional[str] = None


class AttendanceBulkCreate(BaseModel):
    """Schema for bulk attendance entry."""
    attendance_date: date
    records: List[dict]  # [{employee_id, status, remarks}]


class AttendanceUpdate(BaseModel):
    """Schema for updating Attendance."""
    status: Optional[AttendanceStatus] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    remarks: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    """Response schema for Attendance."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    work_hours: Optional[Decimal] = None

    is_late: bool = False
    late_minutes: int = 0
    is_early_out: bool = False
    early_out_minutes: int = 0

    location_in: Optional[dict] = None
    location_out: Optional[dict] = None

    approved_by: Optional[UUID] = None
    approved_by_name: Optional[str] = None

    # Employee info
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    department_name: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class AttendanceListResponse(BaseModel):
    """Response for listing Attendance."""
    items: List[AttendanceResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 1


class AttendanceReportResponse(BaseModel):
    """Response for attendance report/summary."""
    employee_id: UUID
    employee_code: str
    employee_name: str
    department: Optional[str] = None

    # Monthly summary
    total_days: int
    present_days: Decimal
    absent_days: Decimal
    half_days: Decimal
    leaves: Decimal
    holidays: int
    weekends: int
    late_count: int
    early_out_count: int


# ==================== Leave Schemas ====================

class LeaveBalanceResponse(BaseModel):
    """Response schema for Leave Balance."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    leave_type: LeaveType
    financial_year: str

    opening_balance: Decimal
    accrued: Decimal
    taken: Decimal
    adjusted: Decimal
    closing_balance: Decimal
    carry_forward_limit: Decimal


class LeaveBalanceSummary(BaseModel):
    """Summary of all leave balances for an employee."""
    employee_id: UUID
    financial_year: str
    balances: List[LeaveBalanceResponse]


class LeaveRequestBase(BaseModel):
    """Base schema for Leave Request."""
    leave_type: LeaveType
    from_date: date
    to_date: date
    is_half_day: bool = False
    half_day_type: Optional[str] = Field(None, pattern="^(FIRST_HALF|SECOND_HALF)$")
    reason: Optional[str] = None


class LeaveRequestCreate(LeaveRequestBase):
    """Schema for creating Leave Request."""
    employee_id: Optional[UUID] = None  # Auto from token if not provided


class LeaveRequestResponse(LeaveRequestBase):
    """Response schema for Leave Request."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    days: Decimal
    status: LeaveStatus

    applied_on: datetime
    approved_by: Optional[UUID] = None
    approved_by_name: Optional[str] = None
    approved_on: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Employee info
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    department_name: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class LeaveRequestListResponse(BaseModel):
    """Response for listing Leave Requests."""
    items: List[LeaveRequestResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 1


class LeaveApproveRequest(BaseModel):
    """Request to approve/reject leave."""
    action: str = Field(..., pattern="^(APPROVE|REJECT)$")
    rejection_reason: Optional[str] = None


# ==================== Payroll Schemas ====================

class PayrollProcessRequest(BaseModel):
    """Schema for processing payroll."""
    payroll_month: date  # First of month
    financial_year: str  # 2025-26
    employee_ids: Optional[List[UUID]] = None  # If None, process all active


class PayrollResponse(BaseModel):
    """Response schema for Payroll."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payroll_month: date
    financial_year: str
    status: PayrollStatus

    total_employees: int
    total_gross: Decimal
    total_deductions: Decimal
    total_net: Decimal

    processed_by: Optional[UUID] = None
    processed_by_name: Optional[str] = None
    processed_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime


class PayrollListResponse(BaseModel):
    """Response for listing Payrolls."""
    items: List[PayrollResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 1


class PayrollDetailResponse(PayrollResponse):
    """Detailed response with payslips."""
    payslips: List["PayslipResponse"] = []


# ==================== Payslip Schemas ====================

class PayslipResponse(BaseModel):
    """Response schema for Payslip."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payroll_id: UUID
    employee_id: UUID
    payslip_number: str

    # Employee info
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    department_name: Optional[str] = None
    designation: Optional[str] = None

    # Attendance
    working_days: int
    days_present: Decimal
    days_absent: Decimal
    leaves_taken: Decimal

    # Earnings
    basic_earned: Decimal
    hra_earned: Decimal
    conveyance_earned: Decimal
    medical_earned: Decimal
    special_earned: Decimal
    other_earned: Decimal
    overtime_amount: Decimal
    arrears: Decimal
    bonus: Decimal
    gross_earnings: Decimal

    # Deductions - Statutory
    employee_pf: Decimal
    employer_pf: Decimal
    employee_esic: Decimal
    employer_esic: Decimal
    professional_tax: Decimal
    tds: Decimal

    # Deductions - Other
    loan_deduction: Decimal
    advance_deduction: Decimal
    other_deductions: Decimal
    total_deductions: Decimal

    # Net
    net_salary: Decimal

    # Payment
    payment_mode: Optional[str] = None
    payment_date: Optional[date] = None
    payment_reference: Optional[str] = None

    payslip_pdf_url: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class PayslipListResponse(BaseModel):
    """Response for listing Payslips."""
    items: List[PayslipResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 1


# ==================== Dashboard & Reports ====================

class HRDashboardStats(BaseModel):
    """HR Dashboard statistics."""
    total_employees: int
    active_employees: int
    on_leave_today: int
    new_joinings_this_month: int
    exits_this_month: int

    # Attendance today
    present_today: int
    absent_today: int
    not_marked: int

    # Pending actions
    pending_leave_requests: int
    pending_payroll_approval: int

    # Department distribution
    department_wise: List[dict]  # [{department, count}]


class AttendanceReportRequest(BaseModel):
    """Request for attendance report."""
    from_date: date
    to_date: date
    department_id: Optional[UUID] = None
    employee_ids: Optional[List[UUID]] = None


class PFReportResponse(BaseModel):
    """PF ECR report format."""
    employee_id: UUID
    employee_code: str
    employee_name: str
    uan_number: Optional[str] = None

    gross_wages: Decimal
    epf_wages: Decimal  # Basic (capped)
    eps_wages: Decimal
    edli_wages: Decimal

    epf_contribution_employee: Decimal  # 12% EPF
    epf_contribution_employer: Decimal  # 3.67% EPF
    eps_contribution: Decimal  # 8.33% EPS
    edli_contribution: Decimal
    admin_charges: Decimal

    ncp_days: int  # Non-contributing days


class ESICReportResponse(BaseModel):
    """ESIC report format."""
    employee_id: UUID
    employee_code: str
    employee_name: str
    esic_number: Optional[str] = None

    gross_wages: Decimal
    employee_contribution: Decimal  # 0.75%
    employer_contribution: Decimal  # 3.25%
    total_contribution: Decimal

    days_worked: int


# Update forward references
PayrollDetailResponse.model_rebuild()
