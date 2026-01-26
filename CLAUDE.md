# CLAUDE.md - Project Instructions for Claude Code

## Project Root
```
/Users/mantosh/Desktop/Consumer durable 2
```

## Project Overview

**Aquapurite ERP** - A full-stack Consumer Durable ERP system for water purifier manufacturing and distribution.

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (async with psycopg3)
- **Frontend**: Next.js 14+ with TypeScript, Tailwind CSS, shadcn/ui
- **Database**: PostgreSQL (Supabase in production, Docker for local dev)
- **Deployment**: Render.com (Backend API), Vercel (Frontend)

---

# GOVERNANCE RULES (CRITICAL - READ FIRST)

> **MANDATORY: Claude must follow these governance rules before making ANY changes.**

## Rule 1: NO AUTONOMOUS DECISIONS
- Claude will **NOT** make any decisions without explicit user approval
- Claude will **NOT** implement changes until the user says "proceed" or "go ahead"
- Claude will **ONLY** provide analysis, gap reports, and recommendations
- User makes ALL final decisions on what to implement

## Rule 2: GAP ANALYSIS FIRST
Before any implementation work, Claude must:
1. Audit what exists (backend APIs, frontend pages, database tables)
2. Identify what's missing (incomplete features, disconnected endpoints)
3. Document gaps between frontend and backend
4. Present findings to user for review
5. Wait for user approval before coding

## Rule 3: END-TO-END VERIFICATION
Every feature must be traced through:
- **Database** → Table exists? Columns correct?
- **Backend Model** → SQLAlchemy model matches DB?
- **Backend Schema** → Pydantic schema matches model?
- **Backend API** → Endpoint exists and returns correct data?
- **Frontend Page** → Page exists and calls correct API?
- **Frontend Component** → Component renders API response?

## Rule 4: REPORT FORMAT
All gap analysis reports must include:
- What EXISTS (with file paths)
- What's MISSING (with specific details)
- What's INCOMPLETE (partially done work)
- RECOMMENDED actions (prioritized list)

---

# MANDATORY PRE-DEPLOYMENT CHECKLIST

> **CRITICAL: Before pushing ANY code changes, complete this checklist. Do NOT skip steps.**

## Before Making Changes

### 1. Check Existing Data
- [ ] Query production database to see current data format/values
- [ ] Identify any data that might be affected by your changes
- [ ] Example: Before adding URL validation, check if existing URLs are valid

```bash
# Example: Check existing company logo URLs
curl -s "https://aquapurite-erp-api.onrender.com/api/v1/storefront/company" | jq '.logo_url'
```

### 2. Check Import Paths
- [ ] Verify all imports exist in the target modules
- [ ] Check the actual file to confirm function/class names
- [ ] Common mistake: `from app.core.security import get_current_user` ❌
- [ ] Correct: `from app.api.deps import get_current_user` ✅

```bash
# Find where a function is defined
grep -r "def get_current_user" app/
```

### 3. Check Dependencies
- [ ] If adding new imports (e.g., `supabase`), ensure package is in requirements.txt
- [ ] Use lazy imports for optional dependencies to prevent app crashes

```python
# BAD - crashes if package not installed
from supabase import create_client

# GOOD - lazy import
def get_client():
    from supabase import create_client
    return create_client(...)
```

## Before Pushing

### 4. Backward Compatibility
- [ ] Will existing data work with new validation rules?
- [ ] Will existing API consumers break?
- [ ] Are response schemas compatible with current frontend expectations?

### 5. MANDATORY Testing Procedure (DO NOT SKIP)

> **CRITICAL: Claude MUST complete ALL these steps before pushing to production. No exceptions.**

#### Step 5.1: Run Local Build
```bash
cd "/Users/mantosh/Desktop/Consumer durable 2/frontend"
rm -rf .next  # Clean build cache
pnpm build    # Must pass with exit code 0
```
- [ ] Build completes successfully (no TypeScript errors)

#### Step 5.2: Start Local Servers
```bash
# Terminal 1: Start backend
cd "/Users/mantosh/Desktop/Consumer durable 2"
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
cd "/Users/mantosh/Desktop/Consumer durable 2/frontend"
pnpm dev
```
- [ ] Backend running at http://localhost:8000
- [ ] Frontend running at http://localhost:3000

#### Step 5.3: Test API Endpoints with Real Data
```bash
# Health check
curl -s http://localhost:8000/health | jq .

# Test specific endpoints affected by changes
curl -s "http://localhost:8000/api/v1/[endpoint]" | jq .
```
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] All modified API endpoints return expected data

#### Step 5.4: Test Frontend Pages
```bash
# Test all modified pages return HTTP 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/[page-path]
```
- [ ] All modified pages load (HTTP 200 or 307 redirect to login)
- [ ] No console errors in browser DevTools

#### Step 5.5: Only THEN Push to Production
```bash
git add [files]
git commit -m "description"
git push origin main
```

#### Step 5.6: Post-Deployment Verification
```bash
# Verify API health
curl -s https://aquapurite-erp-api.onrender.com/health | jq .

# Verify all modified pages on production
curl -s -o /dev/null -w "%{http_code}" "https://www.aquapurite.org/dashboard/[page]"
```
- [ ] Production API health is `healthy`
- [ ] All modified pages return HTTP 200

**LESSON LEARNED (2026-01-19):** Running `pnpm build` alone is NOT sufficient testing. Claude must start local servers and test actual page loads before deployment.

### 6. Schema Validation Impact
- [ ] Validators on **Base schemas** affect RESPONSES (existing data)
- [ ] Validators on **Create/Update schemas** affect INPUTS only
- [ ] Never add strict validation to response schemas without checking existing data

```python
# BAD - breaks responses if existing data doesn't match
class CompanyBase(BaseModel):
    @field_validator('logo_url')
    def validate_url(cls, v): ...

# GOOD - only validates new inputs
class CompanyCreate(CompanyBase):
    @field_validator('logo_url')
    def validate_url(cls, v): ...
```

## After Deployment

### 7. Verify Deployment
- [ ] Check Render logs for startup errors
- [ ] Test health endpoint: `curl https://aquapurite-erp-api.onrender.com/health`
- [ ] Test affected API endpoints
- [ ] Check frontend console for errors

## Common Mistakes to Avoid

| Mistake | Impact | Prevention |
|---------|--------|------------|
| Adding validation to Base schema | 500 errors on all GET requests | Only validate on Create/Update schemas |
| Wrong import path | App fails to start | Grep for function definition first |
| Missing lazy import | App crashes without package | Wrap optional imports in try/except |
| Not checking existing data | Validation breaks current data | Query production before adding validation |
| Pushing without testing | Production outage | Always test locally first |
| Only running `pnpm build` | Misses runtime errors | Start local servers AND test pages |
| Skipping local server test | Pages may fail at runtime | Always run `pnpm dev` and test in browser |
| Not testing modified pages | Broken pages in production | curl each modified page for HTTP 200 |
| **Missing field in Response schema** | Field silently dropped from API | Match schema fields to service return |
| **Field name mismatch** | Frontend shows 0/null | Use EXACT same names: backend → schema → frontend |
| **Status case mismatch (paid vs PAID)** | Logic failures, wrong counts | Always store UPPERCASE, compare with .upper() |
| **UUID not stringified** | JSON serialization fails | Use str(uuid) or let Pydantic handle |

---

# DEBUGGING GUIDE - FASTEST PATH TO ROOT CAUSE

> **CRITICAL: When debugging production errors, ALWAYS get the actual error message FIRST. Do NOT guess.**

## Step 1: Get the EXACT Error Message (Do This IMMEDIATELY)

### For API Errors (500, 400, etc.)

**FASTEST METHOD - Browser Network Tab:**
1. Open browser DevTools (Cmd+Option+I on Mac, F12 on Windows)
2. Go to **Network** tab
3. Reproduce the error (click the button that fails)
4. Click on the **failed request** (red row)
5. Click **Response** tab → **This shows the EXACT error message**

The FastAPI global exception handler returns detailed JSON:
```json
{
  "error": "The actual error message",
  "type": "ErrorClassName",
  "path": "/api/v1/...",
  "traceback": "Full Python traceback..."
}
```

**DO NOT:**
- ❌ Guess what the error might be
- ❌ Check environment variables without seeing the error first
- ❌ Make multiple code changes hoping one works
- ❌ Spend 30+ minutes debugging without the actual error message

### For Frontend Errors
1. Browser Console (Cmd+Option+J) → Shows JavaScript errors
2. Network tab → Shows failed API calls with response body

### For Startup/Deploy Errors
1. **Render Dashboard** → Logs → Look for Python tracebacks
2. **Vercel Dashboard** → Deployments → Build logs

## Step 2: Production URLs & Dashboards

| Service | URL | Purpose |
|---------|-----|---------|
| Backend API | https://aquapurite-erp-api.onrender.com | FastAPI backend |
| Health Check | https://aquapurite-erp-api.onrender.com/health | Verify API is running |
| API Docs | https://aquapurite-erp-api.onrender.com/docs | Swagger UI |
| ERP Frontend | https://aquapurite.org or https://erp-woad-eight.vercel.app | Admin panel |
| D2C Storefront | https://www.aquapurite.com | Customer-facing site |
| Render Dashboard | https://dashboard.render.com | Backend logs, env vars |
| Vercel Dashboard | https://vercel.com | Frontend logs, env vars |
| Supabase Dashboard | https://supabase.com/dashboard | Database, Storage |

## Step 3: Common Error Patterns & Solutions

### Error: "'ClientOptions' object has no attribute 'storage'"
**Cause:** Supabase SDK version mismatch
**Solution:** Use simple `create_client(url, key)` without ClientOptions

### Error: "Supabase credentials not configured"
**Cause:** Missing env vars in Render
**Check:** Render → Environment → Verify SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_STORAGE_BUCKET

### Error: "Invalid URL format... Got: 'filename.png'"
**Cause:** Validator on Base schema affecting Response (existing data has filename, not URL)
**Solution:** Move validator to Create/Update schemas only, not Base

### Error: "cannot import name 'X' from 'module'"
**Cause:** Wrong import path
**Solution:** `grep -r "def X" app/` to find actual location

### Error: 500 on all GET requests after schema change
**Cause:** Pydantic validator on Base schema failing for existing DB data
**Solution:** Check if validator is on Base schema, move to input schemas

### Error: App crashes on startup (Render)
**Cause:** Usually top-level import of optional package
**Solution:** Use lazy imports inside functions

## Step 4: Quick Diagnostic Commands

```bash
# Check if API is healthy
curl -s https://aquapurite-erp-api.onrender.com/health

# Test specific endpoint (public)
curl -s https://aquapurite-erp-api.onrender.com/api/v1/storefront/company | jq

# Check what's in production database (via API)
curl -s https://aquapurite-erp-api.onrender.com/api/v1/storefront/products | jq '.items[0]'

# Find where a function is defined
grep -r "def function_name" app/

# Find where a class is defined
grep -r "class ClassName" app/

# Check if package is in requirements
grep -i "package_name" requirements.txt
```

## Step 5: Environment Variables Reference

### Render (Backend) - Required
| Variable | Example | Purpose |
|----------|---------|---------|
| DATABASE_URL | postgresql+psycopg://... | Supabase PostgreSQL connection |
| SECRET_KEY | random-string | JWT signing |
| SUPABASE_URL | https://xxx.supabase.co | Storage API |
| SUPABASE_SERVICE_KEY | eyJ... | Storage auth (service role) |
| SUPABASE_STORAGE_BUCKET | uploads | Bucket name |

### Vercel (Frontend) - Required
| Variable | Example | Purpose |
|----------|---------|---------|
| NEXT_PUBLIC_API_URL | https://aquapurite-erp-api.onrender.com | Backend API |

