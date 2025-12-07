"""Rules management API endpoints"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime
from app.database import get_db
from app.models.rule import Rule
from app.logging_config import get_logger

router = APIRouter(prefix="/rules", tags=["rules"])
logger = get_logger(__name__)


class RuleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    severity: str
    type: Optional[str]
   scope: Optional[str]
    conditions_json: Dict[str, Any]
    aggregation_window_seconds: Optional[int]
    thresholds_json: Optional[Dict[str, Any]]
    deduplication_key_template: Optional[str]
    cooldown_seconds: Optional[int]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RuleCreateRequest(BaseModel):
    name: str = Field(..., description="Unique rule name")
    description: Optional[str] = None
    severity: str = Field(..., description="INFO, WARNING, or CRITICAL")
    type: Optional[str] = Field(None, description="Rule type (e.g., WhaleTransfer)")
    scope: Optional[str] = Field(None, description="network, protocol, or wallet")
    conditions_json: Dict[str, Any] = Field(..., description="Matching conditions")
    aggregation_window_seconds: Optional[int] = Field(60, description="Time window for aggregation")
    thresholds_json: Optional[Dict[str, Any]] = None
    deduplication_key_template: Optional[str] = None
    cooldown_seconds: Optional[int] = Field(300, description="Cooldown period")
    enabled: bool = Field(True, description="Whether rule is active")


class RuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    conditions_json: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


@router.get("", response_model=List[RuleResponse])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    enabled_only: bool = False
):
    """
    List all detection rules
    
    Query Parameters:
    - enabled_only: Only return enabled rules (default: false)
    
    Returns:
        List of rules
    """
    query = select(Rule)
    
    if enabled_only:
        query = query.where(Rule.enabled == True)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return [RuleResponse.model_validate(rule) for rule in rules]


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific rule by ID
    
    Path Parameters:
    - rule_id: UUID of the rule
    
    Returns:
        Rule details
    """
    result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return RuleResponse.model_validate(rule)


@router.post("", response_model=RuleResponse, status_code=201)
async def create_rule(
    rule_data: RuleCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new detection rule
    
    Request Body:
    {
        "name": "Whale Transfer > 1M QUBIC",
        "severity": "CRITICAL",
        "type": "WhaleTransfer",
        "conditions_json": {
            "event_name": "Transfer",
            "amount_greater_than": 1000000
        },
        "deduplication_key_template": "whale_{from_address}_{date}",
        "cooldown_seconds": 300
    }
    
    Returns:
        Created rule
    """
    # Validate severity
    if rule_data.severity not in ['INFO', 'WARNING', 'CRITICAL']:
        raise HTTPException(status_code=400, detail="Invalid severity")
    
    # Check for duplicate name
    existing = await db.execute(
        select(Rule).where(Rule.name == rule_data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Rule with this name already exists")
    
    # Create rule
    rule = Rule(**rule_data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    logger.info("rule_created", rule_id=str(rule.id), name=rule.name)
    
    return RuleResponse.model_validate(rule)


@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    update_data: RuleUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing rule
    
    Path Parameters:
    - rule_id: UUID of the rule
    
    Request Body:
    {
        "enabled": false
    }
    
    Returns:
        Updated rule
    """
    result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(rule, key, value)
    
    await db.commit()
    await db.refresh(rule)
    
    logger.info("rule_updated", rule_id=str(rule_id))
    
    return RuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a rule
    
    Path Parameters:
    - rule_id: UUID of the rule
    
    Returns:
        204 No Content
    """
    result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    await db.delete(rule)
    await db.commit()
    
    logger.info("rule_deleted", rule_id=str(rule_id))
    
    return None
