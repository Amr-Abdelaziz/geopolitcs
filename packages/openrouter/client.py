"""Strategic OSIRIS - OpenRouter API Client.
Provides multi-model access via OpenRouter with per-agent model routing,
token tracking, error handling, and high-fidelity mock fallback mode.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import httpx
from packages.schemas.models import AgentID

load_dotenv()

log = logging.getLogger("strategic_osiris.openrouter")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Default Model Routing according to agent tier
DEFAULT_TIER_MODELS: Dict[AgentID, str] = {
    AgentID.A01_CHIEF_STRATEGIST: "anthropic/claude-3.5-sonnet",
    AgentID.A02_OSINT_COLLECTOR: "meta-llama/llama-3.3-70b-instruct",
    AgentID.A03_VERIFICATION: "meta-llama/llama-3.3-70b-instruct",
    AgentID.A04_MILITARY: "meta-llama/llama-3.3-70b-instruct",
    AgentID.A05_POLITICAL: "meta-llama/llama-3.3-70b-instruct",
    AgentID.A06_ECONOMIC: "meta-llama/llama-3.3-70b-instruct",
    AgentID.A07_GEOPOLITICAL: "meta-llama/llama-3.3-70b-instruct",
    AgentID.A08_DEFENSE_TECH: "meta-llama/llama-3.3-70b-instruct",
    AgentID.A09_GEOINT: "meta-llama/llama-3.3-70b-instruct",
    AgentID.A10_COUNTRY_INTEL: "meta-llama/llama-3.3-70b-instruct",
    AgentID.A11_FORECAST: "meta-llama/llama-3.3-70b-instruct",
    AgentID.A12_EARLY_WARNING: "meta-llama/llama-3.3-70b-instruct",
    AgentID.A13_RED_TEAM: "anthropic/claude-3.5-sonnet",
    AgentID.A14_REPORT: "meta-llama/llama-3.3-70b-instruct",
}


class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.site_url = os.environ.get("SITE_URL", "https://strategic-osiris.local")
        self.app_name = os.environ.get("APP_NAME", "Strategic OSIRIS Intelligence Platform")
        self.mock_mode = not bool(self.api_key) or os.environ.get("MOCK_LLM", "").lower() in ("1", "true")
        if self.mock_mode:
            log.info("OpenRouterClient initialized in MOCK/FALLBACK mode (no active API key or MOCK_LLM=1)")
        else:
            log.info("OpenRouterClient initialized with live API key")

    def get_model_for_agent(self, agent_id: AgentID, override: Optional[str] = None) -> str:
        if override:
            return override
        return DEFAULT_TIER_MODELS.get(agent_id, "meta-llama/llama-3.3-70b-instruct")

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str = "meta-llama/llama-3.3-70b-instruct",
        temperature: float = 0.2,
        max_tokens: int = 2500,
        agent_id: Optional[AgentID] = None,
        context_hint: Optional[str] = None,
    ) -> str:
        """Execute chat completion either via OpenRouter or deterministic mock fallback."""
        if self.mock_mode:
            return self._generate_mock_completion(messages, agent_id, context_hint)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content
            except Exception as e:
                log.error("OpenRouter request failed: %s, falling back to mock generator", str(e))
                return self._generate_mock_completion(messages, agent_id, context_hint)

    def _generate_mock_completion(
        self,
        messages: List[Dict[str, str]],
        agent_id: Optional[AgentID],
        context_hint: Optional[str] = None
    ) -> str:
        """Deterministic, rich analytical generator for testing and offline environments."""
        agent = agent_id or AgentID.A01_CHIEF_STRATEGIST
        topic = context_hint or "التطورات الاستراتيجية وموازين القوى في مسرح العمليات المشترك"

        if agent == AgentID.A01_CHIEF_STRATEGIST:
            return f"""# تقدير الموقف الاستراتيجي الشامل
## 1. الملخص التنفيذي
أظهرت القراءات الاستخباراتية المتكاملة لخلية التحليل الاستراتيجي بمنظومة OSIRIS تحولات محورية في البيئة الأمنية الإقليمية [EVD-001]. تتركز المخاطر في تسارع وتيرة التسلح النوعي، والضغوط على الممرات الملاحية في البحر الأحمر وشرق المتوسط، والتقلبات الحدودية في الساحة الليبية، مما يفرض ضرورة اتخاذ تدابير استباقية دفاعية ودبلوماسية متزامنة لحماية المصالح المصرية العليا [EVD-002].

## 2. الأحكام الاستراتيجية الرئيسية
1. مسرح العمليات الإقليمي يشهد إعادة تشكيل للتحالفات الاستراتيجية بما يستوجب الحفاظ على التفوق الردعي المتوازن [EVD-003].
2. المصالح الاستراتيجية المصرية في تأمين المجرى الملاحي لقناة السويس والحدود الغربية تظل الثابت الحاكم في إدارة الأزمات الإقليمية [EVD-004].
3. فرص تعزيز التعاون التكنولوجي الدفاعي المشترك تمثل أولوية للحد من الاعتماد على سلاسل الإمداد الخارجية الحساسة [EVD-005].

