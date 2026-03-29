from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_admin
from app.database import get_db
from app.dkim import generate_dkim_keypair, public_key_to_dns_record, write_dkim_key_to_disk, delete_dkim_key_from_disk
from app.models import Domain, DkimKey
from app.schemas import DkimKeyCreate, DkimKeyResponse

router = APIRouter(prefix="/api/domains/{domain_id}/dkim", tags=["dkim"])


@router.get("/", response_model=list[DkimKeyResponse])
async def list_dkim_keys(
    domain_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    domain = await _get_domain(domain_id, db)
    result = await db.execute(
        select(DkimKey).where(DkimKey.domain_id == domain_id).order_by(DkimKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        DkimKeyResponse(
            id=k.id,
            selector=k.selector,
            public_key=k.public_key,
            key_size=k.key_size,
            active=k.active,
            dns_record=public_key_to_dns_record(k.public_key, k.selector, domain.name),
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.post("/", response_model=DkimKeyResponse, status_code=status.HTTP_201_CREATED)
async def generate_dkim_key(
    domain_id: int,
    data: DkimKeyCreate = DkimKeyCreate(),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    domain = await _get_domain(domain_id, db)

    # Deactivate existing keys with the same selector
    existing = await db.execute(
        select(DkimKey).where(
            DkimKey.domain_id == domain_id,
            DkimKey.selector == data.selector,
            DkimKey.active.is_(True),
        )
    )
    for old_key in existing.scalars().all():
        old_key.active = False

    # Generate new keypair
    private_pem, public_pem = generate_dkim_keypair(data.key_size)

    # Save to database
    dkim_key = DkimKey(
        domain_id=domain.id,
        selector=data.selector,
        private_key=private_pem,
        public_key=public_pem,
        key_size=data.key_size,
        active=True,
    )
    db.add(dkim_key)
    await db.commit()
    await db.refresh(dkim_key)

    # Write private key to disk for Rspamd
    write_dkim_key_to_disk(domain.name, data.selector, private_pem)

    dns_record = public_key_to_dns_record(public_pem, data.selector, domain.name)

    return DkimKeyResponse(
        id=dkim_key.id,
        selector=dkim_key.selector,
        public_key=dkim_key.public_key,
        key_size=dkim_key.key_size,
        active=dkim_key.active,
        dns_record=dns_record,
        created_at=dkim_key.created_at,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dkim_key(
    domain_id: int, key_id: int,
    db: AsyncSession = Depends(get_db), _=Depends(require_admin),
):
    domain = await _get_domain(domain_id, db)
    result = await db.execute(
        select(DkimKey).where(DkimKey.id == key_id, DkimKey.domain_id == domain_id)
    )
    key = result.scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=404, detail="DKIM key not found")

    delete_dkim_key_from_disk(domain.name, key.selector)
    await db.delete(key)
    await db.commit()


async def _get_domain(domain_id: int, db: AsyncSession) -> Domain:
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if domain is None:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain
