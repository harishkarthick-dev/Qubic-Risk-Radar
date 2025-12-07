"""Incident management API endpoints"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.database import get_db
from app.models.incident import Incident, IncidentEvent
from app.models.event import NormalizedEvent
from app.logging_config import get_logger

router = APIRouter(prefix="/incidents", tags=["incidents"])
logger = get_logger(__name__)


# Pydantic schemas
class IncidentResponse(BaseModel):
    id: UUID
    severity: str
    status: str
    type: str
    title: str
    description: Optional[str]
    protocol: Optional[str]
    contract_address: Optional[str]
    primary_wallet: Optional[str]
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime
    metadata_json: Optional[dict]
    
    class Config:
        from_attributes = True


class IncidentDetailResponse(IncidentResponse):
    """Extended incident response with related events"""
    related_events: List[dict] = Field(default_factory=list)


class IncidentUpdateRequest(BaseModel):
    status: Optional[str] = None  # 'acknowledged', 'resolved'


class IncidentListResponse(BaseModel):
    incidents: List[IncidentResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    db: AsyncSession = Depends(get_db),
    severity: Optional[str] = Query(None, description="Filter by severity: INFO, WARNING, CRITICAL"),
    status: Optional[str] = Query(None, description="Filter by status: open, acknowledged, resolved"),
    protocol: Optional[str] = Query(None, description="Filter by protocol name"),
    type: Optional[str] = Query(None, description="Filter by incident type"),
    hours: Optional[int] = Query(None, description="Filter incidents from last N hours"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    List incidents with filtering and pagination
    
    Query Parameters:
    - severity: Filter by severity (INFO, WARNING, CRITICAL)
    - status: Filter by status (open, acknowledged, resolved)
    - protocol: Filter by protocol name
    - type: Filter by incident type
    - hours: Show incidents from last N hours
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    
    Returns:
        Paginated list of incidents
    """
    # Build query
    query = select(Incident)
    
    # Apply filters
    if severity:
        query = query.where(Incident.severity == severity.upper())
    
    if status:
        query = query.where(Incident.status == status.lower())
    
    if protocol:
        query = query.where(Incident.protocol == protocol)
    
    if type:
        query = query.where(Incident.type == type)
    
    if hours:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = query.where(Incident.first_seen_at >= cutoff)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(desc(Incident.first_seen_at)).limit(page_size).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    incidents = result.scalars().all()
    
    return IncidentListResponse(
        incidents=[IncidentResponse.model_validate(inc) for inc in incidents],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific incident
    
    Path Parameters:
    - incident_id: UUID of the incident
    
    Returns:
        Incident details with related events
    """
    # Get incident
    result = await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get related events
    events_result = await db.execute(
        select(NormalizedEvent)
        .join(IncidentEvent, IncidentEvent.normalized_event_id == NormalizedEvent.id)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(NormalizedEvent.timestamp)
    )
    events = events_result.scalars().all()
    
    # Format response
    response_data = IncidentResponse.model_validate(incident).model_dump()
    response_data['related_events'] = [
        {
            'id': str(event.id),
            'event_name': event.event_name,
            'tx_hash': event.tx_hash,
            'from_address': event.from_address,
            'to_address': event.to_address,
            'amount': event.amount,
            'token_symbol': event.token_symbol,
            'timestamp': event.timestamp.isoformat(),
            'tx_status': event.tx_status,
        }
        for event in events
    ]
    
    return response_data


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    update: IncidentUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update incident status (acknowledge or resolve)
    
    Path Parameters:
    - incident_id: UUID of the incident
    
    Request Body:
    {
        "status": "acknowledged" | "resolved"
    }
    
    Returns:
        Updated incident
    """
    # Get incident
    result = await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Update fields
    if update.status:
        if update.status not in ['open', 'acknowledged', 'resolved']:
            raise HTTPException(status_code=400, detail="Invalid status")
        incident.status = update.status
    
    await db.commit()
    await db.refresh(incident)
    
    logger.info(
        "incident_updated",
        incident_id=str(incident_id),
        status=incident.status
    )
    
    return IncidentResponse.model_validate(incident)


@router.get("/stats/summary")
async def get_incident_stats(
    db: AsyncSession = Depends(get_db),
    hours: int = Query(24, description="Time window in hours")
):
    """
    Get incident statistics
    
    Query Parameters:
    - hours: Time window for statistics (default: 24)
    
    Returns:
        Incident counts by severity and status
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Count by severity
    severity_result = await db.execute(
        select(
            Incident.severity,
            func.count(Incident.id).label('count')
        )
        .where(Incident.first_seen_at >= cutoff)
        .group_by(Incident.severity)
    )
    severity_counts = {row.severity: row.count for row in severity_result}
    
    # Count by status
    status_result = await db.execute(
        select(
            Incident.status,
            func.count(Incident.id).label('count')
        )
        .where(Incident.first_seen_at >= cutoff)
        .group_by(Incident.status)
    )
    status_counts = {row.status: row.count for row in status_result}
    
    # Total count
    total_result = await db.execute(
        select(func.count(Incident.id))
        .where(Incident.first_seen_at >= cutoff)
    )
    total = total_result.scalar()
    
    return {
        "time_window_hours": hours,
        "total_incidents": total,
        "by_severity": {
            "CRITICAL": severity_counts.get('CRITICAL', 0),
            "WARNING": severity_counts.get('WARNING', 0),
            "INFO": severity_counts.get('INFO', 0),
        },
        "by_status": {
            "open": status_counts.get('open', 0),
            "acknowledged": status_counts.get('acknowledged', 0),
            "resolved": status_counts.get('resolved', 0),
        }
    }
