# CLAUDE.md - Project Instructions for Claude Code

## Project Overview

**Aquapurite ERP** - A full-stack Consumer Durable ERP system for water purifier manufacturing and distribution.

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (async with psycopg3)
- **Frontend**: Next.js 14+ with TypeScript, Tailwind CSS, shadcn/ui
- **Database**: PostgreSQL (Supabase in production, Docker for local dev)
- **Deployment**: Render.com (Backend API), Vercel (Frontend)

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

### Type Mismatches to Fix
- Change `JSON` → `JSONB` in local
- Change `TIMESTAMP` → `TIMESTAMPTZ` in local
- Change SQLAlchemy `Enum` → `String` in models

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

### Backend (Render)
- Push to `main` branch triggers auto-deploy
- URL: `https://aquapurite-erp-api.onrender.com`
- Uses `DATABASE_URL` env var pointing to Supabase PostgreSQL

### Frontend (Vercel)
- Push to `main` branch triggers auto-deploy
- Uses `NEXT_PUBLIC_API_URL` for backend connection

---

## Known Issues & Fixes

1. **Login fails after model changes**: Use `joinedload` instead of `selectinload` in auth queries
2. **PDF shows wrong item type**: Eagerly load `product` relationship
3. **Lazy loading errors**: Always use eager loading for relationships accessed in templates
4. **Schema mismatch errors**: Run `python -m scripts.schema_audit` and sync local to production

---

## Completed Migrations

### 2026-01-16: ENUM to VARCHAR Migration
- **Migration file**: `alembic/versions/20260116_convert_enum_to_varchar.py`
- **What was done**:
  - Converted 37 ENUM columns to VARCHAR(50) in models: accounting, billing, commission, order, role, stock_transfer, technician, vendor, warehouse
  - Converted JSON columns to JSONB for better query performance
  - Converted TIMESTAMP to TIMESTAMPTZ for timezone safety
  - Dropped 32 old PostgreSQL ENUM types from local database
- **Production note**: Production (Supabase) already uses VARCHAR - migration gracefully skips already-converted columns

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
