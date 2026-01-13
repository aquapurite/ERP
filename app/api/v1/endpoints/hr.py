"""API endpoints for HR & Payroll management with Indian compliance."""
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hr import (
    Department, Employee, SalaryStructure, Attendance, LeaveBalance,
    LeaveRequest, Payroll, Payslip,
    EmploymentType, EmployeeStatus, LeaveType, LeaveStatus,
    AttendanceStatus, PayrollStatus, Gender, MaritalStatus
)
from app.models.user import User, UserRole
from app.models.role import Role
from app.schemas.hr import (
    # Department
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentListResponse, DepartmentDropdown,
    # Employee
    EmployeeCreateWithUser, EmployeeUpdate, EmployeeResponse, EmployeeDetailResponse,
    EmployeeListResponse, EmployeeDropdown,
    # Salary
    SalaryStructureCreate, SalaryStructureUpdate, SalaryStructureResponse,
    # Attendance
    AttendanceCheckIn, AttendanceCheckOut, AttendanceBulkCreate, AttendanceUpdate,
    AttendanceResponse, AttendanceListResponse, AttendanceReportResponse, AttendanceReportRequest,
    # Leave
    LeaveRequestCreate, LeaveRequestResponse, LeaveRequestListResponse,
    LeaveBalanceResponse, LeaveBalanceSummary, LeaveApproveRequest,
    # Payroll
    PayrollProcessRequest, PayrollResponse, PayrollListResponse, PayrollDetailResponse,
    PayslipResponse, PayslipListResponse,
    # Dashboard & Reports
    HRDashboardStats, PFReportResponse, ESICReportResponse,
)
from app.api.deps import DB, CurrentUser, get_current_user, require_permissions
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== Helper Functions ====================

def get_financial_year(d: date = None) -> str:
    """Get financial year string (e.g., '2025-26') for a date."""
    if d is None:
        d = date.today()
    if d.month >= 4:
        return f"{d.year}-{str(d.year + 1)[-2:]}"
    return f"{d.year - 1}-{str(d.year)[-2:]}"


def calculate_pf(basic_salary: Decimal, pf_applicable: bool) -> tuple[Decimal, Decimal]:
    """Calculate PF contribution (Employee & Employer)."""
    if not pf_applicable:
        return Decimal("0"), Decimal("0")
    # PF is on Basic, capped at 15000
    pf_wage = min(basic_salary, Decimal("15000"))
    employee_pf = round(pf_wage * Decimal("0.12"), 2)
    employer_pf = round(pf_wage * Decimal("0.12"), 2)
    return employee_pf, employer_pf


def calculate_esic(gross_salary: Decimal, esic_applicable: bool) -> tuple[Decimal, Decimal]:
    """Calculate ESIC contribution (Employee & Employer)."""
    if not esic_applicable or gross_salary > Decimal("21000"):
        return Decimal("0"), Decimal("0")
    employee_esic = round(gross_salary * Decimal("0.0075"), 2)
    employer_esic = round(gross_salary * Decimal("0.0325"), 2)
    return employee_esic, employer_esic


def calculate_professional_tax(gross_salary: Decimal, month: int, state: str = "Maharashtra") -> Decimal:
    """Calculate Professional Tax based on state slabs."""
    # Maharashtra slabs
    if gross_salary <= Decimal("7500"):
        return Decimal("0")
    elif gross_salary <= Decimal("10000"):
        return Decimal("175")
    else:
        # Rs 300 in February, Rs 200 other months
        return Decimal("300") if month == 2 else Decimal("200")


async def generate_employee_code(db: AsyncSession) -> str:
    """Generate next employee code."""
    result = await db.execute(
        select(Employee.employee_code)
        .order_by(Employee.employee_code.desc())
        .limit(1)
    )
    last_code = result.scalar_one_or_none()

    if last_code:
        try:
            num = int(last_code.split("-")[-1])
            return f"EMP-{str(num + 1).zfill(4)}"
        except (IndexError, ValueError):
            pass

    return "EMP-0001"


# ==================== Department Endpoints ====================

@router.get("/departments", response_model=DepartmentListResponse, dependencies=[Depends(require_permissions("hr:view"))])
async def list_departments(
    db: DB,
    current_user: CurrentUser,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
):
    """List all departments."""
    query = select(Department)

    if is_active is not None:
        query = query.where(Department.is_active == is_active)

    if search:
        query = query.where(
            or_(
                Department.code.ilike(f"%{search}%"),
                Department.name.ilike(f"%{search}%")
            )
        )

    query = query.order_by(Department.code)

    result = await db.execute(query)
    departments = result.scalars().all()

    # Get employee counts
    items = []
    for dept in departments:
        count_result = await db.execute(
            select(func.count(Employee.id))
            .where(Employee.department_id == dept.id)
            .where(Employee.status == EmployeeStatus.ACTIVE)
        )
        emp_count = count_result.scalar() or 0

        # Get head name
        head_name = None
        if dept.head_id:
            head_result = await db.execute(
                select(User).where(User.id == dept.head_id)
            )
            head = head_result.scalar_one_or_none()
            if head:
                head_name = head.full_name

        # Get parent name
        parent_name = None
        if dept.parent_id:
            parent_result = await db.execute(
                select(Department).where(Department.id == dept.parent_id)
            )
            parent = parent_result.scalar_one_or_none()
            if parent:
                parent_name = parent.name

        items.append(DepartmentResponse(
            id=dept.id,
            code=dept.code,
            name=dept.name,
            description=dept.description,
            parent_id=dept.parent_id,
            parent_name=parent_name,
            head_id=dept.head_id,
            head_name=head_name,
            is_active=dept.is_active,
            employee_count=emp_count,
            created_at=dept.created_at,
            updated_at=dept.updated_at,
        ))

    return DepartmentListResponse(items=items, total=len(items), page=1, size=len(items), pages=1)


