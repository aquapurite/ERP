# CLAUDE.md - Project Instructions for Claude Code

## Project Overview

**Aquapurite ERP** - A full-stack Consumer Durable ERP system for water purifier manufacturing and distribution.

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (async with psycopg3)
- **Frontend**: Next.js 14+ with TypeScript, Tailwind CSS, shadcn/ui
- **Database**: PostgreSQL (Supabase in production, Docker for local dev)
- **Deployment**: Render.com (Backend API), Vercel (Frontend)

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

## Debugging Lessons Learned

1. **2026-01-18: Upload 500 error** - Spent 30 min guessing. Solution was in browser Network Response tab showing `'ClientOptions' object has no attribute 'storage'`. **Lesson: ALWAYS check browser Response tab FIRST.**

2. **2026-01-17: Company logo not showing** - Root cause was `logo_url` field contained filename instead of full URL. **Lesson: Check actual data in database before assuming code bug.**

3. **2026-01-17: 500 errors after URL validation** - Added validator to Base schema which broke responses for existing data. **Lesson: Validators on Base schemas affect GET responses too.**

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
