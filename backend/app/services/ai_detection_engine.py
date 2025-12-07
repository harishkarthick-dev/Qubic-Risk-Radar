"""AI Detection Engine using Google Gemini"""
import json
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.ai_detection import AIDetection
from app.models.event import NormalizedEvent

logger = logging.getLogger(__name__)


class AIDetectionEngine:
    """
    Gemini-powered AI detection engine for blockchain threat analysis
    
    Analyzes normalized blockchain events and generates:
    - Anomaly scores (0.0-1.0)
    - Severity ratings (CRITICAL/HIGH/MEDIUM/LOW/INFO)
    - Category classification
    - Pattern detection
    - Risk assessment
    - Actionable recommendations
    """
    
    def __init__(self):
        """Initialize Gemini AI model"""
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set - AI detection disabled")
            self.enabled = False
            return
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.enabled = settings.AI_DETECTION_ENABLED
        logger.info(f"AI Detection Engine initialized with model: {settings.GEMINI_MODEL}")
    
    async def analyze_event(
        self,
        event: NormalizedEvent,
        db: AsyncSession
    ) -> Optional[AIDetection]:
        """
        Analyze a normalized event with AI
        
        Args:
            event: Normalized blockchain event
            db: Database session
            
        Returns:
            AIDetection object with analysis results
        """
        if not self.enabled:
            logger.debug("AI detection disabled, skipping analysis")
            return None
        
        # Check if already analyzed
        existing = await db.execute(
            select(AIDetection).where(AIDetection.event_id == event.id)
        )
        if existing.scalar_one_or_none():
            logger.debug(f"Event {event.id} already analyzed, skipping")
            return existing.scalar_one_or_none()
        
        try:
            start_time = time.time()
            
            # Build analysis prompt
            prompt = self._build_detection_prompt(event)
            
            # Get AI analysis
            response = self.model.generate_content(prompt)
            analysis = self._parse_response(response.text)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Create detection record
            detection = AIDetection(
                event_id=event.id,
                user_id=event.user_id,
                anomaly_score=analysis['anomaly_score'],
                severity=analysis['severity'],
                confidence=analysis['confidence'],
                primary_category=analysis['category'],
                sub_categories=analysis.get('sub_categories'),
                scope=self._determine_scope(event, analysis),
                summary=analysis['summary'],
                detailed_analysis=analysis.get('detailed_analysis'),
                detected_patterns=analysis.get('patterns', []),
                risk_factors=analysis.get('risk_factors', []),
                recommendations=analysis.get('recommendations', []),
                related_addresses=analysis.get('related_addresses', []),
                model_version=settings.GEMINI_MODEL,
                processing_time_ms=processing_time
            )
            
            db.add(detection)
            await db.commit()
            await db.refresh(detection)
            
            logger.info(
                f"AI analysis complete for event {event.id}: "
                f"severity={detection.severity}, "
                f"anomaly={detection.anomaly_score:.2f}, "
                f"category={detection.primary_category}"
            )
            
            return detection
            
        except Exception as e:
            logger.error(f"AI analysis failed for event {event.id}: {str(e)}")
            await db.rollback()
            return None
    
    def _build_detection_prompt(self, event: NormalizedEvent) -> str:
        """
        Build comprehensive AI prompt for detection
        
        Prompt includes:
        - Event details
        - Blockchain context
        - Expected output format
        """
        event_data = event.data or {}
        
        prompt = f"""You are an expert blockchain security analyst specializing in Qubic blockchain threat detection.

Analyze this blockchain event for anomalies, threats, and suspicious patterns:

EVENT DETAILS:
- Type: {event.event_type}
- Contract: {event.contract_name or 'None'}
- Amount: {event_data.get('amount', 'N/A')} QUBIC
- From: {event_data.get('from', 'N/A')}
- To: {event_data.get('to', 'N/A')}
- Transaction Hash: {event_data.get('tx_hash', 'N/A')}
- Timestamp: {event.timestamp.isoformat() if event.timestamp else 'N/A'}

CONTEXT:
- Qubic is a high-performance blockchain
- Large transfers (>1M QUBIC) are considered whale activity
- Sudden exchange deposits may indicate sell pressure
- Unusual contract calls may indicate exploits

TASK:
Analyze this event and respond with ONLY a valid JSON object (no markdown, no code blocks) with these exact fields:

{{
  "anomaly_score": <float 0.0-1.0>,
  "severity": "<CRITICAL|HIGH|MEDIUM|LOW|INFO>",
  "confidence": <float 0.0-1.0>,
  "category": "<WhaleActivity|SecurityThreat|ExchangeFlow|UnusualPattern|NetworkAnomaly|ContractEvent|NormalActivity>",
  "sub_categories": [<optional array of specific sub-types>],
  "summary": "<2-3 sentence summary of what happened>",
  "detailed_analysis": "<optional detailed explanation>",
  "patterns": [<array of detected pattern names>],
  "risk_factors": [<array of risk factor descriptions>],
  "recommendations": [<array of suggested actions>],
  "related_addresses": [<array of relevant addresses>]
}}

SCORING GUIDELINES:
- anomaly_score: How unusual (0.0=normal, 1.0=extremely unusual)
- confidence: How certain you are (0.0=uncertain, 1.0=very certain)
- severity based on risk:
  * CRITICAL: Immediate threats, exploits, massive transfers to exchanges
  * HIGH: Large whale movements, unusual contract behavior
  * MEDIUM: Notable activity, minor anomalies
  * LOW: Small deviations from normal
  * INFO: Normal activity worth noting

Return ONLY the JSON object, no additional text."""

        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse AI response into structured data
        
        Handles:
        - JSON extraction from markdown code blocks
        - Validation of required fields
        - Default values for optional fields
        """
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith('```'):
                # Extract JSON from code block
                lines = text.split('\n')
                text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text
                text = text.replace('```json', '').replace('```', '').strip()
            
            analysis = json.loads(text)
            
            # Validate required fields
            required = ['anomaly_score', 'severity', 'confidence', 'category', 'summary']
            for field in required:
                if field not in analysis:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate ranges
            if not 0.0 <= analysis['anomaly_score'] <= 1.0:
                analysis['anomaly_score'] = min(1.0, max(0.0, analysis['anomaly_score']))
            
            if not 0.0 <= analysis['confidence'] <= 1.0:
                analysis['confidence'] = min(1.0, max(0.0, analysis['confidence']))
            
            # Validate severity
            valid_severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
            if analysis['severity'] not in valid_severities:
                analysis['severity'] = 'MEDIUM'
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response text: {response_text}")
            # Return safe default
            return self._get_default_analysis()
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return self._get_default_analysis()
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return safe default analysis when AI fails"""
        return {
            'anomaly_score': 0.5,
            'severity': 'MEDIUM',
            'confidence': 0.3,
            'category': 'UnusualPattern',
            'summary': 'AI analysis unavailable - manual review recommended',
            'patterns': ['ai_analysis_failed'],
            'risk_factors': ['ai_unavailable'],
            'recommendations': ['Review event manually']
        }
    
    def _determine_scope(
        self,
        event: NormalizedEvent,
        analysis: Dict[str, Any]
    ) -> str:
        """
        Determine scope level: network, protocol, or wallet
        
        Network: Affects entire blockchain (consensus, network issues)
        Protocol: Smart contract or protocol-level events
        Wallet: Individual wallet/address activity
        """
        event_type = event.event_type.lower()
        
        # Network-level events
        if any(keyword in event_type for keyword in [
            'network', 'consensus', 'node', 'epoch', 'tick'
        ]):
            return 'network'
        
        # Protocol-level events
        if event.contract_name or any(keyword in event_type for keyword in [
            'contract', 'deploy', 'sc'
        ]):
            return 'protocol'
        
        # Default to wallet-level
        return 'wallet'
    
    async def batch_analyze(
        self,
        events: List[NormalizedEvent],
        db: AsyncSession
    ) -> List[AIDetection]:
        """
        Batch analyze multiple events
        
        More efficient for generating reports
        """
        detections = []
        
        for event in events:
            detection = await self.analyze_event(event, db)
            if detection:
                detections.append(detection)
        
        return detections


# Global instance
ai_detection_engine = AIDetectionEngine()
