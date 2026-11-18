"""Strategic OSIRIS - Early Warning Indicator & Alert Engine.
Monitors measurable indicators and thresholds for Egypt, Libya, and Israel.
Implements baseline anomaly detection and alert escalation.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from packages.schemas.models import AlertSeverity, IndicatorDefinition, WarningAlert, utc_now

log = logging.getLogger("strategic_osiris.warning")

DEFAULT_INDICATORS: List[IndicatorDefinition] = [
    IndicatorDefinition(
        id="IND-REDSEA-01",
        name="معدل الحوادث والتهديدات الملاحية في جنوب البحر الأحمر وباب المندب",
        region="Red Sea / Bab el-Mandeb",
        country="Egypt",
        description="رصد الحوادث الأمنية التي تستهدف السفن التجارية وناقلات الطاقة باتجاه قناة السويس",
        metric_type="weekly_incidents",
        baseline_value=3.0,
        current_value=5.0,
        threshold_ratio=1.6
    ),
    IndicatorDefinition(
        id="IND-LIBYA-01",
        name="مؤشر التحركات العسكرية غير المنسقة قرب الحدود الغربية المشتركة",
        region="Western Desert / Eastern Libya",
        country="Libya",
        description="متابعة انتشار الفصائل المسلحة ومحاولات التهريب غير النظامي على خط الحدود الليبية",
        metric_type="border_signals",
        baseline_value=2.0,
        current_value=2.5,
        threshold_ratio=1.8
    ),
    IndicatorDefinition(
        id="IND-ISRAEL-01",
        name="مؤشر التصعيد العسكري على الجبهة الشرقية ومحيط غزة",
        region="Gaza / Sinai Frontier",
        country="Israel",
        description="رصد كثافة العمليات العسكرية والاحتكاكات على المحاور الحدودية الشرقية",
        metric_type="kinetic_intensity",
        baseline_value=4.0,
        current_value=7.5,
        threshold_ratio=1.75
    ),
    IndicatorDefinition(
        id="IND-EASTMED-01",
        name="أمن منشآت الطاقة وحقول الغاز في شرق المتوسط",
        region="Eastern Mediterranean",
        country="Egypt",
        description="رصد أي اقتراب غير مصرح به أو تشويش إلكتروني يستهدف منصات الغاز والمياه الاقتصادية",
        metric_type="naval_patrol_anomalies",
        baseline_value=1.0,
        current_value=1.2,
        threshold_ratio=2.0
    ),
]


class IndicatorEngine:
    def __init__(self):
        self.indicators: Dict[str, IndicatorDefinition] = {
            ind.id: ind for ind in DEFAULT_INDICATORS
        }
        self.alerts: List[WarningAlert] = []

    def get_indicators(self) -> List[IndicatorDefinition]:
        return list(self.indicators.values())

    def update_metric(self, indicator_id: str, new_value: float) -> Optional[WarningAlert]:
        """Update current value for an indicator and test whether an alert threshold is breached."""
        if indicator_id not in self.indicators:
            return None
        
        ind = self.indicators[indicator_id]
        ind.current_value = new_value
        
        ratio = ind.current_value / max(0.1, ind.baseline_value)
        
        if ratio >= ind.threshold_ratio:
            severity = AlertSeverity.CRITICAL if ratio >= 2.5 else AlertSeverity.HIGH if ratio >= 2.0 else AlertSeverity.MEDIUM
            alert = WarningAlert(
                id=f"ALT-{len(self.alerts) + 1:04d}",
                indicator_id=ind.id,
                indicator_name=ind.name,
                region=ind.region,
                country=ind.country,
                severity=severity,
                title=f"تجاوز عتبة الإنذار: {ind.name}",
                description=f"سجل المؤشر قيمة {ind.current_value:.1f} مقارنة بخط الأساس {ind.baseline_value:.1f} (نسبة التغير {ratio:.2f}x). يستوجب تكثيف المتابعة الفورية.",
                ratio_to_baseline=round(ratio, 2),
                requires_human_review=True,
                triggered_at=datetime.now(timezone.utc)
            )
            self.alerts.append(alert)
            log.warning("Triggered alert %s for indicator %s (ratio %.2fx)", alert.id, ind.id, ratio)
            return alert
        return None

    def evaluate_all(self) -> List[WarningAlert]:
        """Evaluate all active indicators against their thresholds."""
        new_alerts = []
        for ind in self.indicators.values():
            ratio = ind.current_value / max(0.1, ind.baseline_value)
            if ratio >= ind.threshold_ratio:
                alert = WarningAlert(
                    id=f"ALT-{len(self.alerts) + len(new_alerts) + 1:04d}",
                    indicator_id=ind.id,
                    indicator_name=ind.name,
                    region=ind.region,
                    country=ind.country,
                    severity=AlertSeverity.CRITICAL if ratio >= 2.5 else AlertSeverity.HIGH if ratio >= 2.0 else AlertSeverity.MEDIUM,
                    title=f"تنبيه إنذار مبكر: {ind.name}",
                    description=f"القيمة الحالية {ind.current_value:.1f} تتجاوز خط الأساس {ind.baseline_value:.1f} بمعامل {ratio:.2f}x.",
                    ratio_to_baseline=round(ratio, 2),
                    requires_human_review=True,
                    triggered_at=datetime.now(timezone.utc)
                )
                new_alerts.append(alert)
        self.alerts.extend(new_alerts)
        return new_alerts

    def get_alerts(self, active_only: bool = True) -> List[WarningAlert]:
        if active_only:
            return [a for a in self.alerts if not a.is_dismissed]
        return list(self.alerts)

    def dismiss_alert(self, alert_id: str) -> bool:
        for a in self.alerts:
            if a.id == alert_id:
                a.is_dismissed = True
                return True
        return False
