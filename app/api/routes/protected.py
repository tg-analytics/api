from fastapi import APIRouter, Depends

from app.api import deps
from app.schemas.user import UserRead

router = APIRouter(prefix="/protected", tags=["protected"])


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user=Depends(deps.get_current_user)):
    return current_user
