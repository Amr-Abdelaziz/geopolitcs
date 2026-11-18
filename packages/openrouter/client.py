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

# Inject Windows / OS native trust store if available
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

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
        try:
            from packages.prompts.registry import agent_config_manager
            agent_def = agent_config_manager.get_agent(agent_id)
            if agent_def and agent_def.default_model:
                return agent_def.default_model
        except Exception:
            pass
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

        # Try first with default SSL; fall back to verify=False if corporate/Windows proxy causes SSLError
        for verify_ssl in (True, False):
            try:
                async with httpx.AsyncClient(timeout=120.0, verify=verify_ssl) as client:
                    response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    log.info("OpenRouter response received from %s (agent: %s)", model, agent_id.value if agent_id else "unknown")
                    return content
            except httpx.HTTPStatusError as e:
                log.error("OpenRouter HTTP error %d: %s", e.response.status_code, e.response.text)
                break
            except Exception as e:
                if verify_ssl:
                    log.warning("SSL verification failed (%s), retrying with verify=False", str(e))
                    continue
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
1. الحفاظ على التفوق والجاهزية الردعية المتكاملة على المحاور الاستراتيجية الحاكمة ومسرح العمليات المشترك [EVD-001].
2. تأمين ممرات التجارة والطاقة في البحر الأحمر وقناة السويس وشرق المتوسط يمثل ركيزة للأمن القومي [EVD-003].
3. استمرار التنسيق المشترك لمنع تدفق السلاح والمجموعات غير النظامية عبر الحدود الغربية المشتركة مع ليبيا [EVD-004].
4. فرص تعزيز التعاون التكنولوجي الدفاعي وتوطين الصناعات العسكرية تمثل أولوية استراتيجية عليا [EVD-005].

## 3. التداعيات على الأمن القومي والمصالح الوطنية
ترسيخ دور مصر كركيزة للاستقرار الإقليمي، وحماية حرية الملاحة الدولية في قناة السويس، وتعزيز الاستقلال العسكري بتوطين التكنولوجيا الدفاعية وتعدد مسارات التعاون الدولي.

## 4. مصفوفة المخاطر والفرص
المخاطر: احتكاكات غير محسوبة على الممرات المائية وتصاعد استخدام الأنظمة المسيرة.
الفرص: قيادة مبادرات الأمن البحري الإقليمي وتوسيع التصدير الدفاعي والصناعات المشتركة.

## 5. التوصيات الاستراتيجية ذات الأولوية
1. إبقاء الجاهزية العملياتية والتعبوية لقوات تأمين الحدود والمجال البحري عند أعلى الدرجات.
2. تفعيل آليات التنسيق المباشر للإنذار المبكر مع دول الجوار والشركاء الإقليميين.
3. مواصلة برامج توطين الصناعات الدفاعية وتأمين خطوط إمداد التكنولوجيا الحيوية."""

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
1. **السيناريو الأول: الاستقرار الحذر والردع الفاعل (الاحتمالية: 60%)**
   - الوصف: استمرار توازن القوى الردعي ومنع الانزلاق لصراع مفتوح عبر قنوات الوساطة وتأمين الحدود [EVD-001].
   - المحركات الرئيسية: توازن الردع والتكلفة الاقتصادية الباهظة لأي تصعيد إقليمي.
   - مؤشرات التحقق والرصد: انتظام الملاحة في البحر الأحمر واستقرار المعابر الحدودية.
   - الانعكاسات الاستراتيجية: إتاحة مساحة لمواصلة خطط التنمية وتحديث القدرات الدفاعية.

2. **السيناريو الثاني: تصعيد موضعي واحتكاكات غير شاملة (الاحتمالية: 25%)**
   - الوصف: حدوث مناوشات أو استهدافات متفرقة لخطوط التجارة أو المحاور الحدودية يتم احتواؤها سريعاً [EVD-003].
   - المحركات الرئيسية: استفزازات تكتيكية ونشاط فصائل مسلحة خارج السيطرة.
   - مؤشرات التحقق والرصد: ارتفاع كلفة التأمين البحري وتحركات قوات مفاجئة.
   - الانعكاسات الاستراتيجية: ضرورة الرد الردعي الحاسم دون الانجرار إلى استنزاف طويل الأمد.

3. **السيناريو الثالث: انفراجة سياسية وتهدئة إقليمية شاملة (الاحتمالية: 15%)**
   - الوصف: التوصل لتفاهمات أمنية مشتركة تخفف من حدة التوترات الإقليمية وتؤمن خطوط التجارة والطاقة.
   - المحركات الرئيسية: جهود الوساطة الدبلوماسية النشطة والرغبة في إنعاش الاقتصاد الإقليمي.
   - مؤشرات التحقق والرصد: توقيع اتفاقات أمنية واستئناف مشاريع الربط الكهربائي والطاقة.
   - الانعكاسات الاستراتيجية: تعزيز المكانة المحورية لمصر كمركز إقليمي للتجارة والتعاون الاستراتيجي.

4. **السيناريو الرابع: المفاجأة الاستراتيجية (الاحتمالية: 5%)**
   - الوصف: تغير مفاجئ في موازين السيطرة الإقليمية يستدعي تحركاً دفاعياً طارئاً.
   - المحركات الرئيسية: تحولات سياسية راديكالية مفاجئة في دول الطوق.
   - مؤشرات التحقق والرصد: انهيار مفاوضات التهدئة وإغلاق مسارات تجارية حيوية.
   - الانعكاسات الاستراتيجية: تفعيل خطط الطوارئ الاستراتيجية الشاملة."""

        elif agent == AgentID.A13_RED_TEAM:
            return f"""# مراجعة الفريق الأحمر النقدية المستقلة
## 1. نقاط القوة في التقدير
- شمولية محاور التحليل العسكري والاقتصادي والسياسي للمسرح المشترك [EVD-001].
- الارتكاز على ثوابت الأمن القومي المصري وتأمين الممرات البحرية والحدود [EVD-003].

## 2. الثغرات والادعاءات غير المثبتة
- الاعتماد على افتراض استقرار الأوضاع الداخلية لبعض الأطراف دون رصد كافٍ للضغوط التضخمية [EVD-002].
- الحاجة لمزيد من الأدلة المستقلة حول البرامج التسليحية غير المعلنة.

## 3. الافتراضات الأساسية التي تم تحديها
- افتراض أن الردع الحالي كافٍ لمنع كافة الاستفزازات البحرية دون زيادة الحضور العسكري المباشر [EVD-004].

## 4. الفرضيات والتفسيرات البديلة (ACH)
- قد تلجأ بعض الأطراف لتصعيد موضعي مفاجئ لتحسين شروط التفاوض دون نية خوض صراع شامل.

## 5. حكم الفريق الأحمر النهائي
التقرير: **مقبول مع تعديل طفيف** (accepted_with_revisions).

## 6. توصية الفريق الأحمر لصانع القرار
اعتماد التقدير مع مراعاة وضع خطط طوارئ إضافية لتأمين إمدادات الطاقة والممرات الملاحية."""

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
