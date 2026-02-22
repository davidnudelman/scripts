from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_admin
from app.database import get_db
from app.models import Setting
from app.schemas import SettingUpdate, SettingResponse

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/", response_model=list[SettingResponse])
async def list_settings(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(Setting).order_by(Setting.key))
    return result.scalars().all()


@router.put("/", response_model=SettingResponse)
async def update_setting(
    data: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    result = await db.execute(select(Setting).where(Setting.key == data.key))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = Setting(key=data.key, value=data.value)
        db.add(setting)
    else:
        setting.value = data.value
    await db.commit()
    await db.refresh(setting)
    return setting
