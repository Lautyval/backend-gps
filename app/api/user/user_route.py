from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from app.auth.dependencies import get_main_session, get_current_user
from app.api.user.user_model import User
from app.api.user.user_schema import Token, UserCreate, UserResponse
from app.utils.login_user_utils import verify_password, get_password_hash
from app.auth.jwt_handler import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_main_session)
):
    result = await session.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.alive:
        raise HTTPException(status_code=403, detail="Usuario desactivado")
    
    if user.expiration_date and user.expiration_date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="La cuenta ha expirado")

    access_token = create_access_token(data={"sub": str(user.id)})
    
    enterprise = user.enterprises[0] if user.enterprises else None
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "name": user.name,
            "email": user.email,
            "enterprise": enterprise.fullname if enterprise else "N/A",
            "expiration": user.expiration_date
        }
    }

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_main_session)):
    # 1. Verificar si el usuario ya existe
    result = await session.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario registrado con este correo electrónico"
        )
    
    # 2. Hashear contraseña y crear instancia
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        name=user_in.name,
        email=user_in.email,
        password=hashed_password,
        # Por defecto damos 30 días de expiración si no se especifica
        expiration_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30),
        alive=True
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user

@router.get("/me")
async def get_me(current_payload: dict = Depends(get_current_user), session: AsyncSession = Depends(get_main_session)):
    user_id = int(current_payload["sub"])
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    enterprise = user.enterprises[0] if user.enterprises else None
    return {
        "name": user.name,
        "email": user.email,
        "enterprise": enterprise.fullname if enterprise else "N/A",
        "expiration": user.expiration_date
    }