### Supabase Production Database (Direct Access)
```
Host: db.aavjhutqzwusgdwrczds.supabase.co
Port: 6543
Database: postgres
User: postgres
Password: Aquapurite2026

Connection String:
postgresql://postgres:Aquapurite2026@db.aavjhutqzwusgdwrczds.supabase.co:6543/postgres

For psql:
psql "postgresql://postgres:Aquapurite2026@db.aavjhutqzwusgdwrczds.supabase.co:6543/postgres"
```

## Debugging Lessons Learned

1. **2026-01-18: Upload 500 error** - Spent 30 min guessing. Solution was in browser Network Response tab showing `'ClientOptions' object has no attribute 'storage'`. **Lesson: ALWAYS check browser Response tab FIRST.**

2. **2026-01-17: Company logo not showing** - Root cause was `logo_url` field contained filename instead of full URL. **Lesson: Check actual data in database before assuming code bug.**

3. **2026-01-17: 500 errors after URL validation** - Added validator to Base schema which broke responses for existing data. **Lesson: Validators on Base schemas affect GET responses too.**

4. **2026-01-22: Dashboard Total Customers showing 0** - Backend service returned `total_customers` but Pydantic `OrderSummary` schema didn't include the field, causing it to be silently dropped. **Lesson: Always ensure response schemas include ALL fields returned by the service.**

---

# CODING STANDARDS & RULES

> **CRITICAL: Follow these rules for EVERY code change. These prevent the recurring structural issues that cause cross-module breakages.**

## Rule 1: Schema-Service-API Field Alignment

### Problem This Solves
Services return fields that get silently dropped because Pydantic response schemas don't include them.

### Rule
**Every field returned by a service MUST be defined in the response schema.**

```python
# ❌ BAD - Service returns fields not in schema
# Service returns:
return {
    "total_orders": 38,
    "total_customers": 20,  # NOT in OrderSummary schema!
    "total_revenue": 158104.66,
}

# Schema only has:
class OrderSummary(BaseModel):
    total_orders: int
    total_revenue: Decimal
    # Missing: total_customers!  ← This field gets dropped silently

# ✅ GOOD - Schema includes ALL service fields
class OrderSummary(BaseModel):
    total_orders: int
    total_customers: int = 0  # Added with default
    total_revenue: Decimal
```

### Checklist Before Adding Service Returns
- [ ] Check if the response schema includes the field
- [ ] Add field to schema with appropriate default value
- [ ] Verify field name matches EXACTLY (case-sensitive)

---

## Rule 2: Validator Placement

### Problem This Solves
Validators on Base schemas cause 500 errors on GET requests when existing DB data doesn't match validation rules.

### Rule
**NEVER put validators on Base schemas. Only on Create/Update schemas.**

```python
# ❌ BAD - Validators on Base (affects responses)
class InvoiceBase(BaseModel):
    quantity: Decimal = Field(..., gt=0)  # Breaks if DB has quantity=0

    @field_validator('logo_url')
    def validate_url(cls, v):
        # This runs on GET responses too!
        if not v.startswith('http'):
            raise ValueError('Invalid URL')
        return v

# ✅ GOOD - Validators only on input schemas
class InvoiceBase(BaseModel):
    quantity: Decimal  # No validation here
    logo_url: Optional[str] = None  # No validation here

class InvoiceCreate(InvoiceBase):
    quantity: Decimal = Field(..., gt=0)  # Validate on create

    @field_validator('logo_url')
    def validate_url(cls, v):
        if v and not v.startswith('http'):
            raise ValueError('Invalid URL')
        return v

class InvoiceResponse(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)
    # NO validators - just serialize from DB
```

---

## Rule 3: Field Naming Consistency

### Problem This Solves
Frontend expects `total_orders`, backend returns `total`. Frontend expects `gst_number`, backend returns `gstin`.

### Rule
**Use EXACT same field names across backend service, schema, and frontend types.**

### Standard Field Names (Use These)

| Category | Standard Name | DO NOT Use |
|----------|--------------|------------|
| **IDs** | `customer_id`, `order_id` | `customerId`, `customer` |
| **Counts** | `total_orders`, `total_customers` | `total`, `count`, `orders_count` |
| **Money** | `total_amount`, `subtotal`, `tax_amount` | `grand_total` (unless invoices), `amount` |
| **Status** | `status`, `payment_status` | `order_status`, `paymentStatus` |
| **GST** | `gstin` | `gst_number` (use aliases if needed) |
| **Dates** | `created_at`, `updated_at` | `createdAt`, `dateCreated` |

### Frontend-Backend Alignment
```typescript
// Frontend types/index.ts
export interface OrderStats {
  total_orders: number;      // Match backend exactly
  total_customers: number;   // Match backend exactly
  total_revenue: number;     // Match backend exactly
}

// Backend schemas/order.py
class OrderSummary(BaseModel):
    total_orders: int        # Match frontend exactly
    total_customers: int     # Match frontend exactly
    total_revenue: Decimal   # Match frontend exactly
```

---

## Rule 4: Status & Enum Value Handling

### Problem This Solves
Database has `PAID`, code checks for `paid`, validation fails silently.

### Rule
**All status values MUST be UPPERCASE in database. Use case-insensitive comparison when needed.**

```python
# ❌ BAD - Case mismatch causes silent failures
if order.payment_status == "paid":  # DB has "PAID"
    process_payment()  # Never executes!

# ❌ BAD - Mixing enum .value with string comparison
if order.status == PaymentStatus.PAID.value:  # DB has VARCHAR "PAID"
    # Works but fragile

# ✅ GOOD - Case-insensitive comparison
from sqlalchemy import func, or_

# In queries:
revenue_stmt = select(func.sum(Order.total_amount)).where(
    or_(
        Order.payment_status == "PAID",
        func.upper(Order.payment_status) == "PAID"
    )
)

# In code:
if order.payment_status.upper() == "PAID":
    process_payment()
```

### Status Value Standards
| Status Type | Valid Values | Storage |
|-------------|--------------|---------|
| Order Status | NEW, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED | VARCHAR(50) UPPERCASE |
| Payment Status | PENDING, PAID, PARTIALLY_PAID, REFUNDED, FAILED | VARCHAR(50) UPPERCASE |
| Invoice Status | DRAFT, PENDING_APPROVAL, APPROVED, GENERATED, PAID, CANCELLED | VARCHAR(50) UPPERCASE |

---

## Rule 5: UUID vs String Handling

### Problem This Solves
Some tables use VARCHAR(36) for IDs, others use UUID. Type mismatches cause errors.

### Rule
**Know which tables use VARCHAR IDs. Always convert UUID to string for API responses.**

### Tables Using VARCHAR(36) for ID
- `franchisees` and all `franchisee_*` tables
- `po_serials`
- `model_code_references`
- `serial_sequences`
- `supplier_codes`

### API Response Pattern
```python
# ❌ BAD - UUID object in response (may not serialize)
return {"id": order.id}  # If UUID object, JSON serialization may fail

# ✅ GOOD - Always convert to string
return {"id": str(order.id)}

# ✅ BETTER - Let Pydantic handle it with proper config
class OrderResponse(BaseModel):
    id: UUID  # Pydantic auto-converts to string in JSON

    model_config = ConfigDict(from_attributes=True)
```

---

## Rule 6: Response Schema Completeness

### Problem This Solves
Schema defines 5 fields, service returns 8 fields, frontend expects 8 fields. 3 fields silently dropped.

### Rule
**Response schemas MUST include ALL fields the service returns.**

### Checklist for Adding New Service Fields
1. [ ] Add field to service return dict/object
2. [ ] Add field to Pydantic Response schema (with default if optional)
3. [ ] Add field to Frontend TypeScript interface
4. [ ] Verify field name matches across all 3 layers

### Example - Adding `total_customers` to dashboard
```python
# Step 1: Service (order_service.py)
return {
    "total_orders": total_orders,
    "total_customers": total_customers,  # NEW
}

# Step 2: Schema (schemas/order.py)
class OrderSummary(BaseModel):
    total_orders: int
    total_customers: int = 0  # NEW with default

# Step 3: Frontend (types/index.ts)
export interface OrderStats {
  total_orders: number;
  total_customers: number;  // NEW
}
```

---

## Rule 7: Alias Usage

### Problem This Solves
`gstin` in one schema, `gst_number` in another. Frontend doesn't know which to use.

### Rule
**Minimize aliases. When aliases are necessary, document them clearly.**

```python
# ❌ BAD - Conflicting alias directions
# In dealer.py:
gstin: str = Field(..., alias="gst_number")  # Primary: gstin, Alias: gst_number

# In customer.py:
gst_number: str = Field(..., alias="gstin")  # Primary: gst_number, Alias: gstin
# CONFUSING!

# ✅ GOOD - One direction, documented
class VendorBase(BaseModel):
    """
    Field Aliases:
    - gstin: Primary. Also accepts 'gst_number' for backwards compatibility.
    """
    gstin: str = Field(..., alias="gst_number")  # Accept gst_number, store as gstin

    model_config = ConfigDict(populate_by_name=True)
```

---

## Rule 8: Frontend API Client Patterns

### Problem This Solves
Frontend expects `total`, backend returns `total_orders`. Silent failures.

### Rule
**Frontend API client should NOT transform field names. Use backend field names directly.**

```typescript
// ❌ BAD - Field name transformation in API client
return {
  total_orders: ordersData.total || ordersData.total_orders || 0,  // Guessing!
  total_customers: ordersData.customers || ordersData.total_customers || 0,
};

// ✅ GOOD - Use backend field names directly
return {
  total_orders: ordersData.total_orders || 0,
  total_customers: ordersData.total_customers || 0,
};

// If backend field changes, it should be fixed in backend, not worked around in frontend
```

---

## Rule 9: Error Logging for Field Issues

### Problem This Solves
Fields silently missing, no way to debug.

### Rule
**Log warnings when expected fields are missing.**

```typescript
// Frontend API client with logging
const ordersData = ordersRes.status === 'fulfilled' ? ordersRes.value.data : {};

// Log missing expected fields
if (!ordersData.total_customers && ordersData.total_customers !== 0) {
  console.warn('API Response missing expected field: total_customers', ordersData);
}

return {
  total_orders: ordersData.total_orders ?? 0,
  total_customers: ordersData.total_customers ?? 0,
};
```

---

## Rule 10: Testing Before Deployment

### Mandatory Pre-Deployment Tests

For EVERY change, test these in order:

```bash
# 1. Backend Schema/Service Changes
cd "/Users/mantosh/Desktop/Consumer durable 2"
python3 -c "
from app.schemas.YOUR_SCHEMA import YourResponse
from app.services.your_service import YourService

# Test schema can serialize all service fields
service_data = {'field1': 'value1', 'field2': 'value2'}
response = YourResponse(**service_data)
print('Schema test passed:', response.model_dump())
"

# 2. Frontend Build
cd frontend && pnpm build

# 3. Local Server Test
# Terminal 1:
DATABASE_URL='postgresql+psycopg://...' python3 -m uvicorn app.main:app --port 8000

# Terminal 2:
cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev

# 4. Test API endpoint directly
curl -s http://localhost:8000/api/v1/your-endpoint | python3 -m json.tool

# 5. Verify frontend page loads
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/dashboard/your-page
```

---

## Quick Reference: Common Mistakes to Avoid

| Mistake | Impact | Prevention |
|---------|--------|------------|
| Validator on Base schema | 500 on all GETs | Only validate on Create/Update |
| Missing field in Response schema | Field silently dropped | Match schema to service return |
| Field name mismatch (total vs total_orders) | Frontend shows 0 | Use exact field names |
| Status case mismatch (paid vs PAID) | Logic failures | Always UPPERCASE, compare upper() |
| UUID not converted to string | Serialization error | Use str() or let Pydantic handle |
| Alias in wrong direction | API confusion | Document aliases, minimize use |
| Transform fields in frontend | Hidden bugs | Use backend names directly |

