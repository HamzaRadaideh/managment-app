# app/api/services/auths_repositories.py (for imports)
from app.api.repositories.auths_repositories import AuthRepository, get_auth_repository
from app.utility.auth import get_password_hash, verify_password, create_access_token
from app.schemas.models.users_models import User
from fastapi import Depends, HTTPException, status

class AuthService:
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo

    async def register_user(self, user_create_dto) -> User:
        existing_user = await self.auth_repo.get_user_by_username_or_email(
            user_create_dto.username, user_create_dto.email
        )
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username or email already registered"
            )
        hashed_pw = get_password_hash(user_create_dto.password)
        user_data = user_create_dto.dict()
        user_data['password_hash'] = hashed_pw
        # Remove plain text password from data dict if it exists
        user_data.pop('password', None)
        return await self.auth_repo.create_user(user_data)

    async def authenticate_user(self, username: str, password: str) -> User | None:
        user = await self.auth_repo.get_user_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    def create_token_for_user(self, user: User) -> dict:
        access_token = create_access_token(data={"user_id": user.id})
        return {"access_token": access_token, "token_type": "bearer"}

# Dependency
def get_auth_service(
    auth_repo: AuthRepository = Depends(get_auth_repository)
) -> AuthService:
    return AuthService(auth_repo)

