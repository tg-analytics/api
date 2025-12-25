from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from postgrest.exceptions import APIError

from app.crud.magic_token import create_magic_token, get_magic_token_by_token, delete_magic_token
from app.crud.user import get_user_by_email
from app.db.base import get_supabase
from app.services.resend import ResendConfigurationError, ResendSendError, send_magic_link_email
from app.schemas.magic_link import MagicLinkRequest, MagicLinkResponse, MagicLinkConfirm
from app.core.security import create_access_token
from app.core.config import get_settings

MAGIC_LINK_EXPIRY_MINUTES = 15

router = APIRouter(prefix="/v1.0", tags=["signin"])


@router.post("/signin", response_model=MagicLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_magic_link(
    payload: MagicLinkRequest, 
    client: Client = Depends(get_supabase)
) -> MagicLinkResponse:
    """Create a magic link for passwordless authentication."""
    try:
        user = await get_user_by_email(client, payload.email)

        token = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_EXPIRY_MINUTES)

        # This will now delete any existing tokens for the email before creating a new one
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
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except APIError as exc:
        # Handle Supabase/PostgREST errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc.message if hasattr(exc, 'message') else str(exc)}"
        ) from exc
    except Exception as exc:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating magic link"
        ) from exc


@router.post("/signin/confirm", status_code=status.HTTP_200_OK)
async def confirm_magic_link(
    payload: MagicLinkConfirm,
    client: Client = Depends(get_supabase)
) -> dict:
    """Confirm a magic link and authenticate the user. Creates user, account, and team member if first time."""
    try:
        # Get the magic token
        magic_token = await get_magic_token_by_token(client, payload.token)
        
        if not magic_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired magic link"
            )
        
        # Check if token has been used
        if magic_token.get("used_at"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This magic link has already been used"
            )
        
        # Check if token has expired
        expires_at = datetime.fromisoformat(magic_token["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires_at:
            # Clean up expired token
            await delete_magic_token(client, payload.token)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This magic link has expired"
            )
        
        email = magic_token["email"]
        
        # Check if user exists
        user = await get_user_by_email(client, email)
        
        # If user doesn't exist, create new user with account and team member
        if not user:
            # Extract name from email (part before @)
            name = email.split("@")[0]
            
            # Create user
            user_data = {
                "email": email,
                "first_name": name,
            }
            user_response = client.table("users").insert(user_data).execute()
            
            if not user_response.data or len(user_response.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
            
            user = user_response.data[0]
            user_id = user["id"]
            
            # Create default account
            account_data = {
                "name": f"{name}'s Account",
                "is_default": True,
                "created_by": user_id,
                "updated_by": user_id,
            }
            account_response = client.table("accounts").insert(account_data).execute()
            
            if not account_response.data or len(account_response.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create account"
                )
            
            account = account_response.data[0]
            account_id = account["id"]
            
            # Create team member with owner role
            team_member_data = {
                "account_id": account_id,
                "user_id": user_id,
                "role": "owner",
                "created_by": user_id,
            }
            team_member_response = client.table("team_members").insert(team_member_data).execute()
            
            if not team_member_response.data or len(team_member_response.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create team member"
                )
        
        # Delete the magic token after successful confirmation
        await delete_magic_token(client, payload.token)
        
        # Create JWT access token
        settings = get_settings()
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user["email"], "user_id": user["id"]}, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user.get("first_name"),
            }
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except APIError as exc:
        # Handle Supabase/PostgREST errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc.message if hasattr(exc, 'message') else str(exc)}"
        ) from exc
    except Exception as exc:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during authentication"
        ) from exc