from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password, require_admin
from app.database import get_db
from app.models import Domain, User
from app.schemas import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
async def list_users(
    domain_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    query = select(User).order_by(User.email)
    if domain_id is not None:
        query = query.where(User.domain_id == domain_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    # Validate email format and extract domain
    if "@" not in data.email:
        raise HTTPException(status_code=400, detail="Invalid email format")

    domain_name = data.email.split("@")[1].lower()
    result = await db.execute(select(Domain).where(Domain.name == domain_name, Domain.active.is_(True)))
    domain = result.scalar_one_or_none()
    if domain is None:
        raise HTTPException(status_code=400, detail=f"Domain '{domain_name}' not found or inactive")

    # Check for duplicate
    existing = await db.execute(select(User).where(User.email == data.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already exists")

    user = User(
        domain_id=domain.id,
        email=data.email.lower(),
        password=hash_password(data.password),
        display_name=data.display_name,
        quota=data.quota,
        active=data.active,
        is_admin=data.is_admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, data: UserUpdate,
    db: AsyncSession = Depends(get_db), _=Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if data.password is not None:
        user.password = hash_password(data.password)
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.quota is not None:
        user.quota = data.quota
    if data.active is not None:
        user.active = data.active
    if data.is_admin is not None:
        user.is_admin = data.is_admin

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
