from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_admin
from app.database import get_db
from app.models import Domain, User
from app.schemas import DomainCreate, DomainUpdate, DomainResponse

router = APIRouter(prefix="/api/domains", tags=["domains"])


@router.get("/", response_model=list[DomainResponse])
async def list_domains(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(
        select(
            Domain,
            func.count(User.id).label("user_count"),
        )
        .outerjoin(User, (User.domain_id == Domain.id) & User.active.is_(True))
        .group_by(Domain.id)
        .order_by(Domain.name)
    )
    domains = []
    for domain, user_count in result.all():
        domains.append(DomainResponse(
            id=domain.id,
            name=domain.name,
            active=domain.active,
            created_at=domain.created_at,
            user_count=user_count,
        ))
    return domains


@router.post("/", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(data: DomainCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    existing = await db.execute(select(Domain).where(Domain.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Domain already exists")

    domain = Domain(name=data.name.lower(), active=data.active)
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    return DomainResponse(
        id=domain.id, name=domain.name, active=domain.active,
        created_at=domain.created_at, user_count=0,
    )


@router.put("/{domain_id}", response_model=DomainResponse)
async def update_domain(
    domain_id: int, data: DomainUpdate,
    db: AsyncSession = Depends(get_db), _=Depends(require_admin),
):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if domain is None:
        raise HTTPException(status_code=404, detail="Domain not found")

    if data.active is not None:
        domain.active = data.active
    await db.commit()
    await db.refresh(domain)

    count_result = await db.execute(
        select(func.count(User.id)).where(User.domain_id == domain.id, User.active.is_(True))
    )
    user_count = count_result.scalar()

    return DomainResponse(
        id=domain.id, name=domain.name, active=domain.active,
        created_at=domain.created_at, user_count=user_count,
    )


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(domain_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if domain is None:
        raise HTTPException(status_code=404, detail="Domain not found")
    await db.delete(domain)
    await db.commit()
