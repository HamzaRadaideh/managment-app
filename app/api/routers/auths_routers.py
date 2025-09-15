# app/api/routers/auths_routers.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.contracts.users_dtos import UserCreate, UserOut, Token
from app.schemas.database import get_async_session
from app.api.repositories.auths_repositories import get_auth_repository
from app.api.services.auths_services import get_auth_service
from app.api.repositories.auths_repositories import AuthRepository
from app.api.services.auths_services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    user: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # The service already has its repository injected via get_auth_service
    registered_user = await auth_service.register_user(user)
    return registered_user

@router.post("/login/query", response_model=Token, include_in_schema=False)
async def login_query(username: str, password: str, auth_service: AuthService = Depends(get_auth_service)):
    user = await auth_service.authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return auth_service.create_token_for_user(user)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_service.create_token_for_user(user)

