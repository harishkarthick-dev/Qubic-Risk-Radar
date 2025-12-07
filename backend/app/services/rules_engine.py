"""Rule engine for evaluating events and creating incidents"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import NormalizedEvent
from app.models.rule import Rule
from app.models.incident import Incident, IncidentEvent
from app.logging_config import get_logger
from app.config import settings

logger = get_logger(__name__)


class RuleEngine:
    """Evaluates normalized events against detection rules"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def evaluate_event(self, event: NormalizedEvent) -> List[Incident]:
        """
        Evaluate a normalized event against all active rules
        
        Args:
            event: NormalizedEvent to evaluate
            
        Returns:
            List of created incidents
        """
        if not settings.RULE_EVALUATION_ENABLED:
            return []
        
        # Get all enabled rules
        result = await self.db.execute(
            select(Rule).where(Rule.enabled == True)
        )
        rules = result.scalars().all()
        
        incidents = []
        for rule in rules:
            try:
                if await self._evaluate_rule(event, rule):
                    incident = await self._create_incident(event, rule)
                    if incident:
                        incidents.append(incident)
            except Exception as e:
                logger.error("rule_evaluation_failed", rule_id=str(rule.id), error=str(e))
        
        return incidents
    
    async def _evaluate_rule(self, event: NormalizedEvent, rule: Rule) -> bool:
        """
        Check if event matches rule conditions
        
        Args:
            event: NormalizedEvent to check
            rule: Rule to evaluate
            
        Returns:
            True if event matches rule conditions
        """
        conditions = rule.conditions_json
        
        # Event name match
        if 'event_name' in conditions:
            if event.event_name != conditions['event_name']:
                return False
        
        # Amount threshold
        if 'amount_greater_than' in conditions:
            if not event.amount or event.amount <= conditions['amount_greater_than']:
                return False
        
        if 'amount_less_than' in conditions:
            if not event.amount or event.amount >= conditions['amount_less_than']:
                return False
        
        # Address filters
        if 'from_address' in conditions:
            if event.from_address != conditions['from_address']:
                return False
        
        if 'to_address' in conditions:
            if event.to_address != conditions['to_address']:
                return False
        
        # Contract filter
        if 'contract_address' in conditions:
            if event.contract_address != conditions['contract_address']:
                return False
        
        if 'contract_label' in conditions:
            if event.contract_label != conditions['contract_label']:
                return False
        
        # Token filter
        if 'token_symbol' in conditions:
            if event.token_symbol != conditions['token_symbol']:
                return False
        
        # Transaction status
        if 'tx_status' in conditions:
            if event.tx_status != conditions['tx_status']:
                return False
        
        # Aggregation window check
        if rule.aggregation_window_seconds:
            if not await self._check_aggregation_window(event, rule):
                return False
        
        logger.info(
            "rule_matched",
            rule_name=rule.name,
            event_id=str(event.id),
            event_name=event.event_name
        )
        
        return True
    
    async def _check_aggregation_window(self, event: NormalizedEvent, rule: Rule) -> bool:
        """
        Check if event meets aggregation window thresholds
        
        For example, check if there have been X failures in the last Y seconds
        """
        window_start = event.timestamp - timedelta(seconds=rule.aggregation_window_seconds)
        
        # Count similar events in window
        query = select(func.count(NormalizedEvent.id)).where(
            NormalizedEvent.timestamp >= window_start,
            NormalizedEvent.timestamp <= event.timestamp,
            NormalizedEvent.event_name == event.event_name
        )
        
        if event.contract_address:
            query = query.where(NormalizedEvent.contract_address == event.contract_address)
        
        result = await self.db.execute(query)
        count = result.scalar()
        
        # Check threshold
        thresholds = rule.thresholds_json or {}
        min_count = thresholds.get('min_count', 1)
        
        return count >= min_count
    
    async def _create_incident(self, event: NormalizedEvent, rule: Rule) -> Optional[Incident]:
        """
        Create an incident from a triggered rule
        
        Args:
            event: Triggering event
            rule: Matched rule
            
        Returns:
            Created incident or None if deduplicated
        """
        # Build deduplication key
        dedup_key = None
        if settings.DEDUPLICATION_ENABLED and rule.deduplication_key_template:
            dedup_key = self._build_deduplication_key(event, rule)
            
            # Check if incident with this key exists in cooldown period
            if await self._is_duplicate(dedup_key, rule.cooldown_seconds):
                logger.info("incident_deduplicated", dedup_key=dedup_key)
                return None
        
        # Build incident title and description
        title, description = self._build_incident_content(event, rule)
        
        # Create incident
        incident = Incident(
            severity=rule.severity,
            type=rule.type or 'Unknown',
            title=title,
            description=description,
            protocol=event.contract_label,
            contract_address=event.contract_address,
            primary_wallet=event.from_address,
            first_seen_at=event.timestamp,
            last_seen_at=event.timestamp,
            rule_id=rule.id,
            deduplication_key=dedup_key,
            metadata_json={
                'amount': event.amount,
                'token': event.token_symbol,
                'tx_hash': event.tx_hash,
                'event_name': event.event_name,
            }
        )
        
        self.db.add(incident)
        await self.db.flush()
        
        # Link event to incident
        incident_event = IncidentEvent(
            incident_id=incident.id,
            normalized_event_id=event.id
        )
        self.db.add(incident_event)
        await self.db.commit()
        
        logger.info(
            "incident_created",
            incident_id=str(incident.id),
            severity=incident.severity,
            type=incident.type,
            rule_name=rule.name
        )
        
        return incident
    
    def _build_deduplication_key(self, event: NormalizedEvent, rule: Rule) -> str:
        """Build deduplication key from template"""
        template = rule.deduplication_key_template
        
        replacements = {
            '{from_address}': event.from_address or 'unknown',
            '{to_address}': event.to_address or 'unknown',
            '{contract_address}': event.contract_address or 'unknown',
            '{date}': event.timestamp.strftime('%Y-%m-%d'),
            '{hour}': event.timestamp.strftime('%Y-%m-%d-%H'),
        }
        
        for key, value in replacements.items():
            template = template.replace(key, value)
        
        return template
    
    async def _is_duplicate(self, dedup_key: str, cooldown_seconds: int) -> bool:
        """Check if incident with deduplication key exists in cooldown period"""
        cooldown_cutoff = datetime.utcnow() - timedelta(seconds=cooldown_seconds)
        
        result = await self.db.execute(
            select(Incident).where(
                Incident.deduplication_key == dedup_key,
                Incident.created_at >= cooldown_cutoff
            ).limit(1)
        )
        
        return result.scalar() is not None
    
    def _build_incident_content(self, event: NormalizedEvent, rule: Rule) -> tuple[str, str]:
        """Build incident title and description"""
        
        # Type-specific formatting
        if rule.type == 'WhaleTransfer':
            title = f"Whale Transfer: {event.amount:,} {event.token_symbol}"
            description = (
                f"Large transfer detected on {event.contract_label or 'Qubic network'}.\n\n"
                f"Amount: {event.amount:,} {event.token_symbol}\n"
                f"From: {event.from_address}\n"
                f"To: {event.to_address}\n"
                f"Transaction: {event.tx_hash}"
            )
        elif rule.type == 'FailureSpike':
            title = f"Transaction Failure Spike on {event.contract_label or 'Network'}"
            description = (
                f"Elevated transaction failure rate detected.\n\n"
                f"Contract: {event.contract_address}\n"
                f"Event: {event.event_name}\n"
                f"Status: {event.tx_status}"
            )
        else:
            title = f"{rule.name}"
            description = rule.description or f"Rule '{rule.name}' triggered by event {event.event_name}"
        
        return title, description
