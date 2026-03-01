# ShopBridge Backend

REST API for the ShopBridge UK-to-Ghana shopping concierge platform. Built with **FastAPI**, **PostgreSQL** (async), **SQLAlchemy 2**, and **Pydantic V2**.

## Tech Stack

- **Python 3.11+**
- **FastAPI** – API framework
- **SQLAlchemy 2** (async) + **asyncpg** – PostgreSQL
- **Alembic** – migrations
- **Pydantic V2** – validation and settings
- **python-jose** + **passlib (bcrypt)** – JWT and password hashing
- **Redis** – cache / Celery broker (optional)
- **Docker** – containerization

## Project Structure

```
shopbridge-backend/
├── alembic/           # DB migrations
├── app/
│   ├── api/v1/        # Auth, orders, wallet, users, addresses
│   ├── core/          # Config, security, exceptions
│   ├── db/            # Session, Base
│   ├── models/        # User, Address, Order, Wallet, Transaction
│   ├── repositories/  # Data access
│   ├── schemas/       # Pydantic request/response
│   ├── services/      # Business logic
│   └── main.py
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Setup

### 1. Environment

```bash
cp .env.example .env
# Edit .env: set SECRET_KEY, DATABASE_URL, etc.
```

**Required:**

- `DATABASE_URL` – e.g. `postgresql+asyncpg://user:pass@localhost:5432/shopbridge`
- `SECRET_KEY` – e.g. `openssl rand -hex 32`

**Optional:** Paystack, SMTP, Redis, Celery (see `.env.example`).

### 2. Database

PostgreSQL 15+ with async driver:

```bash
# Create DB
createdb shopbridge

# Run migrations (sync URL for Alembic: use psycopg2)
# In .env set for Alembic: DATABASE_URL=postgresql://user:pass@localhost:5432/shopbridge
alembic upgrade head
```

For the first migration, ensure the DB URL in `.env` uses a **sync** driver for Alembic (e.g. `postgresql://` with `psycopg2`). The app uses `postgresql+asyncpg://` for runtime.

### 3. Run API

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  

### 4. Docker

```bash
docker-compose up -d db redis
# Run migrations (from host or a one-off container)
docker-compose up --build api
```

## API Overview

| Area        | Endpoints |
|------------|-----------|
| **Auth**   | `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `POST /api/v1/auth/refresh` |
| **Users**  | `GET /api/v1/users/me` |
| **Addresses** | `GET/POST /api/v1/addresses`, `GET /api/v1/addresses/{id}` |
| **Orders** | `GET/POST /api/v1/orders`, `GET /api/v1/orders/{id}`, `PATCH /api/v1/orders/{id}/cancel` |
| **Wallet** | `GET /api/v1/wallet`, `GET /api/v1/wallet/transactions`, `POST /api/v1/wallet/fund` |

Auth: `Authorization: Bearer <access_token>`.

Responses use JSON; errors return `{"error": {"code": "...", "message": "..."}}` or FastAPI validation detail.

## Auth Flow

1. **Register** – `POST /api/v1/auth/register` with `full_name`, `email`, `phone` (+233…), `password`. Creates user and wallet. Returns `user` + `token`.
2. **Login** – `POST /api/v1/auth/login` with `email`, `password`. Returns `user` + `token`.
3. Use `token` in header: `Authorization: Bearer <token>`.

## Orders

- **Create** – `POST /api/v1/orders` with `OrderCreate` (product_url, product_name, variant_details, quantity, estimated_price_gbp, delivery_address_id, optional special_instructions). Wallet is debited (GHS). Commission 20%.
- **List** – `GET /api/v1/orders?skip=0&limit=20&status=pending`.
- **Get** – `GET /api/v1/orders/{order_id}`.
- **Cancel** – `PATCH /api/v1/orders/{order_id}/cancel` (refunds wallet if pending/assigned).

## Wallet

- Balance in **GHS**. Fund flow is stubbed; integrate Paystack in `POST /api/v1/wallet/fund`.
- Transactions listed at `GET /api/v1/wallet/transactions`.

## Testing

```bash
pip install pytest pytest-asyncio httpx aiosqlite
pytest
```

Tests use in-memory SQLite when available; for full flow use PostgreSQL and adjust `conftest.py` / `TEST_DATABASE_URL`.

## License

Proprietary – ShopBridge.
