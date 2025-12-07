"""Classification Engine for multi-dimensional categorization"""
import logging
from typing import Dict, List, Set, Any
from app.models.ai_detection import AIDetection
from app.models.event import NormalizedEvent

logger = logging.getLogger(__name__)


class ClassificationEngine:
    """
    Automatic classification and scope detection
    
    Provides:
    - Multi-dimensional categorization
    - Scope determination (network/protocol/wallet)
    - Tag generation
    - Risk level calculation
    """
    
    # Category definitions
    CATEGORIES = {
        'WhaleActivity': {
            'description': 'Large value transfers by whale addresses',
            'keywords': ['whale', 'large', 'massive', 'huge'],
            'min_amount': 1000000  # 1M QUBIC
        },
        'SecurityThreat': {
            'description': 'Potential security threats or exploits',
            'keywords': ['exploit', 'attack', 'vulnerability', 'suspicious', 'malicious'],
            'severity_bias': 'CRITICAL'
        },
        'ExchangeFlow': {
            'description': 'Transfers to/from exchange addresses',
            'keywords': ['exchange', 'binance', 'coinbase', 'kraken'],
            'patterns': ['to_exchange', 'from_exchange']
        },
        'UnusualPattern': {
            'description': 'Anomalous or unusual activity',
            'keywords': ['unusual', 'anomaly', 'strange', 'unexpected'],
            'default': True
        },
        'NetworkAnomaly': {
            'description': 'Network-level issues',
            'keywords': ['network', 'consensus', 'node', 'propagation'],
            'scope': 'network'
        },
        'ContractEvent': {
            'description': 'Smart contract interactions',
            'keywords': ['contract', 'deploy', 'call', 'execute'],
            'scope': 'protocol'
        },
        'NormalActivity': {
            'description': 'Normal blockchain activity',
            'keywords': ['normal', 'regular', 'routine'],
            'severity_cap': 'LOW'
        }
    }
    
    def classify(
        self,
        detection: AIDetection,
        event: NormalizedEvent
    ) -> Dict[str, Any]:
        """
        Perform multi-dimensional classification
        
        Returns:
            Dictionary with classification results
        """
        result = {
            'primary_category': detection.primary_category,
            'sub_categories': self._generate_sub_categories(detection, event),
            'scope': detection.scope,
            'tags': self._generate_tags(detection, event),
            'risk_level': self._calculate_risk_level(detection),
            'priority': self._calculate_priority(detection)
        }
        
        logger.debug(f"Classification complete: {result}")
        return result
    
    def _generate_sub_categories(
        self,
        detection: AIDetection,
        event: NormalizedEvent
    ) -> List[str]:
        """Generate specific sub-categories"""
        sub_cats = set()
        
        event_data = event.data or {}
        amount = event_data.get('amount', 0)
        
        # Amount-based
        if amount > 10000000:  # >10M
            sub_cats.add('MegaWhale')
        elif amount > 1000000:  # >1M
            sub_cats.add('Whale')
        
        # Pattern-based
        if detection.detected_patterns:
            for pattern in detection.detected_patterns:
                if 'exchange' in pattern.lower():
                    sub_cats.add('ExchangeRelated')
                if 'accumulation' in pattern.lower():
                    sub_cats.add('Accumulation')
                if 'dump' in pattern.lower() or 'sell' in pattern.lower():
                    sub_cats.add('PotentialSellPressure')
        
        # Contract-based
        if event.contract_name:
            sub_cats.add('SmartContractInteraction')
        
        return list(sub_cats)
    
    def _generate_tags(
        self,
        detection: AIDetection,
        event: NormalizedEvent
    ) -> List[str]:
        """Generate descriptive tags"""
        tags = set()
        
        # Severity tag
        tags.add(detection.severity.lower())
        
        # Category tag
        tags.add(detection.primary_category.lower().replace(' ', '_'))
        
        # Scope tag
        tags.add(f"scope_{detection.scope}")
        
        # Anomaly score tags
        if detection.anomaly_score >= 0.8:
            tags.add('highly_anomalous')
        elif detection.anomaly_score >= 0.5:
            tags.add('anomalous')
        
        # Confidence tags
        if detection.confidence >= 0.8:
            tags.add('high_confidence')
        elif detection.confidence < 0.5:
            tags.add('low_confidence')
        
        # Event type tag
        if event.event_type:
            tags.add(event.event_type.lower().replace(' ', '_'))
        
        # Contract tag
        if event.contract_name:
            tags.add(f"contract_{event.contract_name.lower()}")
        
        # Pattern tags
        if detection.detected_patterns:
            for pattern in detection.detected_patterns[:3]:  # Max 3 pattern tags
                tags.add(pattern.lower().replace(' ', '_'))
        
        return sorted(list(tags))
    
    def _calculate_risk_level(self, detection: AIDetection) -> str:
        """
        Calculate overall risk level
        
        Combines:
        - Anomaly score
        - Severity
        - Confidence
        """
        # Risk matrix
        if detection.severity == 'CRITICAL' and detection.anomaly_score >= 0.7:
            return 'extreme'
        
        if detection.severity in ['CRITICAL', 'HIGH'] and detection.confidence >= 0.7:
            return 'high'
        
        if detection.severity == 'MEDIUM' or detection.anomaly_score >= 0.6:
            return 'moderate'
        
        if detection.severity == 'LOW':
            return 'low'
        
        return 'minimal'
    
    def _calculate_priority(self, detection: AIDetection) -> int:
        """
        Calculate notification priority (1-10)
        
        Used for routing decisions
        """
        # Base priority from severity
        severity_priority = {
            'CRITICAL': 10,
            'HIGH': 7,
            'MEDIUM': 5,
            'LOW': 3,
            'INFO': 1
        }
        
        priority = severity_priority.get(detection.severity, 5)
        
        # Adjust by anomaly score
        if detection.anomaly_score >= 0.9:
            priority = min(10, priority + 2)
        elif detection.anomaly_score >= 0.7:
            priority = min(10, priority + 1)
        
        # Reduce if low confidence
        if detection.confidence < 0.5:
            priority = max(1, priority - 2)
        
        return priority
    
    def should_create_incident(self, detection: AIDetection) -> bool:
        """
        Determine if detection should create an incident
        
        Criteria:
        - Severity >= MEDIUM
        - OR anomaly_score >= 0.7
        - AND confidence >= 0.5
        """
        if detection.severity in ['CRITICAL', 'HIGH']:
            return True
        
        if detection.severity == 'MEDIUM' and detection.confidence >= 0.6:
            return True
        
        if detection.anomaly_score >= 0.7 and detection.confidence >= 0.5:
            return True
        
        return False


# Global instance
classification_engine = ClassificationEngine()
