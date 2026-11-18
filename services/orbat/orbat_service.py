"""Order of Battle (ORBAT) Service.

Connects directly to GeoConfirmed ORBAT API (https://geoconfirmed.org/api/orbat),
extracts official military unit insignias/logos/emblems, and provides comprehensive,
hierarchical command structures for all 21+ global and regional military theaters.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional
from packages.schemas.models import OrbatCatalogItem, OrbatTreeResponse, OrbatUnit


CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "orbat_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

GEOCONFIRMED_BASE_URL = "https://geoconfirmed.org"


class OrbatService:
    """Manages Order of Battle (ORBAT) catalogs, GeoConfirmed live sync, and unit hierarchies."""

    # Curated Catalog Definitions mapping URL slugs to GeoConfirmed node IDs and metadata
    BUILTIN_CATALOGS: List[Dict[str, Any]] = [
        {"id": 100, "node_id": 100, "code": "Egypt", "name": "القوات المسلحة المصرية (Egyptian Armed Forces)", "url_name": "egypt", "country": "Egypt", "flag": "🇪🇬", "is_geoconfirmed": False},
        {"id": 101, "node_id": 101, "code": "Libya", "name": "التشكيلات العسكرية في ليبيا (LNA & GNU)", "url_name": "libya", "country": "Libya", "flag": "🇱🇾", "is_geoconfirmed": False},
        {"id": 5, "node_id": 34, "code": "Israel", "name": "Israel Defense Forces (IDF)", "url_name": "israel", "country": "Israel", "flag": "🇮🇱", "is_geoconfirmed": True},
        {"id": 9, "node_id": 38, "code": "PalestinianFactions", "name": "Middle Eastern Factions (فصائل المقاومة والشرق الأوسط)", "url_name": "middleeasternfactions", "country": "Regional", "flag": "🇵🇸", "is_geoconfirmed": True},
        {"id": 39, "node_id": 10405, "code": "Yemen", "name": "Yemeni Armed Forces & Formations (القوات اليمنية)", "url_name": "yemen", "country": "Yemen", "flag": "🇾🇪", "is_geoconfirmed": True},
        {"id": 35, "node_id": 6474, "code": "SyriaNew", "name": "Syrian Formations (القوات السورية)", "url_name": "syrianew", "country": "Syria", "flag": "🇸🇾", "is_geoconfirmed": True},
        {"id": 25, "node_id": 989, "code": "Iran", "name": "Armed Forces of the Islamic Republic of Iran", "url_name": "iran", "country": "Iran", "flag": "🇮🇷", "is_geoconfirmed": True},
        {"id": 26, "node_id": 1136, "code": "Sudan", "name": "Sudanese Armed Forces (القوات المسلحة السودانية)", "url_name": "sudan", "country": "Sudan", "flag": "🇸🇩", "is_geoconfirmed": True},
        {"id": 27, "node_id": 1137, "code": "SudanFactions", "name": "Sudan Conflict Factions (قوات الدعم السريع والفصائل)", "url_name": "sudan-factions", "country": "Sudan", "flag": "🇸🇩", "is_geoconfirmed": True},
        {"id": 10, "node_id": 24, "code": "Russia", "name": "Russian Armed Forces (القوات المسلحة الروسية)", "url_name": "russia", "country": "Russia", "flag": "🇷🇺", "is_geoconfirmed": True},
        {"id": 31, "node_id": 4339, "code": "US", "name": "United States Armed Forces", "url_name": "us", "country": "United States", "flag": "🇺🇸", "is_geoconfirmed": True},
        {"id": 15, "node_id": 33, "code": "Ukraine", "name": "Ukrainian Armed Forces (ZSU)", "url_name": "ukraine", "country": "Ukraine", "flag": "🇺🇦", "is_geoconfirmed": True},
        {"id": 1039, "node_id": 11456, "code": "ENDF", "name": "Ethiopian National Defense Force (ENDF)", "url_name": "endf", "country": "Ethiopia", "flag": "🇪🇹", "is_geoconfirmed": True},
        {"id": 2, "node_id": 36, "code": "China", "name": "Chinese People's Liberation Army (PLA)", "url_name": "china", "country": "China", "flag": "🇨🇳", "is_geoconfirmed": True},
        {"id": 36, "node_id": 6825, "code": "France", "name": "French Armed Forces", "url_name": "france", "country": "France", "flag": "🇫🇷", "is_geoconfirmed": True},
        {"id": 38, "node_id": 9282, "code": "Terrorist", "name": "Militant / Irregular Factions", "url_name": "terroristmilitant", "country": "Regional", "flag": "⚠️", "is_geoconfirmed": True},
        {"id": 37, "node_id": 9276, "code": "Fama", "name": "Malian Armed Forces (FAMa)", "url_name": "fama", "country": "Mali", "flag": "🇲🇱", "is_geoconfirmed": True},
        {"id": 34, "node_id": 6034, "code": "KHM", "name": "Royal Cambodian Armed Forces", "url_name": "cambodia", "country": "Cambodia", "flag": "🇰🇭", "is_geoconfirmed": True},
        {"id": 33, "node_id": 6033, "code": "THA", "name": "Royal Thai Armed Forces", "url_name": "thailand", "country": "Thailand", "flag": "🇹🇭", "is_geoconfirmed": True},
        {"id": 11, "node_id": 52, "code": "Rwanda", "name": "Rwanda Defence Force", "url_name": "rwanda", "country": "Rwanda", "flag": "🇷🇼", "is_geoconfirmed": True},
        {"id": 32, "node_id": 4340, "code": "VEN", "name": "National Bolivarian Armed Forces (FANB)", "url_name": "ven", "country": "Venezuela", "flag": "🇻🇪", "is_geoconfirmed": True},
        {"id": 29, "node_id": 2048, "code": "Myanmar", "name": "Myanmar Armed Forces (Tatmadaw)", "url_name": "myanmar", "country": "Myanmar", "flag": "🇲🇲", "is_geoconfirmed": True},
        {"id": 28, "node_id": 2047, "code": "MyanmarO", "name": "Myanmar Opposition Forces", "url_name": "myanmaro", "country": "Myanmar", "flag": "🇲🇲", "is_geoconfirmed": True}
    ]

    def __init__(self):
        self._local_units: Dict[str, OrbatUnit] = {}
        self._cached_trees: Dict[str, OrbatTreeResponse] = {}
        self._init_local_egypt_and_libya()

    def get_catalogs(self) -> List[OrbatCatalogItem]:
        """Return all available ORBAT catalogs (GeoConfirmed + Local)."""
        items: List[OrbatCatalogItem] = []
        for cat in self.BUILTIN_CATALOGS:
            items.append(OrbatCatalogItem(
                id=cat["id"],
                code=cat["code"],
                name=cat["name"],
                url_name=cat["url_name"],
                node_id=cat["node_id"],
                country=cat["country"],
                flag=cat.get("flag", "🌐"),
                is_geoconfirmed=cat["is_geoconfirmed"]
            ))
        return items

    def _init_local_egypt_and_libya(self):
        """Seed high-fidelity Egyptian Armed Forces & Libyan Formations with official emblems."""
        units: List[OrbatUnit] = [
            # ── EGYPTIAN ARMED FORCES (EAF) ──
            OrbatUnit(
                id="EAF-GHQ",
                name_ar="القيادة العامة للقوات المسلحة المصرية",
                name_en="Egyptian Armed Forces GHQ & General Staff",
                country="Egypt",
                echelon="GHQ",
                branch="Joint",
                hq_location="مجمع القيادة الاستراتيجية (الأوكتاجون) - العاصمة الإدارية / القاهرة",
                commander="القائد العام للقوات المسلحة وزير الدفاع والإنتاج الحربي",
                role_and_mission="القيادة العليا والسيطرة الاستراتيجية على كافة أفرع وتشكيلات القوات المسلحة وإدارة مسارح العمليات وتأمين السيادة الوطنية الشاملة.",
                equipment=["شبكات القيادة والسيطرة C4ISR المشتركة", "منظومات الأقمار الصناعية العسكرية (طيبة-1)", "مراكز العمليات المشتركة المؤمنة"],
                readiness_status="High Readiness",
                parent_id=None,
                badge_symbol="🦅",
                badge_color="#10b981",
                logo_url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Eagle_of_Saladin_%28Egyptian_Armed_Forces%29.svg/200px-Eagle_of_Saladin_%28Egyptian_Armed_Forces%29.svg.png",
                logos=["https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Eagle_of_Saladin_%28Egyptian_Armed_Forces%29.svg/200px-Eagle_of_Saladin_%28Egyptian_Armed_Forces%29.svg.png"]
            ),
            OrbatUnit(
                id="EAF-WEST-ZONE",
                name_ar="قيادة المنطقة الغربية العسكرية",
                name_en="Western Military Zone Command",
                country="Egypt",
                echelon="Theatre",
                branch="Ground",
                hq_location="سيدي براني / مرسى مطروح",
                commander="قائد المنطقة الغربية العسكرية",
                role_and_mission="تأمين الاتجاه الاستراتيجي الغربي بالكامل والعمق الصحراوي مع ليبيا، وحماية الشريط الحدودي ومكافحة التسلل والتهريب العابر للحدود.",
                equipment=["دبابات قتال رئيسية M1A1 Abrams", "مركبات مدرعة YPR-765 / BMP-1", "منظومات رادار كشف بعيد المدى", "طائرات بدون طيار للمراقبة الحدودية"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="🛡️",
                badge_color="#10b981",
                logo_url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Eagle_of_Saladin_%28Egyptian_Armed_Forces%29.svg/200px-Eagle_of_Saladin_%28Egyptian_Armed_Forces%29.svg.png"
            ),
            OrbatUnit(
                id="EAF-BDE-BORDER-WEST",
                name_ar="لواء حرس الحدود الغربي وأفواج الهجانة",
                name_en="Western Border Guard Brigade",
                country="Egypt",
                echelon="Brigade",
                branch="Border Guard",
                hq_location="منفذ السلوم البري / خط الحدود الدولية",
                commander="قائد قطاع حرس الحدود الغربي",
                role_and_mission="إحكام السيطرة التامة على منفذ السلوم الدولي، وتسيير دوريات رادارية واستطلاع راكب على امتداد السلك الحدودي الفاصل مع الشرق الليبي.",
                equipment=["مركبات مصفحة طراز تمساح وفهد", "أنظمة استشعار حراري وأبراج مراقبة إلكترونية", "طائرات خفيفة للدوريات الصحراوية"],
                readiness_status="High Readiness",
                parent_id="EAF-WEST-ZONE",
                badge_symbol="🐪",
                badge_color="#059669"
            ),
            OrbatUnit(
                id="EAF-BASE-JULY3",
                name_ar="قاعدة 3 يوليو البحرية والأسطول الشمالي",
                name_en="July 3 Naval Base & Northern Fleet",
                country="Egypt",
                echelon="Base",
                branch="Naval",
                hq_location="منطقة جرجوب - الساحل الشمالي الغربي (البحر المتوسط)",
                commander="قائد الأسطول الشمالي وقاعدة 3 يوليو",
                role_and_mission="حماية المقدرات الاقتصادية وحقول الغاز بشرق وشمال المتوسط وتأمين خطوط الملاحة البحرية وردع أي تهديدات ساحلية على الاتجاه الغربي.",
                equipment=["فرقاطات FREMM (برجاميني وتحيا مصر)", "غواصات طراز تايب 209 الألمانية", "كورفيتات جويند Gowind 2500", "زوارق صواريخ أمباسادور وسوبر فيتا"],
                readiness_status="High Readiness",
                parent_id="EAF-WEST-ZONE",
                badge_symbol="⚓",
                badge_color="#0284c7"
            ),
            OrbatUnit(
                id="EAF-DIV-33-MECH",
                name_ar="الفرقة 33 مشاة ميكانيكية",
                name_en="33rd Mechanized Infantry Division",
                country="Egypt",
                echelon="Division",
                branch="Ground",
                hq_location="محور مطروح - السلوم",
                commander="قائد الفرقة 33 ميكانيكي",
                role_and_mission="الرد السريع وتشكيل نسق دفاعي تعبوي مانع في عمق القطاع الغربي للتعامل مع أي خروقات أمنية كبرى.",
                equipment=["مدرعات M113A2", "مدافع هاوتزر ذاتية الحركة M109A2", "راجمات صواريخ صقر", "صواريخ تاو المضادة للدروع"],
                readiness_status="Patrol/Deterrence",
                parent_id="EAF-WEST-ZONE",
                badge_symbol="⚔️",
                badge_color="#059669"
            ),
            OrbatUnit(
                id="EAF-BDE-AIRDEF-WEST",
                name_ar="لواء الدفاع الجوي التعبوي الغربي",
                name_en="Western Air Defense Brigade",
                country="Egypt",
                echelon="Brigade",
                branch="Air Defense",
                hq_location="نطاق السلوم وقاعدة جرجوب",
                commander="قائد لواء الدفاع الجوي",
                role_and_mission="فرض مظلة حظر جوي وحماية المنشآت الحيوية والقواعد العسكرية الساحلية ضد أي اختراق جوي أو طائرات مسيرة معادية.",
                equipment=["منظومات Antey-2500 (S-300VM)", "منظومات بوك إم 2 (Buk-M2E)", "منظومات تور إم 2 (Tor-M2)", "رادارات إنذار مبكر رنان وبروتيفنيك"],
                readiness_status="High Readiness",
                parent_id="EAF-WEST-ZONE",
                badge_symbol="🛡️",
                badge_color="#0d9488"
            ),

            # ── 2nd Field Army ──
            OrbatUnit(
                id="EAF-2ND-ARMY",
                name_ar="قيادة الجيش الثاني الميداني",
                name_en="2nd Field Army Command",
                country="Egypt",
                echelon="Army",
                branch="Ground",
                hq_location="الإسماعيلية / قطاع شمال سيناء",
                commander="قائد الجيش الثاني الميداني",
                role_and_mission="تأمين الاتجاه الاستراتيجي الشمالي الشرقي، وحماية المجرى الملاحي لقناة السويس وشمال شبه جزيرة سيناء والحدود الشرقية الدولية.",
                equipment=["دبابات قتال M1A1 Abrams", "مركبات قتال مشاة مصفحة", "مدفعية ثقيلة وصاروخية بعيدة المدى", "مروحيات هجومية أباتشي AH-64D"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="⚔️",
                badge_color="#10b981"
            ),
            OrbatUnit(
                id="EAF-DIV-18-MECH",
                name_ar="الفرقة 18 مشاة ميكانيكية",
                name_en="18th Mechanized Infantry Division",
                country="Egypt",
                echelon="Division",
                branch="Ground",
                hq_location="القنطرة شرق / بئر العبد - شمال سيناء",
                commander="قائد الفرقة 18 ميكانيكي",
                role_and_mission="تأمين المحاور والدروب التعبوية المؤدية إلى عمق سيناء وتأمين الضفة الشرقية لقناة السويس.",
                equipment=["ناقلات جند مدرعة YPR", "دبابات M1A1", "راجمات صواريخ كاتيوشا وصقر 45"],
                readiness_status="High Readiness",
                parent_id="EAF-2ND-ARMY",
                badge_symbol="🛡️",
                badge_color="#059669"
            ),
            OrbatUnit(
                id="EAF-DIV-6-ARMOR",
                name_ar="الفرقة 6 مدرعة",
                name_en="6th Armored Division",
                country="Egypt",
                echelon="Division",
                branch="Ground",
                hq_location="وسط سيناء / الإسماعيلية",
                commander="قائد الفرقة 6 مدرع",
                role_and_mission="القوة الضاربة التعبوية للردع والمناورة السريعة في المسرح السيناوي وصد أي محاولات اختراق مدرعة.",
                equipment=["ألوية دبابات أبرامز الحديثة", "مركبات قتال برادلي ومدرعات سيناتور", "مدافع هاوتزر K9A1EGY الموجهة"],
                readiness_status="High Readiness",
                parent_id="EAF-2ND-ARMY",
                badge_symbol="⚡",
                badge_color="#059669"
            ),
            OrbatUnit(
                id="EAF-BDE-BORDER-SINAI",
                name_ar="لواء حرس الحدود بشمال سيناء ومنافذ رفح",
                name_en="Sinai Border Guard Brigade (Rafah Sector)",
                country="Egypt",
                echelon="Brigade",
                branch="Border Guard",
                hq_location="رفح المصرية / الشيخ زويد / محور الحدود",
                commander="قائد قطاع حدود رفح",
                role_and_mission="تأمين خط الحدود الدولية مع قطاع غزة وإسرائيل، ومنع التسلل والتهريب، وإحكام السيطرة الكاملة على المنفذ الحدودي والمنطقة العازلة.",
                equipment=["مدرعات تمساح شيربا مقاومة للألغام MRAP", "أبراج رصد بانورامية وكاميرات حرارية بعيدة المدى", "معدات كشف الأنفاق التحت أرضية"],
                readiness_status="High Readiness",
                parent_id="EAF-2ND-ARMY",
                badge_symbol="🚧",
                badge_color="#047857"
            ),

            # ── 3rd Field Army ──
            OrbatUnit(
                id="EAF-3RD-ARMY",
                name_ar="قيادة الجيش الثالث الميداني",
                name_en="3rd Field Army Command",
                country="Egypt",
                echelon="Army",
                branch="Ground",
                hq_location="السويس / قطاع وسط وجنوب سيناء",
                commander="قائد الجيش الثالث الميداني",
                role_and_mission="تأمين المدخل الجنوبي لقناة السويس، وتأمين خليج السويس ومضايق البحر الأحمر وشبه جزيرة سيناء الجنوبية وحقول البترول والتعدين.",
                equipment=["دبابات M1A1 Abrams", "مدفعية ذاتية الحركة M109", "مروحيات مقاتلة كاموف Ka-52 وأباتشي"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="⚔️",
                badge_color="#10b981"
            ),
            OrbatUnit(
                id="EAF-DIV-4-ARMOR",
                name_ar="الفرقة 4 مدرعة (فرسان مدرعات القوات المسلحة)",
                name_en="4th Armored Division (Knights of EAF)",
                country="Egypt",
                echelon="Division",
                branch="Ground",
                hq_location="السويس",
                commander="قائد الفرقة 4 مدرع",
                role_and_mission="الاحتياطي الاستراتيجي المدرع الأقوى للدولة المصرية والجاهز للتدخل التعبوي الفوري في أي اتجاه عملياتي حرج.",
                equipment=["ألوية دبابات M1A1 المحدثة", "مركبات قتال مدرعة متطورة", "كتائب دفاع جوي شيلكا وتور إم"],
                readiness_status="High Readiness",
                parent_id="EAF-3RD-ARMY",
                badge_symbol="🛡️",
                badge_color="#059669"
            ),
            OrbatUnit(
                id="EAF-DIV-19-MECH",
                name_ar="الفرقة 19 مشاة ميكانيكية",
                name_en="19th Mechanized Infantry Division",
                country="Egypt",
                echelon="Division",
                branch="Ground",
                hq_location="جنوب سيناء / الطور / شرم الشيخ",
                commander="قائد الفرقة 19 ميكانيكي",
                role_and_mission="تأمين السواحل الجنوبية لسيناء ومضيق تيران والمقرات السيادية والمطارات الدولية بجنوب سيناء.",
                equipment=["مدرعات خفيفة ودبابات دعم", "صواريخ كورنيت المضادة للدروع", "رادارات مراقبة بحرية وجوية"],
                readiness_status="Patrol/Deterrence",
                parent_id="EAF-3RD-ARMY",
                badge_symbol="🌊",
                badge_color="#059669"
            ),

            # ── Navy Southern Fleet & Berenice Base ──
            OrbatUnit(
                id="EAF-NAVY-SOUTH",
                name_ar="قيادة الأسطول الجنوبي وقاعدة برنيس العسكرية",
                name_en="Southern Fleet Command & Berenice Base",
                country="Egypt",
                echelon="Base",
                branch="Naval",
                hq_location="قاعدة برنيس العسكرية - رأس بناس (البحر الأحمر)",
                commander="قائد الأسطول الجنوبي بالبحر الأحمر",
                role_and_mission="حماية الملاحة الدولية في البحر الأحمر ومضيق باب المندب وتأمين المداخل الجنوبية لقناة السويس ومنع أي تهديدات بحرية موجهة للمياه السيادية.",
                equipment=["حاملتي المروحيات ميسترال (أنور السادات وجمال عبد الناصر)", "فرقاطات بيري وبيري-Fremm", "كورفيتات ميكو A200 المتطورة", "مروحيات بحرية سي سبرايت وسوبر سي ليون"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="⚓",
                badge_color="#0284c7"
            ),

            # ── Special Forces ──
            OrbatUnit(
                id="EAF-SOF-CMD",
                name_ar="قيادة قوات الصاعقة والمظلات وقوات التدخل السريع",
                name_en="Special Operations Command & Airborne Forces",
                country="Egypt",
                echelon="Corps",
                branch="Special Forces",
                hq_location="إنشاص / القاهرة",
                commander="قائد قوات الصاعقة والمظلات",
                role_and_mission="تنفيذ العمليات الخاصة النوعية خلف خطوط العدو، ومكافحة الإرهاب عالي الخطورة، والانتشار السريع المنقول جواً عبر أي جبهة استراتيجية.",
                equipment=["أسلحة هجومية خاصة وتصويب ليزري", "مروحيات إنزال Chinook CH-47 ومي-24", "عربات صاعقة خفيفة ومظلات تكتيكية"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="⚡",
                badge_color="#f59e0b"
            ),
            OrbatUnit(
                id="EAF-UNIT-777",
                name_ar="الوحدة 777 قتال (مكافحة الإرهاب الدولي)",
                name_en="Task Unit 777 (CT & Hostage Rescue)",
                country="Egypt",
                echelon="Special_Unit",
                branch="Special Forces",
                hq_location="القاهرة",
                commander="قائد الوحدة 777",
                role_and_mission="عمليات تحرير الرهائن ومكافحة الإرهاب الدولي والاقتحام التكتيكي فائق الدقة في كافة البيئات البرية والبحرية والجوية.",
                equipment=["بنادق قنص Sig Sauer و Barrett", "معدات رؤية ليلية جيل رابع", "مركبات اقتحام مدرعة خفيفة"],
                readiness_status="High Readiness",
                parent_id="EAF-SOF-CMD",
                badge_symbol="🎯",
                badge_color="#d97706"
            ),
            OrbatUnit(
                id="EAF-UNIT-999",
                name_ar="الوحدة 999 قتال (العمليات الخاصة خلف الخطوط)",
                name_en="Task Unit 999 (Strategic Recon & Deep Strikes)",
                country="Egypt",
                echelon="Special_Unit",
                branch="Special Forces",
                hq_location="إنشاص",
                commander="قائد الوحدة 999",
                role_and_mission="الاستطلاع الاستراتيجي والعمليات الخاصة العميقة والإغارة التخريبية على خطوط إمداد العدو ومراكزه الحيوية.",
                equipment=["تجهيزات إنزال مظلي حر HALO/HAHO", "أسلحة كتم صوت ومعدات تفجير موجّهة", "أجهزة اتصال وتحديد أهداف عبر الأقمار الصناعية"],
                readiness_status="High Readiness",
                parent_id="EAF-SOF-CMD",
                badge_symbol="🦅",
                badge_color="#d97706"
            ),
            OrbatUnit(
                id="EAF-AIRFORCE",
                name_ar="قيادة القوات الجوية المصرية",
                name_en="Egyptian Air Force (EAF Command)",
                country="Egypt",
                echelon="Corps",
                branch="Air Force",
                hq_location="القاهرة / شبكة القواعد الجوية المشتركة",
                commander="قائد القوات الجوية",
                role_and_mission="السيادة الجوية، الاعتراض التكتيكي، والضربات الاستراتيجية بعيدة المدى وتوفير الدعم والإسناد الجوي القريب لكافة التشكيلات البرية والبحرية.",
                equipment=["مقاتلات Rafale F3R الفرنسية", "مقاتلات F-16 C/D Block 52", "مقاتلات MiG-29M/M2 الروسية", "طائرات الإنذار المبكر E-2C Hawkeye", "مسيرات Wing Loong II المسلحة"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="✈️",
                badge_color="#38bdf8"
            ),
            OrbatUnit(
                id="EAF-AIRDEFENSE",
                name_ar="قيادة قوات الدفاع الجوي المصري",
                name_en="Egyptian Air Defense Command (EADC)",
                country="Egypt",
                echelon="Corps",
                branch="Air Defense",
                hq_location="القاهرة / شبكة مراكز القيادة والإنذار",
                commander="قائد قوات الدفاع الجوي",
                role_and_mission="تأمين المجال الجوي السيادي بالكامل وشل قدرة العدو الجوية وتدمير الصواريخ الباليستية والمجنحة والطائرات المسيرة في كافة الارتفاعات.",
                equipment=["منظومات S-300VM / Antey-2500", "منظومات IRIS-T SLM الألمانية", "منظومات Buk-M2E و Tor-M2", "منظومات بيتشورا 2M المطورة", "شبكة رادارات ثلاثية الأبعاد متعددة الطبقات"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="🛡️",
                badge_color="#0d9488"
            ),

            # ── LIBYAN FORMATIONS ──
            OrbatUnit(
                id="LNA-GHQ",
                name_ar="القيادة العامة للقوات المسلحة بالشرق الليبي (LNA)",
                name_en="Libyan National Army GHQ (Eastern Command)",
                country="Libya",
                echelon="GHQ",
                branch="Joint",
                hq_location="الرجمة / بنغازي",
                commander="القائد العام للقوات المسلحة بالشرق",
                role_and_mission="السيطرة العسكرية على إقليم برقة والهلال النفطي والجنوب الشرقي وتأمين الحدود المشتركة مع مصر وتشاد.",
                equipment=["دبابات T-72 و T-62", "مركبات قتال مدرعة BMP-2", "مقاتلات MiG-21 و MiG-23 وسوخوي Su-24", "منظومات دفاع جوي بانتسير Pantsir-S1"],
                readiness_status="High Readiness",
                parent_id=None,
                badge_symbol="🇱🇾",
                badge_color="#f59e0b"
            ),
            OrbatUnit(
                id="LNA-BDE-106",
                name_ar="اللواء 106 مجحفل (النخبة المدرعة)",
                name_en="106th Reinforced Brigade (LNA Elite Armor)",
                country="Libya",
                echelon="Brigade",
                branch="Ground",
                hq_location="بنغازي / الهلال النفطي",
                commander="قيادة اللواء 106",
                role_and_mission="القوة الضاربة الرئيسية لقوات الشرق، تأمين المواقع والموانئ الحيوية والتدخل التكتيكي السريع في مسارح العمليات.",
                equipment=["دبابات قتال رئيسية T-72 حديثة", "مدرعات مدولبة BTR ومصفحات النمر", "مدافع هاوتزر وراجمات جراد"],
                readiness_status="High Readiness",
                parent_id="LNA-GHQ",
                badge_symbol="⚔️",
                badge_color="#d97706"
            ),
            OrbatUnit(
                id="LNA-BDE-TBZ",
                name_ar="لواء طارق بن زياد المعزز",
                name_en="Tariq bin Ziyad Enhanced Brigade",
                country="Libya",
                echelon="Brigade",
                branch="Ground",
                hq_location="سبها / الجفرة / برقة",
                commander="قيادة لواء طارق بن زياد",
                role_and_mission="الانتشار الميداني الموسع في مدن الجنوب وقاعدة الجفرة والسيطرة على تقاطعات الطرق الصحراوية الإقليمية.",
                equipment=["عربات مسلحة دفع رباعي تويوتا مجهزة برشاشات ثقيلة", "مدرعات قتال ومدافع هاون", "صواريخ كورنيت موجهة"],
                readiness_status="High Readiness",
                parent_id="LNA-GHQ",
                badge_symbol="🛡️",
                badge_color="#d97706"
            ),
            OrbatUnit(
                id="LNA-PFG-OIL",
                name_ar="حرس المنشآت النفطية بالهلال النفطي",
                name_en="Petroleum Facilities Guard (Oil Crescent Sector)",
                country="Libya",
                echelon="Regiment",
                branch="Border Guard",
                hq_location="رأس لانوف / السدرة / البريقة",
                commander="آمر قطاع حرس المنشآت النفطية",
                role_and_mission="تأمين موانئ تصدير النفط الرئيسية وحقول الإنتاج بالهلال النفطي ومنع أي اعتداء أو تخريب للمنشآت الحيوية.",
                equipment=["عربات دوريات صحراوية مسلحة", "معدات رصد ومراقبة للمحطات والموانئ", "أسلحة خفيفة ومتوسطة"],
                readiness_status="Patrol/Deterrence",
                parent_id="LNA-GHQ",
                badge_symbol="🛢️",
                badge_color="#b45309"
            ),
            OrbatUnit(
                id="GNU-GHQ",
                name_ar="رئاسة الأركان العامة وقوات الغرب الليبي (طرابلس)",
                name_en="GNU General Staff & Western Tripoli Formations",
                country="Libya",
                echelon="GHQ",
                branch="Joint",
                hq_location="طرابلس / السرايا الحمراء وقاعدة معيتيقة",
                commander="رئيس الأركان العامة للجيش الليبي (طرابلس)",
                role_and_mission="السيطرة الإدارية والميدانية على العاصمة طرابلس والمنطقة الغربية والمنافذ البحرية والجوية بالتنسيق مع الحلفاء الإقليميين.",
                equipment=["مركبات مصفحة تركية Kirpi و Vuran", "مسيرات بيرقدار Bayraktar TB2", "منظومات دفاع جوي متوسط وقصير المدى Hawk"],
                readiness_status="High Readiness",
                parent_id=None,
                badge_symbol="🏛️",
                badge_color="#f59e0b"
            ),
            OrbatUnit(
                id="GNU-BDE-444",
                name_ar="اللواء 444 قتال (المنطقة العسكرية طرابلس)",
                name_en="444th Combat Brigade (Tripoli Military Zone)",
                country="Libya",
                echelon="Brigade",
                branch="Ground",
                hq_location="طرابلس / ترهونة / بني وليد",
                commander="محمود حمزة (آمر اللواء)",
                role_and_mission="ضبط الأمن ومكافحة عصابات التهريب والهجرة غير الشرعية وتأمين خطوط الإمداد الحيوية الرابطة بين العاصمة والجنوب الغربي.",
                equipment=["مدرعات Kirpi تركية الصنع", "أطقم هاون ومدافع خفيفة", "عربات دفع رباعي مصفحة للتدخل السريع"],
                readiness_status="Active Combat",
                parent_id="GNU-GHQ",
                badge_symbol="⚔️",
                badge_color="#d97706"
            ),
            OrbatUnit(
                id="GNU-DEV-RADAA",
                name_ar="جهاز الردع لمكافحة الإرهاب والجريمة المنظمة",
                name_en="Special Deterrence Force (Radaa Counter-Terrorism)",
                country="Libya",
                echelon="Special_Unit",
                branch="Special Forces",
                hq_location="قاعدة ومطار معيتيقة الدولي - طرابلس",
                commander="عبد الرؤوف كارة",
                role_and_mission="تأمين مطار معيتيقة والمؤسسات السيادية بالعاصمة وملاحقة الخلايا الإرهابية وشبكات الجريمة المنظمة.",
                equipment=["مركبات مصفحة تكتيكية", "أسلحة رشاشة وقناصات حديثة", "شبكات اتصالات واستخبارات داخلية"],
                readiness_status="High Readiness",
                parent_id="GNU-GHQ",
                badge_symbol="🛡️",
                badge_color="#d97706"
            )
        ]

        for u in units:
            self._local_units[u.id] = u

    def fetch_geoconfirmed_node_data(self, node_id: int) -> Optional[Dict[str, Any]]:
        """Fetch node tree from GeoConfirmed or read from disk cache."""
        cache_file = os.path.join(CACHE_DIR, f"geoconfirmed_node_{node_id}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{GEOCONFIRMED_BASE_URL}/api/orbatnode/{node_id}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode("utf-8")
                data = json.loads(content)
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(content)
                return data
        except Exception as e:
            print(f"[OrbatService] Failed to fetch GeoConfirmed node {node_id}: {e}")
            return None

    def _convert_geoconfirmed_node(self, raw: Dict[str, Any], country_name: str, parent_id: Optional[str] = None) -> OrbatUnit:
        """Recursively transform a GeoConfirmed node dictionary into an OrbatUnit."""
        unit_id = f"GC-{raw.get('id')}"
        name = raw.get("name") or "Unnamed Formation"
        native_name = raw.get("nativeName")
        org_level = raw.get("organizationLevel") or self._infer_echelon(name)

        # Parse logos & emblems
        emblems = [x.strip() for x in (raw.get("emblems") or "").split(",") if x.strip()]
        patches = [x.strip() for x in (raw.get("patches") or "").split(",") if x.strip()]
        all_raw_logos = emblems + patches

        resolved_logos: List[str] = []
        for l in all_raw_logos:
            if l.startswith("http://") or l.startswith("https://"):
                resolved_logos.append(l)
            else:
                path = l if l.startswith("/") else f"/{l}"
                resolved_logos.append(f"{GEOCONFIRMED_BASE_URL}{path}")

        primary_logo = resolved_logos[0] if resolved_logos else None

        # Equipment parsing
        equipment: List[str] = []
        if raw.get("gear"):
            equipment.extend([g.strip() for g in str(raw.get("gear")).split(",") if g.strip()][:8])
        if raw.get("gearItems") and isinstance(raw.get("gearItems"), list):
            for gi in raw.get("gearItems")[:6]:
                if isinstance(gi, dict) and gi.get("name"):
                    equipment.append(gi.get("name"))

        role_mission = raw.get("remarks") or f"التشكيل العسكري الرسمي التابع لمسرح العمليات ({country_name})."

        unit = OrbatUnit(
            id=unit_id,
            name_ar=native_name or name,
            name_en=name,
            native_name=native_name,
            country=country_name,
            echelon=org_level,
            branch=raw.get("branch") or self._infer_branch(name),
            hq_location=raw.get("homeBase") or "مسرح العمليات الميداني",
            commander=None,
            role_and_mission=role_mission,
            equipment=equipment,
            readiness_status="High Readiness" if not raw.get("isDisbanded") else "Standby",
            parent_id=parent_id,
            badge_symbol="🛡️" if not primary_logo else "🎖️",
            badge_color=raw.get("color") or "#8b5cf6",
            logo_url=primary_logo,
            logos=resolved_logos,
            unit_number=raw.get("unitNumber"),
            sources=raw.get("sources"),
            geoconfirmed_id=raw.get("id"),
            sub_units=[]
        )

        children = raw.get("children") or []
        for child in children:
            if isinstance(child, dict) and not child.get("isDeleted"):
                child_unit = self._convert_geoconfirmed_node(child, country_name, parent_id=unit_id)
                unit.sub_units.append(child_unit)

        return unit

    def _infer_echelon(self, name: str) -> str:
        """Infer military echelon from formation name."""
        nl = name.lower()
        if any(k in nl for k in ["general staff", "supreme", "headquarters", "ghq", "command"]):
            return "GHQ"
        if "army" in nl or "theatre" in nl or "district" in nl:
            return "Army"
        if "corps" in nl:
            return "Corps"
        if "division" in nl or "flotilla" in nl:
            return "Division"
        if "brigade" in nl or "wing" in nl or "task force" in nl:
            return "Brigade"
        if "regiment" in nl or "group" in nl:
            return "Regiment"
        if "battalion" in nl or "squadron" in nl or "flot" in nl:
            return "Battalion"
        if "base" in nl:
            return "Base"
        if any(k in nl for k in ["special", "commando", "recon", "sof", "spetsnaz"]):
            return "Special_Unit"
        return "Division"

    def _infer_branch(self, name: str) -> str:
        """Infer branch of service from name."""
        nl = name.lower()
        if any(k in nl for k in ["naval", "fleet", "sea", "marine", "submarine"]):
            return "Naval"
        if any(k in nl for k in ["air force", "aviation", "aerospace", "fighter", "bomber"]):
            return "Air Force"
        if any(k in nl for k in ["air defense", "anti-aircraft", "missile", "radar"]):
            return "Air Defense"
        if any(k in nl for k in ["special", "commando", "recon", "sof", "spetsnaz"]):
            return "Special Forces"
        if any(k in nl for k in ["border", "customs", "guard"]):
            return "Border Guard"
        return "Ground"

    def get_unit(self, unit_id: str) -> Optional[OrbatUnit]:
        """Retrieve unit dossier by ID from local database or cached GeoConfirmed trees."""
        if unit_id in self._local_units:
            return self._local_units[unit_id]

        for tree in self._cached_trees.values():
            if tree.flat_units:
                for u in tree.flat_units:
                    if u.id == unit_id:
                        return u
        return None

    def get_orbat_tree(
        self,
        catalog: Optional[str] = None,
        country: Optional[str] = None,
        branch: Optional[str] = None,
        search: Optional[str] = None
    ) -> OrbatTreeResponse:
        """Fetch or construct hierarchical ORBAT with full GeoConfirmed logos and filters."""
        catalogs = self.get_catalogs()
        target_slug = (catalog or country or "Egypt").lower().strip()

        # Check if requesting local Egypt or Libya
        if target_slug in ["egypt", "libya", "all"]:
            units_pool = list(self._local_units.values())
            if target_slug != "all":
                units_pool = [u for u in units_pool if u.country.lower() == target_slug]

            if branch and branch.lower() != "all":
                units_pool = [u for u in units_pool if u.branch.lower() == branch.lower()]

            if search and search.strip():
                q = search.lower().strip()
                units_pool = [
                    u for u in units_pool
                    if q in u.name_ar.lower()
                    or q in u.name_en.lower()
                    or q in u.hq_location.lower()
                    or any(q in eq.lower() for eq in u.equipment)
                ]

            cloned_map: Dict[str, OrbatUnit] = {}
            for u in units_pool:
                cloned = OrbatUnit(**u.model_dump())
                cloned.sub_units = []
                cloned_map[u.id] = cloned

            roots: List[OrbatUnit] = []
            for u in cloned_map.values():
                if u.parent_id and u.parent_id in cloned_map:
                    cloned_map[u.parent_id].sub_units.append(u)
                else:
                    roots.append(u)

            resp = OrbatTreeResponse(
                country=target_slug.title(),
                total_units=len(units_pool),
                roots=roots,
                flat_units=list(cloned_map.values()),
                catalogs=catalogs,
                active_catalog=target_slug
            )
            self._cached_trees[target_slug] = resp
            return resp

        # Find matching GeoConfirmed catalog
        matched_cat = next((c for c in self.BUILTIN_CATALOGS if c["url_name"].lower() == target_slug or c["code"].lower() == target_slug or c["country"].lower() == target_slug), None)
        if not matched_cat:
            matched_cat = next((c for c in self.BUILTIN_CATALOGS if c["code"] == "Israel"), None)

        node_id = matched_cat["node_id"]
        raw_tree = self.fetch_geoconfirmed_node_data(node_id)
        if not raw_tree:
            # Fallback to local units
            return self.get_orbat_tree(catalog="egypt")

        # Convert GeoConfirmed root tree
        root_unit = self._convert_geoconfirmed_node(raw_tree, matched_cat["country"])

        # Flatten units for indexing and filtering
        flat_list: List[OrbatUnit] = []

        def flatten(u: OrbatUnit):
            flat_list.append(u)
            for ch in u.sub_units:
                flatten(ch)

        flatten(root_unit)

        # Apply search or branch filtering if requested
        if (branch and branch.lower() != "all") or (search and search.strip()):
            q = (search or "").lower().strip()
            b = (branch or "").lower().strip()

            def passes_filter(u: OrbatUnit) -> bool:
                match_branch = (b == "all" or not b or u.branch.lower() == b)
                match_search = (not q or q in u.name_ar.lower() or q in u.name_en.lower() or q in u.hq_location.lower() or any(q in eq.lower() for eq in u.equipment))
                return match_branch and match_search

            def filter_tree(u: OrbatUnit) -> Optional[OrbatUnit]:
                filtered_children = []
                for ch in u.sub_units:
                    f_ch = filter_tree(ch)
                    if f_ch:
                        filtered_children.append(f_ch)
                if passes_filter(u) or filtered_children:
                    cloned = OrbatUnit(**u.model_dump())
                    cloned.sub_units = filtered_children
                    return cloned
                return None

            filtered_root = filter_tree(root_unit)
            roots = [filtered_root] if filtered_root else []
        else:
            roots = [root_unit]

        resp = OrbatTreeResponse(
            country=matched_cat["name"],
            total_units=len(flat_list),
            roots=roots,
            flat_units=flat_list,
            catalogs=catalogs,
            active_catalog=matched_cat["url_name"]
        )
        self._cached_trees[matched_cat["url_name"]] = resp
        return resp