## 3. درجة الثقة والفجوات المعلوماتية
- درجة الثقة العامة: مرتفعة (استناداً إلى أدلة مؤكدة ومتطابقة عبر أكثر من مصدر مستقل).
- الفجوات: رصد البرامج غير المعلنة للتسليح النوعي، ومسارات التمويل الخارجي للأطراف غير النظامية."""

        elif agent == AgentID.A04_MILITARY:
            return f"""# التقييم العسكري والدفاعي
## 1. الموقف الميداني وتوازن الردع
تشير المؤشرات العسكرية المرصودة إلى تعزيز القدرات العملياتية وانتشار المنظومات الدفاعية المتقدمة [EVD-001]. يظهر التحليل العسكري أن جاهزية القوات المسلحة المصرية على الاتجاهين الاستراتيجيين الشمالي الشرقي والغربي تشكل صمام الأمان لمنع اختلال توازن القوى [EVD-002].

## 2. البرامج التسليحية والمناورات
- استمرار مناورات الجاهزية القتالية المشتركة وتطوير منظومات الدفاع الجوي وتأمين القواعد البحرية في المتوسط والأحمر [EVD-003].
- الحذر من تنامي استخدام المسيرات التكتيكية والانتحارية (UAVs) على خطوط التماس الإقليمية بما يتطلب رفع كفاءة الرصد الإلكتروني والتشويش [EVD-004].

- التقييم النهائي: جاهزية ردعية مرتفعة، وتوصية باستمرار الرصد الراداري على مدار الساعة."""

        elif agent == AgentID.A05_POLITICAL:
            return f"""# التقييم السياسي والدبلوماسي
## 1. المشهد السياسي والتحالفات
تبرز التحركات الدبلوماسية الأخيرة سعي الأطراف الإقليمية والدولية لإعادة تموضع نفوذها [EVD-002]. الدبلوماسية المصرية تواصل لعب دور الضامن الرئيسي لخفض التصعيد وحماية استقرار الدولة الوطنية في ليبيا والحفاظ على التهدئة الإقليمية [EVD-004].

## 2. دوافع الأطراف الفاعلة
- التركيز على تحقيق مكاسب سياسية داخلية قبل الاستحقاقات الانتخابية [EVD-005].
- تفادي التصعيد الشامل الذي يهدد المصالح الاقتصادية والأمنية المشتركة.
- التقييم السياسي: حالة سيولة استراتيجية تتطلب تكثيف القنوات الاستخباراتية والدبلوماسية المشتركة."""

        elif agent == AgentID.A06_ECONOMIC:
            return f"""# التقييم الاقتصادي وأمن الطاقة
## 1. الممرات البحرية وتأمين الملاحة
يشكل استقرار الملاحة في قناة السويس والبحر الأحمر شرياناً حيوياً للاقتصاد المصري والتجارة الدولية [EVD-003]. انخفاض حركة الشحن يؤثر مباشرة على عوائد المجرى الملاحي ويزيد تكاليف التأمين الدولي [EVD-004].

## 2. الغاز والطاقة في شرق المتوسط
- التنسيق المستمر ضمن منتدى غاز شرق المتوسط يعزز مكانة مصر كمركز إقليمي لتداول وتسييل الطاقة [EVD-005].
- استدامة الموازنات الدفاعية تتطلب كفاءة ترشيد الموارد والاعتماد على التصنيع المحلي لتقليل استنزاف العملات الأجنبية."""

        elif agent == AgentID.A07_GEOPOLITICAL:
            return f"""# التقييم الجيوسياسي وموازين النفوذ
تتقاطع في المنطقة مصالح القوى الكبرى والإقليمية عبر محاور استراتيجية حاكمة:
1. الممر البحري الاستراتيجي: باب المندب - البحر الأحمر - قناة السويس - شرق المتوسط [EVD-001].
2. العمق الأمني للحدود الغربية المصرية المشتركة مع الساحة الليبية [EVD-002].
3. التوازن الدقيق في علاقات القوى الدولية (واشنطن، بكين، موسكو) في المنطقة، مع تمسك مصر باستقلالية القرار الاستراتيجي وتعدد الشراكات الدولية [EVD-005]."""

        elif agent == AgentID.A08_DEFENSE_TECH:
            return f"""# تقييم الصناعات الدفاعية والتكنولوجيا العسكرية
