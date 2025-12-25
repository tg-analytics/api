from fastapi import FastAPI

from app.api.routes import auth, protected, public
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.get("/ping", tags=["public"])
async def ping() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(public.router)
app.include_router(auth.router)
app.include_router(protected.router)
