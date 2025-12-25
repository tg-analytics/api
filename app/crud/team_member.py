from supabase import Client


async def get_user_default_account_id(client: Client, user_id: str) -> str | None:
    """Get the default account ID for a user."""
    response = client.table("accounts").select("id").eq("created_by", user_id).eq("is_default", True).limit(1).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]["id"]
    return None


async def get_team_members_by_account(client: Client, account_id: str) -> list[dict]:
    """Get all team members for an account with user details."""
    response = (
        client.table("team_members")
        .select("id, role, user_id, created_at, users(name)")
        .eq("account_id", account_id)
        .is_("deleted_at", "null")
        .execute()
    )
    
    members = []
    for member in response.data:
        user_name = None
        if member.get("users") and isinstance(member["users"], dict):
            user_name = member["users"].get("name")
        
        members.append({
            "id": member["id"],
            "role": member["role"],
            "user_id": member["user_id"],
            "name": user_name,
            "joined_at": member["created_at"]
        })
    
    return members


async def check_team_member_exists(client: Client, account_id: str, user_id: str) -> bool:
    """Check if a team member already exists."""
    response = (
        client.table("team_members")
        .select("id")
        .eq("account_id", account_id)
        .eq("user_id", user_id)
        .is_("deleted_at", "null")
        .limit(1)
        .execute()
    )
    
    return response.data and len(response.data) > 0


async def create_team_member(
    client: Client,
    account_id: str,
    user_id: str,
    inviter_id: str,
    role: str = "admin"
) -> dict:
    """Create a new team member."""
    member_data = {
        "account_id": account_id,
        "user_id": user_id,
        "role": role,
        "created_by": inviter_id
    }
    
    response = client.table("team_members").insert(member_data).execute()
    
    if not response.data or len(response.data) == 0:
        raise ValueError("Failed to create team member")
    
    return response.data[0]


async def get_team_member_by_id(client: Client, member_id: str) -> dict | None:
    """Get a team member by ID."""
    response = (
        client.table("team_members")
        .select("*")
        .eq("id", member_id)
        .is_("deleted_at", "null")
        .execute()
    )
    
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def update_team_member(
    client: Client,
    member_id: str,
    update_data: dict
) -> dict | None:
    """Update a team member."""
    response = (
        client.table("team_members")
        .update(update_data)
        .eq("id", member_id)
        .is_("deleted_at", "null")
        .execute()
    )
    
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def soft_delete_team_member(
    client: Client,
    member_id: str,
    deleted_by: str
) -> bool:
    """Soft delete a team member."""
    from datetime import datetime, timezone
    
    update_data = {
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": deleted_by
    }
    
    response = (
        client.table("team_members")
        .update(update_data)
        .eq("id", member_id)
        .is_("deleted_at", "null")
        .execute()
    )
    
    return response.data and len(response.data) > 0