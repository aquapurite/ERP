# CLAUDE.md - Aquapurite ERP System Reference

> **Purpose**: This document is the single source of truth for understanding the Aquapurite ERP codebase structure, architecture standards, and development guidelines.

---

## Project Overview

**Aquapurite ERP** - A full-stack Consumer Durable ERP system for water purifier manufacturing and distribution.

| Layer | Technology | Description |
|-------|------------|-------------|
| **Backend** | FastAPI + SQLAlchemy + psycopg3 | Async Python API with PostgreSQL |
| **Frontend** | Next.js 14+ TypeScript | React framework with App Router |
| **UI Components** | Tailwind CSS + shadcn/ui | Modern component library |
| **Database** | PostgreSQL (Supabase) | Production database with Row Level Security |
| **Backend Hosting** | Render.com | Auto-deploy from main branch |
| **Frontend Hosting** | Vercel | Auto-deploy from main branch |

### Production URLs

| Service | URL |
|---------|-----|
| ERP Admin Panel | https://www.aquapurite.org |
| D2C Storefront | https://www.aquapurite.com |
| Backend API | https://aquapurite-erp-api.onrender.com |
| API Documentation | https://aquapurite-erp-api.onrender.com/docs |
| Health Check | https://aquapurite-erp-api.onrender.com/health |

---

## Project Structure

```
/Users/mantosh/Desktop/Consumer durable 2/
├── app/                          # FastAPI Backend
│   ├── api/v1/
│   │   ├── endpoints/            # 76 API route files
│   │   └── router.py             # Main router registration
│   ├── models/                   # 58 SQLAlchemy ORM models
│   ├── schemas/                  # 65 Pydantic request/response schemas
│   ├── services/                 # 53 Business logic services
│   ├── core/                     # Security, config, utilities
│   │   ├── config.py             # Settings from environment
│   │   ├── security.py           # JWT & password hashing
│   │   └── enum_utils.py         # Status/enum helpers
│   └── database.py               # Async database session
├── frontend/                     # Next.js Frontend
│   └── src/
│       ├── app/
│       │   ├── dashboard/        # 26 ERP admin sections
│       │   └── (storefront)/     # 15 D2C customer pages
│       ├── components/           # Reusable UI components
│       ├── lib/api/              # 71 API client modules
│       ├── config/navigation.ts  # Menu structure with permissions
│       └── types/                # TypeScript interfaces
├── alembic/                      # Database migrations
├── scripts/                      # Utility scripts
└── CLAUDE.md                     # This file
```

---

## Backend Architecture

