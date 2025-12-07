"""EasyConnect configuration management API"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.easyconnect_config import EasyConnectConfig
from app.dependencies.auth import get_verified_user
from app.services.auth import create_verification_token  # Reuse for webhook secrets
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/easyconnect", tags=["EasyConnect"])


# Request/Response models
class EasyConnectConfigCreate(BaseModel):
    alert_id: str = Field(..., description="EasyConnect alert ID")
    contract_address: str | None = None
    contract_label: str | None = None
    event_type: str | None = None
    description: str | None = None
    conditions_json: dict = {}


class EasyConnectConfigUpdate(BaseModel):
    is_active: bool | None = None
    description: str | None = None


class EasyConnectConfigResponse(BaseModel):
    id: str
    alert_id: str
    webhook_secret: str
    contract_address: str | None
    contract_label: str | None
    event_type: str | None
    description: str | None
    conditions_json: dict
    is_active: bool
    created_at: str
    updated_at: str


@router.get("/configs", response_model=List[EasyConnectConfigResponse])
async def list_configs(
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all EasyConnect configurations for current user
    """
    result = await db.execute(
        select(EasyConnectConfig)
        .where(EasyConnectConfig.user_id == user.id)
        .order_by(EasyConnectConfig.created_at.desc())
    )
    configs = result.scalars().all()
    
    return [
        {
            "id": str(config.id),
            "alert_id": config.alert_id,
            "webhook_secret": config.webhook_secret,
            "contract_address": config.contract_address,
            "contract_label": config.contract_label,
            "event_type": config.event_type,
            "description": config.description,
            "conditions_json": config.conditions_json or {},
            "is_active": config.is_active,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }
        for config in configs
    ]


@router.post("/configs", response_model=EasyConnectConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    data: EasyConnectConfigCreate,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new EasyConnect configuration
    
    - Generates unique webhook secret per config
    - User provides alert_id from EasyConnect dashboard
    """
    # Check if alert_id already exists for this user
    result = await db.execute(
        select(EasyConnectConfig).where(
            EasyConnectConfig.user_id == user.id,
            EasyConnectConfig.alert_id == data.alert_id
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert ID already configured"
        )
    
    # Generate webhook secret
    webhook_secret = create_verification_token()
    
    # Create config
    config = EasyConnectConfig(
        user_id=user.id,
        alert_id=data.alert_id,
        webhook_secret=webhook_secret,
        contract_address=data.contract_address,
        contract_label=data.contract_label,
        event_type=data.event_type,
        description=data.description,
        conditions_json=data.conditions_json or {}
    )
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    logger.info("easyconnect_config_created", user_id=str(user.id), alert_id=data.alert_id)
    
    return {
        "id": str(config.id),
        "alert_id": config.alert_id,
        "webhook_secret": config.webhook_secret,
        "contract_address": config.contract_address,
        "contract_label": config.contract_label,
        "event_type": config.event_type,
        "description": config.description,
        "conditions_json": config.conditions_json or {},
        "is_active": config.is_active,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat()
    }


@router.patch("/configs/{config_id}", response_model=EasyConnectConfigResponse)
async def update_config(
    config_id: str,
    data: EasyConnectConfigUpdate,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update EasyConnect configuration
    
    - Can toggle active/inactive
    - Can update description
    """
    result = await db.execute(
        select(EasyConnectConfig).where(
            EasyConnectConfig.id == config_id,
            EasyConnectConfig.user_id == user.id
        )
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    # Update fields
    if data.is_active is not None:
        config.is_active = data.is_active
    if data.description is not None:
        config.description = data.description
    
    await db.commit()
    await db.refresh(config)
    
    logger.info("easyconnect_config_updated", config_id=config_id, user_id=str(user.id))
    
    return {
        "id": str(config.id),
        "alert_id": config.alert_id,
        "webhook_secret": config.webhook_secret,
        "contract_address": config.contract_address,
        "contract_label": config.contract_label,
        "event_type": config.event_type,
        "description": config.description,
        "conditions_json": config.conditions_json or {},
        "is_active": config.is_active,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat()
    }


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: str,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete EasyConnect configuration
    """
    result = await db.execute(
        select(EasyConnectConfig).where(
            EasyConnectConfig.id == config_id,
            EasyConnectConfig.user_id == user.id
        )
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    await db.delete(config)
    await db.commit()
    
    logger.info("easyconnect_config_deleted", config_id=config_id, user_id=str(user.id))
