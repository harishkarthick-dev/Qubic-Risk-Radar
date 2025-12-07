"""Metrics API endpoints"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.models.event import NormalizedEvent
from app.models.incident import Incident
from app.logging_config import get_logger

router = APIRouter(prefix="/metrics", tags=["metrics"])
logger = get_logger(__name__)


class NetworkHealthResponse(BaseModel):
    """Network health status"""
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    failure_rate: float
    unique_contracts: int
    time_window_hours: int


class TimeSeriesPoint(BaseModel):
    """Single data point in time series"""
    timestamp: datetime
    value: float


class IncidentTimeSeriesResponse(BaseModel):
    """Incident metrics over time"""
    data_points: List[TimeSeriesPoint]
    interval: str


@router.get("/network", response_model=NetworkHealthResponse)
async def get_network_health(
    db: AsyncSession = Depends(get_db),
    hours: int = Query(1, ge=1, le=168, description="Time window in hours")
):
    """
    Get network health metrics
    
    Query Parameters:
    - hours: Time window for metrics (1-168 hours, default: 1)
    
    Returns:
        Network health statistics including transaction counts and failure rate
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Total transactions
    total_result = await db.execute(
        select(func.count(NormalizedEvent.id))
        .where(NormalizedEvent.timestamp >= cutoff)
    )
    total_txs = total_result.scalar() or 0
    
    # Successful transactions
    success_result = await db.execute(
        select(func.count(NormalizedEvent.id))
        .where(
            NormalizedEvent.timestamp >= cutoff,
            NormalizedEvent.tx_status == 'success'
        )
    )
    successful_txs = success_result.scalar() or 0
    
    # Failed transactions
    failed_txs = total_txs - successful_txs
    
    # Failure rate
    failure_rate = (failed_txs / total_txs * 100) if total_txs > 0 else 0.0
    
    # Unique contracts
    contracts_result = await db.execute(
        select(func.count(func.distinct(NormalizedEvent.contract_address)))
        .where(
            NormalizedEvent.timestamp >= cutoff,
            NormalizedEvent.contract_address.isnot(None)
        )
    )
    unique_contracts = contracts_result.scalar() or 0
    
    return NetworkHealthResponse(
        total_transactions=total_txs,
        successful_transactions=successful_txs,
        failed_transactions=failed_txs,
        failure_rate=round(failure_rate, 2),
        unique_contracts=unique_contracts,
        time_window_hours=hours
    )


@router.get("/incidents/timeseries", response_model=IncidentTimeSeriesResponse)
async def get_incident_timeseries(
    db: AsyncSession = Depends(get_db),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    severity: str = Query(None, description="Filter by severity")
):
    """
    Get incident count over time
    
    Query Parameters:
    - hours: Time window (1-168 hours, default: 24)
    - severity: Filter by severity (optional)
    
    Returns:
        Time series of incident counts
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Determine interval based on time window
    if hours <= 24:
        interval = '1 hour'
        interval_name = 'hourly'
    elif hours <= 168:
        interval = '1 day'
        interval_name = 'daily'
    else:
        interval = '1 week'
        interval_name = 'weekly'
    
    # Build query with time bucketing
    query = select(
        func.date_trunc(interval, Incident.first_seen_at).label('bucket'),
        func.count(Incident.id).label('count')
    ).where(
        Incident.first_seen_at >= cutoff
    ).group_by('bucket').order_by('bucket')
    
    if severity:
        query = query.where(Incident.severity == severity.upper())
    
    result = await db.execute(query)
    rows = result.all()
    
    # Format data points
    data_points = [
        TimeSeriesPoint(timestamp=row.bucket, value=float(row.count))
        for row in rows
    ]
    
    return IncidentTimeSeriesResponse(
        data_points=data_points,
        interval=interval_name
    )


@router.get("/whale-activity")
async def get_whale_activity(
    db: AsyncSession = Depends(get_db),
    hours: int = Query(24, description="Time window in hours"),
    min_amount: int = Query(1000000, description="Minimum transfer amount")
):
    """
    Get whale transfer activity
    
    Query Parameters:
    - hours: Time window (default: 24)
    - min_amount: Minimum transfer amount to qualify as whale (default: 1M)
    
    Returns:
        List of large transfers
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    result = await db.execute(
        select(NormalizedEvent)
        .where(
            NormalizedEvent.timestamp >= cutoff,
            NormalizedEvent.event_name == 'Transfer',
            NormalizedEvent.amount >= min_amount
        )
        .order_by(NormalizedEvent.amount.desc())
        .limit(50)
    )
    events = result.scalars().all()
    
    whale_transfers = [
        {
            'id': str(event.id),
            'timestamp': event.timestamp.isoformat(),
            'from_address': event.from_address,
            'to_address': event.to_address,
            'amount': event.amount,
            'token_symbol': event.token_symbol,
            'tx_hash': event.tx_hash,
            'contract': event.contract_label,
        }
        for event in events
    ]
    
    return {
        "time_window_hours": hours,
        "min_amount": min_amount,
        "transfers": whale_transfers,
        "total_count": len(whale_transfers)
    }


@router.get("/protocols/activity")
async def get_protocol_activity(
    db: AsyncSession = Depends(get_db),
    hours: int = Query(24, description="Time window in hours")
):
    """
    Get activity breakdown by protocol
    
    Query Parameters:
    - hours: Time window (default: 24)
    
    Returns:
        Activity statistics per protocol
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    result = await db.execute(
        select(
            NormalizedEvent.contract_label,
            func.count(NormalizedEvent.id).label('event_count'),
            func.sum(NormalizedEvent.amount).label('total_volume')
        )
        .where(
            NormalizedEvent.timestamp >= cutoff,
            NormalizedEvent.contract_label.isnot(None)
        )
        .group_by(NormalizedEvent.contract_label)
        .order_by(func.count(NormalizedEvent.id).desc())
    )
    rows = result.all()
    
    protocols = [
        {
            'protocol': row.contract_label,
            'event_count': row.event_count,
            'total_volume': row.total_volume or 0,
        }
        for row in rows
    ]
    
    return {
        "time_window_hours": hours,
        "protocols": protocols
    }