@router.get("/departments/dropdown", response_model=List[DepartmentDropdown])
async def get_departments_dropdown(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get departments for dropdown selection."""
    result = await db.execute(
        select(Department)
        .where(Department.is_active == True)
        .order_by(Department.name)
    )
    departments = result.scalars().all()

    return [DepartmentDropdown(id=d.id, code=d.code, name=d.name) for d in departments]


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permissions("hr:create"))])
async def create_department(
    dept_in: DepartmentCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create a new department."""
    # Check if code exists
    existing = await db.execute(
        select(Department).where(Department.code == dept_in.code.upper())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with code {dept_in.code} already exists"
        )

    dept = Department(
        code=dept_in.code.upper(),
        name=dept_in.name,
        description=dept_in.description,
        parent_id=dept_in.parent_id,
        head_id=dept_in.head_id,
        is_active=dept_in.is_active,
    )

    db.add(dept)
    await db.commit()
    await db.refresh(dept)

    return DepartmentResponse(
        id=dept.id,
        code=dept.code,
        name=dept.name,
        description=dept.description,
        parent_id=dept.parent_id,
        head_id=dept.head_id,
        is_active=dept.is_active,
        employee_count=0,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )


@router.get("/departments/{department_id}", response_model=DepartmentResponse, dependencies=[Depends(require_permissions("hr:view"))])
async def get_department(
    department_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get department by ID."""
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    dept = result.scalar_one_or_none()

    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Get counts and names
    count_result = await db.execute(
        select(func.count(Employee.id))
        .where(Employee.department_id == dept.id)
        .where(Employee.status == EmployeeStatus.ACTIVE)
    )
    emp_count = count_result.scalar() or 0

    head_name = None
    if dept.head_id:
        head_result = await db.execute(select(User).where(User.id == dept.head_id))
        head = head_result.scalar_one_or_none()
        if head:
            head_name = head.full_name

    parent_name = None
    if dept.parent_id:
        parent_result = await db.execute(select(Department).where(Department.id == dept.parent_id))
        parent = parent_result.scalar_one_or_none()
        if parent:
            parent_name = parent.name

    return DepartmentResponse(
        id=dept.id,
        code=dept.code,
        name=dept.name,
        description=dept.description,
        parent_id=dept.parent_id,
        parent_name=parent_name,
        head_id=dept.head_id,
        head_name=head_name,
        is_active=dept.is_active,
        employee_count=emp_count,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )


@router.put("/departments/{department_id}", response_model=DepartmentResponse, dependencies=[Depends(require_permissions("hr:update"))])
async def update_department(
    department_id: UUID,
    dept_in: DepartmentUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Update department."""
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    dept = result.scalar_one_or_none()

    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    update_data = dept_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dept, key, value)

    await db.commit()
    await db.refresh(dept)

    return await get_department(department_id, db, current_user)


# ==================== Employee Endpoints ====================

@router.get("/employees", response_model=EmployeeListResponse, dependencies=[Depends(require_permissions("hr:view"))])
async def list_employees(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: Optional[EmployeeStatus] = None,
    department_id: Optional[UUID] = None,
    employment_type: Optional[EmploymentType] = None,
    search: Optional[str] = None,
):
    """List employees with filters."""
    query = select(Employee).options(selectinload(Employee.user))

    # Filters
    if status:
        query = query.where(Employee.status == status)
    if department_id:
        query = query.where(Employee.department_id == department_id)
    if employment_type:
        query = query.where(Employee.employment_type == employment_type)

    # Search
    if search:
        query = query.join(Employee.user).where(
            or_(
                Employee.employee_code.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
            )
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(Employee.employee_code)

    result = await db.execute(query)
    employees = result.scalars().all()

    items = []
    for emp in employees:
        # Get department name
        dept_name = None
        if emp.department_id:
            dept_result = await db.execute(
                select(Department.name).where(Department.id == emp.department_id)
            )
            dept_name = dept_result.scalar_one_or_none()

        # Get manager name
        manager_name = None
        if emp.reporting_manager_id:
            mgr_result = await db.execute(
                select(Employee)
                .options(selectinload(Employee.user))
                .where(Employee.id == emp.reporting_manager_id)
            )
            mgr = mgr_result.scalar_one_or_none()
            if mgr and mgr.user:
                manager_name = mgr.user.full_name

        items.append(EmployeeResponse(
            id=emp.id,
            employee_code=emp.employee_code,
            user_id=emp.user_id,
            email=emp.user.email if emp.user else None,
            first_name=emp.user.first_name if emp.user else None,
            last_name=emp.user.last_name if emp.user else None,
            full_name=emp.user.full_name if emp.user else None,
            phone=emp.user.phone if emp.user else None,
            avatar_url=emp.user.avatar_url if emp.user else None,
            department_id=emp.department_id,
            department_name=dept_name,
            designation=emp.designation,
            employment_type=emp.employment_type,
            status=emp.status,
            joining_date=emp.joining_date,
            reporting_manager_id=emp.reporting_manager_id,
            reporting_manager_name=manager_name,
            created_at=emp.created_at,
            updated_at=emp.updated_at,
        ))

    pages = (total + size - 1) // size
    return EmployeeListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.get("/employees/dropdown", response_model=List[EmployeeDropdown])
async def get_employees_dropdown(
    db: DB,
    current_user: User = Depends(get_current_user),
    department_id: Optional[UUID] = None,
):
    """Get active employees for dropdown."""
    query = (
        select(Employee)
        .options(selectinload(Employee.user))
        .where(Employee.status == EmployeeStatus.ACTIVE)
    )

    if department_id:
        query = query.where(Employee.department_id == department_id)

    query = query.order_by(Employee.employee_code)
    result = await db.execute(query)
    employees = result.scalars().all()

    items = []
    for emp in employees:
        dept_name = None
        if emp.department_id:
            dept_result = await db.execute(
                select(Department.name).where(Department.id == emp.department_id)
            )
            dept_name = dept_result.scalar_one_or_none()

        items.append(EmployeeDropdown(
            id=emp.id,
            employee_code=emp.employee_code,
            full_name=emp.user.full_name if emp.user else emp.employee_code,
            designation=emp.designation,
            department_name=dept_name,
        ))

    return items


@router.post("/employees", response_model=EmployeeDetailResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permissions("hr:create"))])
async def create_employee(
    emp_in: EmployeeCreateWithUser,
    db: DB,
    current_user: CurrentUser,
):
    """Create a new employee with linked User account."""
    # Check if email exists
    existing = await db.execute(
        select(User).where(User.email == emp_in.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {emp_in.email} already exists"
        )

    # Generate employee code
    emp_code = await generate_employee_code(db)

    # Create User account
    user = User(
        email=emp_in.email,
        password_hash=pwd_context.hash(emp_in.password),
        first_name=emp_in.first_name,
        last_name=emp_in.last_name,
        phone=emp_in.phone,
        employee_code=emp_code,
        department=emp_in.designation,  # Sync to user.department field
        designation=emp_in.designation,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()

    # Assign roles if provided
    if emp_in.role_ids:
        for role_id in emp_in.role_ids:
            role_result = await db.execute(select(Role).where(Role.id == role_id))
            if role_result.scalar_one_or_none():
                user_role = UserRole(
                    user_id=user.id,
                    role_id=role_id,
                    assigned_by=current_user.id,
                )
                db.add(user_role)

    # Create Employee record
    employee = Employee(
        employee_code=emp_code,
        user_id=user.id,
        date_of_birth=emp_in.date_of_birth,
        gender=emp_in.gender,
        blood_group=emp_in.blood_group,
        marital_status=emp_in.marital_status,
        nationality=emp_in.nationality,
        personal_email=emp_in.personal_email,
        personal_phone=emp_in.personal_phone,
        emergency_contact_name=emp_in.emergency_contact_name,
        emergency_contact_phone=emp_in.emergency_contact_phone,
        emergency_contact_relation=emp_in.emergency_contact_relation,
        current_address=emp_in.current_address.model_dump() if emp_in.current_address else None,
        permanent_address=emp_in.permanent_address.model_dump() if emp_in.permanent_address else None,
        department_id=emp_in.department_id,
        designation=emp_in.designation,
        employment_type=emp_in.employment_type,
        joining_date=emp_in.joining_date,
        confirmation_date=emp_in.confirmation_date,
        reporting_manager_id=emp_in.reporting_manager_id,
        pan_number=emp_in.pan_number,
        aadhaar_number=emp_in.aadhaar_number,
        uan_number=emp_in.uan_number,
        esic_number=emp_in.esic_number,
        bank_name=emp_in.bank_name,
        bank_account_number=emp_in.bank_account_number,
        bank_ifsc_code=emp_in.bank_ifsc_code,
    )
    db.add(employee)

    # Initialize leave balances for current FY
    fy = get_financial_year(emp_in.joining_date)
    leave_types_defaults = {
        LeaveType.CASUAL: Decimal("12"),
        LeaveType.SICK: Decimal("6"),
        LeaveType.EARNED: Decimal("15"),
    }

    for leave_type, opening in leave_types_defaults.items():
        balance = LeaveBalance(
            employee_id=employee.id,
            leave_type=leave_type,
            financial_year=fy,
            opening_balance=opening,
            closing_balance=opening,
            carry_forward_limit=Decimal("30") if leave_type == LeaveType.EARNED else Decimal("0"),
        )
        db.add(balance)

    await db.commit()
    await db.refresh(employee)

    return await get_employee(employee.id, db, current_user)


@router.get("/employees/{employee_id}", response_model=EmployeeDetailResponse, dependencies=[Depends(require_permissions("hr:view"))])
async def get_employee(
    employee_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get employee details by ID."""
    result = await db.execute(
        select(Employee)
        .options(selectinload(Employee.user))
        .where(Employee.id == employee_id)
    )
    emp = result.scalar_one_or_none()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Get department name
    dept_name = None
    if emp.department_id:
        dept_result = await db.execute(
            select(Department.name).where(Department.id == emp.department_id)
        )
        dept_name = dept_result.scalar_one_or_none()

    # Get manager name
    manager_name = None
    if emp.reporting_manager_id:
        mgr_result = await db.execute(
            select(Employee)
            .options(selectinload(Employee.user))
            .where(Employee.id == emp.reporting_manager_id)
        )
        mgr = mgr_result.scalar_one_or_none()
        if mgr and mgr.user:
            manager_name = mgr.user.full_name

    return EmployeeDetailResponse(
        id=emp.id,
        employee_code=emp.employee_code,
        user_id=emp.user_id,
        email=emp.user.email if emp.user else None,
        first_name=emp.user.first_name if emp.user else None,
        last_name=emp.user.last_name if emp.user else None,
        full_name=emp.user.full_name if emp.user else None,
        phone=emp.user.phone if emp.user else None,
        avatar_url=emp.user.avatar_url if emp.user else None,
        department_id=emp.department_id,
        department_name=dept_name,
        designation=emp.designation,
        employment_type=emp.employment_type,
        status=emp.status,
        joining_date=emp.joining_date,
        reporting_manager_id=emp.reporting_manager_id,
        reporting_manager_name=manager_name,
        date_of_birth=emp.date_of_birth,
        gender=emp.gender,
        blood_group=emp.blood_group,
        marital_status=emp.marital_status,
        nationality=emp.nationality,
        personal_email=emp.personal_email,
        personal_phone=emp.personal_phone,
        emergency_contact_name=emp.emergency_contact_name,
        emergency_contact_phone=emp.emergency_contact_phone,
        emergency_contact_relation=emp.emergency_contact_relation,
        current_address=emp.current_address,
        permanent_address=emp.permanent_address,
        confirmation_date=emp.confirmation_date,
        resignation_date=emp.resignation_date,
        last_working_date=emp.last_working_date,
        pan_number=emp.pan_number,
        aadhaar_number=emp.aadhaar_number,
        uan_number=emp.uan_number,
        esic_number=emp.esic_number,
        bank_name=emp.bank_name,
        bank_account_number=emp.bank_account_number,
        bank_ifsc_code=emp.bank_ifsc_code,
        profile_photo_url=emp.profile_photo_url,
        documents=emp.documents,
        created_at=emp.created_at,
        updated_at=emp.updated_at,
    )


@router.put("/employees/{employee_id}", response_model=EmployeeDetailResponse, dependencies=[Depends(require_permissions("hr:update"))])
async def update_employee(
    employee_id: UUID,
    emp_in: EmployeeUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Update employee details."""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    emp = result.scalar_one_or_none()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    update_data = emp_in.model_dump(exclude_unset=True)

    # Handle address conversion
    if 'current_address' in update_data and update_data['current_address']:
        update_data['current_address'] = update_data['current_address'].model_dump() if hasattr(update_data['current_address'], 'model_dump') else update_data['current_address']
    if 'permanent_address' in update_data and update_data['permanent_address']:
        update_data['permanent_address'] = update_data['permanent_address'].model_dump() if hasattr(update_data['permanent_address'], 'model_dump') else update_data['permanent_address']

    for key, value in update_data.items():
        setattr(emp, key, value)

    await db.commit()
    await db.refresh(emp)

    return await get_employee(employee_id, db, current_user)


# ==================== Salary Structure Endpoints ====================

@router.get("/employees/{employee_id}/salary", response_model=SalaryStructureResponse, dependencies=[Depends(require_permissions("payroll:view"))])
async def get_employee_salary(
    employee_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get employee's salary structure."""
    result = await db.execute(
        select(SalaryStructure)
        .where(SalaryStructure.employee_id == employee_id)
        .where(SalaryStructure.is_active == True)
    )
    salary = result.scalar_one_or_none()

    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary structure not found for this employee"
        )

    return salary


@router.put("/employees/{employee_id}/salary", response_model=SalaryStructureResponse, dependencies=[Depends(require_permissions("payroll:process"))])
async def update_employee_salary(
    employee_id: UUID,
    salary_in: SalaryStructureCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create or update employee's salary structure."""
    # Check employee exists
    emp_result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    if not emp_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Calculate gross and CTC
    gross = (
        salary_in.basic_salary + salary_in.hra + salary_in.conveyance +
        salary_in.medical_allowance + salary_in.special_allowance + salary_in.other_allowances
    )

    # Calculate employer contributions
    _, employer_pf = calculate_pf(salary_in.basic_salary, salary_in.pf_applicable)
    _, employer_esic = calculate_esic(gross, salary_in.esic_applicable)

    monthly_ctc = gross + employer_pf + employer_esic
    annual_ctc = monthly_ctc * 12

    # Deactivate existing structure
    await db.execute(
        select(SalaryStructure)
        .where(SalaryStructure.employee_id == employee_id)
        .where(SalaryStructure.is_active == True)
    )
    existing_result = await db.execute(
        select(SalaryStructure)
        .where(SalaryStructure.employee_id == employee_id)
        .where(SalaryStructure.is_active == True)
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        existing.is_active = False

    # Create new structure
    salary = SalaryStructure(
        employee_id=employee_id,
        effective_from=salary_in.effective_from,
        basic_salary=salary_in.basic_salary,
        hra=salary_in.hra,
        conveyance=salary_in.conveyance,
        medical_allowance=salary_in.medical_allowance,
        special_allowance=salary_in.special_allowance,
        other_allowances=salary_in.other_allowances,
        gross_salary=gross,
        employer_pf=employer_pf,
        employer_esic=employer_esic,
        monthly_ctc=monthly_ctc,
        annual_ctc=annual_ctc,
        pf_applicable=salary_in.pf_applicable,
        esic_applicable=salary_in.esic_applicable,
        pt_applicable=salary_in.pt_applicable,
        is_active=True,
    )

    db.add(salary)
    await db.commit()
    await db.refresh(salary)

    return salary


# ==================== Attendance Endpoints ====================

@router.post("/attendance/check-in", response_model=AttendanceResponse)
async def check_in(
    check_in_data: AttendanceCheckIn,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Record attendance check-in."""
    # Get employee from user or provided ID
    if check_in_data.employee_id:
        emp_id = check_in_data.employee_id
    else:
        result = await db.execute(
            select(Employee).where(Employee.user_id == current_user.id)
        )
        emp = result.scalar_one_or_none()
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No employee profile found for current user"
            )
        emp_id = emp.id

    today = date.today()
    now = datetime.now()

    # Check if already checked in today
    existing = await db.execute(
        select(Attendance)
        .where(Attendance.employee_id == emp_id)
        .where(Attendance.attendance_date == today)
    )
    attendance = existing.scalar_one_or_none()

    if attendance and attendance.check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already checked in today"
        )

    # Check late (assuming 9:30 AM is standard)
    standard_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
    is_late = now > standard_time
    late_minutes = int((now - standard_time).total_seconds() / 60) if is_late else 0

    if attendance:
        attendance.check_in = now
        attendance.is_late = is_late
        attendance.late_minutes = max(0, late_minutes)
        attendance.location_in = check_in_data.location
        attendance.status = AttendanceStatus.PRESENT
    else:
        attendance = Attendance(
            employee_id=emp_id,
            attendance_date=today,
            check_in=now,
            status=AttendanceStatus.PRESENT,
            is_late=is_late,
            late_minutes=max(0, late_minutes),
            location_in=check_in_data.location,
            remarks=check_in_data.remarks,
        )
        db.add(attendance)

    await db.commit()
    await db.refresh(attendance)

    return await _format_attendance_response(attendance, db)


@router.post("/attendance/check-out", response_model=AttendanceResponse)
async def check_out(
    check_out_data: AttendanceCheckOut,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Record attendance check-out."""
    # Get employee
    if check_out_data.employee_id:
        emp_id = check_out_data.employee_id
    else:
        result = await db.execute(
            select(Employee).where(Employee.user_id == current_user.id)
        )
        emp = result.scalar_one_or_none()
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No employee profile found for current user"
            )
        emp_id = emp.id

    today = date.today()
    now = datetime.now()

    # Find today's attendance
    result = await db.execute(
        select(Attendance)
        .where(Attendance.employee_id == emp_id)
        .where(Attendance.attendance_date == today)
    )
    attendance = result.scalar_one_or_none()

    if not attendance or not attendance.check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No check-in found for today"
        )

    if attendance.check_out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already checked out today"
        )

    # Calculate work hours
    work_hours = (now - attendance.check_in).total_seconds() / 3600

    # Check early out (assuming 6:30 PM standard)
    standard_out = now.replace(hour=18, minute=30, second=0, microsecond=0)
    is_early_out = now < standard_out
    early_out_minutes = int((standard_out - now).total_seconds() / 60) if is_early_out else 0

    # Update status based on work hours
    if work_hours < 4:
        attendance.status = AttendanceStatus.HALF_DAY

    attendance.check_out = now
    attendance.work_hours = Decimal(str(round(work_hours, 2)))
    attendance.is_early_out = is_early_out
    attendance.early_out_minutes = max(0, early_out_minutes)
    attendance.location_out = check_out_data.location

    await db.commit()
    await db.refresh(attendance)

    return await _format_attendance_response(attendance, db)


@router.get("/attendance", response_model=AttendanceListResponse, dependencies=[Depends(require_permissions("attendance:view"))])
async def list_attendance(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    employee_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    status: Optional[AttendanceStatus] = None,
):
    """List attendance records with filters."""
    query = select(Attendance)

    if employee_id:
        query = query.where(Attendance.employee_id == employee_id)

    if department_id:
        subq = select(Employee.id).where(Employee.department_id == department_id)
        query = query.where(Attendance.employee_id.in_(subq))

    if from_date:
        query = query.where(Attendance.attendance_date >= from_date)
    if to_date:
        query = query.where(Attendance.attendance_date <= to_date)

    if status:
        query = query.where(Attendance.status == status)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(Attendance.attendance_date.desc())

    result = await db.execute(query)
    records = result.scalars().all()

    items = []
    for att in records:
        items.append(await _format_attendance_response(att, db))

    pages = (total + size - 1) // size
    return AttendanceListResponse(items=items, total=total, page=page, size=size, pages=pages)


async def _format_attendance_response(att: Attendance, db: AsyncSession) -> AttendanceResponse:
    """Format attendance record to response."""
    emp_result = await db.execute(
        select(Employee)
        .options(selectinload(Employee.user))
        .where(Employee.id == att.employee_id)
    )
    emp = emp_result.scalar_one_or_none()

    dept_name = None
    if emp and emp.department_id:
        dept_result = await db.execute(
            select(Department.name).where(Department.id == emp.department_id)
        )
        dept_name = dept_result.scalar_one_or_none()

    approver_name = None
    if att.approved_by:
        approver_result = await db.execute(
            select(User).where(User.id == att.approved_by)
        )
        approver = approver_result.scalar_one_or_none()
        if approver:
            approver_name = approver.full_name

    return AttendanceResponse(
        id=att.id,
        employee_id=att.employee_id,
        attendance_date=att.attendance_date,
        status=att.status,
        check_in=att.check_in,
        check_out=att.check_out,
        work_hours=att.work_hours,
        is_late=att.is_late,
        late_minutes=att.late_minutes,
        is_early_out=att.is_early_out,
        early_out_minutes=att.early_out_minutes,
        location_in=att.location_in,
        location_out=att.location_out,
        remarks=att.remarks,
        approved_by=att.approved_by,
        approved_by_name=approver_name,
        employee_code=emp.employee_code if emp else None,
        employee_name=emp.user.full_name if emp and emp.user else None,
        department_name=dept_name,
        created_at=att.created_at,
        updated_at=att.updated_at,
    )


# ==================== Leave Endpoints ====================

@router.get("/leave-balances/{employee_id}", response_model=LeaveBalanceSummary)
async def get_leave_balances(
    employee_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
    financial_year: Optional[str] = None,
):
    """Get leave balances for an employee."""
    fy = financial_year or get_financial_year()

    result = await db.execute(
        select(LeaveBalance)
        .where(LeaveBalance.employee_id == employee_id)
        .where(LeaveBalance.financial_year == fy)
    )
    balances = result.scalars().all()

    return LeaveBalanceSummary(
        employee_id=employee_id,
        financial_year=fy,
        balances=[LeaveBalanceResponse.model_validate(b) for b in balances]
    )


@router.post("/leave-requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_request(
    leave_in: LeaveRequestCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Apply for leave."""
    # Get employee
    if leave_in.employee_id:
        emp_id = leave_in.employee_id
    else:
        result = await db.execute(
            select(Employee).where(Employee.user_id == current_user.id)
        )
        emp = result.scalar_one_or_none()
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No employee profile found"
            )
        emp_id = emp.id

    # Calculate days
    days = (leave_in.to_date - leave_in.from_date).days + 1
    if leave_in.is_half_day:
        days = Decimal("0.5")
    else:
        days = Decimal(str(days))

    # Check leave balance
    fy = get_financial_year(leave_in.from_date)
    balance_result = await db.execute(
        select(LeaveBalance)
        .where(LeaveBalance.employee_id == emp_id)
        .where(LeaveBalance.leave_type == leave_in.leave_type)
        .where(LeaveBalance.financial_year == fy)
    )
    balance = balance_result.scalar_one_or_none()

    if balance and balance.closing_balance < days and leave_in.leave_type != LeaveType.UNPAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient leave balance. Available: {balance.closing_balance}, Requested: {days}"
        )

    # Create request
    leave_request = LeaveRequest(
        employee_id=emp_id,
        leave_type=leave_in.leave_type,
        from_date=leave_in.from_date,
        to_date=leave_in.to_date,
        days=days,
        is_half_day=leave_in.is_half_day,
        half_day_type=leave_in.half_day_type,
        reason=leave_in.reason,
        status=LeaveStatus.PENDING,
    )

    db.add(leave_request)
    await db.commit()
    await db.refresh(leave_request)

    return await _format_leave_response(leave_request, db)


@router.get("/leave-requests", response_model=LeaveRequestListResponse)
async def list_leave_requests(
    db: DB,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    employee_id: Optional[UUID] = None,
    status: Optional[LeaveStatus] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
):
    """List leave requests."""
    query = select(LeaveRequest)

    if employee_id:
        query = query.where(LeaveRequest.employee_id == employee_id)
    if status:
        query = query.where(LeaveRequest.status == status)
    if from_date:
        query = query.where(LeaveRequest.from_date >= from_date)
    if to_date:
        query = query.where(LeaveRequest.to_date <= to_date)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(LeaveRequest.applied_on.desc())

    result = await db.execute(query)
    requests = result.scalars().all()

    items = [await _format_leave_response(r, db) for r in requests]

    pages = (total + size - 1) // size
    return LeaveRequestListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.put("/leave-requests/{request_id}/approve", dependencies=[Depends(require_permissions("leave:approve"))])
async def approve_leave_request(
    request_id: UUID,
    action_in: LeaveApproveRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Approve or reject leave request."""
    result = await db.execute(
        select(LeaveRequest).where(LeaveRequest.id == request_id)
    )
    leave_req = result.scalar_one_or_none()

    if not leave_req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )

    if leave_req.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Leave request is already {leave_req.status}"
        )

    if action_in.action == "APPROVE":
        leave_req.status = LeaveStatus.APPROVED
        leave_req.approved_by = current_user.id
        leave_req.approved_on = datetime.now()

        # Deduct from balance
        fy = get_financial_year(leave_req.from_date)
        balance_result = await db.execute(
            select(LeaveBalance)
            .where(LeaveBalance.employee_id == leave_req.employee_id)
            .where(LeaveBalance.leave_type == leave_req.leave_type)
            .where(LeaveBalance.financial_year == fy)
        )
        balance = balance_result.scalar_one_or_none()
        if balance:
            balance.taken = balance.taken + leave_req.days
            balance.closing_balance = (
                balance.opening_balance + balance.accrued +
                balance.adjusted - balance.taken
            )

    else:  # REJECT
        leave_req.status = LeaveStatus.REJECTED
        leave_req.approved_by = current_user.id
        leave_req.approved_on = datetime.now()
        leave_req.rejection_reason = action_in.rejection_reason

    await db.commit()
    await db.refresh(leave_req)

    return await _format_leave_response(leave_req, db)


async def _format_leave_response(leave_req: LeaveRequest, db: AsyncSession) -> LeaveRequestResponse:
    """Format leave request to response."""
    emp_result = await db.execute(
        select(Employee)
        .options(selectinload(Employee.user))
        .where(Employee.id == leave_req.employee_id)
    )
    emp = emp_result.scalar_one_or_none()

    dept_name = None
    if emp and emp.department_id:
        dept_result = await db.execute(
            select(Department.name).where(Department.id == emp.department_id)
        )
        dept_name = dept_result.scalar_one_or_none()

    approver_name = None
    if leave_req.approved_by:
        approver_result = await db.execute(
            select(User).where(User.id == leave_req.approved_by)
        )
        approver = approver_result.scalar_one_or_none()
        if approver:
            approver_name = approver.full_name

    return LeaveRequestResponse(
        id=leave_req.id,
        employee_id=leave_req.employee_id,
        leave_type=leave_req.leave_type,
        from_date=leave_req.from_date,
        to_date=leave_req.to_date,
        days=leave_req.days,
        is_half_day=leave_req.is_half_day,
        half_day_type=leave_req.half_day_type,
        reason=leave_req.reason,
        status=leave_req.status,
        applied_on=leave_req.applied_on,
        approved_by=leave_req.approved_by,
        approved_by_name=approver_name,
        approved_on=leave_req.approved_on,
        rejection_reason=leave_req.rejection_reason,
        employee_code=emp.employee_code if emp else None,
        employee_name=emp.user.full_name if emp and emp.user else None,
        department_name=dept_name,
        created_at=leave_req.created_at,
        updated_at=leave_req.updated_at,
    )


# ==================== Payroll Endpoints ====================

@router.get("/payroll", response_model=PayrollListResponse, dependencies=[Depends(require_permissions("payroll:view"))])
async def list_payrolls(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    financial_year: Optional[str] = None,
    status: Optional[PayrollStatus] = None,
):
    """List payroll runs."""
    query = select(Payroll)

    if financial_year:
        query = query.where(Payroll.financial_year == financial_year)
    if status:
        query = query.where(Payroll.status == status)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(Payroll.payroll_month.desc())

    result = await db.execute(query)
    payrolls = result.scalars().all()

    items = []
    for p in payrolls:
        processor_name = None
        if p.processed_by:
            user_result = await db.execute(select(User).where(User.id == p.processed_by))
            user = user_result.scalar_one_or_none()
            if user:
                processor_name = user.full_name

        approver_name = None
        if p.approved_by:
            user_result = await db.execute(select(User).where(User.id == p.approved_by))
            user = user_result.scalar_one_or_none()
            if user:
                approver_name = user.full_name

        items.append(PayrollResponse(
            id=p.id,
            payroll_month=p.payroll_month,
            financial_year=p.financial_year,
            status=p.status,
            total_employees=p.total_employees,
            total_gross=p.total_gross,
            total_deductions=p.total_deductions,
            total_net=p.total_net,
            processed_by=p.processed_by,
            processed_by_name=processor_name,
            processed_at=p.processed_at,
            approved_by=p.approved_by,
            approved_by_name=approver_name,
            approved_at=p.approved_at,
            created_at=p.created_at,
            updated_at=p.updated_at,
        ))

    pages = (total + size - 1) // size
    return PayrollListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.post("/payroll/process", response_model=PayrollResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permissions("payroll:process"))])