### Layer Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│                     API ENDPOINTS                           │
│  app/api/v1/endpoints/*.py                                  │
│  - HTTP request handling                                    │
│  - Input validation via Pydantic schemas                    │
│  - Authorization checks                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     SERVICES                                │
│  app/services/*.py                                          │
│  - Business logic                                           │
│  - Cross-entity operations                                  │
│  - External integrations (Razorpay, Shiprocket, GST)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     MODELS                                  │
│  app/models/*.py                                            │
│  - SQLAlchemy ORM definitions                               │
│  - Database table mappings                                  │
│  - Relationships and constraints                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATABASE                                │
│  PostgreSQL (Supabase)                                      │
│  - 200+ tables                                              │
│  - JSONB for flexible data                                  │
│  - TIMESTAMPTZ for all timestamps                           │
└─────────────────────────────────────────────────────────────┘
```

### API Modules (76 endpoint files)

| Category | Endpoints |
|----------|-----------|
| **Auth & Access** | auth, users, roles, permissions, access_control |
| **Product Catalog** | products, categories, brands, serialization |
| **Orders & CRM** | orders, customers, leads, call_center |
| **Inventory** | inventory, warehouses, transfers, stock_adjustments |
| **Procurement** | vendors, purchase, grn, vendor_invoices, vendor_proformas |
| **Finance** | accounting, billing, banking, tds, auto_journal |
| **Logistics** | shipments, manifests, transporters, serviceability, rate_cards |
| **Service** | service_requests, technicians, installations, amc |
| **Channels** | channels, marketplaces, channel_reports |
| **CMS** | cms, storefront |
| **HR** | hr (employees, attendance, payroll, leave) |
| **Analytics** | insights, ai, dashboard_charts, reports |

### Models (58 model files)

Key domain models:
- `product.py` - Product catalog with variants, specs, images
- `order.py` - Orders, order items, order history
- `customer.py` - Customer profiles, addresses
- `inventory.py` - Stock items, movements, reservations
- `vendor.py` - Vendor management, ledger
- `accounting.py` - GL accounts, journal entries, periods
- `channel.py` - Sales channels, pricing, inventory

### Services (53 service files)

Key business logic:
- `order_service.py` - Order creation, status management
- `inventory_service.py` - Stock management, allocations
- `pricing_service.py` - Channel pricing, rules engine
- `invoice_service.py` - Invoice generation, GST calculation
- `serialization.py` - Barcode generation, serial tracking

---

## Frontend Architecture

### Dashboard Sections (26 modules)

| Section | Path | Description |
|---------|------|-------------|
| **Dashboard** | `/dashboard` | Overview, KPIs, charts |
| **Sales** | `/dashboard/orders` | Orders, channels, distribution |
| **CRM** | `/dashboard/crm` | Customers, leads, call center |
| **Inventory** | `/dashboard/inventory` | Stock, movements, transfers |
| **Procurement** | `/dashboard/procurement` | Vendors, POs, GRN |
| **Finance** | `/dashboard/finance` | GL, invoices, banking, tax |
| **Logistics** | `/dashboard/logistics` | Shipments, manifests, tracking |
| **Service** | `/dashboard/service` | Service requests, warranty, AMC |
| **HR** | `/dashboard/hr` | Employees, payroll, attendance |
| **Master Data** | `/dashboard/catalog` | Products, categories, brands |
| **CMS** | `/dashboard/cms` | D2C content management |

### Storefront Pages (15 pages)

| Page | Path | Description |
|------|------|-------------|
| Products | `/products` | Product catalog with filters |
| Product Detail | `/products/[slug]` | Product page with reviews |
| Cart | `/cart` | Shopping cart |
| Checkout | `/checkout` | Payment flow |
| Account | `/account` | Customer profile, orders |
| Track Order | `/track/order/[orderNumber]` | Public order tracking |

### API Client Structure

```typescript
// frontend/src/lib/api/index.ts

// 71 API modules organized by domain
export const authApi = { login, logout, refreshToken, ... };
export const productsApi = { list, get, create, update, ... };
export const ordersApi = { list, create, updateStatus, ... };
export const customersApi = { list, get, create, ... };
export const inventoryApi = { getStock, getMovements, ... };
export const channelsApi = { list, getPricing, updatePricing, ... };
// ... 65 more API modules
```

### Navigation Configuration

```typescript
// frontend/src/config/navigation.ts

// Menu structure with permission-based access
const navigation = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Sales',
    icon: ShoppingCart,
    permissions: ['ORDERS_VIEW'],
    children: [
      { title: 'Orders', href: '/dashboard/orders' },
      { title: 'Channels', href: '/dashboard/channels' },
      // ...
    ],
  },
  // ... more sections
];
```

---

## Database Standards

### Data Types

| Use Case | Type | Example |
|----------|------|---------|
| Primary Keys | `UUID` | Most tables |
| Primary Keys (legacy) | `VARCHAR(36)` | franchisees, po_serials |
| Status Fields | `VARCHAR(50)` | NEVER use PostgreSQL ENUM |
| JSON Data | `JSONB` | NEVER use JSON |
| Timestamps | `TIMESTAMPTZ` | NEVER use TIMESTAMP |
| Money | `NUMERIC(18,2)` | Exact decimal precision |
| Percentages | `NUMERIC(5,2)` | e.g., 99.99% |

### Status Values

All status fields use UPPERCASE VARCHAR strings:

| Status Type | Values |
|-------------|--------|
| Order Status | NEW, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED |
| Payment Status | PENDING, PAID, PARTIALLY_PAID, REFUNDED, FAILED |
| Invoice Status | DRAFT, APPROVED, GENERATED, PAID, CANCELLED |

### SQLAlchemy Patterns

```python
# Model definition
from sqlalchemy import String, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
import uuid

class Order(Base):
    __tablename__ = "orders"

    # UUID primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Status as VARCHAR (not ENUM)
    status: Mapped[str] = mapped_column(String(50), default="NEW")

    # Timestamps with timezone
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # JSON data as JSONB
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
```

### Pydantic Schema Patterns

```python
# Response schema - inherit from BaseResponseSchema
from app.schemas.base import BaseResponseSchema
from uuid import UUID

class OrderResponse(BaseResponseSchema):
    """Response schema - inherits UUID serialization."""
    id: UUID
    status: str
    total_amount: Decimal

# Create/Update schema - add validators here
class OrderCreate(BaseModel):
    customer_id: UUID
    items: List[OrderItemCreate]

    @field_validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('Order must have at least one item')
        return v
```

---

## Coding Standards

### Rule 1: Response Schema Completeness

Every field returned by a service MUST be defined in the response schema.

```python
# ❌ BAD - Field silently dropped
# Service returns: {"total_orders": 38, "total_customers": 20}
# Schema only has: total_orders: int
# Result: total_customers is lost!

# ✅ GOOD - All fields defined
class OrderSummary(BaseModel):
    total_orders: int
    total_customers: int  # Include ALL fields
```

### Rule 2: Validator Placement

NEVER put validators on Base schemas. Only on Create/Update schemas.

```python
# ❌ BAD - Breaks GET responses
class CompanyBase(BaseModel):
    @field_validator('logo_url')
    def validate_url(cls, v): ...  # Runs on responses too!

# ✅ GOOD - Only validates inputs
class CompanyCreate(CompanyBase):
    @field_validator('logo_url')
    def validate_url(cls, v): ...
```

### Rule 3: Timezone-Aware Datetime

ALWAYS use `datetime.now(timezone.utc)`, NEVER `datetime.utcnow()`.

```python
from datetime import datetime, timezone

# ❌ BAD - Timezone-naive
created_at = datetime.utcnow()

# ✅ GOOD - Timezone-aware
created_at = datetime.now(timezone.utc)
```

### Rule 4: Field Naming Consistency

Use EXACT same field names across backend and frontend.

```
Backend Service → Pydantic Schema → Frontend Type
total_orders      total_orders       total_orders   ✓ SAME
```

### Rule 5: Category Hierarchy

Products are assigned to LEAF categories (subcategories), not parent categories.

```
✅ CORRECT: Product → "RO+UV Water Purifiers" (subcategory)
❌ WRONG:   Product → "Water Purifiers" (parent)
```

Implement cascading dropdowns: Parent Category → Subcategory → Products

### Rule 6: Database Structure Verification (CRITICAL)

**Before implementing any new feature or modification, ALWAYS verify the database structure in Supabase:**

1. **Check if required tables exist** in production database
2. **Check if required columns exist** with correct data types
3. **Supabase is the SINGLE SOURCE OF TRUTH** - SQLAlchemy models must match

```bash
# Verify database structure using Python script:
python3 -c "
import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host='db.aavjhutqzwusgdwrczds.supabase.co',
        port=6543,
        user='postgres',
        password='Aquapurite2026',
        database='postgres',
        statement_cache_size=0
    )

    # Check table columns
    cols = await conn.fetch('''
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'YOUR_TABLE_NAME'
        ORDER BY ordinal_position
    ''')
    for c in cols:
        print(f'{c[\"column_name\"]}: {c[\"data_type\"]}')

    await conn.close()

asyncio.run(main())
"
```

**If table/column doesn't exist:**
- Create migration in Supabase SQL Editor first
- Then update SQLAlchemy model to match
- NEVER assume database schema matches model

**Common checks:**
| Change Type | Verify |
|------------|--------|
| New model field | Column exists in table |
| Foreign key | Referenced table/column exists |
| New table | Table created in Supabase |
| Data type change | Column type matches |

---

## Development Guide

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop (for local PostgreSQL)

### Local Development

```bash
# 1. Start local PostgreSQL
cd "/Users/mantosh/Desktop/Consumer durable 2"
docker-compose up -d

# 2. Run backend
uvicorn app.main:app --reload --port 8000

# 3. Run frontend (separate terminal)
cd frontend
pnpm dev
```

### Environment Variables

Create `.env` file in project root:

```env
# Database (local Docker)
DATABASE_URL=postgresql+psycopg://aquapurite:aquapurite@localhost:5432/aquapurite_erp

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Supabase (for storage)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_STORAGE_BUCKET=uploads
```

### Supabase Production Database

```
Host: db.aavjhutqzwusgdwrczds.supabase.co
Port: 6543
Database: postgres
User: postgres
Password: Aquapurite2026

Connection String:
postgresql://postgres:Aquapurite2026@db.aavjhutqzwusgdwrczds.supabase.co:6543/postgres
```

### Pre-Deployment Checklist

Before pushing any code:

1. **Build frontend**: `cd frontend && pnpm build`
2. **Test locally**: Start both servers and verify changes
3. **Verify API health**: `curl http://localhost:8000/health`
4. **Check for TypeScript errors**: Build must pass
5. **Commit and push**: `git push origin main`

---

## Rules of Engagement (Development Workflow)

Follow these practices for efficient and safe deployments:

### MANDATORY PRE-DEPLOYMENT CHECKLIST

**NEVER push to production without completing ALL steps:**

| Step | Action | Command/Location |
|------|--------|------------------|
| 1 | **Build Frontend** | `cd frontend && pnpm build` |
| 2 | **Start Local Backend** | `uvicorn app.main:app --reload --port 8000` |
| 3 | **Start Local Frontend** | `cd frontend && pnpm dev` |
| 4 | **Test Affected Pages** | Open browser, test the specific feature |
| 5 | **Test API Endpoints** | Use real data, check request/response |
| 6 | **Verify Database Schema** | Check Supabase matches model (SINGLE SOURCE OF TRUTH) |
| 7 | **Push to Production** | `git push origin main` |
| 8 | **Verify Production** | Test on live site after deploy completes |

```bash
# Complete workflow example:
cd "/Users/mantosh/Desktop/Consumer durable 2"

# Step 1: Build frontend
cd frontend && pnpm build
cd ..

# Step 2-3: Start local servers (in separate terminals)
# Terminal 1:
uvicorn app.main:app --reload --port 8000

# Terminal 2:
cd frontend && pnpm dev

# Step 4-5: Test in browser at http://localhost:3000
# - Navigate to affected pages
# - Test with real data
# - Check browser console for errors
# - Check backend terminal for errors

# Step 6: If database changes needed, verify Supabase schema first

# Step 7: Only after ALL tests pass
git add -A && git commit -m "message" && git push origin main

# Step 8: Wait for deploy, then verify on production
```

### Why This Matters

- **Step 1 (Build)**: Catches TypeScript errors before deploy
- **Step 4-5 (Test Locally)**: Catches 90% of bugs
- **Step 6 (Schema)**: Supabase is the source of truth - models must match
- **Step 8 (Verify Production)**: Confirms deploy worked correctly

### 2. Use Smart Deployments

Configuration is already set up to skip unnecessary deployments:

**Vercel** (`vercel.json`):
- Skips deployment if only backend files changed
- Deploys only when `frontend/` directory has changes

**Render** (configure in dashboard):
- Go to Render Dashboard → aquapurite-api service
- Settings → Build & Deploy → Auto-Deploy
- Add to "Ignored Paths": `frontend/**`
- This skips backend rebuild when only frontend files change

### 3. Batch Related Changes

Instead of pushing after every small fix:

```bash
# ❌ BAD - 5 separate deployments
git commit -m "Fix typo"
git push
# wait 5 mins...
git commit -m "Fix another thing"
git push
# wait 5 mins...

# ✅ GOOD - 1 deployment with all fixes
git commit -m "Fix typo in orders"
git commit -m "Fix validation in products"
git commit -m "Update category tree view"
git push  # Single deployment with all changes
```

### 4. Use Feature Branches (Best Practice)

For larger changes, use feature branches:

```bash
# Create feature branch
git checkout -b feature/new-category-tree

# Make multiple commits
git commit -m "Add tree structure"
git commit -m "Add expand/collapse"
git commit -m "Style improvements"

# When ready, merge to main and push
git checkout main
git merge feature/new-category-tree
git push  # Single deployment
```

### 5. Separate Backend and Frontend Commits

Group changes by deployment target:

```bash
# ✅ GOOD - Isolated deployments
git commit -m "Backend: Fix product API response"
git commit -m "Frontend: Update category page"
git push

# Smart deployment will:
# - Deploy backend only if app/ changed
# - Deploy frontend only if frontend/ changed
```

### Summary

| Practice | Benefit |
|----------|---------|
| Test locally first | Catch issues before deployment |
| Smart deployments | Skip unnecessary rebuilds |
| Batch changes | Fewer deployment cycles |
| Feature branches | Keep main stable |
| Separate commits | Isolated deployments |

---

## Deployment

> **CRITICAL**: Always deploy from the PROJECT ROOT directory, NOT from frontend/

### Git Repository

```
Repository: git@github.com:aquapurite/ERP.git
Branch: main
Remote: origin
```

### Vercel Configuration (Frontend)

**IMPORTANT: There are 3 Vercel projects - use the CORRECT one!**

| Project Name | Domain | Purpose | Deploy From |
|--------------|--------|---------|-------------|
| `erp` | **www.aquapurite.org** | ERP Admin Panel | Project Root |
| `d2c` | www.aquapurite.com | D2C Storefront | Project Root |
| `frontend` | ❌ DO NOT USE | Old/test project | - |

**Vercel Account Details:**
- Team/Scope: `anupam-singhs-projects-ffea0ac8`
- Account: Run `npx vercel whoami` to verify

### Deploy ERP Frontend (www.aquapurite.org)

```bash
# ALWAYS run from project root, NOT from frontend/
cd "/Users/mantosh/Desktop/Consumer durable 2"

# Step 1: Link to the correct project (erp, NOT frontend)
npx vercel link --project=erp --yes

# Step 2: Deploy to production
npx vercel --prod

# Expected output should show:
# Aliased: https://www.aquapurite.org
```

### Deploy D2C Storefront (www.aquapurite.com)

```bash
cd "/Users/mantosh/Desktop/Consumer durable 2"
npx vercel link --project=d2c --yes
npx vercel --prod
```

### Backend (Render.com)

**Service Details:**
- Service Name: `aquapurite-erp-api`
- URL: https://aquapurite-erp-api.onrender.com
- Health Check: https://aquapurite-erp-api.onrender.com/health
- API Docs: https://aquapurite-erp-api.onrender.com/docs

**Deployment:**
- Render auto-deploys when code is pushed to `main` branch on GitHub
- If auto-deploy is not working, manually trigger from Render Dashboard:
  1. Go to https://dashboard.render.com
  2. Select `aquapurite-erp-api` service
  3. Click "Manual Deploy" → "Deploy latest commit"

### Complete Deployment Checklist

```bash
# 1. Commit and push changes
cd "/Users/mantosh/Desktop/Consumer durable 2"
git add .
git commit -m "your message"
git push origin main

# 2. Deploy frontend to Vercel (ERP)
npx vercel link --project=erp --yes
npx vercel --prod
# Verify: https://www.aquapurite.org

# 3. Backend auto-deploys to Render
# Verify: curl https://aquapurite-erp-api.onrender.com/health
```

### Troubleshooting Deployment Issues

**Wrong Vercel project?**
```bash
# Check current linked project
cat .vercel/project.json

# Re-link to correct project
npx vercel link --project=erp --yes
```

**Render not auto-deploying?**
1. Check GitHub connection in Render Dashboard
2. Verify branch is set to `main`
3. Use Manual Deploy as fallback

---

## Key Business Flows

### Order-to-Cash Flow

```
CREATE ORDER → PAY → ALLOCATE → PICK → PACK → SHIP → DELIVER → INVOICE → GL
```

### Procurement Flow (P2P)

```
REQUISITION → PO → APPROVE → RECEIVE (GRN) → 3-WAY MATCH → VENDOR INVOICE → PAYMENT
```

### Serialization Flow

```
PO APPROVED → SERIALS GENERATED → GRN ACCEPT → STOCK ITEMS CREATED → BARCODE TRACKING
```

### Barcode Format

`APFSZAIEL00000001` (17 characters for FG)
- `AP`: Brand prefix (Aquapurite)
- `FS`: Supplier code (2 letters)
- `Z`: Year code (A=2000, Z=2025)
- `A`: Month code (A=Jan, L=Dec)
- `IEL`: Model code (3 letters)
- `00000001`: Serial number (8 digits)

---

## Governance Rules

### Rule 1: No Autonomous Decisions

Claude will NOT make decisions without explicit user approval. Always present options and wait for "proceed" or "go ahead".

### Rule 2: Gap Analysis First

Before implementing, audit what exists:
1. Check backend APIs
2. Check frontend pages
3. Check database tables
4. Present findings for review

### Rule 3: End-to-End Verification

Every feature must be traced: Database → Model → Schema → API → Frontend Page → Component

### Rule 4: Backward Compatibility

Always check:
- Will existing data work with new validation?
- Will existing API consumers break?
- Are response schemas compatible?

---

## Quick Reference

### Common Commands

```bash
# Build frontend
cd frontend && pnpm build

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Check API health
curl https://aquapurite-erp-api.onrender.com/health

# Connect to production database
psql "postgresql://postgres:Aquapurite2026@db.aavjhutqzwusgdwrczds.supabase.co:6543/postgres"
```

### File Locations

| What | Where |
|------|-------|
| API Endpoints | `app/api/v1/endpoints/` |
| SQLAlchemy Models | `app/models/` |
| Pydantic Schemas | `app/schemas/` |
| Business Services | `app/services/` |
| Dashboard Pages | `frontend/src/app/dashboard/` |
| Storefront Pages | `frontend/src/app/(storefront)/` |
| API Clients | `frontend/src/lib/api/` |
| Navigation Config | `frontend/src/config/navigation.ts` |
| Types/Interfaces | `frontend/src/types/` |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Backend API Files | 76 |
| SQLAlchemy Models | 58 |
| Pydantic Schemas | 65 |
| Business Services | 53 |
| Dashboard Sections | 26 |
| Storefront Pages | 15 |
| Frontend API Clients | 71 |
| Database Tables | 200+ |

---

*Last Updated: 2026-01-28*
