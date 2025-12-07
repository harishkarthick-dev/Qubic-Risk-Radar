"""Test rule engine condition matching and incident creation"""
import pytest
from datetime import datetime
from app.services.rules_engine import RuleEngine
from app.models.event import NormalizedEvent
from app.models.rule import Rule


@pytest.mark.asyncio
async def test_whale_transfer_rule_match(db_session):
    """Test that whale transfer rule triggers correctly"""
    # Create rule
    rule = Rule(
        name="Test Whale Rule",
        severity="CRITICAL",
        type="WhaleTransfer",
        conditions_json={
            "event_name": "Transfer",
            "amount_greater_than": 1000000
        },
        enabled=True
    )
    db_session.add(rule)
    await db_session.commit()
    
    # Create matching event
    event = NormalizedEvent(
        chain="QUBIC",
        event_name="Transfer",
        amount=5000000,
        token_symbol="QUBIC",
        from_address="WHALE123",
        to_address="EXCHANGE456",
        timestamp=datetime.utcnow(),
        tx_hash="test_tx",
        tx_status="success"
    )
    db_session.add(event)
    await db_session.commit()
    
    # Evaluate rule
    engine = RuleEngine(db_session)
    incidents = await engine.evaluate_event(event)
    
    assert len(incidents) == 1
    assert incidents[0].severity == "CRITICAL"
    assert incidents[0].type == "WhaleTransfer"


@pytest.mark.asyncio
async def test_rule_no_match_below_threshold(db_session):
    """Test that rule doesn't trigger below threshold"""
    rule = Rule(
        name="Test Whale Rule",
        severity="CRITICAL",
        conditions_json={
            "event_name": "Transfer",
            "amount_greater_than": 1000000
        },
        enabled=True
    )
    db_session.add(rule)
    await db_session.commit()
    
    # Event below threshold
    event = NormalizedEvent(
        chain="QUBIC",
        event_name="Transfer",
        amount=500000,  # Below threshold
        timestamp=datetime.utcnow(),
        tx_hash="test_tx",
        tx_status="success"
    )
    db_session.add(event)
    await db_session.commit()
    
    engine = RuleEngine(db_session)
    incidents = await engine.evaluate_event(event)
    
    assert len(incidents) == 0


@pytest.mark.asyncio
async def test_deduplication(db_session):
    """Test incident deduplication"""
    rule = Rule(
        name="Test Dedup Rule",
        severity="WARNING",
        conditions_json={"event_name": "Transfer"},
        deduplication_key_template="test_{date}",
        cooldown_seconds=3600,
        enabled=True
    )
    db_session.add(rule)
    await db_session.commit()
    
    # First event
    event1 = NormalizedEvent(
        event_name="Transfer",
        timestamp=datetime.utcnow(),
        tx_hash="tx1",
        tx_status="success"
    )
    db_session.add(event1)
    await db_session.commit()
    
    engine = RuleEngine(db_session)
    incidents1 = await engine.evaluate_event(event1)
    
    assert len(incidents1) == 1
    
    # Second event (should be deduplicated)
    event2 = NormalizedEvent(
        event_name="Transfer",
        timestamp=datetime.utcnow(),
        tx_hash="tx2",
        tx_status="success"
    )
    db_session.add(event2)
    await db_session.commit()
    
    incidents2 = await engine.evaluate_event(event2)
    
    assert len(incidents2) == 0  # Deduplicated


# Pytest fixtures
@pytest.fixture
async def db_session():
    """Create test database session"""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session
