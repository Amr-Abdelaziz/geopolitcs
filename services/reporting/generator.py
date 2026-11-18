"""Strategic OSIRIS - Bilingual Strategic Report Generator.
Produces formal military/diplomatic assessments in Arabic and English,
supporting Markdown, HTML, and JSON representations.
"""
from __future__ import annotations

from typing import Dict, Optional
from packages.schemas.models import StrategicAssessment


class ReportGenerator:
    @staticmethod
    def to_arabic_markdown(assessment: StrategicAssessment) -> str:
        scenarios_text = "\n\n".join(
            f"### {s.title} (الاحتمالية: {int(s.probability_estimate * 100)}%)\n"
            f"- **الوصف:** {s.description}\n"
            f"- **المحركات:** {', '.join(s.drivers)}\n"
            f"- **المؤشرات الحاكمة:** {', '.join(s.indicators_to_watch)}\n"
            f"- **التداعيات:** {s.strategic_implications}"
            for s in assessment.scenarios
        )

        recommendations_text = "\n".join(
            f"{i+1}. {rec}" for i, rec in enumerate(assessment.recommendations)
        )

        key_judgments_text = "\n".join(
            f"- {kj}" for kj in assessment.key_judgments
        )

        red_team_text = ""
        if assessment.red_team_critique:
            rtc = assessment.red_team_critique
            red_team_text = f"""
## المراجعة النقدية المستقلة (الفريق الأحمر - Red Team)
- **الحكم العام للمراجعة:** {rtc.verdict}
- **نقاط القوة:**
{chr(10).join(f"  * {s}" for s in rtc.strengths)}
- **الاعتراضات والافتراضات غير المثبتة:**
{chr(10).join(f"  * {w}" for w in rtc.weaknesses)}
- **توصيات الفريق الأحمر لصانع القرار:** {rtc.recommendations_for_chief}
"""

        citations_text = "\n".join(
            f"- **[{c.id}]** {c.title} ({c.source_name} - موثوقية: {c.reliability.value}{c.credibility.value})\n  {c.content_snippet}"
            for c in assessment.citations
        )

        status_text = "معتمد للنشر" if assessment.status == "approved" else "قيد المراجعة والاعتماد البشري"

        return f"""# تقدير موقف استراتيجي: {assessment.research_question}

**معرف التقدير:** {assessment.id}  
**الجهة المصدرة:** منظومة OSIRIS للتحليل الاستراتيجي والاستخبارات مفتوحة المصدر  
**الدولة المرجعية:** {assessment.reference_country}  
**النطاق الجغرافي المستهدف:** {', '.join(assessment.target_countries)}  
**الإطار الزمني:** {assessment.time_horizon}  
**الحالة:** {status_text} ({assessment.status.value})  
**تاريخ الإعداد:** {assessment.created_at.strftime('%Y-%m-%d %H:%M UTC')}  
**المراجع المعتمد:** {assessment.approval_reviewer or 'بانتظار المراجعة'}  

---

## 1. الملخص التنفيذي
{assessment.executive_summary_ar}

## 2. الأحكام الاستراتيجية الرئيسية
{key_judgments_text}

## 3. التقييم العسكري والدفاعي
{assessment.military_assessment or 'لا تتوفر تفاصيل إضافية.'}

## 4. التقييم السياسي والدبلوماسي
{assessment.political_assessment or 'لا تتوفر تفاصيل إضافية.'}

## 5. التقييم الاقتصادي وأمن الطاقة
{assessment.economic_assessment or 'لا تتوفر تفاصيل إضافية.'}

## 6. التقييم الجيوسياسي وموازين النفوذ
{assessment.geopolitical_assessment or 'لا تتوفر تفاصيل إضافية.'}

## 7. الصناعات الدفاعية والتكنولوجيا العسكرية
{assessment.defense_tech_assessment or 'لا تتوفر تفاصيل إضافية.'}

## 8. الانعكاسات على الأمن القومي والمصالح المصرية
{assessment.national_interest_implications or 'الحفاظ على التفوق والجاهزية الشاملة على كافة الاتجاهات الاستراتيجية.'}

## 9. مصفوفة المخاطر والفرص
{assessment.risks_and_opportunities or 'متابعة حثيثة للمتغيرات الحدودية والبحرية.'}

## 10. السيناريوهات المستقبلية
{scenarios_text}

## 11. التوصيات ذات الأولوية لصانع القرار
{recommendations_text}

{red_team_text}

---

## 12. سجل الأدلة والمصادر الموثقة (Admiralty Standard)
{citations_text}
"""

    @staticmethod
    def to_html(assessment: StrategicAssessment) -> str:
        md = ReportGenerator.to_arabic_markdown(assessment)
        html_lines = []
        for line in md.splitlines():
            if line.startswith("# "):
                html_lines.append(f"<h1 class='text-2xl font-bold mb-4 text-emerald-400'>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2 class='text-xl font-semibold mt-6 mb-3 text-cyan-300 border-b border-gray-700 pb-1'>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3 class='text-lg font-medium mt-4 mb-2 text-amber-300'>{line[4:]}</h3>")
            elif line.startswith("- "):
                html_lines.append(f"<li class='mr-4 mb-1 text-gray-200'>{line[2:]}</li>")
            elif line.startswith("---"):
                html_lines.append("<hr class='my-6 border-gray-700'/>")
            elif line.strip():
                html_lines.append(f"<p class='mb-3 text-gray-300 leading-relaxed'>{line}</p>")
        
        body_content = "\n".join(html_lines)
        return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>Strategic Assessment - {assessment.id}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    body {{ font-family: 'Cairo', sans-serif; }}
  </style>
</head>
<body class="bg-gray-950 text-gray-100 p-8 min-h-screen">
  <div class="max-w-4xl mx-auto bg-gray-900 border border-gray-800 rounded-xl p-8 shadow-2xl">
    <div class="flex justify-between items-center mb-6 border-b border-gray-800 pb-4">
      <div class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></span>
        <span class="font-bold tracking-wider text-emerald-400">STRATEGIC OSIRIS INTELLIGENCE FUSION</span>
      </div>
      <span class="px-3 py-1 rounded bg-gray-800 text-xs font-mono text-gray-400">ID: {assessment.id}</span>
    </div>
    {body_content}
  </div>
</body>
</html>"""
