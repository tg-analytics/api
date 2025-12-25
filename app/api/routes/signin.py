from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.config import get_settings
from app.core.security import create_access_token
from app.crud.magic_token import create_magic_token, get_magic_token_by_token, mark_magic_token_used
from app.crud.user import get_user_by_email
from app.db.base import get_supabase
from app.schemas.magic_link import (
    MagicLinkConfirmRequest,
    MagicLinkConfirmResponse,
    MagicLinkRequest,
    MagicLinkResponse,
)
from app.services.resend import ResendConfigurationError, ResendSendError, send_magic_link_email

MAGIC_LINK_EXPIRY_MINUTES = 15

router = APIRouter(prefix="/v1.0/signin", tags=["signin"])


async def create_user_with_account(
    client: Client, email: str, name: str | None = None
) -> dict:
    """Create user, default account, and team member in a transaction."""
    # Create user
    user_data = {
        "email": email,
        "name": name or email.split("@")[0]
    }
    
    user_response = client.table("users").insert(user_data).execute()
    
    if not user_response.data or len(user_response.data) == 0:
        raise ValueError("Failed to create user")
    
    user = user_response.data[0]
    user_id = user["id"]
    
    # Create default account
    account_data = {
        "name": f"{user['name']}'s Workspace",
        "is_default": True,
        "created_by": user_id,
    }
    
    account_response = client.table("accounts").insert(account_data).execute()
    
    if not account_response.data or len(account_response.data) == 0:
        raise ValueError("Failed to create account")
    
    account = account_response.data[0]
    account_id = account["id"]
    
    # Create team member with OWNER role
    team_member_data = {
        "user_id": user_id,
        "account_id": account_id,
        "role": "OWNER",
    }
    
    team_member_response = client.table("team_members").insert(team_member_data).execute()
    
    if not team_member_response.data or len(team_member_response.data) == 0:
        raise ValueError("Failed to create team member")
    
    return user


@router.post("", response_model=MagicLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_magic_link(
    payload: MagicLinkRequest, 
    client: Client = Depends(get_supabase)
) -> MagicLinkResponse:
    """Create a magic link for passwordless authentication."""
    user = await get_user_by_email(client, payload.email)

    token = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_EXPIRY_MINUTES)

    await create_magic_token(
        client,
        email=payload.email,
        token=token,
        expires_at=expires_at,
        user_id=user["id"] if user else None,
    )

    try:
        await send_magic_link_email(
            recipient=payload.email, 
            token=token, 
            expires_at=expires_at
        )
    except ResendConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ResendSendError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return MagicLinkResponse(token=token, expires_at=expires_at)


@router.post("/confirm", response_model=MagicLinkConfirmResponse)
async def confirm_magic_link(
    payload: MagicLinkConfirmRequest,
    client: Client = Depends(get_supabase)
) -> MagicLinkConfirmResponse:
    """Confirm magic link and create user if needed."""
    
    # Get magic token
    magic_token = await get_magic_token_by_token(client, payload.token)
    
    if not magic_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Verify token matches email
    if magic_token["email"] != payload.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token does not match email"
        )
    
    # Check if token is already used
    if magic_token.get("used_at"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has already been used"
        )
    
    # Check if token is expired
    expires_at = datetime.fromisoformat(magic_token["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired"
        )
    
    # Get or create user
    user = await get_user_by_email(client, payload.email)
    
    if not user:
        # Create new user with account and team member
        try:
            user = await create_user_with_account(client, payload.email)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            ) from e
    
    # Mark token as used
    await mark_magic_token_used(client, payload.token)
    
    # Create JWT token
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    expires_at_time = datetime.now(timezone.utc) + access_token_expires
    
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    
    return MagicLinkConfirmResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at_time,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name"),
            "role": user.get("role", "USER"),
            "status": user.get("status", "ACTIVE"),
            "is_guest": user.get("is_guest", False),
        }
    )