async def process_payroll(
    payroll_in: PayrollProcessRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Process monthly payroll."""
    # Check if already processed
    existing = await db.execute(
        select(Payroll)
        .where(Payroll.payroll_month == payroll_in.payroll_month)
        .where(Payroll.status != PayrollStatus.DRAFT)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payroll for {payroll_in.payroll_month} is already processed"
        )

    # Get active employees
    emp_query = select(Employee).where(Employee.status == EmployeeStatus.ACTIVE)
    if payroll_in.employee_ids:
        emp_query = emp_query.where(Employee.id.in_(payroll_in.employee_ids))

    emp_result = await db.execute(emp_query)
    employees = emp_result.scalars().all()

    if not employees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active employees found for payroll processing"
        )

    # Create payroll
    payroll = Payroll(
        payroll_month=payroll_in.payroll_month,
        financial_year=payroll_in.financial_year,
        status=PayrollStatus.PROCESSING,
        processed_by=current_user.id,
        processed_at=datetime.now(),
    )
    db.add(payroll)
    await db.flush()

    # Process each employee
    total_gross = Decimal("0")
    total_deductions = Decimal("0")
    total_net = Decimal("0")
    payslip_count = 0
    month = payroll_in.payroll_month.month

    for emp in employees:
        # Get salary structure
        salary_result = await db.execute(
            select(SalaryStructure)
            .where(SalaryStructure.employee_id == emp.id)
            .where(SalaryStructure.is_active == True)
        )
        salary = salary_result.scalar_one_or_none()

        if not salary:
            continue

        # Get attendance for the month
        month_start = payroll_in.payroll_month
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        att_result = await db.execute(
            select(Attendance)
            .where(Attendance.employee_id == emp.id)
            .where(Attendance.attendance_date >= month_start)
            .where(Attendance.attendance_date <= month_end)
        )
        attendances = att_result.scalars().all()

        # Calculate working days
        working_days = sum(1 for d in range((month_end - month_start).days + 1)
                         if (month_start + timedelta(days=d)).weekday() < 5)

        days_present = sum(1 for a in attendances if a.status == AttendanceStatus.PRESENT)
        half_days = sum(1 for a in attendances if a.status == AttendanceStatus.HALF_DAY)
        days_present += half_days * Decimal("0.5")

        leaves_taken = sum(1 for a in attendances if a.status == AttendanceStatus.ON_LEAVE)
        days_absent = working_days - days_present - leaves_taken

        # Calculate pro-rata earnings
        ratio = Decimal(str(days_present)) / Decimal(str(working_days)) if working_days > 0 else Decimal("1")

        basic_earned = round(salary.basic_salary * ratio, 2)
        hra_earned = round(salary.hra * ratio, 2)
        conveyance_earned = round(salary.conveyance * ratio, 2)
        medical_earned = round(salary.medical_allowance * ratio, 2)
        special_earned = round(salary.special_allowance * ratio, 2)
        other_earned = round(salary.other_allowances * ratio, 2)

        gross_earnings = (basic_earned + hra_earned + conveyance_earned +
                        medical_earned + special_earned + other_earned)

        # Calculate deductions
        employee_pf, employer_pf = calculate_pf(basic_earned, salary.pf_applicable)
        employee_esic, employer_esic = calculate_esic(gross_earnings, salary.esic_applicable)
        pt = calculate_professional_tax(gross_earnings, month) if salary.pt_applicable else Decimal("0")

        total_ded = employee_pf + employee_esic + pt
        net_salary = gross_earnings - total_ded

        # Generate payslip number
        payslip_count += 1
        payslip_number = f"PS-{payroll_in.payroll_month.strftime('%Y%m')}-{str(payslip_count).zfill(4)}"

        # Create payslip
        payslip = Payslip(
            payroll_id=payroll.id,
            employee_id=emp.id,
            payslip_number=payslip_number,
            working_days=working_days,
            days_present=days_present,
            days_absent=Decimal(str(days_absent)),
            leaves_taken=Decimal(str(leaves_taken)),
            basic_earned=basic_earned,
            hra_earned=hra_earned,
            conveyance_earned=conveyance_earned,
            medical_earned=medical_earned,
            special_earned=special_earned,
            other_earned=other_earned,
            gross_earnings=gross_earnings,
            employee_pf=employee_pf,
            employer_pf=employer_pf,
            employee_esic=employee_esic,
            employer_esic=employer_esic,
            professional_tax=pt,
            total_deductions=total_ded,
            net_salary=net_salary,
        )
        db.add(payslip)

        total_gross += gross_earnings
        total_deductions += total_ded
        total_net += net_salary

    # Update payroll totals
    payroll.total_employees = payslip_count
    payroll.total_gross = total_gross
    payroll.total_deductions = total_deductions
    payroll.total_net = total_net
    payroll.status = PayrollStatus.PROCESSED

    await db.commit()
    await db.refresh(payroll)

    return PayrollResponse(
        id=payroll.id,
        payroll_month=payroll.payroll_month,
        financial_year=payroll.financial_year,
        status=payroll.status,
        total_employees=payroll.total_employees,
        total_gross=payroll.total_gross,
        total_deductions=payroll.total_deductions,
        total_net=payroll.total_net,
        processed_by=payroll.processed_by,
        processed_at=payroll.processed_at,
        created_at=payroll.created_at,
        updated_at=payroll.updated_at,
    )


@router.put("/payroll/{payroll_id}/approve", response_model=PayrollResponse, dependencies=[Depends(require_permissions("payroll:approve"))])
async def approve_payroll(
    payroll_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Approve processed payroll."""
    result = await db.execute(
        select(Payroll).where(Payroll.id == payroll_id)
    )
    payroll = result.scalar_one_or_none()

    if not payroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll not found"
        )

    if payroll.status != PayrollStatus.PROCESSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payroll must be in PROCESSED status to approve. Current: {payroll.status}"
        )

    payroll.status = PayrollStatus.APPROVED
    payroll.approved_by = current_user.id
    payroll.approved_at = datetime.now()

    await db.commit()
    await db.refresh(payroll)

    return payroll