---

## Field Naming Quick Reference

### Backend → Frontend Mapping
```
Backend Service    → Pydantic Schema    → Frontend Type
----------------   ----------------     ----------------
total_orders       total_orders         total_orders      ✓ SAME
total_customers    total_customers      total_customers   ✓ SAME
total_revenue      total_revenue        total_revenue     ✓ SAME

# If any layer differs, FIX IT at the source (backend)
```

---

# DATABASE ARCHITECTURE STANDARDS

> **CRITICAL: Production (Supabase) is the SINGLE SOURCE OF TRUTH.**
> All local development, SQLAlchemy models, Pydantic schemas, and API endpoints MUST match production schema exactly.

## Environment Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION (Supabase)                    │
│                    ══════════════════════                   │
│                    SOURCE OF TRUTH                          │
│                    All schema decisions start here          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL (Docker)                           │
│                    ═══════════════                          │
│                    MUST MIRROR PRODUCTION                   │
│                    Used for development & testing           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CODE LAYERS                              │
│                    ═══════════                              │
│    SQLAlchemy Models → Pydantic Schemas → API Endpoints     │
│                    All must match DB schema                 │
└─────────────────────────────────────────────────────────────┘
```

## Data Type Standards

### 1. Primary Keys & Foreign Keys

| Decision | Standard | Rationale |
|----------|----------|-----------|
| **Type** | `VARCHAR` or `UUID` | Match what production uses for each table |
| **Default** | UUID for new tables | Better for distributed systems, non-guessable |

**Current Production State:**
- Most tables: `UUID`
- Some tables use `VARCHAR`: `franchisees`, `po_serials`, `model_code_references`, `serial_sequences`, `supplier_codes`

**SQLAlchemy Pattern (for UUID tables):**
```python
from sqlalchemy.dialects.postgresql import UUID
import uuid

