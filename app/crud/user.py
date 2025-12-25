from supabase import Client

from app.schemas.user import UserCreate
from app.services.password import get_password_hash, verify_password


async def get_user_by_email(client: Client, email: str) -> dict | None:
    """Get user by email from Supabase."""
    response = client.table("users").select("*").eq("email", email).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def get_user_by_id(client: Client, user_id: str) -> dict | None:
    """Get user by ID from Supabase."""
    response = client.table("users").select("*").eq("id", user_id).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def create_user(client: Client, user_in: UserCreate) -> dict:
    """Create a new user in Supabase."""
    hashed_password = get_password_hash(user_in.password)
    
    user_data = {
        "email": user_in.email,
        "name": user_in.email.split("@")[0],  # Default name from email
        "hashed_password": hashed_password,
    }
    
    response = client.table("users").insert(user_data).execute()
    
    if not response.data or len(response.data) == 0:
        raise ValueError("Failed to create user")
    
    return response.data[0]


async def authenticate_user(client: Client, email: str, password: str) -> dict | None:
    """Authenticate a user with email and password."""
    user = await get_user_by_email(client, email)
    
    if user and verify_password(password, user.get("hashed_password", "")):
        return user
    return None


async def update_user(client: Client, user_id: str, update_data: dict) -> dict | None:
    """Update user data in Supabase."""
    response = client.table("users").update(update_data).eq("id", user_id).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None