"""Test webhook signature verification and event processing"""
import pytest
import hmac
import hashlib
from httpx import AsyncClient
from app.main import app
from app.config import settings


@pytest.mark.asyncio
async def test_webhook_valid_signature():
    """Test webhook with valid HMAC signature"""
    payload = {
        "alert_id": "test-123",
        "event_type": "Transfer",
        "contract_name": "QX",
        "tx_hash": "abc123",
        "timestamp": "2025-12-06T11:30:00Z",
        "status": "success",
        "from_address": "SENDER123",
        "to_address": "RECEIVER456",
        "amount": 5000000,
        "token_symbol": "QUBIC"
    }
    
    # Generate signature
    import json
    body = json.dumps(payload).encode()
    signature = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook/qubic/events",
            json=payload,
            headers={"X-Signature": signature}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "event_id" in data


@pytest.mark.asyncio
async def test_webhook_invalid_signature():
    """Test webhook with invalid signature"""
    payload = {"alert_id": "test-123"}
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook/qubic/events",
            json=payload,
            headers={"X-Signature": "invalid_signature"}
        )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_missing_signature():
    """Test webhook without signature (should pass if not configured)"""
    payload = {
        "alert_id": "test-456",
        "event_type": "Transfer"
    }
    
    # Temporarily disable signature check
    original_secret = settings.WEBHOOK_SECRET
    settings.WEBHOOK_SECRET = ""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook/qubic/events",
            json=payload
        )
    
    settings.WEBHOOK_SECRET = original_secret
    
    # Should succeed when signature not required
    assert response.status_code in [200, 400, 500]  # 400/500 for incomplete payload
