"""Events API endpoints"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.models.event import Event, NormalizedEvent
from app.logging_config import get_logger

router = APIRouter(prefix="/events", tags=["events"])
logger = get_logger(__name__)


class NormalizedEventResponse(BaseModel):
    id: UUID
    chain: str
    contract_address: Optional[str]
    contract_label: Optional[str]
    event_name: str
    tx_hash: str
    tx_status: str
    from_address: str
    to_address: str
    amount: Optional[int]
    token_symbol: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    events: list[NormalizedEventResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=EventListResponse)
async def list_events(
    db: AsyncSession = Depends(get_db),
    contract: Optional[str] = Query(None, description="Filter by contract label"),
    event_name: Optional[str] = Query(None, description="Filter by event name"),
    tx_status: Optional[str] = Query(None, description="Filter by transaction status"),
    hours: Optional[int] = Query(None, description="Filter events from last N hours"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    List normalized events with filtering and pagination
    
    Query Parameters:
    - contract: Filter by contract label (e.g., 'QX')
    - event_name: Filter by event name (e.g., 'Transfer')
    - tx_status: Filter by status ('success' or 'failure')
    - hours: Show events from last N hours
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    
    Returns:
        Paginated list of normalized events
    """
    # Build query
    query = select(NormalizedEvent)
    
    # Apply filters
    if contract:
        query = query.where(NormalizedEvent.contract_label == contract)
    
    if event_name:
        query = query.where(NormalizedEvent.event_name == event_name)
    
    if tx_status:
        query = query.where(NormalizedEvent.tx_status == tx_status)
    
    if hours:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = query.where(NormalizedEvent.timestamp >= cutoff)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(desc(NormalizedEvent.timestamp)).limit(page_size).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    events = result.scalars().all()
    
    return EventListResponse(
        events=[NormalizedEventResponse.model_validate(evt) for evt in events],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{event_id}", response_model=NormalizedEventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific event
    
    Path Parameters:
    - event_id: UUID of the normalized event
    
    Returns:
        Event details
    """
    result = await db.execute(
        select(NormalizedEvent).where(NormalizedEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Event not found")
    
    return NormalizedEventResponse.model_validate(event)