@router.get("/payslips", response_model=PayslipListResponse)
async def list_payslips(
    db: DB,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    payroll_id: Optional[UUID] = None,
    employee_id: Optional[UUID] = None,
):
    """List payslips."""
    query = select(Payslip)

    if payroll_id:
        query = query.where(Payslip.payroll_id == payroll_id)
    if employee_id:
        query = query.where(Payslip.employee_id == employee_id)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(Payslip.created_at.desc())

    result = await db.execute(query)
    payslips = result.scalars().all()

    items = []
    for ps in payslips:
        emp_result = await db.execute(
            select(Employee)
            .options(selectinload(Employee.user))
            .where(Employee.id == ps.employee_id)
        )
        emp = emp_result.scalar_one_or_none()

        dept_name = None
        if emp and emp.department_id:
            dept_result = await db.execute(
                select(Department.name).where(Department.id == emp.department_id)
            )
            dept_name = dept_result.scalar_one_or_none()

        items.append(PayslipResponse(
            id=ps.id,
            payroll_id=ps.payroll_id,
            employee_id=ps.employee_id,
            payslip_number=ps.payslip_number,
            employee_code=emp.employee_code if emp else None,
            employee_name=emp.user.full_name if emp and emp.user else None,
            department_name=dept_name,
            designation=emp.designation if emp else None,
            working_days=ps.working_days,
            days_present=ps.days_present,
            days_absent=ps.days_absent,
            leaves_taken=ps.leaves_taken,
            basic_earned=ps.basic_earned,
            hra_earned=ps.hra_earned,
            conveyance_earned=ps.conveyance_earned,
            medical_earned=ps.medical_earned,
            special_earned=ps.special_earned,
            other_earned=ps.other_earned,
            overtime_amount=ps.overtime_amount,
            arrears=ps.arrears,
            bonus=ps.bonus,
            gross_earnings=ps.gross_earnings,
            employee_pf=ps.employee_pf,
            employer_pf=ps.employer_pf,
            employee_esic=ps.employee_esic,
            employer_esic=ps.employer_esic,
            professional_tax=ps.professional_tax,
            tds=ps.tds,
            loan_deduction=ps.loan_deduction,
            advance_deduction=ps.advance_deduction,
            other_deductions=ps.other_deductions,
            total_deductions=ps.total_deductions,
            net_salary=ps.net_salary,
            payment_mode=ps.payment_mode,
            payment_date=ps.payment_date,
            payment_reference=ps.payment_reference,
            payslip_pdf_url=ps.payslip_pdf_url,
            created_at=ps.created_at,
            updated_at=ps.updated_at,
        ))

    pages = (total + size - 1) // size
    return PayslipListResponse(items=items, total=total, page=page, size=size, pages=pages)


