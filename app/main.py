from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    account_channels,
    advertisers,
    api_keys,
    auth,
    billing,
    channels,
    home,
    mini_apps,
    notifications,
    protected,
    public,
    rankings,
    signin,
    team_members,
    trackers,
    users,
)
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.api_route("/ping", methods=["GET", "HEAD", "OPTIONS"], tags=["public"])
async def ping() -> dict[str, str]:
    return {"status": "ok"}


# Include routers
app.include_router(public.router)
app.include_router(auth.router)
app.include_router(protected.router)
app.include_router(signin.router)
app.include_router(users.router)
app.include_router(team_members.router)
app.include_router(notifications.router)
app.include_router(channels.router)
app.include_router(home.router)
app.include_router(advertisers.router)
app.include_router(mini_apps.router)
app.include_router(rankings.router)
app.include_router(trackers.router)
app.include_router(account_channels.router)
app.include_router(api_keys.router)
app.include_router(billing.router)


@app.get("/", tags=["public"])
async def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.app_name}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
