from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database.session import get_db
from app.modules.authentication.service import AuthService
from app.modules.authentication.schemas import (
    LoginRequest, LoginResponse, UserResponse, ChangePasswordRequest,
    BootstrapRequest, BootstrapResponse
)
from app.shared.security.auth_dependencies import get_current_user
from app.modules.authentication.models import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/bootstrap", response_model=BootstrapResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap(request: BootstrapRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.bootstrap(request)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.login(request)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.change_password(str(current_user.id), request)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    return None