# ==================== Dashboard Endpoints ====================

@router.get("/dashboard", response_model=HRDashboardStats, dependencies=[Depends(require_permissions("hr:view"))])
async def get_hr_dashboard(
    db: DB,
    current_user: CurrentUser,
):
    """Get HR dashboard statistics."""
    today = date.today()
    month_start = today.replace(day=1)

    # Employee counts
    total_result = await db.execute(select(func.count(Employee.id)))
    total_employees = total_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(Employee.id))
        .where(Employee.status == EmployeeStatus.ACTIVE)
    )
    active_employees = active_result.scalar() or 0

    # New joinings this month
    new_joinings_result = await db.execute(
        select(func.count(Employee.id))
        .where(Employee.joining_date >= month_start)
    )
    new_joinings = new_joinings_result.scalar() or 0

    # Exits this month
    exits_result = await db.execute(
        select(func.count(Employee.id))
        .where(Employee.status.in_([EmployeeStatus.RESIGNED, EmployeeStatus.TERMINATED]))
        .where(Employee.last_working_date >= month_start)
    )
    exits = exits_result.scalar() or 0

    # Attendance today
    present_result = await db.execute(
        select(func.count(Attendance.id))
        .where(Attendance.attendance_date == today)
        .where(Attendance.status == AttendanceStatus.PRESENT)
    )
    present_today = present_result.scalar() or 0

    absent_result = await db.execute(
        select(func.count(Attendance.id))
        .where(Attendance.attendance_date == today)
        .where(Attendance.status == AttendanceStatus.ABSENT)
    )
    absent_today = absent_result.scalar() or 0

    on_leave_result = await db.execute(
        select(func.count(Attendance.id))
        .where(Attendance.attendance_date == today)
        .where(Attendance.status == AttendanceStatus.ON_LEAVE)
    )
    on_leave_today = on_leave_result.scalar() or 0

    marked_result = await db.execute(
        select(func.count(Attendance.id))
        .where(Attendance.attendance_date == today)
    )
    marked_today = marked_result.scalar() or 0
    not_marked = active_employees - marked_today

    # Pending leave requests
    pending_leaves_result = await db.execute(
        select(func.count(LeaveRequest.id))
        .where(LeaveRequest.status == LeaveStatus.PENDING)
    )
    pending_leave_requests = pending_leaves_result.scalar() or 0

    # Pending payroll
    pending_payroll_result = await db.execute(
        select(func.count(Payroll.id))
        .where(Payroll.status == PayrollStatus.PROCESSED)
    )
    pending_payroll = pending_payroll_result.scalar() or 0

    # Department distribution
    dept_result = await db.execute(
        select(Department.name, func.count(Employee.id))
        .join(Employee, Employee.department_id == Department.id)
        .where(Employee.status == EmployeeStatus.ACTIVE)
        .group_by(Department.name)
        .order_by(func.count(Employee.id).desc())
    )
    dept_distribution = [{"department": name, "count": count} for name, count in dept_result.all()]

    return HRDashboardStats(
        total_employees=total_employees,
        active_employees=active_employees,
        on_leave_today=on_leave_today,
        new_joinings_this_month=new_joinings,
        exits_this_month=exits,
        present_today=present_today,
        absent_today=absent_today,
        not_marked=not_marked,
        pending_leave_requests=pending_leave_requests,
        pending_payroll_approval=pending_payroll,
        department_wise=dept_distribution,
    )
