from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.auth.dependencies import get_main_session, get_current_user
from app.api.user.user_schema import Token, UserCreate, UserResponse, UserLogin, UserUpdate
from app.utils.login_user_utils import verify_password, get_password_hash
from app.auth.jwt_handler import create_access_token
from app.api.user import user_repository as repository

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    session: AsyncSession = Depends(get_main_session)
):
    user = await repository.get_by_email(session, user_login.email)
    
    if not user or not verify_password(user_login.password, user.password):
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
            "enterprise_id": enterprise.id if enterprise else None,
            "enterprise": enterprise.fullname if enterprise else "N/A",
            "expiration": user.expiration_date
        }
    }

@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_main_session)):
    if await repository.get_by_email(session, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario registrado con este correo electrónico"
        )
    
    hashed_password = get_password_hash(user_in.password)
    user = await repository.create(session, user_in, hashed_password)
    
    # Generate token for immediate login after registration
    access_token = create_access_token(data={"sub": str(user.id)})
    enterprise = user.enterprises[0] if user.enterprises else None
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "name": user.name,
            "email": user.email,
            "enterprise_id": enterprise.id if enterprise else None,
            "enterprise": enterprise.fullname if enterprise else "N/A",
            "expiration": user.expiration_date
        }
    }


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    hashed_password = None
    if user_in.password:
        hashed_password = get_password_hash(user_in.password)
    
    db_user = await repository.update(session, user_id, user_in, hashed_password)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    success = await repository.deactivate(session, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"status": "deactivated"}

@router.get("/me")
async def get_me(current_payload: dict = Depends(get_current_user), session: AsyncSession = Depends(get_main_session)):
    user_id = int(current_payload["sub"])
    user = await repository.get_by_id(session, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    enterprise = user.enterprises[0] if user.enterprises else None
    return {
        "name": user.name,
        "email": user.email,
        "enterprise_id": enterprise.id if enterprise else None,
        "enterprise": enterprise.fullname if enterprise else "N/A",
        "expiration": user.expiration_date
    }

