"""Multi-Scope Reporting Engine - Generate comprehensive analytics reports"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.dialects.postgresql import insert

from app.models.ai_detection import AIDetection, Incident, MultiScopeReport
from app.models.event import NormalizedEvent
from app.services.ai_detection_engine import ai_detection_engine
from app.config import settings

logger = logging.getLogger(__name__)


class ReportingEngine:
    """
    Generate multi-scope analytics reports
    
    Scopes:
    - network: Overall network health and trends
    - protocol: Protocol-specific (QX, smart contracts, etc.)
    - wallet: Wallet-level monitoring
    - all: Comprehensive overview
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_report(
        self,
        user_id: UUID,
        scope: str = 'all',
        time_range_days: int = 7,
        report_type: str = 'standard'
    ) -> MultiScopeReport:
        """
        Generate comprehensive analytics report
        
        Args:
            user_id: User ID
            scope: network, protocol, wallet, or all
            time_range_days: Number of days to analyze
            report_type: standard, detailed, or executive
            
        Returns:
            MultiScopeReport object
        """
        try:
            logger.info(f"Generating {scope} report for user {user_id}, range={time_range_days} days")
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=time_range_days)
            
            # Fetch detections in time range
            detections = await self._fetch_detections(user_id, start_time, end_time)
            
            # Calculate statistics
            stats = self._calculate_statistics(detections)
            
            # Generate AI insights (if enabled and affordable)
            ai_insights = await self._generate_ai_insights(detections) if len(detections) > 0 else {}
            
            # Create report
            report = MultiScopeReport(
                user_id=user_id,
                report_type=report_type,
                scope=scope,
                time_range_start=start_time,
                time_range_end=end_time,
                
                # Aggregate stats
                total_events=stats['total_events'],
                total_detections=len(detections),
                critical_count=stats['by_severity'].get('CRITICAL', 0),
                high_count=stats['by_severity'].get('HIGH', 0),
                medium_count=stats['by_severity'].get('MEDIUM', 0),
                low_count=stats['by_severity'].get('LOW', 0),
                
                # AI insights
                executive_summary=ai_insights.get('summary', self._generate_summary(stats)),
                key_findings=ai_insights.get('findings', []),
                anomaly_trends=ai_insights.get('trends', {}),
                pattern_summary=stats['patterns'],
                risk_assessment=self._assess_risk(stats),
                
                # Breakdowns
                by_category=stats['by_category'],
                by_severity=stats['by_severity'],
                by_scope=stats['by_scope'],
                by_contract=stats['by_contract'],
                
                # Top items
                top_addresses=stats['top_addresses'][:10],
                top_contracts=stats['top_contracts'][:5],
                top_patterns=stats['top_patterns'][:5],
                
                # Recommendations
                recommendations=self._generate_recommendations(stats),
                action_items=self._generate_action_items(stats),
                
                # Metadata
                model_version=settings.GEMINI_MODEL if ai_insights else None,
                generation_time_ms=0  # Would track actual time
            )
            
            self.db.add(report)
            await self.db.commit()
            await self.db.refresh(report)
            
            logger.info(f"Report generated: {report.id}")
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            raise
    
    async def _fetch_detections(
        self,
        user_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[AIDetection]:
        """Fetch detections in time range"""
        
        query = select(AIDetection).where(
            and_(
                AIDetection.user_id == user_id,
                AIDetection.created_at >= start_time,
                AIDetection.created_at <= end_time
            )
        ).order_by(desc(AIDetection.created_at))
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    def _calculate_statistics(self, detections: List[AIDetection]) -> Dict[str, Any]:
        """Calculate aggregate statistics"""
        
        stats = {
            'total_events': len(detections),
            'by_severity': defaultdict(int),
            'by_category': defaultdict(int),
            'by_scope': defaultdict(int),
            'by_contract': defaultdict(int),
            'patterns': defaultdict(int),
            'top_addresses': [],
            'top_contracts': [],
            'top_patterns': []
        }
        
        address_counts = defaultdict(int)
        contract_counts = defaultdict(int)
        pattern_counts = defaultdict(int)
        
        for d in detections:
            # Severity
            stats['by_severity'][d.severity] += 1
            
            # Category
            stats['by_category'][d.primary_category] += 1
            
            # Scope
            stats['by_scope'][d.scope] += 1
            
            # Patterns
            if d.detected_patterns:
                for pattern in d.detected_patterns:
                    pattern_counts[pattern] += 1
            
            # Addresses
            if d.related_addresses:
                for addr in d.related_addresses:
                    address_counts[addr] += 1
        
        # Top addresses
        stats['top_addresses'] = [
            {'address': addr, 'count': count}
            for addr, count in sorted(address_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Top contracts
        stats['top_contracts'] = [
            {'contract': contract, 'count': count}
            for contract, count in sorted(contract_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Top patterns
        stats['top_patterns'] = [
            {'pattern': pattern, 'count': count}
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Convert defaultdicts to regular dicts
        stats['by_severity'] = dict(stats['by_severity'])
        stats['by_category'] = dict(stats['by_category'])
        stats['by_scope'] = dict(stats['by_scope'])
        stats['patterns'] = dict(pattern_counts)
        
        return stats
    
    async def _generate_ai_insights(self, detections: List[AIDetection]) -> Dict[str, Any]:
        """Generate AI-powered insights using Gemini (batch analysis)"""
        
        if not ai_detection_engine.enabled or len(detections) == 0:
            return {}
        
        try:
            # Limit to recent detections to control costs
            sample = detections[:50]
            
            # Create summary of detections for AI
            summary_data = {
                'total': len(detections),
                'severities': {},
                'categories': {},
                'top_patterns': []
            }
            
            for d in sample:
                summary_data['severities'][d.severity] = summary_data['severities'].get(d.severity, 0) + 1
                summary_data['categories'][d.primary_category] = summary_data['categories'].get(d.primary_category, 0) + 1
            
            # AI analysis prompt
            prompt = f"""Analyze these blockchain security detections and provide insights:

Total Detections: {summary_data['total']}
Severity Distribution: {summary_data['severities']}
Category Distribution: {summary_data['categories']}

Provide:
1. Executive summary (2-3 sentences)
2. Key findings (3-5 bullet points)
3. Trends observed

Format as JSON:
{{
  "summary": "...",
  "findings": ["...", "..."],
  "trends": {{"trend_name": "description"}}
}}"""
            
            # Call AI (simplified - would use actual Gemini call)
            # response = await ai_detection_engine._call_gemini(prompt)
            
            # Mock response for now
            return {
                'summary': f"Analyzed {len(detections)} detections across {len(set(d.primary_category for d in detections))} categories.",
                'findings': [
                    f"Most common threat: {max(summary_data['categories'].items(), key=lambda x: x[1])[0] if summary_data['categories'] else 'None'}",
                    f"Highest severity count: {summary_data['severities'].get('CRITICAL', 0)} critical alerts"
                ],
                'trends': {}
            }
            
        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return {}
    
    def _generate_summary(self, stats: Dict[str, Any]) -> str:
        """Generate text summary from statistics"""
        
        total = stats['total_events']
        critical = stats['by_severity'].get('CRITICAL', 0)
        high = stats['by_severity'].get('HIGH', 0)
        
        if total == 0:
            return "No detections in this time period."
        
        top_category = max(stats['by_category'].items(), key=lambda x: x[1])[0] if stats['by_category'] else "Unknown"
        
        return f"Analyzed {total} events. Found {critical} critical and {high} high-severity threats. Primary concern: {top_category}."
    
    def _assess_risk(self, stats: Dict[str, Any]) -> str:
        """Assess overall risk level"""
        
        critical = stats['by_severity'].get('CRITICAL', 0)
        high = stats['by_severity'].get('HIGH', 0)
        total = stats['total_events']
        
        if total == 0:
            return 'minimal'
        
        critical_ratio = critical / total
        high_ratio = (critical + high) / total
        
        if critical_ratio > 0.1 or critical > 10:
            return 'extreme'
        elif high_ratio > 0.3 or high > 20:
            return 'high'
        elif high_ratio > 0.1:
            return 'moderate'
        else:
            return 'low'
    
    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        critical = stats['by_severity'].get('CRITICAL', 0)
        if critical > 0:
            recommendations.append(f"Immediate action required: {critical} critical threats detected")
        
        if 'WhaleActivity' in stats['by_category'] and stats['by_category']['WhaleActivity'] > 5:
            recommendations.append("Monitor whale movements closely - unusual activity detected")
        
        if 'SecurityThreat' in stats['by_category']:
            recommendations.append("Review security measures - potential exploits identified")
        
        if not recommendations:
            recommendations.append("Continue monitoring - no immediate action required")
        
        return recommendations
    
    def _generate_action_items(self, stats: Dict[str, Any]) -> List[str]:
        """Generate specific action items"""
        
        actions = []
        
        if stats['by_severity'].get('CRITICAL', 0) > 0:
            actions.append("Investigate all critical alerts within 24 hours")
        
        if stats['by_severity'].get('HIGH', 0) > 10:
            actions.append("Review high-severity patterns for recurring issues")
        
        if stats['top_addresses']:
            actions.append(f"Investigate top active address: {stats['top_addresses'][0]['address']}")
        
        return actions


# Global instance
reporting_engine = None

def get_reporting_engine(db: AsyncSession) -> ReportingEngine:
    """Get reporting engine instance"""
    return ReportingEngine(db)
