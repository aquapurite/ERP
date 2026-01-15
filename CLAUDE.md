# CLAUDE.md - Project Instructions for Claude Code

## Project Overview

**Aquapurite ERP** - A full-stack Consumer Durable ERP system for water purifier manufacturing and distribution.

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (async with psycopg3)
- **Frontend**: Next.js 14+ with TypeScript, Tailwind CSS, shadcn/ui
- **Database**: PostgreSQL (Supabase in production, Docker for local dev)
- **Deployment**: Render.com (Backend API), Vercel (Frontend)

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
└── scripts/                # Utility scripts
```

## Critical Technical Notes

### Database UUID Handling

All tables use **native PostgreSQL UUID** columns (or TEXT in SQLite) for ID fields. This provides:
- Type safety and validation at database level
- Efficient storage (16 bytes vs 36 bytes for VARCHAR)
- Consistent handling across all models

**Key Points:**
- Use `UUID(as_uuid=True)` for all UUID columns in SQLAlchemy models
- Pass UUID objects directly in all queries (ORM and raw SQL)
- PostgreSQL natively handles UUID type - no string conversion needed
- Use `joinedload` instead of `selectinload` for eager loading to avoid psycopg3 issues

Example model definition:
```python
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

class POSerial(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id"),
        nullable=False
    )
```

### Barcode/Serial Number System

**Barcode Format**: `APFSZAIEL00000001` (17 characters for FG, 16 for SP)
- `AP`: Brand prefix (Aquapurite)
- `FS`: Supplier code (2 letters)
- `Z`: Year code (A=2000, Z=2025, AA=2026)
- `A`: Month code (A=Jan, L=Dec)
- `IEL`: Model code (3 letters)
- `00000001`: Serial number (8 digits, continuous per model)

**Key Models:**
- `POSerial`: Individual barcodes linked to PO items
- `ProductSerialSequence`: Tracks last serial per model (continuous, no reset by year/month)
- `ModelCodeReference`: Maps product SKU to 3-letter model code
- `SupplierCode`: Maps vendor to 2-letter supplier code

### Product Item Types

```python
class ProductItemType(str, Enum):
    FINISHED_GOODS = "FG"   # Water Purifiers
    SPARE_PART = "SP"       # Filters, Sub-assemblies
    COMPONENT = "CO"        # Electrical components
    CONSUMABLE = "CN"       # Cartridges, Membranes
    ACCESSORY = "AC"        # Add-ons
```

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

# View PostgreSQL logs
docker-compose logs -f postgres

# Connect to PostgreSQL shell
docker exec -it aquapurite_db psql -U aquapurite -d aquapurite_erp

# Run migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## API Endpoints Reference

### Purchase Orders
- `POST /api/v1/purchase/orders` - Create PO
- `PUT /api/v1/purchase/orders/{id}/approve` - Approve PO (generates serials)
- `GET /api/v1/purchase/orders/{id}/pdf` - Download PO PDF with barcodes
- `GET /api/v1/purchase/orders/{id}/fix-barcodes` - Regenerate serials for PO

### Serialization
- `POST /api/v1/serialization/generate` - Generate serials for PO
- `GET /api/v1/serialization/po/{po_id}/export` - Export barcodes as CSV

## Key Files for Common Tasks

| Task | Files |
|------|-------|
| PO PDF Generation | `app/api/v1/endpoints/purchase.py` (lines 3300-4200) |
| Serial Generation | `app/services/serialization.py` |
| Authentication | `app/services/auth_service.py`, `app/core/security.py` |
| Database Models | `app/models/` |
| API Schemas | `app/schemas/` |

## Testing Approach

1. **Syntax Check**: `python3 -m py_compile app/api/v1/endpoints/purchase.py`
2. **Local Server**: Run with `uvicorn` and test via browser/Postman
3. **Production**: Deploy to Render and test on live database

## Deployment

### Backend (Render)
- Push to `main` branch triggers auto-deploy
- URL: `https://aquapurite-erp-api.onrender.com`
- Uses `DATABASE_URL` env var pointing to Supabase PostgreSQL

### Frontend (Vercel)
- Push to `main` branch triggers auto-deploy
- Uses `NEXT_PUBLIC_API_URL` for backend connection

## Known Issues & Fixes

1. **Login fails after model changes**: Use `joinedload` instead of `selectinload` in auth queries
2. **PDF shows wrong item type**: Eagerly load `product` relationship and check `Product.item_type`
3. **Advance payment shows 0**: Calculate 25% of grand total if `delivery_schedules[0].advance_amount` is 0
4. **Lazy loading errors**: Always use eager loading (`selectinload`, `joinedload`) for relationships accessed in templates

## Code Style

- Use async/await for all database operations
- Pydantic models for request/response validation
- SQLAlchemy 2.0 style with `Mapped` type hints
- Handle Decimal types carefully (use `quantize()` for precision)

## Environment Variables

```env
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
```
