from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_admin
from app.database import get_db
from app.models import Alias, Domain
from app.schemas import AliasCreate, AliasUpdate, AliasResponse

router = APIRouter(prefix="/api/aliases", tags=["aliases"])


@router.get("/", response_model=list[AliasResponse])
async def list_aliases(
    domain_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    query = select(Alias).order_by(Alias.source)
    if domain_id is not None:
        query = query.where(Alias.domain_id == domain_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=AliasResponse, status_code=status.HTTP_201_CREATED)
async def create_alias(data: AliasCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    if "@" not in data.source:
        raise HTTPException(status_code=400, detail="Source must be a full email address")

    domain_name = data.source.split("@")[1].lower()
    result = await db.execute(select(Domain).where(Domain.name == domain_name))
    domain = result.scalar_one_or_none()
    if domain is None:
        raise HTTPException(status_code=400, detail=f"Domain '{domain_name}' not found")

    # Check for duplicate
    existing = await db.execute(
        select(Alias).where(Alias.source == data.source.lower(), Alias.destination == data.destination.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Alias already exists")

    alias = Alias(
        domain_id=domain.id,
        source=data.source.lower(),
        destination=data.destination.lower(),
        active=data.active,
    )
    db.add(alias)
    await db.commit()
    await db.refresh(alias)
    return alias


@router.put("/{alias_id}", response_model=AliasResponse)
async def update_alias(
    alias_id: int, data: AliasUpdate,
    db: AsyncSession = Depends(get_db), _=Depends(require_admin),
):
    result = await db.execute(select(Alias).where(Alias.id == alias_id))
    alias = result.scalar_one_or_none()
    if alias is None:
        raise HTTPException(status_code=404, detail="Alias not found")

    if data.destination is not None:
        alias.destination = data.destination.lower()
    if data.active is not None:
        alias.active = data.active

    await db.commit()
    await db.refresh(alias)
    return alias


@router.delete("/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alias(alias_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(Alias).where(Alias.id == alias_id))
    alias = result.scalar_one_or_none()
    if alias is None:
        raise HTTPException(status_code=404, detail="Alias not found")
    await db.delete(alias)
    await db.commit()
