"""Tests for Early Warning Indicators and Alert Engine."""
import pytest
from packages.schemas.models import AlertSeverity
from services.warning.indicator_engine import IndicatorEngine


def test_indicator_breach_triggers_alert():
    """Verify that updating an indicator past threshold generates an alert."""
    engine = IndicatorEngine()
    indicators = engine.get_indicators()
    assert len(indicators) >= 4

    # Red Sea indicator has baseline 3.0, threshold 1.6
    # Raising current value to 7.0 should trigger HIGH or CRITICAL alert
    alert = engine.update_metric("IND-REDSEA-01", 7.0)
    assert alert is not None
    assert alert.indicator_id == "IND-REDSEA-01"
    assert alert.ratio_to_baseline >= 2.0
    assert alert.severity in (AlertSeverity.HIGH, AlertSeverity.CRITICAL)
    assert alert.requires_human_review is True

    # Check alert appears in active alerts
    active = engine.get_alerts(active_only=True)
    assert any(a.id == alert.id for a in active)

    # Dismiss alert
    dismissed = engine.dismiss_alert(alert.id)
    assert dismissed is True
    assert not any(a.id == alert.id for a in engine.get_alerts(active_only=True))


def test_indicator_within_baseline_no_alert():
    """Verify that normal values do not trigger alerts."""
    engine = IndicatorEngine()
    alert = engine.update_metric("IND-EASTMED-01", 1.0)
    assert alert is None
