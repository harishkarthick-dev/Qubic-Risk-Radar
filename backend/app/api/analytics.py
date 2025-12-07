"""API endpoints for analytics and reports"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from pydantic import BaseModel

from app.database import get_db
from app.models.ai_detection import MultiScopeReport, AIDetection
from app.models.user import User
from app.api.auth import get_verified_user
from app.services.reporting_engine import get_reporting_engine
from app.logging_config import get_logger

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
logger = get_logger(__name__)


# Pydantic models
class ReportGenerateRequest(BaseModel):
    scope: str = 'all'  # network, protocol, wallet, or all
    time_range_days: int = 7
    report_type: str = 'standard'  # standard, detailed, or executive


class ReportResponse(BaseModel):
    id: str
    scope: str
    report_type: str
    time_range_start: datetime
    time_range_end: datetime
    total_detections: int
    critical_count: int
    high_count: int
    executive_summary: Optional[str]
    risk_assessment: Optional[str]
    generated_at: datetime
    
    class Config:
        from_attributes = True


class DetailedReportResponse(ReportResponse):
    key_findings: Optional[List[str]]
    by_category: Optional[dict]
    by_severity: Optional[dict]
    top_addresses: Optional[List[dict]]
    top_patterns: Optional[List[dict]]
    recommendations: Optional[List[str]]
    action_items: Optional[List[str]]
    
    class Config:
        from_attributes = True


class AnalyticsOverview(BaseModel):
    total_detections: int
    detections_today: int
    detections_this_week: int
    by_severity: dict
    by_category: dict
    trend_7days: List[dict]


@router.post("/reports/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerateRequest,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new analytics report
    
    Scopes:
    - all: Comprehensive overview
    - network: Network-level analysis
    - protocol: Protocol-specific (QX, contracts)
    - wallet: Wallet-level monitoring
    
    Types:
    - standard: Basic statistics and insights
    - detailed: Full breakdown with AI analysis
    - executive: High-level summary for decision makers
    """
    try:
        engine = get_reporting_engine(db)
        
        report = await engine.generate_report(
            user_id=user.id,
            scope=request.scope,
            time_range_days=request.time_range_days,
            report_type=request.report_type
        )
        
        return ReportResponse.from_orm(report)
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    scope: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """List generated reports"""
    try:
        conditions = [MultiScopeReport.user_id == user.id]
        
        if scope:
            conditions.append(MultiScopeReport.scope == scope)
        
        query = (
            select(MultiScopeReport)
            .where(and_(*conditions))
            .order_by(desc(MultiScopeReport.generated_at))
            .limit(limit)
        )
        
        result = await db.execute(query)
        reports = result.scalars().all()
        
        return [ReportResponse.from_orm(r) for r in reports]
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}", response_model=DetailedReportResponse)
async def get_report(
    report_id: UUID,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed report"""
    try:
        query = select(MultiScopeReport).where(
            and_(
                MultiScopeReport.id == report_id,
                MultiScopeReport.user_id == user.id
            )
        )
        
        result = await db.execute(query)
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return DetailedReportResponse.from_orm(report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics overview and trends"""
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        
        # Total detections
        total_query = select(func.count()).select_from(AIDetection).where(
            AIDetection.user_id == user.id
        )
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        # Today's detections
        today_query = select(func.count()).select_from(AIDetection).where(
            and_(
                AIDetection.user_id == user.id,
                AIDetection.created_at >= today_start
            )
        )
        today_result = await db.execute(today_query)
        today = today_result.scalar()
        
        # This week
        week_query = select(func.count()).select_from(AIDetection).where(
            and_(
                AIDetection.user_id == user.id,
                AIDetection.created_at >= week_start
            )
        )
        week_result = await db.execute(week_query)
        week = week_result.scalar()
        
        # Fetch all detections for breakdown
        all_query = select(AIDetection).where(AIDetection.user_id == user.id)
        all_result = await db.execute(all_query)
        all_detections = all_result.scalars().all()
        
        # Calculate breakdowns
        by_severity = {}
        by_category = {}
        
        for d in all_detections:
            by_severity[d.severity] = by_severity.get(d.severity, 0) + 1
            by_category[d.primary_category] = by_category.get(d.primary_category, 0) + 1
        
        # 7-day trend
        trend = []
        for i in range(7):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_count = sum(1 for d in all_detections if day_start <= d.created_at < day_end)
            
            trend.append({
                'date': day_start.isoformat(),
                'count': day_count
            })
        
        trend.reverse()  # Chronological order
        
        return AnalyticsOverview(
            total_detections=total,
            detections_today=today,
            detections_this_week=week,
            by_severity=by_severity,
            by_category=by_category,
            trend_7days=trend
        )
        
    except Exception as e:
        logger.error(f"Error getting overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/severity")
async def get_severity_stats(
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get severity distribution over time"""
    try:
        start_time = datetime.utcnow() - timedelta(days=days)
        
        query = select(AIDetection).where(
            and_(
                AIDetection.user_id == user.id,
                AIDetection.created_at >= start_time
            )
        )
        
        result = await db.execute(query)
        detections = result.scalars().all()
        
        by_severity = {}
        for d in detections:
            by_severity[d.severity] = by_severity.get(d.severity, 0) + 1
        
        return {
            'time_range_days': days,
            'total': len(detections),
            'by_severity': by_severity
        }
        
    except Exception as e:
        logger.error(f"Error getting severity stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/categories")
async def get_category_stats(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get top categories"""
    try:
        start_time = datetime.utcnow() - timedelta(days=days)
        
        query = select(AIDetection).where(
            and_(
                AIDetection.user_id == user.id,
                AIDetection.created_at >= start_time
            )
        )
        
        result = await db.execute(query)
        detections = result.scalars().all()
        
        categories = {}
        for d in detections:
            categories[d.primary_category] = categories.get(d.primary_category, 0) + 1
        
        top_categories = sorted(
            categories.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return {
            'time_range_days': days,
            'categories': [
                {'name': cat, 'count': count}
                for cat, count in top_categories
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting category stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/timeline")
async def get_timeline_trend(
    days: int = Query(30, ge=7, le=90),
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detection timeline trend"""
    try:
        start_time = datetime.utcnow() - timedelta(days=days)
        
        query = select(AIDetection).where(
            and_(
                AIDetection.user_id == user.id,
                AIDetection.created_at >= start_time
            )
        ).order_by(AIDetection.created_at)
        
        result = await db.execute(query)
        detections = result.scalars().all()
        
        # Group by day
        daily_counts = {}
        for d in detections:
            day = d.created_at.date().isoformat()
            daily_counts[day] = daily_counts.get(day, 0) + 1
        
        timeline = [
            {'date': day, 'count': count}
            for day, count in sorted(daily_counts.items())
        ]
        
        return {
            'time_range_days': days,
            'timeline': timeline,
            'total_detections': len(detections)
        }
        
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))
