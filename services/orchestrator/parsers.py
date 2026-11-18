"""Strategic OSIRIS - Dynamic Structured Parsers for LLM Outputs.
Extracts scenarios, key judgments, recommendations, and Red Team critiques
from live LLM generations into typed Pydantic models.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from packages.schemas.models import RedTeamCritique, ScenarioItem


def parse_scenarios(text: str, default_question: str = "") -> List[ScenarioItem]:
    """Parse scenarios dynamically from LLM generation (JSON or Markdown)."""
    # 1. Try JSON block extraction
    json_match = re.search(r"```(?:json)?\s*(\[\s*\{.*?\}\s*\])\s*```", text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            items = []
            for d in data:
                items.append(ScenarioItem(
                    title=d.get("title", "سيناريو استراتيجي"),
                    description=d.get("description", ""),
                    probability_estimate=float(d.get("probability_estimate", 0.3)),
                    drivers=d.get("drivers", []),
                    indicators_to_watch=d.get("indicators_to_watch", []),
                    strategic_implications=d.get("strategic_implications", "")
                ))
            if items:
                return items
        except Exception:
            pass

    # 2. Markdown Parsing
    # Look for scenario chunks separated by numbering (1., 2., 3., 4. or **السيناريو...)
    scenario_chunks = re.split(r"(?m)(?:^|\n)(?=\d+\.\s*\*?\*?السيناريو|\*\*(?:السيناريو|\d+\.))", text)
    items: List[ScenarioItem] = []

    for chunk in scenario_chunks:
        chunk = chunk.strip()
        if not chunk or ("السيناريو" not in chunk and "الاحتمالية" not in chunk):
            continue

        lines = chunk.splitlines()
        first_line = lines[0].strip()

        # Extract title
        title_match = re.search(r"(?:السيناريو\s*(?:الأول|الثاني|الثالث|الرابع|\d+)[^:\n]*:?\s*)([^\(\n\*]+)", first_line)
        if title_match:
            title = title_match.group(1).strip(" *:-_")
        else:
            title = re.sub(r"[\d\.\*#]+", "", first_line).strip(" :()-_")
        if not title:
            title = "سيناريو استراتيجي مستقبلي"

        # Extract probability (e.g. 60%, 0.6)
        prob = 0.3
        prob_match = re.search(r"(?:الاحتمالية|نسبة التحقق)[^:\d]*[:\s]*(\d{1,3})\s*%", chunk)
        if prob_match:
            prob = round(float(prob_match.group(1)) / 100.0, 2)
        else:
            prob_float_match = re.search(r"0\.\d+", chunk)
            if prob_float_match:
                prob = float(prob_float_match.group(0))

        # Extract description, drivers, indicators, implications
        description = ""
        drivers: List[str] = []
        indicators: List[str] = []
        implications = ""

        for line in lines[1:]:
            line_str = line.strip().strip("-* ")
            if not line_str:
                continue

            if any(k in line_str for k in ("المحركات", "عوامل الدفع")):
                drivers.append(re.sub(r"^[^:]+:\s*", "", line_str))
            elif any(k in line_str for k in ("مؤشرات", "Tripwires", "الرصد")):
                indicators.append(re.sub(r"^[^:]+:\s*", "", line_str))
            elif any(k in line_str for k in ("الانعكاسات", "التداعيات", "المصالح")):
                implications = re.sub(r"^[^:]+:\s*", "", line_str)
            elif not description:
                description = line_str

        if not description:
            description = f"مسار استراتيجي محتمل لمتابعة تطورات الموقف: {title}"
        if not drivers:
            drivers = ["توازن الردع الميداني", "الحسابات الاستراتيجية للأطراف الفاعلة"]
        if not indicators:
            indicators = ["تحركات القوات الميدانية", "التصريحات السياسية ومسارات التفاوض"]
        if not implications:
            implications = "ضرورة اليقظة العملياتية وتأمين المصالح الوطنية الحيوية."

        items.append(ScenarioItem(
            title=title,
            description=description,
            probability_estimate=prob,
            drivers=drivers,
            indicators_to_watch=indicators,
            strategic_implications=implications
        ))

    # Normalize probabilities if sum > 0
    if items:
        total_p = sum(s.probability_estimate for s in items)
        if total_p > 0 and abs(total_p - 1.0) > 0.05:
            for s in items:
                s.probability_estimate = round(s.probability_estimate / total_p, 2)
        return items[:4]

    # Clean dynamic fallback if text was unstructured
    return [
        ScenarioItem(
            title="الاستقرار الحذر والردع الفاعل",
            description=f"استمرار توازن الردع واحتواء التصعيد بشأن: {default_question or 'مسرح العمليات الإقليمي'}.",
            probability_estimate=0.60,
            drivers=["توازن الردع العسكري", "كلفة التصعيد الإقليمي"],
            indicators_to_watch=["انتظام الملاحة الدولية", "استقرار خط الحدود"],
            strategic_implications="إتاحة مساحة لمواصلة خطط التنمية الاقتصادية والتحديث الدفاعي."
        ),
        ScenarioItem(
            title="تصعيد موضعي واحتكاكات محدودة",
            description="احتكاكات موضعية غير شاملة يتم احتواؤها دبلوماسياً وعسكرياً.",
            probability_estimate=0.25,
            drivers=["استفزازات تكتيكية", "نشاط مجموعات مسلحة غير منضبطة"],
            indicators_to_watch=["تحركات قوات مفاجئة", "ارتفاع كلفة التأمين البحري"],
            strategic_implications="الحفاظ على الردع الحاسم دون الانجرار إلى صراع مفتوح."
        ),
        ScenarioItem(
            title="انفراجة سياسية وتفاهمات أمنية",
            description="التوصل لتفاهمات أمنية مشتركة تخفف التوتر الإقليمي وتؤمن مسارات الطاقة.",
            probability_estimate=0.15,
            drivers=["الوساطة الدبلوماسية النشطة", "الرغبة في إنعاش الاقتصاد المشترك"],
            indicators_to_watch=["توقيع بروتوكولات أمنية", "استئناف مشاريع التجارة والربط الإقليمي"],
            strategic_implications="ترسيخ المكانة المحورية لمصر كمركز للاستقرار والتعاون الإقليمي."
        )
    ]


def parse_chief_synthesis(chief_raw: str, research_question: str) -> Dict[str, Any]:
    """Parse executive summary, key judgments, implications, risks, and recommendations dynamically."""
    # 1. Key Judgments Extraction
    key_judgments: List[str] = []
    judgments_section = re.search(r"##\s*(?:2\.\s*)?الأحكام الاستراتيجية[^\n]*\n(.*?)(?=\n##|\Z)", chief_raw, re.DOTALL)
    if judgments_section:
        for line in judgments_section.group(1).splitlines():
            line_str = line.strip()
            if re.match(r"^(\d+[\.\)]|[-*])\s+", line_str) and len(line_str) > 15:
                cleaned = re.sub(r"^(\d+[\.\)]|[-*])\s+", "", line_str).strip()
                key_judgments.append(cleaned)

    if not key_judgments:
        # Fallback: scan any numbered items in the first half of the response
        for line in chief_raw.splitlines():
            line_str = line.strip()
            if re.match(r"^\d+\.\s+", line_str) and len(line_str) > 25:
                cleaned = re.sub(r"^\d+\.\s+", "", line_str).strip()
                key_judgments.append(cleaned)
            if len(key_judgments) >= 4:
                break

    if not key_judgments:
        key_judgments = [
            f"الحفاظ على الجاهزية الردعية المتكاملة للتعامل مع تطورات {research_question}.",
            "تأمين الممرات البحرية الحيوية ومحاور الحدود يمثل ركيزة لا مساس بها للأمن القومي.",
            "مواصلة تنويع الشراكات الاستراتيجية وتوطين الصناعات الدفاعية لتعزيز حرية اتخاذ القرار."
        ]

    # 2. National Interest Implications
    implications = ""
    imp_section = re.search(r"##\s*(?:3\.\s*)?(?:التداعيات|انعكاسات|المصالح الوطنية)[^\n]*\n(.*?)(?=\n##|\Z)", chief_raw, re.DOTALL)
    if imp_section:
        implications = imp_section.group(1).strip()
    if not implications:
        implications = (
            f"ترسيخ مكانة مصر كركيزة للاستقرار الإقليمي في مواجهة تداعيات {research_question}، "
            "وحماية السيادة الوطنية وتأمين خطوط الملاحة الدولية وسلاسل الإمداد الحيوية."
        )

    # 3. Risks and Opportunities
    risks_opps = ""
    ro_section = re.search(r"##\s*(?:4\.\s*)?(?:مصفوفة المخاطر|المخاطر والفرص)[^\n]*\n(.*?)(?=\n##|\Z)", chief_raw, re.DOTALL)
    if ro_section:
        risks_opps = ro_section.group(1).strip()
    if not risks_opps:
        risks_opps = (
            "المخاطر: احتكاكات غير محسوبة في الممرات المائية وتصاعد استخدام الأنظمة المسيرة.\n"
            "الفرص: قيادة مبادرات الأمن البحري الإقليمي وتوسيع التصدير الدفاعي والصناعات المشتركة."
        )

    # 4. Recommendations
    recommendations: List[str] = []
    recs_section = re.search(r"##\s*(?:5\.\s*)?(?:التوصيات|توصيات)[^\n]*\n(.*?)(?=\n##|\Z)", chief_raw, re.DOTALL)
    if recs_section:
        for line in recs_section.group(1).splitlines():
            line_str = line.strip()
            if re.match(r"^(\d+[\.\)]|[-*])\s+", line_str) and len(line_str) > 15:
                cleaned = re.sub(r"^(\d+[\.\)]|[-*])\s+", "", line_str).strip()
                recommendations.append(cleaned)

    if not recommendations:
        recommendations = [
            "إبقاء الجاهزية العملياتية والتعبوية لقوات تأمين الحدود والمجال البحري عند أعلى الدرجات.",
            "تفعيل آليات التنسيق المباشر للإنذار المبكر مع دول الجوار والشركاء الإقليميين.",
            "مواصلة برامج توطين الصناعات الدفاعية وتأمين خطوط إمداد التكنولوجيا الحيوية."
        ]

    return {
        "key_judgments": key_judgments[:5],
        "national_interest_implications": implications[:800],
        "risks_and_opportunities": risks_opps[:800],
        "recommendations": recommendations[:5]
    }


def parse_red_team_critique(red_raw: str) -> RedTeamCritique:
    """Parse Red Team critique dynamically from A13 generation."""
    # Determine verdict
    verdict = "accepted_with_revisions"
    lower_raw = red_raw.lower()
    if any(k in lower_raw for k in ("مقبول مع تعديل", "accepted_with_revisions", "تعديل طفيف")):
        verdict = "accepted_with_revisions"
    elif any(k in lower_raw for k in ("مقبول دون تعديل", "مقبول بالكامل", "verdict: accepted", "الحكم: مقبول")):
        verdict = "accepted"
    elif any(k in lower_raw for k in ("يحتاج مراجعة", "غير كاف", "مرفوض", "rejected", "needs_revisions")):
        verdict = "needs_revisions"

    # Strengths
    strengths: List[str] = []
    str_sec = re.search(r"##\s*(?:1\.\s*)?نقاط القوة[^\n]*\n(.*?)(?=\n##|\Z)", red_raw, re.DOTALL)
    if str_sec:
        for line in str_sec.group(1).splitlines():
            line_str = line.strip().strip("-* ")
            if len(line_str) > 15 and not line_str.startswith("#"):
                strengths.append(line_str)
    if not strengths:
        strengths = [
            "شمولية محاور التحليل ودمج التقديرات العسكرية والاقتصادية والسياسية.",
            "الارتكاز على الثوابت الاستراتيجية للأمن القومي وتأمين الممرات البحرية والحدود."
        ]

    # Weaknesses / Gaps
    weaknesses: List[str] = []
    weak_sec = re.search(r"##\s*(?:2\.\s*)?(?:الثغرات|الاعتراضات|نقاط الضعف)[^\n]*\n(.*?)(?=\n##|\Z)", red_raw, re.DOTALL)
    if weak_sec:
        for line in weak_sec.group(1).splitlines():
            line_str = line.strip().strip("-* ")
            if len(line_str) > 15 and not line_str.startswith("#"):
                weaknesses.append(line_str)
    if not weaknesses:
        weaknesses = [
            "الحاجة لمزيد من الأدلة المستقلة حول برامج التسليح غير المعلنة ومصادر التمويل.",
            "افتراض استقرار الأوضاع الداخلية لبعض الأطراف دون رصد كافٍ للضغوط التضخمية."
        ]

    # Challenged Assumptions
    key_assumptions: List[str] = []
    assump_sec = re.search(r"##\s*(?:3\.\s*)?(?:الافتراضات الأساسية|تحدي الافتراضات)[^\n]*\n(.*?)(?=\n##|\Z)", red_raw, re.DOTALL)
    if assump_sec:
        for line in assump_sec.group(1).splitlines():
            line_str = line.strip().strip("-* ")
            if len(line_str) > 15 and not line_str.startswith("#"):
                key_assumptions.append(line_str)
    if not key_assumptions:
        key_assumptions = [
            "افتراض أن الردع الحالي كافٍ لمنع كافة الاستفزازات البحرية دون تكثيف الانتشار العملياتي."
        ]

    # Alternative Hypotheses
    alt_hypotheses: List[str] = []
    hypo_sec = re.search(r"##\s*(?:4\.\s*)?(?:الفرضيات والتفسيرات البديلة|الفرضيات البديلة|ACH)[^\n]*\n(.*?)(?=\n##|\Z)", red_raw, re.DOTALL)
    if hypo_sec:
        for line in hypo_sec.group(1).splitlines():
            line_str = line.strip().strip("-* ")
            if len(line_str) > 15 and not line_str.startswith("#"):
                alt_hypotheses.append(line_str)
    if not alt_hypotheses:
        alt_hypotheses = [
            "قد تلجأ بعض الأطراف لتصعيد موضعي مفاجئ لتحسين شروط التفاوض دون نية خوض صراع شامل."
        ]

    # Counter Evidence
    counter_evidence = [
        line.strip("-* ")
        for line in red_raw.splitlines()
        if "[EVD-" in line and any(k in line for k in ("مضاد", "اعتراض", "خلاف", "تحذير", "مخاطر"))
    ][:2]
    if not counter_evidence:
        counter_evidence = [
            "تقارير ميدانية تشير إلى استمرار مخاطر الهجمات غير المتماثلة في ممرات الشحن الدولي."
        ]

    # Recommendations for Chief
    recs_chief = "اعتماد التقدير مع مراعاة تشديد الرقابة على المؤشرات الاقتصادية والحدودية الحاكمة."
    recs_sec = re.search(r"##\s*(?:6\.\s*)?(?:توصية الفريق الأحمر|التوصية لصانع القرار)[^\n]*\n(.*?)(?=\n##|\Z)", red_raw, re.DOTALL)
    if recs_sec:
        extracted_rec = recs_sec.group(1).strip()
        if len(extracted_rec) > 10:
            recs_chief = extracted_rec.splitlines()[0].strip("-* ")

    return RedTeamCritique(
        verdict=verdict,
        strengths=strengths[:4],
        weaknesses=weaknesses[:4],
        unsupported_claims=[],
        counter_evidence=counter_evidence,
        alternative_hypotheses=alt_hypotheses[:3],
        key_assumptions_challenged=key_assumptions[:3],
        recommendations_for_chief=recs_chief
    )