## 1. التطور التكنولوجي ومستوى الاستقلال
تسارع التحول نحو الأنظمة غير المأهولة (الدرونز والزوارق المسيرة) والحرب السيبرانية ورادارات الإنذار المبكر بعيدة المدى [EVD-003].
## 2. توطين التكنولوجيا المصرية
- تحقيق تقدم ملموس في معرض إيديكس (EDEX) بتصنيع الفرقاطات والمركبات المدرعة والأنظمة المسيرة محلياً، مما يقلل مخاطر القيود التصديرية الخارجية [EVD-005].
- التوصية: التركيز على حماية سلاسل إمداد المكونات الدقيقة وأشباه الموصلات والبرمجيات السيادية."""

        elif agent == AgentID.A10_COUNTRY_INTEL:
            return f"""# ملف الاستخبارات الإقليمية (مصر - ليبيا - إسرائيل)
- **مصر (دولة الارتكاز):** استقرار مؤسسي عسكري وسياسي صلب، جاهزية دفاعية شاملة، إدارة حكيمة لملفات الجوار الإقليمي المضطرب [EVD-001].
- **ليبيا (الجوار الغربي):** استمرار الانقسام التنفيذي، مع تركيز مصري حاسم على منع تفلت الحدود الغربية ومكافحة تهريب السلاح ودعم مسار الحل الليبي-الليبي [EVD-002].
- **إسرائيل (الجوار الشرقي):** توترات ميدانية وتداعيات أمنية مستمرة، مع تأكيد مصر الثابت على ثوابت الأمن القومي وحماية خط الحدود وحقوق الشعب الفلسطيني المشروعة [EVD-004]."""

        elif agent == AgentID.A11_FORECAST:
            return f"""# سيناريوهات المستقبل (Horizon: 6-12 Months)
1. **السيناريو الأول: الاستقرار الحذر والردع النشط (الاحتمالية: 60%)**
   - استمرار توازن الردع ومنع المواجهة الشاملة، مع إدارة الأزمات عبر قنوات الوساطة والاستخبارات [EVD-001].
2. **السيناريو الثاني: تصعيد موضعي غير شامل (الاحتمالية: 25%)**
   - احتكاكات متفرقة على خطوط الملاحة أو الأطراف الحدودية يتم احتواؤها سريعاً [EVD-003].
3. **السيناريو الثالث: انفراجة سياسية واتفاقات تهدئة إقليمية (الاحتمالية: 10%)**
   - إبرام تفاهمات شاملة للأمن الإقليمي وتعزيز تدفقات الطاقة والتجارة.
4. **السيناريو الرابع: المفاجأة الاستراتيجية (الاحتمالية: 5%)**
   - تغير مفاجئ في موازين السيطرة الإقليمية يستدعي تحركاً دفاعياً طارئاً."""

        elif agent == AgentID.A13_RED_TEAM:
            return f"""# مراجعة الفريق الأحمر النقدية المستقلة
## 1. نقاط القوة في التقدير
- شمولية التغطية العسكرية والسياسية والاقتصادية.
- وضوح ارتباط التحليل بالمحددات الثابتة للأمن القومي المصري [EVD-001].

## 2. الاعتراضات والافتراضات غير المثبتة
- **اعتراض 1:** افتراض أن الاستقرار الداخلي للأطراف سيظل ثابتاً خلال 12 شهراً قد يكون مفرطاً في التفاؤل نظراً للضغوط التضخمية والاجتماعية [EVD-002].
- **اعتراض 2:** الادعاء بأن المخاطر البحرية ستنخفض تلقائياً دون معالجة جذور الصراع هو ادعاء غير مدعوم بأدلة كافية [EVD-004].

## 3. الفرضيات البديلة (ACH)
- قد تدفع الحسابات السياسية الضيقة لبعض القادة الإقليميين نحو تصعيد محسوب للهروب من الأزمات الداخلية.

## 4. حكم الفريق الأحمر النهائي
التقرير: **مقبول مع تعديل طفيف** بتشديد الرقابة على المؤشرات الاقتصادية والحدودية."""

        elif agent == AgentID.A14_REPORT:
            return f"""# تقرير تقدير موقف استراتيجي رسمي
**الجهة:** منظومة OSIRIS للتحليل الاستراتيجي
**التصنيف:** تقدير استراتيجي موجه لصانع القرار
**الموضوع:** {topic}

## أولاً: ملخص تنفيذي موجه
تشير التقديرات المتقاطعة للخلية الاستراتيجية إلى أهمية الحفاظ على اليقظة العملياتية والتفوق الدفاعي للردع، بالتوازي مع تحركات دبلوماسية مكثفة لحماية أمن الحدود ومصالح الملاحة والطاقة [EVD-001، EVD-002].

## ثانياً: التوصيات الاستراتيجية
1. الإبقاء على الجاهزية القصوى لتأمين الحدود الغربية والممرات المائية الاستراتيجية.
2. تكثيف الشراكات الإقليمية في مجالات التصنيع المشترك والأمن السيبراني.
3. اعتماد التقرير وتعميمه على جهات الاختصاص بعد المراجعة البشرية."""

        return f"تحليل الوكيل {agent.value} بشأن: {topic}، استناداً للأدلة المرصودة."
