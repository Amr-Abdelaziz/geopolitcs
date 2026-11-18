"""Strategic OSIRIS - Knowledge Base Document Ingestion Tool.
Allows analysts to populate the Strategic Defense Doctrine & Geopolitical Treaties Bank
via CLI, batch file loading (JSON/Markdown), or automated directory scanning.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from packages.schemas.models import AdmiraltyCredibility, AdmiraltyReliability, KnowledgeDocument
from services.knowledge.knowledge_engine import KnowledgeEngine, knowledge_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ingest_documents")

EXPANDED_STRATEGIC_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "id": "DOC-TRT-007",
        "title_ar": "معاهدة السلام المصرية الإسرائيلية 1979 والملحق العسكري الأمني لسيناء",
        "title_en": "1979 Egypt-Israel Peace Treaty & Military Security Annex (Sinai Zones A-D)",
        "category": "treaty",
        "country_coverage": ["Egypt", "Israel"],
        "summary": "التقسيم الأمني والعسكري لشبه جزيرة سيناء (المناطق أ، ب، ج) والمنطقة الإسرائيلية (د)، آليات الأنشطة المتفق عليها (Agreed Activities Mechanism)، والسيادة الكاملة على معبر رفح ومحور فيلادلفيا.",
        "content": (
            "تنظم معاهدة السلام 1979 والملحق الأمني العسكري ترتيبات الانتشار وتحديد القوات على جانبي الحدود الدولية:\n"
            "1. تقسيم المناطق الأمنية في سيناء:\n"
            "- المنطقة (أ): تمتد من قناة السويس شرقاً حتى الخط (أ)، يُسمح فيها بفرقة مشاة ميكانيكية مصرية كاملة التسليح (دبابات، مدفعية، دفاع جوي).\n"
            "- المنطقة (ب): تمتد بين الخط (أ) والخط (ب) في وسط سيناء، يُسمح فيها بكتائب حرس حدود مسلحة بأسلحة خفيفة ومركبات مدولبة.\n"
            "- المنطقة (ج): تشمل الشريط الحدودي الملاصق للحدود الدولية وخليج العقبة، تتمركز فيها قوات الشرطة المدنية وقوات حفظ السلام الدولية (MFO).\n"
            "- المنطقة (د): شريط ضيق داخل الأراضي الإسرائيلية (بعرض 3-4 كم)، يُسمح فيه بانتشار محدود لأربع كتائب مشاة دون دبابات أو مدفعية ثقيلة.\n"
            "2. آلية الأنشطة المتفق عليها (Agreed Activities Mechanism): تم تفعيلها بتوافق ثنائي مشترك لمكافحة الإرهاب، "
            "مما أتاح لمصر زيادة تسليح وانتشار القوات المسلحة وطائرات الأباتشي والمقاتلات في المنطقتين (ب) و(ج) لشمال سيناء لدحر التنظيمات المسلحة.\n"
            "3. السيادة الوطنية على الحدود ومحور فيلادلفيا: ترفض مصر رفضاً قاطعاً أي تعديل أحادي الجانب أو وجود عسكري إسرائيلي دائم "
            "في محور فيلادلفيا أو معبر رفح، وتؤكد على السيادة التامة والإشراف الفلسطيني-المصري المشترك وفق الاتفاقيات المعتمدة."
        ),
        "reliability": AdmiraltyReliability.A,
        "credibility": AdmiraltyCredibility.ONE,
        "key_entities": [
            "معاهدة السلام 1979", "المنطقة أ و ب و ج", "محور فيلادلفيا", "معبر رفح",
            "القوات متعددة الجنسيات (MFO)", "آلية الأنشطة المتفق عليها"
        ],
        "sources": [
            "نص معاهدة السلام المصرية الإسرائيلية وملحقها العسكري (واشنطن 1979)",
            "وثائق وزارة الخارجية المصرية",
            "Multinational Force and Observers (MFO) Reports"
        ]
    },
    {
        "id": "DOC-MR-008",
        "title_ar": "اتفاقية القسطنطينية 1888 ونظام حرية الملاحة الدولية بقناة السويس",
        "title_en": "1888 Constantinople Convention & Maritime Navigation Regime in the Suez Canal",
        "category": "treaty",
        "country_coverage": ["Egypt", "Regional"],
        "summary": "الميثاق الدولي المنظم لحرية الملاحة البحرية لجميع السفن التجارية والحربية في السلم والحرب، مع حفظ حقوق مصر السيادية في الدفاع الوطني.",
        "content": (
            "تُمثل اتفاقية القسطنطينية الموقعة في 29 أكتوبر 1888 الحجر الأساس للوضع القانوني الدولي لقناة السويس:\n"
            "1. حرية المرور الملاحي (المادة 1): تظل قناة السويس البحرية حرة ومفتوحة دائماً، في وقت الحرب كما في وقت السلم، "
            "لكل سفينة تجارية أو حربية دون تمييز لجنسيتها أو علمها.\n"
            "2. حظر الأعمال العدائية في المجرى الملاحي (المادة 4): لا يجوز ممارسة أي حق من حقوق الحرب أو ارتكاب أي عمل عدائي "
            "أو أي حركة يكون الغرض منها عرقلة الملاحة الحرة في القناة أو في موانئ الدخول، حتى وإن كانت مصر في حالة حرب.\n"
            "3. حقوق مصر السيادية الدفاعية (المادتان 9 و10): يحق للدولة المصرية اتخاذ كافة التدابير والتدخلات الأمنية والعسكرية "
            "اللازمة لضمان أمن الدفاع عن مصر وحفظ النظام العام وسلامة المجرى الملاحي ومنشآته الحيوية."
        ),
        "reliability": AdmiraltyReliability.A,
        "credibility": AdmiraltyCredibility.ONE,
        "key_entities": [
            "اتفاقية القسطنطينية 1888", "قناة السويس", "هيئة قناة السويس",
            "السيادة الوطنية المصرية", "حرية المرور الملاحي"
        ],
        "sources": [
            "نص اتفاقية القسطنطينية 1888 (الوثائق الرسمية)",
            "موسوعة المعاهدات الدولية - الأمم المتحدة",
            "الجريدة الرسمية لجمهورية مصر العربية"
        ]
    },
    {
        "id": "DOC-RSC-009",
        "title_ar": "ميثاق مجلس الدول العربية والأفريقية المطلة على البحر الأحمر وخليج عدن",
        "title_en": "Charter of the Council of Arab & African States Bordering the Red Sea & Gulf of Aden",
        "category": "treaty",
        "country_coverage": ["Egypt", "Saudi Arabia", "Yemen", "Sudan", "Jordan", "Djibouti", "Somalia", "Regional"],
        "summary": "الإطار المؤسسي الإقليمي (الرياض 2020) لحماية أمن الممرات المائية، مكافحة القرصنة والإرهاب، ومنع التواجد العسكري الأجنبي غير المتوافق عليه.",
        "content": (
            "تأسس مجلس الدول المشاطئة للبحر الأحمر وخليج عدن في يناير 2020 بمشاركة 8 دول مطلة (مصر، السعودية، السودان، الأردن، اليمن، جيبوتي، الصومال، وإريتريا مراقباً):\n"
            "1. الأهداف الجيوسياسية: حماية أمن وحرية الملاحة الدولية في البحر الأحمر ومضيق باب المندب، "
            "ومنع أي قوى إقليمية غير عربية أو غير مشاطئة من تحويل البحر الأحمر إلى مسرح لصراعات النفوذ والوكالة.\n"
            "2. التعاون الأمني المشترك: تبادل المعلومات الاستخباراتية البحرية لمكافحة شبكات تهريب الأسلحة والمخدرات، ومكافحة القرصنة والهجمات الحوثية غير النمطية.\n"
            "3. التعاون الاقتصادي والبيئي: تنمية الموانئ وحماية البيئة البحرية والشعب المرجانية، وتأمين كابلات الاتصالات البحرية التي يمر منها نحو 17% من حركة الإنترنت العالمية."
        ),
        "reliability": AdmiraltyReliability.A,
        "credibility": AdmiraltyCredibility.ONE,
        "key_entities": [
            "مجلس الدول المشاطئة للبحر الأحمر", "مضيق باب المندب", "خليج عدن",
            "الأسطول الجنوبي المصري", "الأمن البحري الإقليمي"
        ],
        "sources": [
            "ميثاق تأسيس مجلس الدول المشاطئة للبحر الأحمر وخليج عدن (الرياض 2020)",
            "بيانات وزارة الخارجية المصرية",
            "Arab Gulf States Institute in Washington (AGSIW)"
        ]
    },
    {
        "id": "DOC-ARM-010",
        "title_ar": "توازنات التسليح وشبكات الدفاع الجوي المتكامل في الشرق الأوسط",
        "title_en": "Regional Arms Balances, Air Superiority & Integrated Air Defense Umbrella",
        "category": "military_analysis",
        "country_coverage": ["Egypt", "Israel", "Libya", "Regional"],
        "summary": "تقييم ترسانات المقاتلات متعددة المهام (الرافال، F-16، F-35)، شبكات الدفاع الجوي الصاروخي متعددة الطبقات، والقدرات البحرية الهجومية والدفاعية.",
        "content": (
            "يخضع ميزان القوى العسكري في الشرق الأوسط لمعادلات التفوق التكنولوجي والردع التراكمي:\n"
            "1. التفوق الجوي والضربات الدقيقة:\n"
            "- القوات الجوية المصرية: تعتمد على تنويع مصادر التسليح الاستراتيجي بمقاتلات الرافال الفرنسية (Dassault Rafale F3R) المسلحة بصواريخ ميتيور (Meteor) وسكالب (SCALP EG)، "
            "ومقاتلات MiG-29M2 و F-16 Block 52 وطائرات الإنذار المبكر E-2C Hawkeye.\n"
            "- إسرائيل: تحتفظ بالتفوق النوعي بمقاتلات الجيل الخامس الشبحية F-35I Adir وقنابل الاختراق الموجهة JDAM.\n"
            "2. مظلة الدفاع الجوي المتكامل:\n"
            "تمتلك مصر شبكة دفاع جوي هي الأكثر كثافة إقليمياً، تدمج بين المنظومات الروسية بعيدة المدى (S-300VM / Antey-2500) "
            "ومتوسطة المدى (Buk-M2E، Pechora-2M) وقصيرة المدى (Tor-M2E)، بالإضافة إلى المنظومات الألمانية المتقدمة (IRIS-T SLM/SLX) "
            "ورادارات الإنذار المبكر ثلاثية الأبعاد (منظومات القائد ورادار رادار الميدان)، لتوفير تغطية 360 درجة ضد الصواريخ الباليستية والمجنحة والطائرات المسيرة.\n"
            "3. الردع البحري في الأعماق: غواصات تايب 209/1400 الألمانية وفرقاطات الفريم وميكو A-200 تمنح البحرية المصرية قدرات فرض حظر بحري واستهداف الأعماق الساحلية."
        ),
        "reliability": AdmiraltyReliability.A,
        "credibility": AdmiraltyCredibility.ONE,
        "key_entities": [
            "مقاتلات الرافال F3R", "منظومة الدفاع الجوي S-300VM", "منظومة IRIS-T SLM",
            "غواصات تايب 209", "حاملة المروحيات ميسترال", "قوات الدفاع الجوي المصرية"
        ],
        "sources": [
            "The Military Balance 2025 - International Institute for Strategic Studies (IISS)",
            "Stockholm International Peace Research Institute (SIPRI) Arms Transfers Database",
            "Jane's Defence Weekly"
        ]
    }
]


def ingest_from_json_file(file_path: Path, engine: KnowledgeEngine) -> int:
    """Read a JSON file containing one or more KnowledgeDocument items and ingest them."""
    if not file_path.exists():
        log.error("File not found: %s", file_path)
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data if isinstance(data, list) else [data]
    count = 0
    for item in items:
        try:
            doc = KnowledgeDocument(**item)
            engine.ingest_document(doc)
            count += 1
            log.info("✓ Successfully ingested: [%s] %s", doc.id, doc.title_ar)
        except Exception as e:
            log.error("✗ Failed to ingest item: %s. Error: %s", item.get("id", "UNKNOWN"), e)
    return count


def ingest_from_markdown_file(file_path: Path, engine: KnowledgeEngine) -> Optional[KnowledgeDocument]:
    """Parse a Markdown document with YAML/JSON frontmatter or structured headers and ingest it."""
    if not file_path.exists():
        log.error("File not found: %s", file_path)
        return None

    text = file_path.read_text(encoding="utf-8")
    doc_id = f"DOC-MD-{file_path.stem.upper()}"
    title_ar = file_path.stem
    title_en = file_path.name
    category = "military_analysis"
    countries = ["Regional"]
    summary = text[:200].replace("\n", " ") + "..."

    doc = KnowledgeDocument(
        id=doc_id,
        title_ar=title_ar,
        title_en=title_en,
        category=category,
        country_coverage=countries,
        summary=summary,
        content=text,
        reliability=AdmiraltyReliability.B,
        credibility=AdmiraltyCredibility.TWO,
        key_entities=[file_path.stem],
        sources=[file_path.name]
    )
    engine.ingest_document(doc)
    log.info("✓ Ingested Markdown document: [%s] %s", doc.id, doc.title_ar)
    return doc


def seed_expanded_library(engine: KnowledgeEngine) -> int:
    """Seed comprehensive defense treaties, boundary annexes, and arms balance analyses."""
    count = 0
    for item in EXPANDED_STRATEGIC_DOCUMENTS:
        doc = KnowledgeDocument(**item)
        engine.ingest_document(doc)
        count += 1
        log.info("✓ Seeded strategic document: [%s] %s", doc.id, doc.title_ar)
    return count


def main():
    parser = argparse.ArgumentParser(description="Strategic OSIRIS - Knowledge Base Document Ingestion")
    parser.add_argument("--seed-expanded", action="store_true", help="Seed 4 major regional treaties & defense documents")
    parser.add_argument("--file", type=str, help="Path to JSON or Markdown file to ingest")
    parser.add_argument("--dir", type=str, help="Directory containing JSON and MD files to ingest")
    parser.add_argument("--list", action="store_true", help="List all documents currently in the knowledge base")

    args = parser.parse_args()

    engine = knowledge_engine

    if args.seed-expanded if hasattr(args, "seed-expanded") else args.seed_expanded:
        log.info("Seeding expanded strategic doctrine and treaty library...")
        seeded = seed_expanded_library(engine)
        log.info("Finished seeding %d documents.", seeded)

    if args.file:
        p = Path(args.file)
        if p.suffix.lower() == ".json":
            ingest_from_json_file(p, engine)
        elif p.suffix.lower() in (".md", ".txt"):
            ingest_from_markdown_file(p, engine)
        else:
            log.error("Unsupported file extension: %s. Use .json, .md, or .txt", p.suffix)

    if args.dir:
        folder = Path(args.dir)
        if folder.exists() and folder.is_dir():
            count = 0
            for fp in folder.glob("*.json"):
                count += ingest_from_json_file(fp, engine)
            for fp in folder.glob("*.md"):
                if ingest_from_markdown_file(fp, engine):
                    count += 1
            log.info("Ingested %d total documents from directory %s", count, folder)
        else:
            log.error("Directory not found: %s", folder)

    if args.list or len(sys.argv) == 1:
        docs = engine.get_all()
        print(f"\n================ STRATEGIC KNOWLEDGE BASE REPOSITORY ({len(docs)} Documents) ================")
        for d in docs:
            print(f"[{d.id}] ({d.category.upper()}) {d.title_ar}")
            print(f"   Countries: {', '.join(d.country_coverage)} | Admiralty: {d.reliability.value}{d.credibility.value}")
            print(f"   Entities: {', '.join(d.key_entities[:4])}")
            print("-" * 80)


if __name__ == "__main__":
    main()