class MyModel(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
```

**SQLAlchemy Pattern (for VARCHAR tables - match production):**
```python
class Franchisee(Base):
    id: Mapped[str] = mapped_column(
        String(36),  # VARCHAR in production
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
```

**Research References:**
- [UUID vs Serial Primary Keys - pganalyze](https://pganalyze.com/blog/5mins-postgres-uuid-vs-serial-primary-keys)
- [Choosing UUID Types - Leapcell](https://leapcell.io/blog/choosing-the-optimal-uuid-type-for-postgresql-primary-keys)

---

### 2. Status Fields (ENUM vs VARCHAR)

| Decision | Standard | Rationale |
|----------|----------|-----------|
| **Database** | `VARCHAR` | Production uses VARCHAR; easier migrations |
| **Application** | Python `Enum` | Type safety in code via Pydantic |
| **Validation** | Pydantic schemas | Validate at API layer, not database |

**Why NOT PostgreSQL ENUMs:**
- Cannot remove values from PostgreSQL ENUMs (only add)
- ALTER TYPE is expensive and requires admin rights
- Harder to deploy schema changes across environments
- Production already uses VARCHAR

**SQLAlchemy Pattern:**
```python
# DON'T use SQLAlchemy Enum in model (creates PostgreSQL ENUM)
# status: Mapped[StatusEnum] = mapped_column(SQLAlchemyEnum(StatusEnum))

# DO use String and validate in Pydantic
class Order(Base):
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
```

**Pydantic Pattern:**
```python
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class OrderCreate(BaseModel):
    status: OrderStatus = OrderStatus.PENDING  # Validates at API layer
```

**Research References:**
- [ENUM vs VARCHAR Deep Dive](https://medium.com/@zulfikarditya/database-enums-vs-constrained-varchar-a-technical-deep-dive-for-modern-applications-30d9d6bba9f8)
- [PostgreSQL ENUM Pitfalls](https://medium.com/swlh/postgresql-3-ways-to-replace-enum-305861e089bc)

#### Complete Data Flow Pattern

```
INPUT (API Request):
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Pydantic Enum  │ →  │  .value auto    │ →  │  VARCHAR in DB  │
│  OrderStatus.   │    │  conversion     │    │  "PENDING"      │
│  PENDING        │    │  by Pydantic    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘

OUTPUT (API Response):
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  VARCHAR in DB  │ →  │  String in      │ →  │  Return as-is   │
│  "PENDING"      │    │  SQLAlchemy     │    │  NO .value      │
│                 │    │  model.status   │    │  needed!        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Code Patterns by Layer

**Layer 1 - SQLAlchemy Model:**
```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class Order(Base):
    # Use String, NOT SQLAlchemy Enum
    # Type hint is Mapped[str], NOT Mapped[OrderStatus]
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        comment="PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED"
    )
```

**Layer 2 - Pydantic Schema (Input Validation):**
```python
from enum import Enum
from pydantic import BaseModel

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"

class OrderCreate(BaseModel):
    status: OrderStatus = OrderStatus.PENDING  # Enum for validation
```

**Layer 3 - API Endpoint (Response):**
```python
@router.get("/{order_id}")
async def get_order(order_id: UUID, db: DB):
    order = await db.get(Order, order_id)
    return {
        "id": str(order.id),
        "status": order.status,  # ✅ CORRECT: Already a string
        # "status": order.status.value,  # ❌ WRONG: Fails with AttributeError
    }
```

**Layer 4 - Business Logic (Comparisons):**
```python
from app.core.enum_utils import is_status, status_in, get_enum_value

# Comparing DB value with enum
if is_status(order.status, OrderStatus.PENDING):
    # Process pending order

# Check multiple statuses
if status_in(order.status, OrderStatus.PENDING, OrderStatus.CONFIRMED):
    # Process

# Safe value extraction (works for both enum and string)
status_str = get_enum_value(data.status)  # Works whether data is Pydantic or DB
```

#### Utility Module: `app/core/enum_utils.py`

```python
from app.core.enum_utils import (
    get_enum_value,    # Safe .value extraction
    get_enum_name,     # Safe .name extraction
    to_enum,           # Convert string to enum
    is_status,         # Compare DB string with enum
    status_in,         # Check if DB string in multiple enums
    enum_comment,      # Generate column comment string
)
```

---

### 3. JSON Fields

| Decision | Standard | Rationale |
|----------|----------|-----------|
| **Type** | `JSONB` (always) | ~125x faster queries, supports indexing |
| **Never** | `JSON` | Only preserves text format (rarely needed) |

**SQLAlchemy Pattern:**
```python
from sqlalchemy.dialects.postgresql import JSONB

class Employee(Base):
    documents: Mapped[dict] = mapped_column(JSONB, default=dict)
    current_address: Mapped[dict] = mapped_column(JSONB, nullable=True)
```

**Research References:**
- [JSON vs JSONB Complete Comparison](https://www.dbvis.com/thetable/json-vs-jsonb-in-postgresql-a-complete-comparison/)
- [PostgreSQL JSON Documentation](https://www.postgresql.org/docs/current/datatype-json.html)

---

### 4. Timestamps

| Decision | Standard | Rationale |
|----------|----------|-----------|
| **Type** | `TIMESTAMP WITH TIME ZONE` | Stores absolute point in time |
| **Never** | `TIMESTAMP WITHOUT TIME ZONE` | Ambiguous, causes timezone bugs |
| **Storage** | UTC internally | PostgreSQL converts automatically |

**SQLAlchemy Pattern:**
```python
from sqlalchemy import DateTime
from datetime import datetime, timezone

class Order(Base):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  # TIMESTAMPTZ
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
```

**Research References:**
- [PostgreSQL Don't Do This - Timestamps](https://wiki.postgresql.org/wiki/Don't_Do_This)
- [PostgreSQL Timestamps Explained](https://www.yugabyte.com/blog/postgresql-timestamps-timezones/)

---

### 5. Numeric Fields

| Use Case | Type | Rationale |
|----------|------|-----------|
| **Money/Currency** | `NUMERIC(18,2)` | Exact decimal precision |
| **Percentages** | `NUMERIC(5,2)` | e.g., 99.99% |
| **Quantities** | `NUMERIC(15,2)` | Large numbers with decimals |
| **Measurements** | `DOUBLE PRECISION` | When exact precision not critical |

**SQLAlchemy Pattern:**
```python
from sqlalchemy import Numeric
from decimal import Decimal

class Product(Base):
    mrp: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("18.00"))
```

---

## Schema Synchronization Workflow

### Before Making Any Schema Changes

```bash
# 1. Run schema audit to check current state
export PRODUCTION_DB_URL="postgresql+psycopg://..."
python -m scripts.schema_audit

# 2. Review differences
# 3. If local differs from production, sync local FIRST
```

### Adding New Features (New Tables/Columns)

```
Step 1: Design in Production (Supabase)
        └── Use Supabase Dashboard or SQL
        └── This becomes the source of truth

Step 2: Create Alembic Migration for Local
        └── alembic revision -m "add_feature_x"
        └── Write migration to match production EXACTLY

Step 3: Update SQLAlchemy Models
        └── Match production schema exactly
        └── Use correct types (VARCHAR not ENUM, JSONB not JSON, etc.)

Step 4: Update Pydantic Schemas
        └── Match model field names
        └── Add validation as needed

Step 5: Update API Endpoints
        └── Use updated schemas

Step 6: Test Locally
        └── alembic upgrade head
        └── Test all affected endpoints

Step 7: Commit & Deploy
        └── Migration runs on Render deploy
```

### Fixing Schema Mismatches

```
Step 1: Run schema audit
        └── python -m scripts.schema_audit

Step 2: Production is ALWAYS right
        └── Update local to match production
        └── NEVER change production to match local (unless intentional feature)

Step 3: Update in order:
        └── Alembic migration (local DB)
        └── SQLAlchemy models
        └── Pydantic schemas
        └── API endpoints
```

---

## Current Schema Differences (To Be Fixed)

### Tables Using VARCHAR IDs (Production)
These tables use `VARCHAR` in production, not `UUID`:
- `franchisees` and all `franchisee_*` tables
- `po_serials`
- `model_code_references`
- `serial_sequences`
- `supplier_codes`

### Columns Missing in Local
- `employees.first_name`, `employees.last_name`
- `permissions.resource`
- `user_roles.is_primary`
- `products.weight_kg`
- `leave_balances.created_at`, `leave_balances.updated_at`

### Columns Only in Local (Remove or Migrate)
- `role_permissions.granted_by`

### Type Mismatches (FIXED - 2026-01-16)
All type mismatches have been resolved:
- ✅ `JSON` → `JSONB` (194 columns)
- ✅ `TIMESTAMP` → `TIMESTAMPTZ` (478 columns)
- ✅ SQLAlchemy `Enum` → `String(50)` (150 columns)
- ✅ Removed `.value`/`.name` calls on VARCHAR fields (200 occurrences)

---

## Migration Best Practices

### Expand and Contract Pattern
For breaking changes, use this safe pattern:

```
Phase 1: EXPAND
├── Add new column/table alongside existing
├── Update code to write to BOTH old and new
└── Deploy

Phase 2: MIGRATE
├── Backfill data from old to new
├── Verify data integrity
└── Monitor

Phase 3: CONTRACT
├── Update code to read/write only new
├── Remove old column/table
└── Deploy
```

### Never Do
- ❌ Drop columns without checking production usage
- ❌ Change column types without migration plan
- ❌ Use `--autogenerate` without reviewing the migration
- ❌ Assume local schema is correct

### Always Do
- ✅ Check production schema first
- ✅ Review auto-generated migrations before applying
- ✅ Test migrations in local before production
- ✅ Keep migrations small and focused

**Research References:**
- [Evolutionary Database Design - Martin Fowler](https://martinfowler.com/articles/evodb.html)
- [Database Migrations Best Practices](https://www.liquibase.com/resources/guides/database-schema-migration)
- [Supabase Multi-Environment Migrations](https://dev.to/parth24072001/supabase-managing-database-migrations-across-multiple-environments-local-staging-production-4emg)

---

## Useful Scripts

### Schema Audit
```bash
# Compare production vs local
export PRODUCTION_DB_URL="postgresql+psycopg://postgres:PASSWORD@db.PROJECT.supabase.co:6543/postgres"
python -m scripts.schema_audit
```

### Role Setup (Production)
```bash
# Setup roles on production
export DATABASE_URL="postgresql+psycopg://..."
python -m scripts.setup_production_roles
```

---

# PROJECT STRUCTURE

## Directory Structure

```
/
├── app/                    # FastAPI Backend
│   ├── api/v1/endpoints/   # API route handlers
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic layer
│   ├── core/               # Security, config, utilities
│   └── database.py         # Database connection setup
├── frontend/               # Next.js Frontend
│   └── src/app/dashboard/  # Main dashboard pages
├── alembic/                # Database migrations
├── scripts/                # Utility scripts
│   ├── schema_audit.py     # Compare production vs local schemas
│   ├── seed_rbac.py        # Seed roles and permissions
│   └── setup_production_roles.py  # Setup roles on production
└── CLAUDE.md               # This file - architecture standards
```

---

## Barcode/Serial Number System

**Barcode Format**: `APFSZAIEL00000001` (17 characters for FG, 16 for SP)
- `AP`: Brand prefix (Aquapurite)
- `FS`: Supplier code (2 letters)
- `Z`: Year code (A=2000, Z=2025, AA=2026)
- `A`: Month code (A=Jan, L=Dec)
- `IEL`: Model code (3 letters)
- `00000001`: Serial number (8 digits, continuous per model)

**Key Models:**
- `POSerial`: Individual barcodes linked to PO items
- `ProductSerialSequence`: Tracks last serial per model
- `ModelCodeReference`: Maps product SKU to 3-letter model code
- `SupplierCode`: Maps vendor to 2-letter supplier code

---

## Local Development Setup

### Prerequisites
- Docker Desktop installed
- Python 3.11+
- Node.js 18+

### Quick Start

```bash
cd "/Users/mantosh/Desktop/Consumer durable 2"

# 1. Start PostgreSQL (first time or after restart)
docker-compose up -d

# 2. Copy environment file (first time only)
cp .env.local .env

# 3. Run database migrations
alembic upgrade head

# 4. Start backend server
uvicorn app.main:app --reload --port 8000

# 5. Start frontend (in another terminal)
cd frontend && pnpm dev
```

### Database Commands

```bash
# Start PostgreSQL
docker-compose up -d

# Stop PostgreSQL
docker-compose down

# Connect to PostgreSQL shell
docker exec -it aquapurite_db psql -U aquapurite -d aquapurite_erp

# Run migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

---

## API Endpoints Reference

### Purchase Orders
- `POST /api/v1/purchase/orders` - Create PO
- `PUT /api/v1/purchase/orders/{id}/approve` - Approve PO (generates serials)
- `GET /api/v1/purchase/orders/{id}/pdf` - Download PO PDF with barcodes

### Serialization
- `POST /api/v1/serialization/generate` - Generate serials for PO
- `GET /api/v1/serialization/po/{po_id}/export` - Export barcodes as CSV

---

## Key Files for Common Tasks

| Task | Files |
|------|-------|
| PO PDF Generation | `app/api/v1/endpoints/purchase.py` |
| Serial Generation | `app/services/serialization.py` |
| Authentication | `app/services/auth_service.py`, `app/core/security.py` |
| Database Models | `app/models/` |
| API Schemas | `app/schemas/` |
| Schema Audit | `scripts/schema_audit.py` |

---

## Deployment

### Project Structure & Vercel Configuration

```
/Users/mantosh/Desktop/Consumer durable 2/
├── app/                    # FastAPI Backend (deployed to Render)
├── frontend/               # Next.js Frontend (deployed to Vercel)
├── .vercel/                # Vercel CLI config - MUST be at ROOT, not in frontend/
│   └── project.json        # Links to "erp" project
└── CLAUDE.md
```

### CRITICAL: Vercel Project Mapping

| Vercel Project | Domain | Purpose | Deploy From |
|----------------|--------|---------|-------------|
| `erp` | www.aquapurite.org | ERP Admin Panel | Root directory (`Consumer durable 2/`) |
| `d2c` | www.aquapurite.com | D2C Storefront | Same codebase, different Vercel project |
| `frontend` | N/A | DO NOT USE | Legacy/unused |

### Vercel Account
- **Account**: `aquapurite-4359` (anupam-singhs-projects-ffea0ac8)
- **Dashboard**: https://vercel.com/anupam-singhs-projects-ffea0ac8

### Correct Deployment Commands

```bash
# ALWAYS deploy from the ROOT directory, NOT from frontend/
cd "/Users/mantosh/Desktop/Consumer durable 2"

# Check you're logged into correct account
npx vercel whoami
# Should show: aquapurite-4359

# If wrong account, logout and re-login
npx vercel logout
npx vercel login
```

#### Deploy to ERP (www.aquapurite.org)
```bash
# Link to ERP project (only needed once, or if .vercel is deleted)
npx vercel link --project=erp --yes

# Deploy to production
npx vercel --prod
```

#### Deploy to D2C Storefront (www.aquapurite.com)
```bash
# Switch link to D2C project
npx vercel link --project=d2c --yes

# Deploy to production
npx vercel --prod

# IMPORTANT: Switch back to ERP after D2C deployment
npx vercel link --project=erp --yes
```

### Rollback Commands (if deployment breaks)
```bash
# List recent deployments
npx vercel ls

# Rollback to a specific deployment
npx vercel promote <deployment-url> --yes

# Example:
# npx vercel promote erp-abc123-anupam-singhs-projects-ffea0ac8.vercel.app --yes
```

### Common Deployment Mistakes to AVOID

| Mistake | Why It's Wrong | Correct Approach |
|---------|----------------|------------------|
| `cd frontend && vercel --prod` | Creates separate `.vercel` folder, wrong project | Always deploy from ROOT |
| Deploying to `frontend` project | Wrong project, not linked to aquapurite.org | Use `erp` project |
| Not checking `vercel whoami` | May deploy to wrong Vercel account | Always verify account first |
| Deleting root `.vercel` folder | Loses project link | If deleted, re-link with `vercel link --project=erp --yes` |

### Backend (Render)
- Push to `main` branch triggers auto-deploy
- URL: `https://aquapurite-erp-api.onrender.com`
- Uses `DATABASE_URL` env var pointing to Supabase PostgreSQL

### Frontend (Vercel) - Auto-Deploy
- Git push to `main` branch SHOULD trigger auto-deploy
- If auto-deploy not working, manually deploy:
  ```bash
  cd "/Users/mantosh/Desktop/Consumer durable 2"
  npx vercel --prod
  ```

### Vercel Project Settings (for reference)
The `erp` project has these settings configured in Vercel dashboard:
- **Root Directory**: `frontend`
- **Build Command**: `pnpm install && pnpm build`
- **Framework**: Next.js

---

## Known Issues & Fixes

1. **Login fails after model changes**: Use `joinedload` instead of `selectinload` in auth queries
2. **PDF shows wrong item type**: Eagerly load `product` relationship
3. **Lazy loading errors**: Always use eager loading for relationships accessed in templates
4. **Schema mismatch errors**: Run `python -m scripts.schema_audit` and sync local to production

---

## Completed Migrations

### 2026-01-16: ENUM to VARCHAR Migration (Complete)

**Migration files**:
- `alembic/versions/20260116_convert_enum_to_varchar.py` (Phase 1)
- `alembic/versions/20260116_convert_enum_to_varchar_phase2.py` (Phase 2)

**Scope of Changes**:
| Type | Count | Details |
|------|-------|---------|
| ENUM → VARCHAR | ~150 columns | All status/type fields across 48 model files |
| JSON → JSONB | ~194 columns | All JSON fields for better query performance |
| TIMESTAMP → TIMESTAMPTZ | ~478 columns | All timestamps for timezone safety |
| Code fixes (.value removal) | ~200 occurrences | 39 endpoint/service files |

**Git Commits**:
1. `4871464` - refactor: Convert all remaining models to production schema
2. `90db682` - fix: Remove .name/.value calls on VARCHAR fields in auth
3. `ffb8eb8` - fix: Pin bcrypt<4.1.0 for passlib compatibility
4. `db7d315` - fix: Remove .value/.name calls on VARCHAR fields (39 files)

**Files Modified**:
- Models (48): All files in `app/models/`
- Endpoints (27): accounting, approvals, auth, billing, purchase, etc.
- Services (11): customer360, serialization, allocation, etc.
- Middleware (1): region_filter.py
- Utilities (1): `app/core/enum_utils.py` (NEW - helper functions)

**Architectural Pattern Established**:
```
Database (VARCHAR) → SQLAlchemy (String) → API Response (use directly)
                                        ↑
Pydantic (Enum) ─────────────────────────┘ (for INPUT validation only)
```

**Production note**: Production (Supabase) already uses VARCHAR - migration gracefully skips already-converted columns

---

## 2026-01-22: Order-to-Cash Flow Testing & Fixes (Complete)

**Session Summary**: Comprehensive end-to-end testing of the D2C order flow with all schema fixes and service corrections.

### Tested Flow (All Passed)
```
CREATE ORDER → PAY → ALLOCATE → SHIP → PICK/PACK → MANIFEST → INVOICE → GL + P&L
```

### Schema Fixes Applied to Production

| Table | Column | Fix Applied | Reason |
|-------|--------|-------------|--------|
| `shipments` | `payment_mode` | Added VARCHAR(50) | Column was missing |
| `shipments` | `packaging_type` | ENUM → VARCHAR(50) | Per CLAUDE.md standards |
| `shipments` | `ship_to_address` | JSON → JSONB | Per CLAUDE.md standards |
| `shipment_tracking` | `status` | Added VARCHAR(50) | Column was missing |
| `manifests` | `business_type` | ENUM → VARCHAR(50) | Per CLAUDE.md standards |
| `journal_entries` | `created_by` | Made nullable | Allow system-generated entries |

**SQL Commands Used**:
```sql
-- Add missing columns
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS payment_mode VARCHAR(50) DEFAULT 'PREPAID';
ALTER TABLE shipment_tracking ADD COLUMN IF NOT EXISTS status VARCHAR(50);

-- Convert ENUM to VARCHAR
ALTER TABLE shipments ALTER COLUMN packaging_type TYPE VARCHAR(50) USING packaging_type::VARCHAR(50);
ALTER TABLE manifests ALTER COLUMN business_type TYPE VARCHAR(50) USING business_type::VARCHAR(50);

-- Convert JSON to JSONB
ALTER TABLE shipments ALTER COLUMN ship_to_address TYPE JSONB USING ship_to_address::JSONB;

-- Fix nullable constraint
ALTER TABLE journal_entries ALTER COLUMN created_by DROP NOT NULL;
```

### Code Fixes Applied

| File | Line | Fix | Impact |
|------|------|-----|--------|
| `app/services/shipment_service.py` | 665 | Added `await self.db.flush()` before tracking entry | Ensures shipment.id is assigned before creating tracking |
| `app/services/auto_journal_service.py` | 587 | Removed `is_auto_generated=True` | Field doesn't exist in JournalEntry model |
| `app/services/auto_journal_service.py` | 1093+ | Added helper methods | `_get_or_create_period`, `_generate_entry_number`, `_post_journal_entry` |
| `app/services/order_service.py` | 515 | Added `await self.db.commit()` after journal entry | Ensures journal entries are persisted |

### Demo Data Created

**Transporter Serviceability** (15 routes from Delhi):
```python
transporters.id = 'd96e629d-17bf-4d07-b3d7-6fccb5052f87'  # Delhivery India
# Routes: Delhi to Mumbai, Bangalore, Chennai, Kolkata, Hyderabad, etc.
```

**Warehouse Serviceability** (15 pincodes):
```python
warehouse.id = '94afba0f-3de0-483a-8cba-5d96c071f4d0'  # Delhi Warehouse
# Pincodes: 400001 (Mumbai), 560001 (Bangalore), 600001 (Chennai), etc.
```

**D2C Allocation Rule**:
```python
channel_code = 'D2C'
priority = 1
warehouse_ids = ['94afba0f-3de0-483a-8cba-5d96c071f4d0']
```

**GL Accounts Created** (Chart of Accounts):
| Code | Name | Type | SubType |
|------|------|------|---------|
| 1010 | Cash in Hand | ASSET | CASH |
| 1020 | Bank Account | ASSET | BANK |
| 1300 | Accounts Receivable | ASSET | ACCOUNTS_RECEIVABLE |
| 4000 | Sales Revenue | REVENUE | SALES_REVENUE |
| 2310 | CGST Payable | LIABILITY | TAX_PAYABLE |
| 2320 | SGST Payable | LIABILITY | TAX_PAYABLE |
| 2330 | IGST Payable | LIABILITY | TAX_PAYABLE |
| + 16 more accounts... |

**Financial Period**:
```python
period_code = 'FY2526'
period_name = 'FY 2025-26'
start_date = '2025-04-01'
end_date = '2026-03-31'
status = 'OPEN'
is_current = True
```

### Test Scripts Created

| Script | Purpose | Location |
|--------|---------|----------|
| `test_d2c_order.py` | D2C order creation with allocation | `scripts/` |
| `test_payment_flow.py` | Payment with journal entry | `scripts/` |
| `test_shipment_flow.py` | Shipment lifecycle | `scripts/` |
| `test_manifest_flow.py` | Manifest and goods issue | `scripts/` |
| `test_invoice_flow.py` | Invoice generation | `scripts/` |
| `test_gl_pnl_flow.py` | GL and P&L verification | `scripts/` |

### Schema Verification Results (All Passed)

```
✅ No PostgreSQL ENUMs - all status fields are VARCHAR
✅ All JSON columns are JSONB
✅ All timestamps have timezone (TIMESTAMPTZ)
✅ Numeric precision adequate (12,2 for amounts, 15,2 for GL)
```

### Example Journal Entry Created

```
Entry: JV-202601-0001
Type: RECEIPT (ORDER_PAYMENT)
Status: POSTED

Lines:
  DR Cash in Hand (1010):       212.40
  CR Accounts Receivable (1300): 212.40

GL Posted: 2 entries
Account Balances Updated: Yes
```

### Troubleshooting Reference

**Error**: `'is_auto_generated' is an invalid keyword argument for JournalEntry`
**Fix**: Remove `is_auto_generated=True` from journal entry creation

**Error**: `null value in column "shipment_id" violates not-null constraint`
**Fix**: Add `await self.db.flush()` before creating ShipmentTracking

**Error**: `null value in column "created_by" violates not-null constraint`
**Fix**: `ALTER TABLE journal_entries ALTER COLUMN created_by DROP NOT NULL`

**Error**: `column "payment_mode" of relation "shipments" does not exist`
**Fix**: `ALTER TABLE shipments ADD COLUMN IF NOT EXISTS payment_mode VARCHAR(50)`

**Error**: `column "business_type" is of type businesstype but expression is of type character varying`
**Fix**: `ALTER TABLE manifests ALTER COLUMN business_type TYPE VARCHAR(50)`

---

## Code Style

- Use async/await for all database operations
- Pydantic models for request/response validation
- SQLAlchemy 2.0 style with `Mapped` type hints
- Handle Decimal types carefully (use `quantize()` for precision)
- **NEVER use PostgreSQL ENUMs** - use VARCHAR + Pydantic validation
- **ALWAYS use JSONB** - never JSON
- **ALWAYS use TIMESTAMPTZ** - never TIMESTAMP

---

## Environment Variables

```env
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
```

---

## Checklist Before Any Database Change

- [ ] Checked production schema first
- [ ] Local change matches production (or is intentional new feature)
- [ ] SQLAlchemy model uses correct types (VARCHAR not ENUM, JSONB not JSON)
- [ ] Pydantic schema matches model fields
- [ ] Alembic migration created and reviewed
- [ ] Tested locally with `alembic upgrade head`
- [ ] No ad-hoc patches - structural solution only

---

## D2C Storefront Architecture

### Overview

The D2C (Direct-to-Consumer) storefront is a Next.js 14 application located in `/frontend/src/app/(storefront)/`. It connects to the FastAPI backend for product catalog, categories, and content management.

### File Structure

```
frontend/src/
├── app/(storefront)/                    # Storefront routes (public)
│   ├── layout.tsx                       # Storefront layout with header/footer
│   ├── page.tsx                         # Homepage
│   ├── products/
│   │   ├── page.tsx                     # Products listing page
│   │   └── [slug]/page.tsx              # Product detail page
│   ├── category/[slug]/page.tsx         # Category products page
│   └── cart/, checkout/, etc.
├── components/storefront/
│   ├── layout/
│   │   ├── header.tsx                   # Main header with navigation
│   │   ├── footer.tsx                   # Footer with CMS content
│   │   └── mega-menu.tsx                # Category mega menu (to implement)
│   ├── products/
│   │   ├── product-card.tsx             # Product card component
│   │   └── product-grid.tsx             # Products grid with filters
│   └── home/
│       ├── hero-section.tsx             # Homepage hero
│       └── featured-products.tsx        # Featured products
└── lib/storefront/
    └── api.ts                           # Storefront API client
```

### Category Hierarchy (ERP → D2C Mega Menu)

#### Database Schema (categories table)

```sql
-- Categories have parent-child relationship
categories (
  id UUID PRIMARY KEY,
  name VARCHAR,
  slug VARCHAR UNIQUE,
  description TEXT,
  parent_id UUID REFERENCES categories(id),  -- NULL for top-level
  level INTEGER,                              -- 0=root, 1=child, 2=grandchild
  image_url VARCHAR,
  is_active BOOLEAN DEFAULT true,
  display_order INTEGER DEFAULT 0,
  company_id UUID REFERENCES companies(id)
)
```

#### Category Hierarchy Example

```
Water Purifiers (parent_id=NULL, level=0)
├── RO+UV Water Purifiers (parent_id=water_purifiers_id, level=1)
├── UV Water Purifiers (parent_id=water_purifiers_id, level=1)
└── RO Water Purifiers (parent_id=water_purifiers_id, level=1)

Spare Parts & Accessories (parent_id=NULL, level=0)
├── Filters (parent_id=spare_parts_id, level=1)
├── Membranes (parent_id=spare_parts_id, level=1)
└── UV Lamps (parent_id=spare_parts_id, level=1)
```

#### API Endpoint for Category Tree

```python
# GET /api/v1/storefront/categories/tree
# Returns nested category structure for mega menu

@router.get("/categories/tree")
async def get_category_tree(db: AsyncSession = Depends(get_db)):
    """
    Returns categories in nested tree format for mega menu.
    Only returns active categories with products.
    """
    # Fetch all active categories with product count
    query = select(Category).where(
        Category.is_active == True
    ).order_by(Category.display_order, Category.name)

    result = await db.execute(query)
    categories = result.scalars().all()

    # Build tree structure
    return build_category_tree(categories)
```

### Mega Menu Implementation

#### Header Component Pattern

```tsx
// frontend/src/components/storefront/layout/header.tsx

export default function StorefrontHeader() {
  const [categoryTree, setCategoryTree] = useState<CategoryNode[]>([]);

  useEffect(() => {
    // Fetch category tree on mount
    storefrontApi.getCategoryTree().then(setCategoryTree);
  }, []);

  return (
    <header>
      <nav>
        {categoryTree.map(category => (
          <MegaMenuItem key={category.id} category={category} />
        ))}
      </nav>
    </header>
  );
}
```

#### Mega Menu Component

```tsx
// frontend/src/components/storefront/layout/mega-menu.tsx

interface CategoryNode {
  id: string;
  name: string;
  slug: string;
  image_url?: string;
  children: CategoryNode[];
  product_count: number;
}

export function MegaMenuItem({ category }: { category: CategoryNode }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
      className="relative"
    >
      <Link href={`/category/${category.slug}`}>
        {category.name}
      </Link>

      {isOpen && category.children.length > 0 && (
        <div className="absolute top-full left-0 bg-white shadow-lg p-4 grid grid-cols-3 gap-4 min-w-[600px]">
          {category.children.map(child => (
            <Link
              key={child.id}
              href={`/category/${child.slug}`}
              className="flex items-center gap-2 hover:text-primary"
            >
              {child.image_url && (
                <img src={child.image_url} alt="" className="w-8 h-8" />
              )}
              <span>{child.name}</span>
              <span className="text-muted-foreground text-sm">
                ({child.product_count})
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Performance Optimization

#### 1. N+1 Query Prevention

**Problem**: Stock queries executing N times for N products

```python
# BAD: N+1 query pattern
for product in products:
    stock = await get_stock(product.id)  # N queries!
```

**Solution**: Batch query with single JOIN or subquery

```python
# GOOD: Single query with aggregated stock
query = select(
    Product,
    func.coalesce(
        select(func.sum(Inventory.quantity_on_hand))
        .where(Inventory.product_id == Product.id)
        .correlate(Product)
        .scalar_subquery(),
        0
    ).label('total_stock')
).where(Product.is_active == True)
```

#### 2. React Query for Client-Side Caching

```tsx
// frontend/src/lib/storefront/hooks.ts

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { storefrontApi } from './api';

export function useProducts(filters: ProductFilters) {
  return useQuery({
    queryKey: ['storefront-products', filters],
    queryFn: () => storefrontApi.getProducts(filters),
    staleTime: 5 * 60 * 1000,  // 5 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
  });
}

export function useCategoryTree() {
  return useQuery({
    queryKey: ['storefront-category-tree'],
    queryFn: () => storefrontApi.getCategoryTree(),
    staleTime: 10 * 60 * 1000,  // 10 minutes (categories change rarely)
  });
}

export function useProductDetail(slug: string) {
  return useQuery({
    queryKey: ['storefront-product', slug],
    queryFn: () => storefrontApi.getProductBySlug(slug),
    staleTime: 5 * 60 * 1000,
  });
}
```

#### 3. Composite API Endpoints

**Problem**: Multiple API calls on page load

```tsx
// BAD: 4 API calls on homepage
const [categories, products, banners, brands] = await Promise.all([
  api.getCategories(),
  api.getProducts(),
  api.getBanners(),
  api.getBrands(),
]);
```

**Solution**: Single composite endpoint

```python
# GET /api/v1/storefront/homepage
@router.get("/homepage")
async def get_homepage_data(db: AsyncSession = Depends(get_db)):
    """
    Returns all data needed for homepage in single request.
    Cached for 5 minutes.
    """
    cache_key = "storefront:homepage"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Parallel queries with asyncio.gather
    categories, featured, banners, brands = await asyncio.gather(
        get_category_tree(db),
        get_featured_products(db, limit=8),
        get_active_banners(db),
        get_brands_with_products(db),
    )

    result = {
        "categories": categories,
        "featured_products": featured,
        "banners": banners,
        "brands": brands,
    }

    await cache.set(cache_key, result, ttl=300)  # 5 min cache
    return result
```

#### 4. Debouncing Filter Changes

```tsx
// frontend/src/app/(storefront)/products/page.tsx

import { useDebouncedCallback } from 'use-debounce';

export default function ProductsPage() {
  const [filters, setFilters] = useState<ProductFilters>({});

  // Debounce filter changes to prevent rapid API calls
  const debouncedSetFilters = useDebouncedCallback(
    (newFilters: ProductFilters) => {
      setFilters(newFilters);
    },
    300  // 300ms debounce
  );

  const { data, isLoading } = useProducts(filters);

  return (
    <div>
      <FilterSidebar onFilterChange={debouncedSetFilters} />
      <ProductGrid products={data?.items} loading={isLoading} />
    </div>
  );
}
```

#### 5. Prefetching on Hover

```tsx
// Prefetch product detail on hover
export function ProductCard({ product }: { product: Product }) {
  const queryClient = useQueryClient();

  const handleMouseEnter = () => {
    // Prefetch product detail data
    queryClient.prefetchQuery({
      queryKey: ['storefront-product', product.slug],
      queryFn: () => storefrontApi.getProductBySlug(product.slug),
    });
  };

  return (
    <Link
      href={`/products/${product.slug}`}
      onMouseEnter={handleMouseEnter}
    >
      {/* Product card content */}
    </Link>
  );
}
```

### Caching Strategy

#### Backend (Redis)

| Cache Key | TTL | Invalidation |
|-----------|-----|--------------|
| `storefront:homepage` | 5 min | On product/banner update |
| `storefront:category-tree` | 10 min | On category create/update/delete |
| `storefront:products:{filters_hash}` | 2 min | On product update |
| `storefront:product:{slug}` | 5 min | On specific product update |
| `cms:menu:{location}` | 10 min | On menu item CRUD |

#### Frontend (React Query)

| Query Key | staleTime | cacheTime |
|-----------|-----------|-----------|
| `storefront-category-tree` | 10 min | 30 min |
| `storefront-products` | 2 min | 10 min |
| `storefront-product` | 5 min | 30 min |
| `storefront-homepage` | 5 min | 15 min |

### API Endpoints (Storefront)

```
GET  /api/v1/storefront/homepage          # Composite homepage data
GET  /api/v1/storefront/categories/tree   # Category tree for mega menu
GET  /api/v1/storefront/products          # Products with filters & stock
GET  /api/v1/storefront/products/{slug}   # Single product detail
GET  /api/v1/storefront/brands            # Active brands
```

### Key Implementation Files

| Component | File | Purpose |
|-----------|------|---------|
| Header | `components/storefront/layout/header.tsx` | Navigation with mega menu |
| Mega Menu | `components/storefront/layout/mega-menu.tsx` | Category dropdown |
| Products Page | `app/(storefront)/products/page.tsx` | Product listing with filters |
| React Query Hooks | `lib/storefront/hooks.ts` | Data fetching hooks |
| Storefront API | `lib/storefront/api.ts` | API client functions |
| Backend Routes | `app/api/v1/endpoints/storefront.py` | FastAPI endpoints |

### Checklist for D2C Performance

- [ ] Category tree API with product counts implemented
- [ ] Mega menu component with hover state
- [ ] N+1 queries fixed (stock, categories, brands)
- [ ] React Query provider added to storefront layout
- [ ] Custom hooks for data fetching
- [ ] Composite homepage endpoint
- [ ] Filter debouncing (300ms)
- [ ] Product prefetch on hover
- [ ] Redis caching with proper invalidation
- [ ] Image optimization with next/image

---

## Channel Pricing Architecture (2026-01-24)

### Overview

The Channel Pricing system manages product prices across multiple sales channels (D2C, B2B, Marketplaces, Offline). It follows industry best practices for omnichannel pricing with a hybrid strategy - uniform MRP with channel-specific selling prices.

### Data Source of Truth

| Data | Source of Truth | Used By |
|------|-----------------|---------|
| **Product Name, SKU, Specs** | Product Master (`products` table) | All systems |
| **Base MRP** | Product Master (`products.mrp`) | Reference price |
| **Cost Price (COGS)** | GRN/Weighted Avg Cost (`product_costs` table) | Margin calculation |
| **HSN Code, GST Rate** | Product Master | Invoice, GST filing |
| **Channel Selling Price** | **ChannelPricing** (`channel_pricing` table) | Order, Invoice |
| **Commission, Fees** | SalesChannel + ChannelPricing | Invoice, P&L |
| **Pricing Rules** | PricingRules (`pricing_rules` table) | Order pricing |

### Pricing Architecture Layers

```
LAYER 1: PRODUCT MASTER (Source of Truth)
├── Base MRP (Maximum Retail Price) - NEVER changes per channel
├── Cost Price (from GRN/COGS - auto-calculated)
├── HSN Code & GST Rate
├── Specifications
└── Category & Brand

LAYER 2: SALES CHANNEL CONFIGURATION
├── Channel Type: D2C / B2B / MARKETPLACE / OFFLINE
├── Commission % (for marketplaces)
├── Fixed Fees (per order)
├── Default Markup/Discount %
├── Tax Settings (inclusive/exclusive)
└── Payment Terms

LAYER 3: PRICING RULES ENGINE
├── Volume Discounts: Qty 1-10 = 0%, 11-50 = 5%, 50+ = 10%
├── Customer Segment: VIP = 5% off, Dealer = 15% off
├── Promotional: Date range discounts
├── Bundle: Product A + B = 12% off
└── Time-based: Weekend/Festival pricing

LAYER 4: CHANNEL PRICING (Product-Level Override)
├── Channel + Product + Variant (unique combo)
├── MRP Override (optional)
├── Selling Price (channel-specific)
├── Transfer Price (for B2B/Dealers)
├── Max Discount % (guard rail)
├── Effective From/To (temporal pricing)
└── Is Listed (visibility on channel)

LAYER 5: ORDER PRICING CALCULATION
├── Get ChannelPricing for product
├── Apply Pricing Rules (volume, segment, promo)
├── Validate against Max Discount %
└── Store in OrderItem.unit_price

LAYER 6: INVOICE GENERATION
├── Line Items from Order (with channel pricing)
├── GST Calculation (from Product Master HSN)
├── Channel Commission/Fees (for marketplace)
└── Net Receivable calculation

LAYER 7: GL & P&L POSTING
├── Revenue by Channel
├── Commission Expense (for marketplaces)
├── COGS (from Product Cost)
└── Channel Profitability Report
```

### Database Tables

#### Core Pricing Tables
```sql
-- Channel-specific product pricing
channel_pricing (
    id UUID PRIMARY KEY,
    channel_id UUID REFERENCES sales_channels(id),
    product_id UUID REFERENCES products(id),
    variant_id UUID REFERENCES product_variants(id),  -- Optional
    mrp NUMERIC(12,2),
    selling_price NUMERIC(12,2) NOT NULL,
    transfer_price NUMERIC(12,2),  -- For B2B/Dealers
    discount_percentage NUMERIC(5,2),
    max_discount_percentage NUMERIC(5,2),
    effective_from TIMESTAMPTZ,
    effective_to TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    is_listed BOOLEAN DEFAULT TRUE,
    UNIQUE(channel_id, product_id, variant_id)
)

-- Pricing rules engine
pricing_rules (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,  -- VOLUME_DISCOUNT, SEGMENT, PROMO, BUNDLE, TIME_BASED
    channel_id UUID,  -- NULL = all channels
    category_id UUID,  -- NULL = all categories
    product_id UUID,   -- NULL = all products
    conditions JSONB NOT NULL,
    discount_type VARCHAR(20) NOT NULL,  -- PERCENTAGE, FIXED_AMOUNT
    discount_value NUMERIC(10,2) NOT NULL,
    effective_from TIMESTAMPTZ,
    effective_to TIMESTAMPTZ,
    priority INT DEFAULT 100,
    is_combinable BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
)

-- Audit trail
pricing_history (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,  -- CHANNEL_PRICING, PRICING_RULE
    entity_id UUID NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    change_reason TEXT
)
```

### Pricing Calculation Flow

```python
async def calculate_line_price(
    product_id: UUID,
    channel_id: UUID,
    quantity: int,
    customer_segment: str = "STANDARD"
) -> Decimal:
    """
    Calculate final price for order line item.

    1. Get channel pricing (or fallback to product price)
    2. Apply pricing rules (volume, segment, promo)
    3. Validate against max discount
    4. Return final price
    """
    # Step 1: Get base price from ChannelPricing
    channel_pricing = await get_channel_pricing(product_id, channel_id)

    if channel_pricing and channel_pricing.selling_price:
        base_price = channel_pricing.selling_price
    else:
        product = await get_product(product_id)
        base_price = product.selling_price or product.mrp

    # Step 2: Apply pricing rules
    final_price = await apply_pricing_rules(
        base_price, product_id, channel_id, quantity, customer_segment
    )

    # Step 3: Validate against max discount
    if channel_pricing and channel_pricing.max_discount_percentage:
        min_allowed = base_price * (1 - channel_pricing.max_discount_percentage / 100)
        final_price = max(final_price, min_allowed)

    return final_price
```

### API Endpoints

```
# Channel Pricing CRUD
GET    /api/v1/channels/{id}/pricing              # List pricing for channel
POST   /api/v1/channels/{id}/pricing              # Create pricing
PUT    /api/v1/channels/{id}/pricing/{pricing_id} # Update pricing
DELETE /api/v1/channels/{id}/pricing/{pricing_id} # Delete pricing
POST   /api/v1/channels/{id}/pricing/bulk         # Bulk create/update
POST   /api/v1/channels/{id}/pricing/import       # Import from CSV
GET    /api/v1/channels/{id}/pricing/export       # Export to CSV
POST   /api/v1/channels/{id}/pricing/copy-from/{source_id}  # Copy from channel

# Pricing Rules
GET    /api/v1/pricing-rules                      # List all rules
POST   /api/v1/pricing-rules                      # Create rule
PUT    /api/v1/pricing-rules/{id}                 # Update rule
DELETE /api/v1/pricing-rules/{id}                 # Delete rule

# Price Calculation
POST   /api/v1/pricing/calculate                  # Calculate price
GET    /api/v1/pricing/compare/{product_id}       # Compare across channels

# History & Validation
GET    /api/v1/channels/{id}/pricing/history      # Pricing change history
POST   /api/v1/pricing/validate                   # Validate pricing
GET    /api/v1/pricing/alerts                     # Below margin threshold
```

### Frontend Pages

| Page | Path | Purpose |
|------|------|---------|
| Channel Pricing Dashboard | `/dashboard/channels/pricing` | Main pricing management |
| Pricing Rules | `/dashboard/channels/pricing/rules` | Rule engine management |
| Pricing History | `/dashboard/channels/pricing/history` | Audit trail |
| Bulk Import | `/dashboard/channels/pricing/import` | CSV upload |
| Price Comparison | `/dashboard/channels/pricing/compare` | Cross-channel comparison |

### Implementation Checklist

**Phase 1: Critical Fix (Invoice Integration)** - COMPLETE (2026-01-24)
- [x] Create PricingService with `get_channel_price()` method
- [x] Modify order creation to use ChannelPricing
- [x] Ensure invoice uses OrderItem.unit_price (already set correctly from order)
- [x] Add fallback to product.selling_price if no channel pricing

**Phase 2: Enhanced UI** - COMPLETE (2026-01-24)
- [x] Channel Pricing page with tabs (Pricing, Commission, Rules, History)
- [x] Channel + Category + Product selectors (cascading dropdowns)
- [x] Margin calculation display
- [ ] Bulk edit functionality (Add Rule button disabled)

**Phase 3: Pricing Rules Engine** - COMPLETE
- [x] Create pricing_rules table (exists in database)
- [x] Create PricingRuleService (in pricing_service.py)
- [x] Volume discount rules (default rules applied)
- [x] Customer segment pricing (VIP, Dealer, Distributor)
- [ ] Promotional/time-based pricing UI

**Phase 4: Audit & History** - COMPLETE
- [x] Create pricing_history table (exists in database)
- [x] Track all pricing changes
- [x] History UI with filters (History tab in Channel Pricing page)

**Phase 5: Bulk Operations** - COMPLETE (2026-01-25)
- [x] CSV import endpoint (backend exists, UI added)
- [x] CSV export endpoint (backend exists, UI added)
- [ ] Copy pricing between channels

**Phase 6: Reports** - PARTIAL
- [x] Cross-channel price comparison (`/dashboard/channels/pricing/compare`) (2026-01-25)
- [x] Margin alerts (below threshold) - Stats card exists
- [ ] Channel profitability report

### Key Files

| Component | File |
|-----------|------|
| Channel Model | `app/models/channel.py` |
| Channel Schemas | `app/schemas/channel.py` |
| Channel Endpoints | `app/api/v1/endpoints/channels.py` |
| Pricing Service | `app/services/pricing_service.py` (NEW) |
| Order Service | `app/services/order_service.py` |
| Invoice Service | `app/services/invoice_service.py` |
| Frontend Pricing Page | `frontend/src/app/dashboard/channels/pricing/page.tsx` |

### References

- [G2 Omnichannel Pricing Guide](https://learn.g2.com/omnichannel-pricing)
- [Revionics Multi-Channel Strategy](https://revionics.com/blog/multi-channel-pricing-strategy-start-the-omnichannel-journey)
- [BigCommerce B2B Pricing](https://www.bigcommerce.com/articles/b2b-ecommerce/b2b-pricing-strategy/)

---

## Category Hierarchy & Cascading Filter Pattern (2026-01-24)

### Overview

The category system follows a **hierarchical parent-child structure**. All UI components that filter by category MUST implement **cascading dropdowns** to respect this hierarchy.

### Category Hierarchy Structure

```
categories table:
├── id (UUID) - Primary Key
├── name (VARCHAR)
├── slug (VARCHAR, UNIQUE)
├── parent_id (UUID, FK → categories.id)
│   └── NULL = Root/Parent category
│   └── Non-NULL = Sub-category (child)
└── children (relationship) - list of subcategories
```

**Current Category Data:**

| Category | Type | Parent | Has Image |
|----------|------|--------|-----------|
| **Water Purifiers** | ROOT | NULL | ✅ Yes |
| **Spare Parts** | ROOT | NULL | ✅ Yes |
| RO+UV Water Purifiers | SUB | Water Purifiers | No |
| UV Water Purifiers | SUB | Water Purifiers | No |
| Spare Parts - Economical | SUB | Spare Parts | No |
| Spare Parts - Premium | SUB | Spare Parts | No |

**Visual Hierarchy:**
```
Water Purifiers (ROOT)
├── RO+UV Water Purifiers
├── UV Water Purifiers
└── RO Water Purifiers

Spare Parts (ROOT)
├── Spare Parts - Economical
└── Spare Parts - Premium
```

### Product Assignment Rules

**CRITICAL**: Products are assigned to **LEAF categories (subcategories)**, NOT parent categories.

```
✅ CORRECT:
Product "Aquapurite Optima" → category_id = "RO+UV Water Purifiers" (subcategory)

❌ WRONG:
Product "Aquapurite Optima" → category_id = "Water Purifiers" (parent)
```

**Why?**
- Parent categories are for grouping/navigation
- Subcategories are for actual product classification
- Filtering by parent should include ALL products in its children

### Cascading Filter Pattern (MANDATORY)

Any UI that filters products by category MUST implement this pattern:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: Channel     │  Step 2: Parent       │  Step 3: Subcategory        │
│  [Select Channel ▼]  │  [Select Parent ▼]    │  [Select Subcategory ▼]     │
└─────────────────────────────────────────────────────────────────────────────┘
         │                      │                          │
         ▼                      ▼                          ▼
    All channels         ROOT categories only      Children of selected parent
    from API             (parent_id = NULL)        (parent_id = selected)
                                                           │
                                                           ▼
                                              Products filtered by subcategory
```

### Implementation Requirements

#### 1. Backend API - Category Endpoints

```python
# GET /api/v1/categories/roots - Parent categories only
@router.get("/roots")
async def get_root_categories(db: DB):
    """Returns only ROOT categories (parent_id IS NULL)"""
    stmt = select(Category).where(Category.parent_id.is_(None))
    ...

# GET /api/v1/categories/{parent_id}/children - Subcategories
@router.get("/{parent_id}/children")
async def get_subcategories(parent_id: UUID, db: DB):
    """Returns children of a parent category"""
    stmt = select(Category).where(Category.parent_id == parent_id)
    ...
```

#### 2. Backend API - Products with Hierarchy

```python
# GET /api/v1/products?category_id=X&include_children=true
# When include_children=true, fetch products from category AND all subcategories

async def get_products(category_id: UUID, include_children: bool = False):
    if include_children:
        # Get all descendant category IDs
        category_ids = await get_category_descendants(category_id)
        filters.append(Product.category_id.in_(category_ids))
    else:
        filters.append(Product.category_id == category_id)
```

#### 3. Frontend - Cascading Dropdowns

```typescript
// State
const [parentCategoryId, setParentCategoryId] = useState<string>('');
const [subcategoryId, setSubcategoryId] = useState<string>('');

// Fetch ROOT categories (parent_id = NULL)
const { data: parentCategories } = useQuery({
  queryKey: ['categories-roots'],
  queryFn: () => categoriesApi.getRoots(),
});

// Fetch CHILDREN of selected parent
const { data: subcategories } = useQuery({
  queryKey: ['categories-children', parentCategoryId],
  queryFn: () => categoriesApi.getChildren(parentCategoryId),
  enabled: !!parentCategoryId,
});

// Fetch products in selected subcategory
const { data: products } = useQuery({
  queryKey: ['products', subcategoryId],
  queryFn: () => productsApi.list({ category_id: subcategoryId }),
  enabled: !!subcategoryId,
});
```

#### 4. Frontend - Add Pricing Rule Dialog

```
┌──────────────────────────────────────────────────────────────┐
│           Add Channel Pricing                                │
├──────────────────────────────────────────────────────────────┤
│  Parent Category:    [Water Purifiers ▼]                     │
│                      (Only ROOT categories)                  │
│                                                              │
│  Subcategory:        [RO+UV Water Purifiers ▼]               │
│                      (Children of selected parent)           │
│                                                              │
│  Product:            [Aquapurite Optima ▼]                   │
│                      (Products in subcategory - DROPDOWN)    │
│                                                              │
│  MRP:                [₹29,999]  (Auto-filled from product)   │
│  Selling Price:      [₹24,999]                               │
│  Transfer Price:     [₹18,999]                               │
└──────────────────────────────────────────────────────────────┘
```

### Pages That Must Use Cascading Filters

| Page | Path | Implementation |
|------|------|----------------|
| **Channel Pricing** | `/dashboard/channels/pricing` | Channel → Parent → Sub → Product |
| **Product Catalog** | `/dashboard/catalog` | Parent → Sub → Products Table |
| **Inventory** | `/dashboard/inventory` | Parent → Sub → Stock Items |
| **Orders** | `/dashboard/orders` | Filter by category hierarchy |
| **Reports** | Various | Category drill-down |

### Anti-Patterns to AVOID

```
❌ WRONG: Single flat dropdown with ALL categories
<Select>
  <SelectItem value="water-purifiers">Water Purifiers</SelectItem>
  <SelectItem value="ro-uv">RO+UV Water Purifiers</SelectItem>  <!-- Mixed! -->
  <SelectItem value="spare-parts">Spare Parts</SelectItem>
</Select>

❌ WRONG: Search box instead of dropdown for products
<Input placeholder="Search products..." />

❌ WRONG: Filtering by parent but expecting products
// Products are in subcategories, NOT parent categories!
productsApi.list({ category_id: parentCategoryId }) // Returns 0 products

✅ CORRECT: Cascading dropdowns
<Select value={parentId} onChange={setParentId}>  {/* Parent only */}
  {rootCategories.map(c => ...)}
</Select>
<Select value={subId} onChange={setSubId}>  {/* Children of parent */}
  {subcategories.map(c => ...)}
</Select>
<Select value={productId} onChange={setProductId}>  {/* Products in sub */}
  {products.map(p => ...)}  {/* DROPDOWN, not search */}
</Select>
```

### Key Files for Category Hierarchy

| Component | File |
|-----------|------|
| Category Model | `app/models/category.py` |
| Category Service | `app/services/product_service.py` (get_category_tree, etc.) |
| Category Endpoints | `app/api/v1/endpoints/categories.py` |
| Product Model | `app/models/product.py` (category_id FK) |
| Channel Pricing UI | `frontend/src/app/dashboard/channels/pricing/page.tsx` |

### Checklist for Category-Based Features

- [ ] Parent category dropdown shows only ROOT categories (parent_id = NULL)
- [ ] Subcategory dropdown filters by selected parent
- [ ] Product selection uses DROPDOWN, not search input
- [ ] Products are fetched by subcategory, not parent category
- [ ] MRP/price auto-populated from product master when selected
- [ ] Backend supports `include_children` for hierarchy traversal

---

## Inventory Architecture (2026-01-24)

### Overview

The Inventory module follows a **dual-table architecture** with clear separation between aggregate inventory and serialized stock items. This design supports both high-level inventory management and individual unit tracking with full traceability.

### Data Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INVENTORY DATA MODEL                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐         ┌─────────────────────┐                   │
│  │  inventory_summary  │         │    stock_items      │                   │
│  │  (Aggregate View)   │         │  (Serialized View)  │                   │
│  ├─────────────────────┤         ├─────────────────────┤                   │
│  │ product_id          │         │ serial_number       │                   │
│  │ warehouse_id        │         │ barcode             │                   │
│  │ total_quantity      │ ◄────── │ product_id          │                   │
│  │ available_quantity  │  SUM()  │ warehouse_id        │                   │
│  │ reserved_quantity   │         │ status              │                   │
│  │ reorder_level       │         │ grn_number          │                   │
│  └─────────────────────┘         │ po_serial_id        │                   │
│                                  └─────────────────────┘                   │
│                                           │                                 │
│                                           ▼                                 │
│                                  ┌─────────────────────┐                   │
│                                  │   stock_movements   │                   │
│                                  │   (Audit Trail)     │                   │
│                                  ├─────────────────────┤                   │
│                                  │ movement_type       │                   │
│                                  │ quantity            │                   │
│                                  │ reference_type      │                   │
│                                  │ reference_id        │                   │
│                                  └─────────────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Navigation Structure

```
Inventory (Menu Section)
├── Dashboard              → Overview stats, alerts, quick actions
├── Stock Summary          → Aggregate view (inventory_summary table)
│   ├── Filter: Item Type [All | FG | SP | CO | CN | AC]
│   ├── Filter: Warehouse
│   └── Filter: Status [In Stock | Low Stock | Out of Stock]
├── Serialized Items       → Individual units (stock_items table)
│   ├── Filter: Item Type
│   ├── Filter: Status [AVAILABLE | RESERVED | ALLOCATED | etc.]
│   ├── Filter: GRN Number
│   └── Shows: Serial#, Barcode, Location, Status, GRN link
├── Stock Movements        → Audit trail (stock_movements table)
│   ├── Filter: Movement Type [RECEIPT | ISSUE | TRANSFER | RETURN]
│   ├── Filter: Date Range
│   └── Shows: Full history with references
├── Warehouses             → Warehouse management
└── Stock Adjustments      → Manual adjustments with reason codes
```

### View Types

| View | Data Source | Purpose | Use Case |
|------|-------------|---------|----------|
| **Stock Summary** | `inventory_summary` | Aggregate qty by product+warehouse | "How many RO Membranes in Delhi?" |
| **Serialized Items** | `stock_items` | Individual serialized units | "Where is serial APAAASED00000001?" |
| **Stock Movements** | `stock_movements` | Complete audit trail | "What happened to stock on Jan 24?" |

### Item Type Classification

Products are classified by `item_type` field in `products` table:

| Code | Name | Description | Serialized |
|------|------|-------------|------------|
| `FG` | Finished Goods | Water Purifiers, complete units | Yes |
| `SP` | Spare Parts | Filters, Membranes, UV Lamps | Yes |
| `CO` | Components | Internal parts, assemblies | Optional |
| `CN` | Consumables | Packaging, labels, chemicals | No |
| `AC` | Accessories | Stands, covers, tools | Optional |

### Stock Item Status Flow

```
GENERATED (PO Serial)
      │
      ▼ [GRN Accept]
AVAILABLE ──────────────────────────────────────────┐
      │                                              │
      ├──▶ RESERVED ──▶ ALLOCATED ──▶ PICKED        │
      │         │              │          │          │
      │         └──────────────┴──────────┘          │
      │                   │                          │
      │                   ▼                          │
      │              PACKED ──▶ SHIPPED ──▶ SOLD    │
      │                                              │
      ├──▶ DAMAGED ──▶ QUARANTINE ──▶ SCRAPPED     │
      │                                              │
      └──▶ RETURNED ◄──────────────────────────────┘
```

### GRN → Stock Items Flow

```
1. PO Created
      │
      ▼
2. PO Approved → Serials generated in `po_serials` (status: GENERATED)
      │
      ▼
3. GRN Created with serial_numbers in items
      │
      ▼
4. GET /grn/{id}/validate-serials → Match against po_serials
      │
      ├── All match → serial_validation_status = "VALIDATED"
      │
      └── Mismatch → serial_validation_status = "PARTIAL_MATCH" or "NO_MATCH"
                          │
                          ▼
               POST /grn/{id}/force (Director only)
                          │
                          ▼
                    is_forced = true
      │
      ▼
5. POST /grn/{id}/accept
      │
      ├── Update po_serials.status = "RECEIVED"
      ├── Create stock_items (status: AVAILABLE)
      ├── Link po_serials.stock_item_id
      ├── Update inventory_summary quantities
      └── Create stock_movements (type: RECEIPT)
```

### API Endpoints

```
# Stock Summary (Aggregate)
GET  /api/v1/inventory/stock-items                    # Default: aggregate view
GET  /api/v1/inventory/stock-items?view=aggregate     # Explicit aggregate
GET  /api/v1/inventory/stock-items?item_type=FG       # Filter by item type

# Serialized Items
GET  /api/v1/inventory/stock-items?view=serialized    # Individual stock items
GET  /api/v1/inventory/stock-items?view=serialized&grn_number=GRN/TEST/26-01/00006

# Stock Movements
GET  /api/v1/inventory/movements                      # Audit trail
GET  /api/v1/inventory/movements?type=RECEIPT         # Filter by type

# Stats
GET  /api/v1/inventory/stats                          # Summary stats
GET  /api/v1/inventory/low-stock                      # Low stock alerts
```

### Database Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `inventory_summary` | Aggregate inventory per product/warehouse | product_id, warehouse_id, total_quantity, available_quantity |
| `stock_items` | Individual serialized items | serial_number, product_id, warehouse_id, status, grn_number |
| `stock_movements` | Audit trail for all inventory changes | movement_type, quantity, reference_type, reference_id |
| `po_serials` | Serials generated at PO approval | barcode, po_id, status, stock_item_id |

### Key Files

| Component | File |
|-----------|------|
| Inventory Models | `app/models/inventory.py` |
| Inventory Service | `app/services/inventory_service.py` |
| Inventory Endpoints | `app/api/v1/endpoints/inventory.py` |
| GRN Service | `app/services/grn_service.py` |
| Stock Items Page | `frontend/src/app/dashboard/inventory/stock-items/page.tsx` |

### Implementation Checklist (Phase 2)

- [x] Add `item_type` filter to Stock Summary endpoint (2026-01-24)
- [x] Create Serialized Items view with tabs in Stock Items page (2026-01-24)
- [x] Add GRN column to Serialized Items view (2026-01-24)
- [x] Add Item Type badges to product display (2026-01-24)
- [x] Add Serial Number and GRN search filters (2026-01-24)
- [x] Create Stock Movements page (`/dashboard/inventory/movements`) (2026-01-24)
- [x] Update Inventory navigation menu (2026-01-24)
- [ ] Create reusable InventoryTable component

### Best Practices

1. **Always update both tables**: When stock changes, update `stock_items` AND `inventory_summary`
2. **Create movement records**: Every stock change must have a `stock_movements` entry
3. **Use transactions**: Wrap multi-table updates in database transactions
4. **Validate serials**: Always validate serial numbers against `po_serials` before acceptance
5. **Track references**: Link movements to source documents (GRN, Order, Transfer)

---

## System Audit Report (2026-01-25, Updated 2026-01-26)

### Executive Summary

Comprehensive audit of 204 database tables, 76 API endpoint files, 182+ frontend pages, and security configurations.

| Area | Grade | Critical | High | Medium |
|------|-------|----------|------|--------|
| Backend API | A- | 4 | 11 | 15 |
| ERP Frontend | B | 8 | 6 | 12 |
| D2C Storefront | B+ | 2 | 7 | 13 |
| Database Schema | A | 0 | 3 | 6 |
| Security | C+ | 2 | 8 | 8 |
| **Overall** | **B+** | **16** | **35** | **54** |

### Critical Issues (P0 - Fix Immediately)

| Issue | File | Status | Date |
|-------|------|--------|------|
| Rotate OIDC token | Vercel Dashboard | ⚠️ MANUAL | - |
| Remove Razorpay test key fallback | `checkout/page.tsx` | ✅ FIXED | 2026-01-25 |
| Add security headers | `next.config.ts` | ✅ FIXED | 2026-01-25 |
| JWT in localStorage (XSS vulnerable) | `client.ts` | ⏳ Requires backend | - |

### High Priority Issues (P1)

| Issue | File | Status | Date |
|-------|------|--------|------|
| Transaction rollback in order creation | `order_service.py` | ✅ FIXED | 2026-01-25 |
| N+1 queries in product list | `product_service.py` | ✅ VERIFIED | 2026-01-25 |
| Add composite indexes | Product, Order models | ✅ FIXED | 2026-01-25 |
| Add FK constraints to channel tables | Supabase production | ✅ FIXED | 2026-01-26 |
| Rate limiting on login | ERP + Storefront | ✅ FIXED | 2026-01-25 |
| Input validation on channel schemas | `schemas/channel.py` | ✅ FIXED | 2026-01-25 |

### Medium Priority Issues (P2)

| Issue | Status | Date |
|-------|--------|------|
| Error boundaries for storefront | ✅ FIXED (5 files) | 2026-01-25 |
| Global error handler in query-provider | ✅ FIXED | 2026-01-25 |
| Add missing SEO metadata (7 pages) | ✅ FIXED | 2026-01-25 |
| Add loading skeletons (5 pages) | ✅ FIXED | 2026-01-25 |
| Cart validation on restore | ✅ FIXED | 2026-01-25 |
| Dashboard error states | ✅ FIXED | 2026-01-25 |
| Contact/Support page | ✅ FIXED | 2026-01-25 |
| Convert JSON to JSONB (105 columns) | ✅ FIXED | 2026-01-26 |
| Fix timestamps to TIMESTAMPTZ (485 columns) | ✅ FIXED | 2026-01-26 |
| Product Q&A backend endpoints | ✅ FIXED | 2026-01-26 |
| Partner payouts backend endpoint | ✅ FIXED | 2026-01-26 |

### Fixes Applied (2026-01-25 & 2026-01-26)

**Security:**
- Removed Razorpay test key fallback in `checkout/page.tsx`
- Added security headers (X-Content-Type-Options, X-Frame-Options, HSTS, etc.) to `next.config.ts`
- Added rate limiting on ERP admin login (`(auth)/login/page.tsx`) with 5 attempts, 5-min lockout
- Added OTP verification rate limiting on storefront login (`(storefront)/account/login/page.tsx`)

**Backend:**
- Added transaction rollback with proper exception handling in `order_service.py`
- Added `IntegrityError` and `SQLAlchemyError` imports for proper error handling
- Added `@model_validator` cross-field validation to ChannelPricing schemas (selling_price <= mrp, date range validation)

**Backend (2026-01-26):**
- Implemented Product Q&A endpoints (`app/api/v1/endpoints/questions.py`):
  - GET /api/v1/questions/product/{product_id} - Get questions for a product (public)
  - POST /api/v1/questions - Ask a question (authenticated customer)
  - POST /api/v1/questions/{question_id}/answers - Answer a question
  - POST /api/v1/questions/{question_id}/helpful - Vote question helpful
  - POST /api/v1/questions/answers/{answer_id}/helpful - Vote answer helpful
- Added ProductQuestion, ProductAnswer, QuestionHelpful, AnswerHelpful models (`app/models/product_review.py`)
- Added Partner payouts endpoint: GET /api/v1/partners/{partner_id}/payouts (admin)
- Updated frontend questionsApi to use real backend endpoints instead of mock data

**Database Schema (Supabase Production) - 2026-01-26:**
- Added 9 FK constraints to channel tables:
  - `channel_pricing`: channel_id, product_id, variant_id → CASCADE
  - `channel_inventory`: channel_id, warehouse_id, product_id, variant_id → CASCADE
  - `channel_orders`: channel_id → RESTRICT, order_id → CASCADE
- Created `product_channel_settings` table (was missing in production) with proper FK constraints
- Converted 105 JSON columns → JSONB (better query performance)
- Converted 485 TIMESTAMP columns → TIMESTAMPTZ (timezone safety)

**Performance:**
- Added composite index `ix_product_category_active_status` on products table
- Added composite index `ix_product_item_type_active` on products table
- Added composite indexes `ix_order_status_created`, `ix_order_customer_created`, `ix_order_payment_status` on orders table

**Frontend:**
- Created error.tsx files for storefront routes (main, checkout, account, products, partner)
- Enhanced QueryProvider with global error handlers, retry logic, and better caching
- Added toast notifications for mutation errors
- Added SEO metadata layout files for 7 storefront pages
- Added loading skeleton files for 5 storefront pages
- Added cart validation on localStorage restore with price/availability checks
- Added error states to ERP dashboard with retry functionality
- Created Contact/Support page for storefront

### Database Type Issues (ALL FIXED 2026-01-26)

| Issue Type | Before | After | Status |
|------------|--------|-------|--------|
| JSON columns | 105 | 0 | ✅ Converted to JSONB |
| Timestamps WITHOUT timezone | 485 | 0 | ✅ Converted to TIMESTAMPTZ |
| PostgreSQL ENUMs | 0 | 0 | ✅ Good (using VARCHAR) |
| JSONB columns | 31 | 136 | ✅ Complete |
| TIMESTAMPTZ columns | 86 | 571 | ✅ Complete |

### Recommended Indexes (Add to Production)

```sql
CREATE INDEX ix_product_category_active_status ON products(category_id, is_active, status);
CREATE INDEX ix_order_status_created ON orders(status, created_at);
CREATE INDEX ix_order_customer_created ON orders(customer_id, created_at);
CREATE INDEX ix_gl_period_account_date ON general_ledger(period_id, account_id, posting_date);
CREATE INDEX ix_dealer_type_status_tier ON dealers(dealer_type, status, tier);
```

### Full Audit Report

See: `/AUDIT_REPORT_2026-01-25.md` for complete findings with file locations and remediation steps

