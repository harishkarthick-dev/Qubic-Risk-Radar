"""Event normalization service - converts EasyConnect payloads to standard format"""
from typing import Dict, Any, Optional
from datetime import datetime
from app.models.event import NormalizedEvent
from app.logging_config import get_logger

logger = get_logger(__name__)


class EventNormalizer:
    """Normalizes EasyConnect webhook payloads into structured event data"""
    
    @staticmethod
    def normalize_easyconnect_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert EasyConnect webhook payload to normalized event data
        
        Args:
            payload: Raw EasyConnect webhook payload
            
        Returns:
            Dictionary with normalized event fields
        """
        try:
            # Extract timestamp
            timestamp_str = payload.get('timestamp')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()
            
            # Build normalized data
            normalized_data = {
                'chain': 'QUBIC',
                'contract_address': payload.get('contract_address', ''),
                'contract_label': payload.get('contract_name', ''),
                'event_name': payload.get('event_type') or payload.get('method', ''),
                'tx_hash': payload.get('tx_hash', ''),
                'tx_status': payload.get('status', 'unknown'),
                'from_address': payload.get('from_address', ''),
                'to_address': payload.get('to_address', ''),
                'amount': payload.get('amount', 0),
                'token_symbol': payload.get('token_symbol', 'QUBIC'),
                'block_height': payload.get('block_height'),
                'tick': payload.get('tick'),
                'timestamp': timestamp,
                'metadata_json': {
                    'alert_id': payload.get('alert_id'),
                    'contract_index': payload.get('contract_index'),
                    'procedure': payload.get('procedure'),
                    'price': payload.get('price'),
                    'quantity': payload.get('quantity'),
                    'metadata': payload.get('metadata', {}),
                }
            }
            
            logger.info(
                "normalized_event",
                event_name=normalized_data['event_name'],
                contract=normalized_data['contract_label'],
                tx_hash=normalized_data['tx_hash'][:16] if normalized_data['tx_hash'] else None
            )
            
            return normalized_data
            
        except Exception as e:
            logger.error("normalization_failed", error=str(e), payload=payload)
            raise
    
    @staticmethod
    def normalize_generic_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback normalizer for non-EasyConnect payloads (future extensibility)
        
        Args:
            payload: Generic webhook payload
            
        Returns:
            Dictionary with normalized event fields
        """
        return {
            'chain': payload.get('chain', 'QUBIC'),
            'contract_address': payload.get('contract', ''),
            'contract_label': payload.get('protocol', ''),
            'event_name': payload.get('event', ''),
            'tx_hash': payload.get('transaction_hash', ''),
            'tx_status': payload.get('status', 'unknown'),
            'from_address': payload.get('from', ''),
            'to_address': payload.get('to', ''),
            'amount': payload.get('value', 0),
            'token_symbol': payload.get('token', 'QUBIC'),
            'timestamp': datetime.utcnow(),
            'metadata_json': payload
        }
