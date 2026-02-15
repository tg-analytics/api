from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.api import deps
from app.crud.account_settings import (
    get_user_notification_settings,
    get_user_preferences,
    update_user_notification_settings,
    update_user_preferences,
)
from app.crud.user import get_user_with_default_account
from app.db.base import get_supabase
from app.schemas.account_settings import (
    NotificationSettings,
    NotificationSettingsEnvelope,
    NotificationSettingsUpdateRequest,
    UserPreferences,
    UserPreferencesEnvelope,
    UserPreferencesUpdateRequest,
)
from app.schemas.user import UserMeResponse, UserUpdate
from app.services.user import update_user_profile

router = APIRouter(prefix="/v1.0/users", tags=["users"])


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_details(
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase)
) -> UserMeResponse:
    """Get current user details with default account."""
    user_data = await get_user_with_default_account(client, current_user["id"])

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserMeResponse(**user_data)


@router.patch("/me", response_model=UserMeResponse)
async def update_current_user_details(
    payload: UserUpdate,
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase)
) -> UserMeResponse:
    """Update current user's profile information."""
    updated_user = await update_user_profile(client, current_user["id"], payload)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return updated_user


@router.get("/me/preferences", response_model=UserPreferencesEnvelope)
async def get_current_user_preferences(
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> UserPreferencesEnvelope:
    preferences = await get_user_preferences(client, current_user["id"])
    return UserPreferencesEnvelope(data=UserPreferences(**preferences), meta={})


@router.patch("/me/preferences", response_model=UserPreferencesEnvelope)
async def patch_current_user_preferences(
    payload: UserPreferencesUpdateRequest,
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> UserPreferencesEnvelope:
    try:
        updated = await update_user_preferences(
            client,
            current_user["id"],
            payload.model_dump(exclude_none=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return UserPreferencesEnvelope(data=UserPreferences(**updated), meta={})


@router.get("/me/notifications", response_model=NotificationSettingsEnvelope)
async def get_current_user_notification_settings(
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> NotificationSettingsEnvelope:
    settings = await get_user_notification_settings(client, current_user["id"])
    return NotificationSettingsEnvelope(data=NotificationSettings(**settings), meta={})


@router.patch("/me/notifications", response_model=NotificationSettingsEnvelope)
async def patch_current_user_notification_settings(
    payload: NotificationSettingsUpdateRequest,
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> NotificationSettingsEnvelope:
    try:
        updated = await update_user_notification_settings(
            client,
            current_user["id"],
            payload.model_dump(exclude_none=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return NotificationSettingsEnvelope(data=NotificationSettings(**updated), meta={})
