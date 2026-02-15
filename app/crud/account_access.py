from supabase import Client

_WRITE_ROLES = {"owner", "admin"}


async def get_account_membership_role(client: Client, account_id: str, user_id: str) -> str | None:
    response = (
        client.table("team_members")
        .select("role")
        .eq("account_id", account_id)
        .eq("user_id", user_id)
        .eq("status", "accepted")
        .is_("deleted_at", "null")
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    role = response.data[0].get("role")
    if role is None:
        return None
    return str(role).lower()


async def ensure_account_access(
    client: Client,
    *,
    account_id: str,
    header_account_id: str,
    user_id: str,
    require_write: bool = False,
) -> str:
    if account_id != header_account_id:
        raise PermissionError("X-Account-Id must match accountId path parameter")

    role = await get_account_membership_role(client, account_id, user_id)
    if role is None:
        raise PermissionError("You are not a member of this account")

    if require_write and role not in _WRITE_ROLES:
        raise PermissionError("Only owner/admin can update account settings.")

    return role
