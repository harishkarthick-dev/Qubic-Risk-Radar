"""API endpoints for AI Detections"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from pydantic import BaseModel

from app.database import get_db
from app.models.ai_detection import AIDetection, Incident
from app.models.event import NormalizedEvent
from app.models.user import User
from app.api.auth import get_verified_user
from app.logging_config import get_logger

router = APIRouter(prefix="/api/detections", tags=["detections"])
logger = get_logger(__name__)


# Pydantic models for responses
class DetectionResponse(BaseModel):
    id: str
    event_id: str
    severity: str
    anomaly_score: float
    confidence: float
    primary_category: str
    sub_categories: Optional[List[str]] = None
    scope: str
    summary: str
    detailed_analysis: Optional[str] = None
    detected_patterns: Optional[List[str]] = None
    risk_factors: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    related_addresses: Optional[List[str]] = None
    model_version: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    id: str
    detection_id: str
    title: str
    severity: str
    category: str
    scope: str
    status: str
    impact_score: Optional[float] = None
    urgency: Optional[str] = None
    first_detected_at: datetime
    last_updated_at: datetime
    resolved_at: Optional[datetime] = None
    user_notes: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DetectionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    detections: List[DetectionResponse]


class DetectionStatsResponse(BaseModel):
    total_detections: int
    by_severity: dict
    by_category: dict
    by_scope: dict
    avg_anomaly_score: float
    avg_confidence: float


class FeedbackRequest(BaseModel):
    is_accurate: bool
    feedback_text: Optional[str] = None
    suggested_category: Optional[str] = None
    suggested_severity: Optional[str] = None


@router.get("", response_model=DetectionListResponse)
async def list_detections(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    min_anomaly_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List AI detections with filtering and pagination
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - severity: Filter by severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)
    - category: Filter by category
    - scope: Filter by scope (network, protocol, wallet)
    - min_anomaly_score: Minimum anomaly score
    - days: Look back period in days (default: 7, max: 90)
    """
    try:
        # Build base query
        conditions = [AIDetection.user_id == user.id]
        
        # Add time filter
        since = datetime.utcnow() - timedelta(days=days)
        conditions.append(AIDetection.created_at >= since)
        
        # Add optional filters
        if severity:
            conditions.append(AIDetection.severity == severity.upper())
        
        if category:
            conditions.append(AIDetection.primary_category == category)
        
        if scope:
            conditions.append(AIDetection.scope == scope)
        
        if min_anomaly_score is not None:
            conditions.append(AIDetection.anomaly_score >= min_anomaly_score)
        
        # Get total count
        count_query = select(func.count()).select_from(AIDetection).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        offset = (page - 1) * page_size
        query = (
            select(AIDetection)
            .where(and_(*conditions))
            .order_by(desc(AIDetection.created_at))
            .offset(offset)
            .limit(page_size)
        )
        
        result = await db.execute(query)
        detections = result.scalars().all()
        
        return DetectionListResponse(
            total=total,
            page=page,
            page_size=page_size,
            detections=[DetectionResponse.from_orm(d) for d in detections]
        )
        
    except Exception as e:
        logger.error("list_detections_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=DetectionStatsResponse)
async def get_detection_stats(
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detection statistics
    
    Returns aggregated stats for the specified time period
    """
    try:
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get all detections in period
        query = select(AIDetection).where(
            and_(
                AIDetection.user_id == user.id,
                AIDetection.created_at >= since
            )
        )
        result = await db.execute(query)
        detections = result.scalars().all()
        
        # Calculate stats
        total = len(detections)
        
        by_severity = {}
        by_category = {}
        by_scope = {}
        total_anomaly = 0
        total_confidence = 0
        
        for d in detections:
            # Severity
            by_severity[d.severity] = by_severity.get(d.severity, 0) + 1
            
            # Category
            by_category[d.primary_category] = by_category.get(d.primary_category, 0) + 1
            
            # Scope
            by_scope[d.scope] = by_scope.get(d.scope, 0) + 1
            
            # Scores
            total_anomaly += d.anomaly_score
            total_confidence += d.confidence
        
        return DetectionStatsResponse(
            total_detections=total,
            by_severity=by_severity,
            by_category=by_category,
            by_scope=by_scope,
            avg_anomaly_score=total_anomaly / total if total > 0 else 0.0,
            avg_confidence=total_confidence / total if total > 0 else 0.0
        )
        
    except Exception as e:
        logger.error("detection_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{detection_id}", response_model=DetectionResponse)
async def get_detection(
    detection_id: UUID,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific detection
    """
    try:
        query = select(AIDetection).where(
            and_(
                AIDetection.id == detection_id,
                AIDetection.user_id == user.id
            )
        )
        result = await db.execute(query)
        detection = result.scalar_one_or_none()
        
        if not detection:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        return DetectionResponse.from_orm(detection)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_detection_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{detection_id}/feedback")
async def submit_feedback(
    detection_id: UUID,
    feedback: FeedbackRequest,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback on AI detection accuracy
    
    This helps improve the AI model over time
    """
    try:
        # Verify detection exists and belongs to user
        query = select(AIDetection).where(
            and_(
                AIDetection.id == detection_id,
                AIDetection.user_id == user.id
            )
        )
        result = await db.execute(query)
        detection = result.scalar_one_or_none()
        
        if not detection:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        # TODO: Store feedback in feedback table (Phase 2)
        # For now, just log it
        logger.info(
            "detection_feedback_received",
            detection_id=str(detection_id),
            is_accurate=feedback.is_accurate,
            has_text=bool(feedback.feedback_text)
        )
        
        return {
            "status": "success",
            "message": "Feedback received. Thank you for helping improve our AI!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("submit_feedback_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Incidents endpoints
@router.get("/incidents", response_model=List[IncidentResponse])
async def list_incidents(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=180),
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List incidents created from detections
    """
    try:
        conditions = [Incident.user_id == user.id]
        
        since = datetime.utcnow() - timedelta(days=days)
        conditions.append(Incident.created_at >= since)
        
        if status:
            conditions.append(Incident.status == status.lower())
        
        if severity:
            conditions.append(Incident.severity == severity.upper())
        
        query = (
            select(Incident)
            .where(and_(*conditions))
            .order_by(desc(Incident.created_at))
            .limit(100)
        )
        
        result = await db.execute(query)
        incidents = result.scalars().all()
        
        return [IncidentResponse.from_orm(i) for i in incidents]
        
    except Exception as e:
        logger.error("list_incidents_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get incident details"""
    try:
        query = select(Incident).where(
            and_(
                Incident.id == incident_id,
                Incident.user_id == user.id
            )
        )
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        return IncidentResponse.from_orm(incident)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_incident_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


class IncidentUpdateRequest(BaseModel):
    status: Optional[str] = None
    user_notes: Optional[str] = None
    assigned_to: Optional[str] = None


@router.put("/incidents/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    update: IncidentUpdateRequest,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Update incident status, notes, or assignment"""
    try:
        query = select(Incident).where(
            and_(
                Incident.id == incident_id,
                Incident.user_id == user.id
            )
        )
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Update fields
        if update.status is not None:
            incident.status = update.status.lower()
            incident.last_updated_at = datetime.utcnow()
            
            if update.status.lower() == 'resolved':
                incident.resolved_at = datetime.utcnow()
        
        if update.user_notes is not None:
            incident.user_notes = update.user_notes
            incident.last_updated_at = datetime.utcnow()
        
        if update.assigned_to is not None:
            incident.assigned_to = update.assigned_to
            incident.last_updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(incident)
        
        return IncidentResponse.from_orm(incident)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_incident_error", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: UUID,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark incident as resolved"""
    try:
        query = select(Incident).where(
            and_(
                Incident.id == incident_id,
                Incident.user_id == user.id
            )
        )
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        incident.status = 'resolved'
        incident.resolved_at = datetime.utcnow()
        incident.last_updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"status": "success", "message": "Incident resolved"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("resolve_incident_error", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
