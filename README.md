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
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

3. Run migrations:

```bash
alembic upgrade head
```

4. Start the API:

```bash
uvicorn app.main:app --reload
```

### Endpoints

- `GET /public/ping` — health check
- `POST /auth/register` — create user
- `POST /auth/token` — obtain JWT access token
- `GET /protected/me` — current user profile (requires Bearer token)
