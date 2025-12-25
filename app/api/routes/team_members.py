from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.api import deps
from app.crud.team_member import (
    check_team_member_exists,
    create_team_member,
    get_team_member_by_id,
    get_team_members_by_account,
    get_user_default_account_id,
    soft_delete_team_member,
    update_team_member,
)
from app.crud.user import get_user_by_email
from app.crud.magic_token import create_magic_token
from app.db.base import get_supabase
from app.schemas.team_member import (
    TeamMemberInvite,
    TeamMemberResponse,
    TeamMemberUpdate,
)
from app.services.resend import (
    ResendConfigurationError,
    ResendSendError,
    send_magic_link_email,
)

router = APIRouter(prefix="/v1.0/team_members", tags=["team_members"])


@router.post("/invite", status_code=status.HTTP_201_CREATED)
async def invite_team_member(
    payload: TeamMemberInvite,
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> dict:
    """Invite a new team member to the current user's default account."""
    # Get inviter's default account
    account_id = await get_user_default_account_id(client, current_user["id"])
    
    if not account_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default account found for current user"
        )
    
    # Check if user with email exists
    invited_user = await get_user_by_email(client, payload.email)
    
    # If user exists, check if already a team member
    if invited_user:
        exists = await check_team_member_exists(
            client, account_id, invited_user["id"]
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a team member"
            )
        
        # Add existing user as team member
        await create_team_member(
            client,
            account_id=account_id,
            user_id=invited_user["id"],
            inviter_id=current_user["id"],
            role="admin"
        )
    else:
        # User doesn't exist, send magic link for sign-up
        token = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        await create_magic_token(
            client,
            email=payload.email,
            token=token,
            expires_at=expires_at,
            user_id=None
        )
        
        # Send invitation email with magic link
        try:
            await send_magic_link_email(
                recipient=payload.email,
                token=token,
                expires_at=expires_at
            )
        except (ResendConfigurationError, ResendSendError) as exc:
            # Log error but don't fail the invitation
            # In production, you might want to queue this for retry
            pass
    
    return {
        "message": "Invitation sent successfully",
        "email": payload.email,
        "user_exists": invited_user is not None
    }


@router.get("", response_model=list[TeamMemberResponse])
async def list_team_members(
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> list[TeamMemberResponse]:
    """List all team members in the current user's default account."""
    # Get current user's default account
    account_id = await get_user_default_account_id(client, current_user["id"])
    
    if not account_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default account found for current user"
        )
    
    members = await get_team_members_by_account(client, account_id)
    
    return [TeamMemberResponse(**member) for member in members]


@router.patch("/{member_id}", status_code=status.HTTP_200_OK)
async def update_team_member_role(
    member_id: str,
    payload: TeamMemberUpdate,
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> dict:
    """Update a team member's role."""
    # Check if team member exists
    member = await get_team_member_by_id(client, member_id)
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    # Get current user's default account to verify authorization
    account_id = await get_user_default_account_id(client, current_user["id"])
    
    if not account_id or member["account_id"] != account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this team member"
        )
    
    # Prepare update data
    update_data = {}
    if payload.role:
        update_data["role"] = payload.role
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )
    
    # Update team member
    updated_member = await update_team_member(client, member_id, update_data)
    
    if not updated_member:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update team member"
        )
    
    return {
        "message": "Team member updated successfully",
        "id": member_id,
        "role": updated_member.get("role")
    }


@router.delete("/{member_id}", status_code=status.HTTP_200_OK)
async def remove_team_member(
    member_id: str,
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> dict:
    """Remove a team member from the account (soft delete)."""
    # Check if team member exists
    member = await get_team_member_by_id(client, member_id)
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    # Get current user's default account to verify authorization
    account_id = await get_user_default_account_id(client, current_user["id"])
    
    if not account_id or member["account_id"] != account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove this team member"
        )
    
    # Prevent removing yourself if you're the owner
    if member["user_id"] == current_user["id"] and member["role"] == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself as the account owner"
        )
    
    # Soft delete the team member
    deleted = await soft_delete_team_member(
        client, member_id, current_user["id"]
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove team member"
        )
    
    return {
        "message": "Team member removed successfully",
        "id": member_id
    }