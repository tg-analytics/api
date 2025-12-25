# FastAPI Starter Kit

Simple FastAPI starter template with JWT auth, PostgreSQL via SQLAlchemy, and Alembic migrations.

## Quickstart

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set environment variables (optional) in `.env`:

```
APP_NAME=fastapi-starter-kit
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_DB_PASSWORD=<database-password-from-settings-database>
# Alternatively, you can use the service role key, but prefer the DB password for migrations/local runs.
# SUPABASE_SERVICE_KEY=<service-role-key-from-settings-api>
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

If you use Supabase, set `SUPABASE_URL` to your project URL (ending with `.supabase.co`) and supply either:

- `SUPABASE_DB_PASSWORD`: copy from **Settings → Database → Connection string → Password** (works best for local runs and migrations).
- `SUPABASE_SERVICE_KEY`: the **service_role** key from **Settings → API** (can also unlock Postgres).

When `DATABASE_URL` is not provided, the app will derive the correct Postgres connection string automatically from the Supabase values.

3. Run migrations:

```bash
alembic upgrade head
```

4. Start the API:

```bash
uvicorn app.main:app --reload
```

### Endpoints

- `GET /ping` — public health check
- `GET /public/ping` — health check
- `POST /auth/register` — create user
- `POST /auth/token` — obtain JWT access token
- `GET /protected/me` — current user profile (requires Bearer token)
